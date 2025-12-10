# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023-2025 Valory AG
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
from typing import Any, Callable, Dict, Optional, TYPE_CHECKING, cast

from aea.crypto.base import Crypto, LedgerApi
from aea.helpers.logging import setup_logger
from requests.exceptions import ConnectionError as RequestsConnectionError

from autonomy.chain.config import ChainType
from autonomy.chain.exceptions import (
    ChainInteractionError,
    ChainTimeoutError,
    RPCError,
    TxBuildError,
    TxSettleError,
    TxVerifyError,
)


if TYPE_CHECKING:
    from web3.contract import Contract
    from web3.types import EventData, TxReceipt


logger = setup_logger(name="autonomy.tx")
DEFAULT_ON_CHAIN_INTERACT_TIMEOUT = 60.0
DEFAULT_ON_CHAIN_INTERACT_RETRIES = 5
DEFAULT_ON_CHAIN_INTERACT_SLEEP = 3.0
DEFAULT_MISSING_EVENT_EXCEPTION = Exception(
    "Could not verify transaction. Event not found."
)

ERRORS_TO_REPRICE = {
    "feetoolow",
    "is too low for the next block",
    "replacementnotallowed",
    "gas too low",
}

ERRORS_TO_RETRY = ERRORS_TO_REPRICE | {
    "wrong transaction nonce",
    "nonce too low",
    "got empty transaction",
    "alreadyknown",
    "already_exists",
    "already known",
    "oldnonce",
    "replacement transaction underpriced",
    "is contract deployed correctly and chain synced?",
}


def should_retry(error: str) -> bool:
    """Check an error message to check if we should raise an error or retry the tx"""
    error = error.lower()
    for _error in ERRORS_TO_RETRY:
        if _error in error:
            return True
    return False


def should_reprice(error: str) -> bool:
    """Check an error message to check if we should reprice the transaction"""
    error = error.lower()
    for _error in ERRORS_TO_REPRICE:
        if _error in error:
            return True
    return False


def already_known(error: str) -> bool:
    """Check if the transaction is already sent"""
    return "alreadyknown" in error


class TxSettler:  # pylint: disable=too-many-instance-attributes
    """Tx settlement helper"""

    tx_dict: Optional[Dict] = None
    tx_hash: Optional[str] = None
    tx_receipt: Optional["TxReceipt"] = None

    def __init__(
        self,
        ledger_api: LedgerApi,
        crypto: Crypto,
        chain_type: ChainType,
        tx_builder: Callable[[], Dict],
        timeout: Optional[float] = None,
        retries: Optional[int] = None,
        sleep: Optional[float] = None,
    ) -> None:
        """Initialize object."""
        self.chain_type = chain_type
        self.ledger_api = ledger_api
        self.crypto = crypto
        self.tx_builder = tx_builder
        self.timeout = timeout or DEFAULT_ON_CHAIN_INTERACT_TIMEOUT
        self.retries = retries or DEFAULT_ON_CHAIN_INTERACT_RETRIES
        self.sleep = sleep or DEFAULT_ON_CHAIN_INTERACT_SLEEP

    def _get_preferred_gas_price_strategy(self, tx_dict: dict) -> str | None:
        """Get the preferred gas price strategy based on tx_dict fields."""
        if "maxFeePerGas" in tx_dict and "maxPriorityFeePerGas" in tx_dict:
            return "eip1559"

        if "gasPrice" in tx_dict:
            return "gas_station"

        return None

    def _reprice(self, tx_dict: Dict) -> Optional[Dict]:
        """Reprice transaction."""
        gas_price_strategy = self._get_preferred_gas_price_strategy(tx_dict)
        if gas_price_strategy == "eip1559":
            old_price = {
                "maxFeePerGas": tx_dict["maxFeePerGas"],
                "maxPriorityFeePerGas": tx_dict["maxPriorityFeePerGas"],
            }
        elif gas_price_strategy == "gas_station":
            old_price = {"gasPrice": tx_dict["gasPrice"]}
        else:
            # This means something went wrong when building the transaction
            # returning a None value to the main loop will tell the main loop
            # to rebuild the transaction
            return None

        tx_dict.update(
            self.ledger_api.try_get_gas_pricing(
                gas_price_strategy=gas_price_strategy,
                old_price=old_price,
            )
        )
        return tx_dict

    def transact(self, dry_run: bool = False) -> "TxSettler":
        """Make a transaction and return a receipt"""
        retries = 0
        deadline = datetime.now().timestamp() + self.timeout
        while retries < self.retries and deadline >= datetime.now().timestamp():
            retries += 1
            try:
                self.tx_dict = self.tx_dict or self.tx_builder()
                if self.tx_dict is None:
                    raise TxBuildError("Got empty transaction")

                if dry_run:  # Return with only the transaction dict on dry-run
                    return self

                self.tx_dict.update(
                    self.ledger_api.try_get_gas_pricing(
                        gas_price_strategy=self._get_preferred_gas_price_strategy(
                            self.tx_dict
                        ),
                    )
                )
                self.tx_dict = self.ledger_api.update_with_gas_estimate(
                    {
                        **self.tx_dict,
                        "gas": self.tx_dict.get("gas", 0),
                    }
                )
                tx_signed = self.crypto.sign_transaction(transaction=self.tx_dict)
                self.tx_hash = self.ledger_api.send_signed_transaction(
                    tx_signed=tx_signed,
                    raise_on_try=True,
                )
                return self
            except RequestsConnectionError as e:
                raise RPCError("Cannot connect to the given RPC") from e
            except Exception as e:  # pylint: disable=broad-except
                error = str(e)
                if not should_retry(error):
                    raise ChainInteractionError(error) from e

                if already_known(error):
                    logger.warning(
                        "Transaction already known, returning with its tx_hash set."
                    )
                    return self

                if should_reprice(error):
                    logger.warning(f"Low gas error: {e}; Repricing the transaction...")
                    self.tx_hash = None
                    self.tx_dict = self._reprice(self.tx_dict or {})  # type: ignore
                    continue

                self.tx_dict = None
                self.tx_hash = None
                logger.error(
                    f"Unexpected error occured when interacting with chain: {e}; "
                    f"will retry in {self.sleep}..."
                )
                time.sleep(self.sleep)

        raise ChainTimeoutError(
            f"Failed to send transaction after {self.retries} retries"
        )

    def settle(self) -> "TxSettler":
        """Wait for the tx to be mined."""
        if self.tx_hash is None:
            raise TxSettleError("Cannot settle the transaction before it is sent.")

        self.tx_receipt = self.ledger_api.api.eth.wait_for_transaction_receipt(
            transaction_hash=cast(str, self.tx_hash),
            timeout=self.timeout,
            poll_latency=self.sleep,
        )
        rpc_sync_check_deadline = datetime.now().timestamp() + self.timeout
        retries = 0
        while self.ledger_api.api.eth.block_number < self.tx_receipt.blockNumber:
            logger.warning(
                f"RPC state not synced with block {self.tx_receipt.blockNumber}. "
                f"Retrying in {self.sleep} seconds..."
            )
            time.sleep(self.sleep)
            retries += 1

            if retries > self.retries:
                raise ChainTimeoutError(
                    f"RPC node not synced with block {self.tx_receipt.blockNumber} "
                    f"after {self.retries} retries."
                )

            if datetime.now().timestamp() >= rpc_sync_check_deadline:
                raise ChainTimeoutError(
                    f"RPC node not synced with block {self.tx_receipt.blockNumber} "
                    f"after {self.timeout} seconds."
                )

        return self

    def get_events(
        self,
        contract: "Contract",
        event_name: str,
    ) -> tuple["EventData", ...]:
        """Get events from the tx receipt."""
        if self.tx_receipt is None:
            raise TxVerifyError("Cannot get events before the transaction is settled.")

        Event = getattr(contract.events, event_name, None)
        if Event is None:
            raise TxVerifyError(f"Contract has no event with name '{event_name}'")

        return cast(tuple["EventData", ...], Event().process_receipt(self.tx_receipt))

    def verify_events(
        self,
        contract: "Contract",
        event_name: str,
        expected_event_arg_name: str,
        expected_event_arg_value: Any,
    ) -> "TxSettler":
        """Verify that an event is in the tx receipt."""
        events = self.get_events(contract, event_name)

        for event in events:
            if (
                event.get("args", {}).get(expected_event_arg_name, None)
                == expected_event_arg_value
            ):
                return self

        raise TxVerifyError(
            f"Could not find event '{event_name}' with argument '{expected_event_arg_name}: "
            f"{expected_event_arg_value}' in the tx with hash {self.tx_hash}"
        )
