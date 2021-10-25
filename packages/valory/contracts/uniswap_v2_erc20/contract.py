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


class UniswapV2ERC20Contract(Contract):
    """The Uniswap V2 ERC-20 contract."""

    @classmethod
    def approve(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        owner_address: str,
        spender_address: str,
        value: int,
    ) -> Optional[JSONLike]:
        """Set the allowance."""
        contract = cls.get_instance(ledger_api, contract_address)
        tx = contract.functions.approve(spender_address, value)
        tx = cls._build_transaction(ledger_api, owner_address, tx)
        return tx

    @classmethod
    def transfer(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        from_address: str,
        to_address: str,
        value: int,
    ) -> Optional[JSONLike]:
        """Transfer funds from from_address to to_address."""
        contract = cls.get_instance(ledger_api, contract_address)
        tx = contract.functions.transfer(to_address, value)
        tx = cls._build_transaction(ledger_api, from_address, tx)
        return tx

    @classmethod
    def transfer_from(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        from_address: str,
        to_address: str,
        value: int,
    ) -> Optional[JSONLike]:
        """(Third-party) transfer funds from from_address to to_address."""
        contract = cls.get_instance(ledger_api, contract_address)
        tx = contract.functions.transferFrom(from_address, to_address, value)
        tx = cls._build_transaction(ledger_api, from_address, tx)
        return tx

    @classmethod
    def permit(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        owner_address: str,
        spender_address: str,
        value: int,
        deadline: int,
        v: int,
        r: bytes,
        s: bytes,
    ) -> Optional[JSONLike]:
        """Sets the allowance for a spender where approval is granted via a signature."""
        contract = cls.get_instance(ledger_api, contract_address)
        tx = contract.functions.permit(
            owner_address, spender_address, value, deadline, v, r, s
        )
        tx = cls._build_transaction(ledger_api, owner_address, tx)
        return tx

    @classmethod
    def allowance(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        owner_address: str,
        spender_address: str,
    ) -> Optional[JSONLike]:
        """Gets the allowance for a spender."""
        contract = cls.get_instance(ledger_api, contract_address)
        tx = contract.functions.allowance(
            owner_address, spender_address
        ).buildTransaction()
        tx = ledger_api.update_with_gas_estimate(tx)

        return tx

    @classmethod
    def balance_of(
        cls, ledger_api: LedgerApi, contract_address: str, owner_address: str
    ) -> Optional[JSONLike]:
        """Gets an account's balance."""
        contract = cls.get_instance(ledger_api, contract_address)
        tx = contract.functions.balanceOf(owner_address).buildTransaction()
        tx = ledger_api.update_with_gas_estimate(tx)

        return tx

    @classmethod
    def _build_transaction(
        cls, ledger_api: LedgerApi, owner_address: str, tx: Any, gas: int = 300000
    ) -> Optional[JSONLike]:
        """Set the allowance."""
        nonce = ledger_api.api.eth.getTransactionCount(owner_address)
        tx = tx.buildTransaction(
            {
                "gas": gas,
                "gasPrice": ledger_api.api.toWei("50", "gwei"),
                "nonce": nonce,
            }
        )
        tx = ledger_api.update_with_gas_estimate(tx)

        return tx
