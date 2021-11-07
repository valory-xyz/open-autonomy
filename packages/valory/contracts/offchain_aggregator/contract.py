# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021 Valory AG
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

"""This module contains the class to connect to an Offchain Aggregator contract."""
import logging
from typing import Any, Optional

from aea.common import JSONLike
from aea.configurations.base import PublicId
from aea.contracts.base import Contract
from aea.crypto.base import LedgerApi
from eth_abi import encode_abi


PUBLIC_ID = PublicId.from_str("valory/offchain_aggregator:0.1.0")

_logger = logging.getLogger(
    f"aea.packages.{PUBLIC_ID.author}.contracts.{PUBLIC_ID.name}.contract"
)


class OffchainAggregatorContract(Contract):
    """The Offchain Aggregator contract."""

    contract_id = PUBLIC_ID

    @classmethod
    def get_raw_transaction(
        cls, ledger_api: LedgerApi, contract_address: str, **kwargs: Any
    ) -> Optional[JSONLike]:
        """Get the Safe transaction."""
        raise NotImplementedError

    @classmethod
    def get_raw_message(
        cls, ledger_api: LedgerApi, contract_address: str, **kwargs: Any
    ) -> Optional[bytes]:
        """Get raw message."""
        raise NotImplementedError

    @classmethod
    def get_state(
        cls, ledger_api: LedgerApi, contract_address: str, **kwargs: Any
    ) -> Optional[JSONLike]:
        """Get state."""
        raise NotImplementedError

    @classmethod
    def get_deploy_transaction(
        cls, ledger_api: LedgerApi, deployer_address: str, **kwargs: Any
    ) -> Optional[JSONLike]:
        """
        Get deploy transaction.

        :param ledger_api: ledger API object.
        :param deployer_address: the deployer address.
        :param kwargs: the keyword arguments.
        :return: an optional JSON-like object.
        """
        return super().get_deploy_transaction(ledger_api, deployer_address, **kwargs)

    @classmethod
    def get_transmit_data(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        epoch_: int,
        round_: int,
        amount_: int,
    ) -> JSONLike:
        """
        Handler method for the 'get_active_project' requests.

        Implement this method in the sub class if you want
        to handle the contract requests manually.

        :param ledger_api: the ledger apis.
        :param contract_address: the contract address.
        :param epoch_: the epoch
        :param round_: the round
        :param amount_: the amount
        :return: the tx  # noqa: DAR202
        """
        instance = cls.get_instance(ledger_api, contract_address)
        report = cls.get_report(epoch_, round_, amount_)
        data = instance.encodeABI(fn_name="transmit", args=[report])
        return {"data": data}

    @classmethod
    def get_report(
        cls,
        epoch_: int,
        round_: int,
        amount_: int,
    ) -> bytes:
        """
        Get report serialised.

        :param epoch_: the epoch
        :param round_: the round
        :param amount_: the amount
        :return: the tx  # noqa: DAR202
        """
        left_pad = "0" * 22
        TEMP_CONFIG = 0
        config_digest = TEMP_CONFIG.to_bytes(16, "big").hex()
        epoch_hex = epoch_.to_bytes(4, "big").hex()
        round_hex = round_.to_bytes(1, "big").hex()
        raw_report = left_pad + config_digest + epoch_hex + round_hex
        report = encode_abi(["bytes32", "int192"], [bytes.fromhex(raw_report), amount_])
        return report

    @classmethod
    def transmit(  # pylint: disable=too-many-arguments
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        sender_address: str,
        gas: int,
        gas_price: int,
        epoch_: int,
        round_: int,
        amount_: int,
    ) -> Optional[JSONLike]:
        """
        Handler method for the 'get_active_project' requests.

        Implement this method in the sub class if you want
        to handle the contract requests manually.

        :param ledger_api: the ledger apis.
        :param contract_address: the contract address.
        :param sender_address: the sender address.
        :param gas: the max gas used.
        :param gas_price: the gas price.
        :param epoch_: the epoch
        :param round_: the round
        :param amount_: the amount
        :return: the tx  # noqa: DAR202
        """
        report = cls.get_report(epoch_, round_, amount_)
        return cls._prepare_tx(
            ledger_api,
            contract_address,
            sender_address,
            gas,
            gas_price,
            "transmit",
            report,
        )

    @classmethod
    def _prepare_tx(  # pylint: disable=too-many-arguments
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        sender_address: str,
        gas: int,
        gas_price: int,
        method_name: str,
        *method_args: Any,
    ) -> Optional[JSONLike]:
        """Prepare tx method."""
        contract = cls.get_instance(ledger_api, contract_address)
        method = getattr(contract.functions, method_name)
        tx = method(*method_args)
        tx = cls._build_transaction(ledger_api, sender_address, tx, gas, gas_price)
        return tx

    @classmethod
    def _build_transaction(  # pylint: disable=too-many-arguments
        cls,
        ledger_api: LedgerApi,
        sender_address: str,
        tx: Any,
        gas: int,
        gas_price: int,
        eth_value: int = 0,
    ) -> Optional[JSONLike]:
        """Set the allowance."""
        nonce = ledger_api.api.eth.getTransactionCount(sender_address)
        tx = tx.buildTransaction(
            {
                "gas": gas,
                "gasPrice": gas_price,
                "nonce": nonce,
                "value": eth_value,
            }
        )
        return tx
