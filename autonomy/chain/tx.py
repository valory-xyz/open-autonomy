# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023-2024 Valory AG
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

"""Tx settlement helper."""

import time
from datetime import datetime
from typing import Callable, Dict, Optional, cast

from aea.configurations.data_types import PublicId
from aea.crypto.base import Crypto, LedgerApi
from requests.exceptions import ConnectionError as RequestsConnectionError

from autonomy.chain.base import registry_contracts
from autonomy.chain.config import ChainType, ContractConfigs
from autonomy.chain.exceptions import (
    ChainInteractionError,
    ChainTimeoutError,
    RPCError,
    TxBuildError,
)


DEFAULT_ON_CHAIN_INTERACT_TIMEOUT = 60.0
DEFAULT_ON_CHAIN_INTERACT_RETRIES = 5.0
DEFAULT_ON_CHAIN_INTERACT_SLEEP = 3.0

ERRORS_TO_RETRY = (
    "FeeTooLow",
    "wrong transaction nonce",
    "INTERNAL_ERROR: nonce too low",
    "Got empty transaction",
    "AlreadyKnown",
    "ALREADY_EXISTS",
    "already known",
    "ReplacementNotAllowed",
    "OldNonce",
)


def should_rebuild(error: str) -> bool:
    """Check if we should rebuild the transaction."""
    for _error in ("wrong transaction nonce", "OldNonce"):
        if _error in error:
            return True
    return False


def should_retry(error: str) -> bool:
    """Check an error message to check if we should raise an error or retry the tx"""
    if "Transaction with hash" in error and "not found" in error:
        return True
    for _error in ERRORS_TO_RETRY:
        if _error in error:
            return True
    return False


def should_reprice(error: str) -> bool:
    """Check an error message to check if we should reprice the transaction"""
    return "FeeTooLow" in error or "ReplacementNotAllowed" in error


class TxSettler:
    """Tx settlement helper"""

    tx: Optional[Dict]

    def __init__(  # pylint: disable=too-many-arguments
        self,
        ledger_api: LedgerApi,
        crypto: Crypto,
        chain_type: ChainType,
        timeout: Optional[float] = None,
        retries: Optional[int] = None,
        sleep: Optional[float] = None,
    ) -> None:
        """Initialize object."""
        self.chain_type = chain_type
        self.ledger_api = ledger_api
        self.crypto = crypto
        self.tx = None
        self.timeout = timeout or DEFAULT_ON_CHAIN_INTERACT_TIMEOUT
        self.retries = retries or DEFAULT_ON_CHAIN_INTERACT_RETRIES
        self.sleep = sleep or DEFAULT_ON_CHAIN_INTERACT_SLEEP

    def build(
        self,
        method: Callable[[], Dict],
        contract: str,
        kwargs: Dict,
    ) -> Dict:
        """Build transaction."""
        return method(  # type: ignore
            ledger_api=self.ledger_api,
            contract_address=ContractConfigs.get(name=contract).contracts[
                self.chain_type
            ],
            raise_on_try=True,
            **kwargs,
        )

    def _reprice(self, tx_dict: Dict) -> Optional[Dict]:
        """Reprice transaction."""
        if "maxFeePerGas" not in tx_dict or "maxPriorityFeePerGas" not in tx_dict:
            # This means something went wrong when building the transaction
            # returning a None value to the main loop will tell the main loop
            # to rebuild the transaction
            return None

        old_price = {
            "maxFeePerGas": tx_dict[  # pylint: disable=unsubscriptable-object
                "maxFeePerGas"
            ],
            "maxPriorityFeePerGas": tx_dict[  # pylint: disable=unsubscriptable-object
                "maxPriorityFeePerGas"
            ],
        }
        tx_dict.update(
            self.ledger_api.try_get_gas_pricing(
                old_price=old_price,
            )
        )
        return tx_dict

    @staticmethod
    def _already_known(error: str) -> bool:
        """Check if the transaction is alreade sent"""
        return "AlreadyKnown" in error

    def transact(
        self,
        method: Callable[[], Dict],
        contract: str,
        kwargs: Dict,
        dry_run: bool = False,
    ) -> Dict:
        """Make a transaction and return a receipt"""
        retries = 0
        tx_dict = None
        tx_digest = None
        already_known = False
        deadline = datetime.now().timestamp() + self.timeout
        while retries < self.retries and deadline >= datetime.now().timestamp():
            retries += 1
            try:
                if not already_known:
                    tx_dict = tx_dict or self.build(
                        method=method,
                        contract=contract,
                        kwargs=kwargs,
                    )
                    if tx_dict is None:
                        raise TxBuildError("Got empty transaction")

                    # Return transaction dict on dry-run
                    if dry_run:
                        return tx_dict

                    tx_signed = self.crypto.sign_transaction(transaction=tx_dict)
                    tx_digest = self.ledger_api.send_signed_transaction(
                        tx_signed=tx_signed,
                        raise_on_try=True,
                    )
                tx_receipt = self.ledger_api.api.eth.get_transaction_receipt(
                    cast(str, tx_digest)
                )
                if tx_receipt is not None:
                    return tx_receipt
            except RequestsConnectionError as e:
                raise RPCError("Cannot connect to the given RPC") from e
            except Exception as e:  # pylint: disable=broad-except
                error = str(e)
                if self._already_known(error):
                    already_known = True
                    continue  # pragma: nocover
                if not should_retry(error):
                    raise ChainInteractionError(error) from e
                if should_reprice(error):
                    print(f"Low gas error: {e}; Repricing the transaction...")
                    tx_dict = self._reprice(cast(Dict, tx_dict))
                    continue  # pragma: nocover
                if "Transaction with hash" in error and "not found" in error:
                    already_known = True
                    print(
                        f"Error getting transaction receipt: {e}; "
                        f"Will retry in {self.sleep}..."
                    )
                    time.sleep(self.sleep)
                    continue  # pragma: nocover

                if should_rebuild(error):
                    tx_dict = None

                tx_digest = None
                already_known = False
                print(
                    f"Error occured when interacting with chain: {e}; "
                    f"will retry in {self.sleep}..."
                )
                time.sleep(self.sleep)
        raise ChainTimeoutError("Timed out when waiting for transaction to go through")

    def process(
        self,
        event: str,
        receipt: Dict,
        contract: PublicId,
    ) -> Dict:
        """Process tx receipt."""
        return registry_contracts.get_contract(contract).get_events(
            ledger_api=self.ledger_api,
            contract_address=ContractConfigs.get(contract.name).contracts[
                self.chain_type
            ],
            receipt=receipt,
            event=event,
        )
