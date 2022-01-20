# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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

"""This module contains the class to connect to a ERC20 contract."""
import logging
from typing import Any, Optional, cast

from aea.common import JSONLike
from aea.configurations.base import PublicId
from aea.contracts.base import Contract
from aea_ledger_ethereum import EthereumApi
from hexbytes import HexBytes
from web3.exceptions import TransactionNotFound


PUBLIC_ID = PublicId.from_str("valory/uniswap_v2_erc20:0.1.0")

_logger = logging.getLogger(
    f"aea.packages.{PUBLIC_ID.author}.contracts.{PUBLIC_ID.name}.contract"
)


def rebuild_receipt(tx_receipt: JSONLike) -> JSONLike:
    """Convert all tx receipt's event topics to HexBytes"""
    for i in range(len(tx_receipt["logs"])):  # type: ignore
        tx_receipt["logs"][i]["topics"] = [HexBytes(topic) for topic in tx_receipt["logs"][i]["topics"]]  # type: ignore
    return tx_receipt


def snake_to_camel(string: str) -> str:
    """Convert snake_case to camelCase"""

    if "_" in string:
        camel_case = string.split("_")
        for i in range(1, len(camel_case)):
            camel_case[i] = camel_case[i][0].upper() + camel_case[i][1:]
        string = ("").join(camel_case)
    return string


# pylint: disable=too-many-arguments,invalid-name
class UniswapV2ERC20Contract(Contract):
    """The Uniswap V2 ERC-20 contract."""

    contract_id = PUBLIC_ID

    @classmethod
    def get_method_data(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        method_name: str,
        **kwargs: Any,
    ) -> JSONLike:
        """
        Get a contract call encoded data.

        :param ledger_api: the ledger apis.
        :param contract_address: the contract address.
        :param method_name: the contract method name
        :param kwargs: the contract method args
        :return: the tx  # noqa: DAR202
        """
        instance = cls.get_instance(ledger_api, contract_address)

        # Ensure the method name and its arguments are camel-cased
        # to match the contract interface
        method_name = snake_to_camel(method_name)
        kwargs = {snake_to_camel(k): v for k, v in kwargs.items()}

        # Get an ordered argument list from the method's abi
        method = instance.get_function_by_name(method_name)
        input_names = [i["name"] for i in method.abi["inputs"]]
        args = [kwargs[i] for i in input_names]

        # Encode and return the contract call
        data = instance.encodeABI(fn_name=method_name, args=args)
        return {"data": bytes.fromhex(data[2:])}  # type: ignore

    @classmethod
    def approve(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        sender_address: str,
        spender_address: str,
        value: int,
        **kwargs: int,
    ) -> Optional[JSONLike]:
        """Set the allowance for spender_address on behalf of sender_address."""
        return cls._prepare_tx(
            ledger_api,
            contract_address,
            sender_address,
            "approve",
            spender_address,
            value,
            **kwargs,
        )

    @classmethod
    def transfer(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        sender_address: str,
        to_address: str,
        value: int,
        **kwargs: int,
    ) -> Optional[JSONLike]:
        """Transfer funds from sender_address to to_address."""
        return cls._prepare_tx(
            ledger_api,
            contract_address,
            sender_address,
            "transfer",
            to_address,
            value,
            **kwargs,
        )

    @classmethod
    def transfer_from(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        sender_address: str,
        from_address: str,
        to_address: str,
        value: int,
        **kwargs: int,
    ) -> Optional[JSONLike]:
        """As sender_address (third-party) transfer funds from from_address to to_address."""
        return cls._prepare_tx(
            ledger_api,
            contract_address,
            sender_address,
            "transferFrom",
            from_address,
            to_address,
            value,
            **kwargs,
        )

    @classmethod
    def permit(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        sender_address: str,
        owner_address: str,
        spender_address: str,
        value: int,
        deadline: int,
        v: int,
        r: bytes,
        s: bytes,
        **kwargs: int,
    ) -> Optional[JSONLike]:
        """Sets the allowance for a spender on behalf of owner where approval is granted via a signature. Sender can differ from owner."""
        return cls._prepare_tx(
            ledger_api,
            contract_address,
            sender_address,
            "permit",
            owner_address,
            spender_address,
            value,
            deadline,
            v,
            r,
            s,
            **kwargs,
        )

    @classmethod
    def allowance(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        owner_address: str,
        spender_address: str,
    ) -> Optional[JSONLike]:
        """Gets the allowance for a spender."""
        return cls._call(
            ledger_api,
            contract_address,
            "allowance",
            owner_address,
            spender_address,
        )

    @classmethod
    def balance_of(
        cls, ledger_api: EthereumApi, contract_address: str, owner_address: str
    ) -> Optional[JSONLike]:
        """Gets an account's balance."""
        return cls._call(
            ledger_api,
            contract_address,
            "balanceOf",
            owner_address,
        )

    @classmethod
    def _call(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        method_name: str,
        *method_args: Any,
    ) -> Optional[JSONLike]:
        """Call method."""
        contract = cls.get_instance(ledger_api, contract_address)
        method = getattr(contract.functions, method_name)
        result = method(*method_args).call()
        return result

    @classmethod
    def _prepare_tx(  # pylint: disable=too-many-arguments
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        sender_address: str,
        method_name: str,
        *method_args: Any,
        eth_value: int = 0,
        gas: Optional[int] = None,
        gas_price: Optional[int] = None,
        max_fee_per_gas: Optional[int] = None,
        max_priority_fee_per_gas: Optional[int] = None,
    ) -> Optional[JSONLike]:
        """Prepare tx method."""
        contract = cls.get_instance(ledger_api, contract_address)
        method = getattr(contract.functions, method_name)
        tx = method(*method_args)
        tx = cls._build_transaction(
            ledger_api,
            sender_address,
            tx,
            eth_value,
            gas,
            gas_price,
            max_fee_per_gas,
            max_priority_fee_per_gas,
        )
        return tx

    @classmethod
    def _build_transaction(  # pylint: disable=too-many-arguments
        cls,
        ledger_api: EthereumApi,
        sender_address: str,
        tx: Any,
        eth_value: int = 0,
        gas: Optional[int] = None,
        gas_price: Optional[int] = None,
        max_fee_per_gas: Optional[int] = None,
        max_priority_fee_per_gas: Optional[int] = None,
    ) -> Optional[JSONLike]:
        """Build transaction method."""
        nonce = ledger_api.api.eth.get_transaction_count(sender_address)
        tx_params = {
            "nonce": nonce,
            "value": eth_value,
        }
        if gas is not None:
            tx_params["gas"] = gas
        if gas_price is not None:
            tx_params["gasPrice"] = gas_price
        if max_fee_per_gas is not None:
            tx_params["maxFeePerGas"] = max_fee_per_gas  # pragma: nocover
        if max_priority_fee_per_gas is not None:
            tx_params[
                "maxPriorityFeePerGas"
            ] = max_priority_fee_per_gas  # pragma: nocover
        if (
            gas_price is None
            and max_fee_per_gas is None
            and max_priority_fee_per_gas is None
        ):
            tx_params.update(ledger_api.try_get_gas_pricing())  # pragma: nocover
        tx = tx.buildTransaction(tx_params)
        return tx

    @classmethod
    def get_tx_transfer_logs(  # pylint: disable=too-many-arguments,too-many-locals
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        tx_hash: str,
        target_address: Optional[str] = None,
    ) -> JSONLike:
        """
        Get all transfer events derived from a transaction.

        :param ledger_api: the ledger API object
        :param contract_address: the contract address
        :param tx_hash: the transaction hash
        :param target_address: optional address to filter tranfer events to just those that affect it
        :return: the verified status
        """
        ledger_api = cast(EthereumApi, ledger_api)
        contract = cls.get_instance(ledger_api, contract_address)

        try:
            tx_receipt = ledger_api.get_transaction_receipt(tx_hash)
            if tx_receipt is None:
                raise ValueError  # pragma: nocover

        except (TransactionNotFound, ValueError):  # pragma: nocover
            return dict(logs=[])

        # Due to serialization, event topics must be converted again to HexBytes or processReceipt will fail
        tx_receipt = rebuild_receipt(tx_receipt)

        transfer_logs = contract.events.Transfer().processReceipt(tx_receipt)

        transfer_logs = [
            {
                "from": log["args"]["from"],
                "to": log["args"]["to"],
                "value": log["args"]["value"],
                "token_address": log["address"],
            }
            for log in transfer_logs
        ]

        if target_address:
            transfer_logs = list(
                filter(
                    lambda log: target_address in (log["from"], log["to"]),  # type: ignore
                    transfer_logs,
                )
            )

        return dict(logs=transfer_logs)

    @classmethod
    def get_tx_transfered_amount(  # pylint: disable=too-many-arguments,too-many-locals
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        tx_hash: str,
        token_address: str,
        source_address: Optional[str] = None,
        destination_address: Optional[str] = None,
    ) -> JSONLike:
        """
        Get the amount of a token transferred as a result of a transaction.

        :param ledger_api: the ledger API object
        :param contract_address: the contract address
        :param tx_hash: the transaction hash
        :param token_address: the token's address
        :param source_address: the source address
        :param destination_address: the destination address
        :return: the incoming amount
        """

        transfer_logs: list = cls.get_tx_transfer_logs(ledger_api, contract_address, tx_hash)["logs"]  # type: ignore

        token_events = list(
            filter(
                lambda log: log["token_address"] == ledger_api.api.toChecksumAddress(token_address),  # type: ignore
                transfer_logs,
            )
        )

        if source_address:
            token_events = list(
                filter(
                    lambda log: log["from"] == ledger_api.api.toChecksumAddress(source_address),  # type: ignore
                    token_events,
                )
            )

        if destination_address:
            token_events = list(
                filter(
                    lambda log: log["to"] == ledger_api.api.toChecksumAddress(destination_address),  # type: ignore
                    token_events,
                )
            )

        amount = 0 if not token_events else sum([event["value"] for event in list(token_events)])  # type: ignore
        return dict(amount=amount)
