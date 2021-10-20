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

from aea.configurations.base import PublicId
from aea.contracts.base import Contract
from aea.common import JSONLike
from typing import Optional, cast
from aea_ledger_ethereum import EthereumApi
from aea.crypto.base import LedgerApi
from web3.exceptions import TransactionNotFound


PUBLIC_ID = PublicId.from_str("valory/uniswap_v2_erc20:0.1.0")

_logger = logging.getLogger(
    f"aea.packages.{PUBLIC_ID.author}.contracts.{PUBLIC_ID.name}.contract"
)


class UniswapV2ERC20(Contract):
    """The Uniswap V2 ERC-20 contract."""

    @classmethod
    def approve(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        contract_abi: str,
        owner_address: str,
        spender_address: int,
        value: int,
    ) -> Optional[JSONLike]:
        """Set the allowance."""

        ledger_api = cast(EthereumApi, ledger_api)
        contract = ledger_api.api.eth.contract(address=contract_address, abi=contract_abi)
        tx_hash = contract.functions.approve(spender_address, value).transact({'from': owner_address})

        try:
            tx_receipt = ledger_api.api.eth.wait_for_transaction_receipt(tx_hash)
            if tx_receipt is None:
                raise ValueError
            return dict(success=True, tx_hash=tx_hash, tx_receipt=tx_receipt)
        except (TransactionNotFound, ValueError):
            return dict(success=False, tx_hash=tx_hash)

    @classmethod
    def transfer(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        contract_abi: str,
        from_address: str,
        to_address: str,
        value: int
    ) -> Optional[JSONLike]:
        """Transfer funds from from_address to to_address."""

        ledger_api = cast(EthereumApi, ledger_api)
        contract = ledger_api.api.eth.contract(address=contract_address, abi=contract_abi)
        tx_hash = contract.functions.transfer(to_address, value).transact({'from': from_address})

        try:
            tx_receipt = ledger_api.api.eth.wait_for_transaction_receipt(tx_hash)
            if tx_receipt is None:
                raise ValueError
            return dict(success=True, tx_hash=tx_hash, tx_receipt=tx_receipt)
        except (TransactionNotFound, ValueError):
            return dict(success=False, tx_hash=tx_hash)

    @classmethod
    def transfer_from(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        contract_abi: str,
        from_address: str,
        to_address: str,
        value: int
    ) -> Optional[JSONLike]:
        """(Third-party) transfer funds from from_address to to_address."""

        ledger_api = cast(EthereumApi, ledger_api)
        contract = ledger_api.api.eth.contract(address=contract_address, abi=contract_abi)
        tx_hash = contract.functions.transferFrom(from_address, to_address, value).transact({'from': to_address}) # Check this last from

        try:
            tx_receipt = ledger_api.api.eth.wait_for_transaction_receipt(tx_hash)
            if tx_receipt is None:
                raise ValueError
            return dict(success=True, tx_hash=tx_hash, tx_receipt=tx_receipt)
        except (TransactionNotFound, ValueError):
            return dict(success=False, tx_hash=tx_hash)

    @classmethod
    def permit(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        contract_abi: str,
        owner_address: str,
        spender_address: str,
        value: int,
        deadline: int,
        v: int,
        r: bytes,
        s: bytes,
    ) -> Optional[JSONLike]:
        """Modify the allowance mapping using a signed message."""

        ledger_api = cast(EthereumApi, ledger_api)
        contract = ledger_api.api.eth.contract(address=contract_address, abi=contract_abi)

        # Can't find API reference for permit
        # https://web3py.readthedocs.io/en/stable/examples.html#working-with-an-erc20-token-contract

        raise NotImplementedError

        try:
            if tx_receipt is None:
                raise ValueError
            return dict(success=True, tx_hash=tx_hash, tx_receipt=tx_receipt)
        except (TransactionNotFound, ValueError):
            return dict(success=False, tx_hash=tx_hash)