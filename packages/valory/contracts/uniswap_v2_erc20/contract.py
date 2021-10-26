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
        return cls._call(
            ledger_api,
            contract_address,
            "approve",
            owner_address,
            (spender_address, value),
        )

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
        return cls._call(
            ledger_api, contract_address, "transfer", from_address, (to_address, value)
        )

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
        return cls._call(
            ledger_api,
            contract_address,
            "transferFrom",
            from_address,
            (from_address, to_address, value),
        )

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
        return cls._call(
            ledger_api,
            contract_address,
            "permit",
            owner_address,
            (owner_address, spender_address, value, deadline, v, r, s),
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
            None,
            (owner_address, spender_address),
        )

    @classmethod
    def balance_of(
        cls, ledger_api: LedgerApi, contract_address: str, owner_address: str
    ) -> Optional[JSONLike]:
        """Gets an account's balance."""
        return cls._call(
            ledger_api, contract_address, "balanceOf", None, (owner_address,)
        )

    @classmethod
    def _call(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        method_name: str,
        owner_address: str = None,
        *method_args: tuple,
    ) -> Optional[JSONLike]:
        """Call method."""
        contract = cls.get_instance(ledger_api, contract_address)
        method = getattr(contract.functions, method_name)
        tx = method(method_args)

        if owner_address:
            return cls._build_transaction(ledger_api, owner_address, tx)
        return tx.buildTransaction()

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
