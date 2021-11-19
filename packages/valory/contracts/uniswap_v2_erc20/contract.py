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

"""This module contains the class to connect to a ERC20 contract."""
import logging
from typing import Any, Optional

from aea.common import JSONLike
from aea.configurations.base import PublicId
from aea.contracts.base import Contract
from aea.crypto.base import LedgerApi


PUBLIC_ID = PublicId.from_str("valory/uniswap_v2_erc20:0.1.0")

_logger = logging.getLogger(
    f"aea.packages.{PUBLIC_ID.author}.contracts.{PUBLIC_ID.name}.contract"
)


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

    @classmethod
    def get_method_data(
        cls,
        ledger_api: LedgerApi,
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
        ledger_api: LedgerApi,
        contract_address: str,
        sender_address: str,
        gas: int,
        gas_price: int,
        spender_address: str,
        value: int,
    ) -> Optional[JSONLike]:
        """Set the allowance for spender_address on behalf of sender_address."""
        return cls._prepare_tx(
            ledger_api,
            contract_address,
            sender_address,
            gas,
            gas_price,
            "approve",
            spender_address,
            value,
        )

    @classmethod
    def transfer(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        sender_address: str,
        gas: int,
        gas_price: int,
        to_address: str,
        value: int,
    ) -> Optional[JSONLike]:
        """Transfer funds from sender_address to to_address."""
        return cls._prepare_tx(
            ledger_api,
            contract_address,
            sender_address,
            gas,
            gas_price,
            "transfer",
            to_address,
            value,
        )

    @classmethod
    def transfer_from(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        sender_address: str,
        gas: int,
        gas_price: int,
        from_address: str,
        to_address: str,
        value: int,
    ) -> Optional[JSONLike]:
        """As sender_address (third-party) transfer funds from from_address to to_address."""
        return cls._prepare_tx(
            ledger_api,
            contract_address,
            sender_address,
            gas,
            gas_price,
            "transferFrom",
            from_address,
            to_address,
            value,
        )

    @classmethod
    def permit(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        sender_address: str,
        gas: int,
        gas_price: int,
        owner_address: str,
        spender_address: str,
        value: int,
        deadline: int,
        v: int,
        r: bytes,
        s: bytes,
    ) -> Optional[JSONLike]:
        """Sets the allowance for a spender on behalf of owner where approval is granted via a signature. Sender can differ from owner."""
        return cls._prepare_tx(
            ledger_api,
            contract_address,
            sender_address,
            gas,
            gas_price,
            "permit",
            owner_address,
            spender_address,
            value,
            deadline,
            v,
            r,
            s,
        )

    @classmethod
    def allowance(
        cls,
        ledger_api: LedgerApi,
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
        cls, ledger_api: LedgerApi, contract_address: str, owner_address: str
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
        ledger_api: LedgerApi,
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
    def _prepare_tx(
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
    def _build_transaction(
        cls,
        ledger_api: LedgerApi,
        sender_address: str,
        tx: Any,
        gas: int,
        gas_price: int,
        eth_value: int = 0,
    ) -> Optional[JSONLike]:
        """Build transaction method."""
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
