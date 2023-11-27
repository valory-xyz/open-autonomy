# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023 Valory AG
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
from typing import Any, Callable, Dict, Optional

from aea.configurations.data_types import PublicId
from aea.crypto.base import Crypto, LedgerApi
from requests.exceptions import ConnectionError as RequestsConnectionError

from autonomy.chain.base import registry_contracts
from autonomy.chain.config import ChainType, ContractConfigs
from autonomy.chain.exceptions import ChainTimeoutError, RPCError, TxBuildError


DEFAULT_ON_CHAIN_INTERACT_TIMEOUT = 60.0
DEFAULT_ON_CHAIN_INTERACT_RETRIES = 5.0
DEFAULT_ON_CHAIN_INTERACT_SLEEP = 3.0

ERRORS_TO_RETRY = (
    "FeeTooLow",
    "wrong transaction nonce",
    "INTERNAL_ERROR: nonce too low",
)


def should_retry(error: str) -> bool:
    """Check an error message to check if we should raise an error or retry the tx"""
    for _error in ERRORS_TO_RETRY:
        if _error in error:
            return True
    return False


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

    def wait(
        self, waitable: Callable, w3_error_handler: Callable[[Exception], Any]
    ) -> Any:
        """Wait for a chain interaction."""
        retries = 0
        deadline = datetime.now().timestamp() + self.timeout
        while retries < self.retries and deadline >= datetime.now().timestamp():
            try:
                result = waitable()
                if result is not None:
                    return result
                time.sleep(self.sleep)
            except RequestsConnectionError as e:
                raise RPCError("Cannot connect to the given RPC") from e
            except Exception as e:  # pylint: disable=broad-except
                w3_error_handler(e)
            retries += 1
        return None

    def build(
        self,
        method: Callable[[], Dict],
        contract: str,
        kwargs: Dict,
    ) -> Dict:
        """Build transaction."""

        def _waitable() -> Dict:
            return method(  # type: ignore
                ledger_api=self.ledger_api,
                contract_address=ContractConfigs.get(name=contract).contracts[
                    self.chain_type
                ],
                raise_on_try=True,
                **kwargs,
            )

        def _w3_error_handler(e: Exception) -> None:
            if not should_retry(str(e)):
                raise TxBuildError(f"Error building transaction: {e}") from e
            print(
                f"Error occured when interacting with chain: {e}; "
                f"will retry in {self.sleep}..."
            )
            time.sleep(self.sleep)

        tx = self.wait(
            waitable=_waitable,
            w3_error_handler=_w3_error_handler,
        )
        if tx is not None:
            return tx
        raise ChainTimeoutError("Timed out when building the transaction")

    def transact(self, tx: Dict) -> Dict:
        """Make a transaction and return a receipt"""
        tx_signed = self.crypto.sign_transaction(transaction=tx)
        tx_digest = self.ledger_api.send_signed_transaction(tx_signed=tx_signed)
        receipt = self.wait(
            waitable=lambda: self.ledger_api.api.eth.get_transaction_receipt(tx_digest),
            w3_error_handler=lambda e: None,
        )
        if receipt is not None:
            return receipt
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
