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
from typing import Any, List, Optional, cast

from aea.common import JSONLike
from aea.configurations.base import PublicId
from aea.contracts.base import Contract
from aea_ledger_ethereum import EthereumApi


PUBLIC_ID = PublicId.from_str("valory/uniswap_v2_erc20:0.1.0")

_logger = logging.getLogger(
    f"aea.packages.{PUBLIC_ID.author}.contracts.{PUBLIC_ID.name}.contract"
)


# pylint: disable=too-many-arguments,invalid-name
class UniswapV2ERC20Contract(Contract):
    """The Uniswap V2 ERC-20 contract."""

    contract_id = PUBLIC_ID

    @classmethod
    def approve(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        spender_address: str,
        value: int,
        **kwargs: Any,
    ) -> Optional[JSONLike]:
        """Set the allowance for spender_address on behalf of sender_address."""
        contract_instance = cls.get_instance(ledger_api, contract_address)

        return ledger_api.build_transaction(
            contract_instance,
            "approve",
            method_args=dict(
                spender=spender_address,
                value=value,
            ),
            tx_args=kwargs,
        )

    @classmethod
    def transfer(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        to_address: str,
        value: int,
        **tx_args: Any,
    ) -> Optional[JSONLike]:
        """Transfer funds from sender_address to to_address."""
        contract_instance = cls.get_instance(ledger_api, contract_address)

        return ledger_api.build_transaction(
            contract_instance,
            "transfer",
            method_args={
                "to": to_address,
                "value": value,
            },
            tx_args=tx_args,
        )

    @classmethod
    def transfer_from(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        from_address: str,
        to_address: str,
        value: int,
        **tx_args: Any,
    ) -> Optional[JSONLike]:
        """As sender_address (third-party) transfer funds from from_address to to_address."""
        contract_instance = cls.get_instance(ledger_api, contract_address)

        return ledger_api.build_transaction(
            contract_instance,
            "transferFrom",
            method_args={
                "from": from_address,
                "to": to_address,
                "value": value,
            },
            tx_args=tx_args,
        )

    @classmethod
    def permit(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        owner_address: str,
        spender_address: str,
        value: int,
        deadline: int,
        v: int,
        r: bytes,
        s: bytes,
        **kwargs: Any,
    ) -> Optional[JSONLike]:
        """Sets the allowance for a spender on behalf of owner where approval is granted via a signature. Sender can differ from owner."""
        contract_instance = cls.get_instance(ledger_api, contract_address)

        return ledger_api.build_transaction(
            contract_instance,
            "permit",
            method_args=dict(
                owner=owner_address,
                spender=spender_address,
                value=value,
                deadline=deadline,
                v=v,
                r=r,
                s=s,
            ),
            tx_args=kwargs,
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
        contract_instance = cls.get_instance(ledger_api, contract_address)

        return ledger_api.contract_method_call(
            contract_instance=contract_instance,
            method_name="allowance",
            owner=owner_address,
            spender=spender_address,
        )

    @classmethod
    def balance_of(
        cls, ledger_api: EthereumApi, contract_address: str, owner_address: str
    ) -> Optional[JSONLike]:
        """Gets an account's balance."""
        contract_instance = cls.get_instance(ledger_api, contract_address)

        return ledger_api.contract_method_call(
            contract_instance=contract_instance,
            method_name="balanceOf",
            owner=owner_address,
        )

    @classmethod
    def get_transaction_transfer_logs(  # type: ignore  # pylint: disable=too-many-arguments,too-many-locals,unused-argument,arguments-differ
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        tx_hash: str,
        target_address: Optional[str] = None,
    ) -> JSONLike:
        """
        Get all transfer events derived from a transaction.

        :param ledger_api: the ledger API object
        :param contract_address: the address of the contract
        :param tx_hash: the transaction hash
        :param target_address: optional address to filter tranfer events to just those that affect it
        :return: the verified status
        """
        transfer_logs_data: Optional[JSONLike] = super(
            UniswapV2ERC20Contract, cls
        ).get_transaction_transfer_logs(  # type: ignore
            ledger_api,
            tx_hash,
            target_address,
        )
        transfer_logs: List = []

        if transfer_logs_data:

            transfer_logs = cast(
                List,
                transfer_logs_data["logs"],
            )

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
