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

"""This module contains the class to connect to a Uniswap V2 Router02 contract."""
import logging
from typing import Optional

from aea.common import JSONLike
from aea.configurations.base import PublicId
from aea.contracts.base import Contract
from aea.crypto.base import LedgerApi


PUBLIC_ID = PublicId.from_str("valory/uniswap_v2_router02:0.1.0")

_logger = logging.getLogger(
    f"aea.packages.{PUBLIC_ID.author}.contracts.{PUBLIC_ID.name}.contract"
)


class UniswapV2Router02(Contract):
    """The Uniswap V2 Router02 contract."""

    @classmethod
    def add_liquidity(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        owner_address: str,
        token_a: str,
        token_b: str,
        amount_a_desired: int,
        amount_b_desired: int,
        amount_a_min: int,
        amount_b_min: int,
        to_address: str,
        deadline,
        gas: int = 300000,
    ) -> Optional[JSONLike]:
        """Add liquidity."""

        nonce = ledger_api.api.eth.getTransactionCount(owner_address)
        contract = cls.get_instance(ledger_api, contract_address)

        tx = contract.functions.addLiquidity(
            token_a,
            token_b,
            amount_a_desired,
            amount_b_desired,
            amount_a_min,
            amount_b_min,
            to_address,
            deadline,
        ).buildTransaction(
            {
                "gas": gas,
                "gasPrice": ledger_api.api.toWei("50", "gwei"),
                "nonce": nonce,
            }
        )
        tx = ledger_api.update_with_gas_estimate(tx)

        return tx

    @classmethod
    def add_liquidity_ETH(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        owner_address: str,
        token: str,
        amount_token_desired: int,
        amount_token_min: int,
        amount_ETH_min: int,
        to_address: str,
        deadline,
        gas: int = 300000,
    ) -> Optional[JSONLike]:
        """Add liquidity ETH."""

        nonce = ledger_api.api.eth.getTransactionCount(owner_address)
        contract = cls.get_instance(ledger_api, contract_address)

        tx = contract.functions.addLiquidityETH(
            token,
            amount_token_desired,
            amount_token_min,
            amount_ETH_min,
            to_address,
            deadline,
        ).buildTransaction(
            {
                "gas": gas,
                "gasPrice": ledger_api.api.toWei("50", "gwei"),
                "nonce": nonce,
            }
        )
        tx = ledger_api.update_with_gas_estimate(tx)

        return tx

    @classmethod
    def remove_liquidity(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        owner_address: str,
        token_a: str,
        token_b: str,
        liquidity: int,
        amount_a_min: int,
        amount_b_min: int,
        to_address: str,
        deadline: int,
        gas: int = 300000,
    ) -> Optional[JSONLike]:
        """Remove liquidity."""

        nonce = ledger_api.api.eth.getTransactionCount(owner_address)
        contract = cls.get_instance(ledger_api, contract_address)

        tx = contract.functions.removeLiquidity(
            token_a,
            token_b,
            liquidity,
            amount_a_min,
            amount_b_min,
            to_address,
            deadline,
        ).buildTransaction(
            {
                "gas": gas,
                "gasPrice": ledger_api.api.toWei("50", "gwei"),
                "nonce": nonce,
            }
        )
        tx = ledger_api.update_with_gas_estimate(tx)

        return tx

    @classmethod
    def remove_liquidity_ETH(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        owner_address: str,
        token: str,
        liquidity: int,
        amount_token_min: int,
        amount_ETH_min: int,
        to_address: str,
        deadline: int,
        gas: int = 300000,
    ) -> Optional[JSONLike]:
        """Remove liquidity ETH."""

        nonce = ledger_api.api.eth.getTransactionCount(owner_address)
        contract = cls.get_instance(ledger_api, contract_address)

        tx = contract.functions.removeLiquidityETH(
            token, liquidity, amount_token_min, amount_ETH_min, to_address, deadline
        ).buildTransaction(
            {
                "gas": gas,
                "gasPrice": ledger_api.api.toWei("50", "gwei"),
                "nonce": nonce,
            }
        )
        tx = ledger_api.update_with_gas_estimate(tx)

        return tx

    @classmethod
    def remove_liquidity_with_permit(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        owner_address: str,
        token_a: str,
        token_b: str,
        liquidity: int,
        amount_a_min: int,
        amount_b_min: int,
        to_address: str,
        deadline: int,
        approve_max: bool,
        v: int,
        r: bytes,
        s: bytes,
        gas: int = 300000,
    ) -> Optional[JSONLike]:
        """Remove liquidity with permit."""

        nonce = ledger_api.api.eth.getTransactionCount(owner_address)
        contract = cls.get_instance(ledger_api, contract_address)

        tx = contract.functions.removeLiquidityWithPermit(
            token_a,
            token_b,
            liquidity,
            amount_a_min,
            amount_b_min,
            to_address,
            deadline,
            approve_max,
        ).buildTransaction(
            {
                "gas": gas,
                "gasPrice": ledger_api.api.toWei("50", "gwei"),
                "nonce": nonce,
            }
        )
        tx = ledger_api.update_with_gas_estimate(tx)

        return tx

    @classmethod
    def remove_liquidity_ETH_with_permit(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        owner_address: str,
        token: str,
        liquidity: int,
        amount_token_min: int,
        amount_ETH_min: int,
        to_address: str,
        deadline: int,
        approve_max: bool,
        v: int,
        r: bytes,
        s: bytes,
        gas: int = 300000,
    ) -> Optional[JSONLike]:
        """Remove liquidity ETH with permit."""

        nonce = ledger_api.api.eth.getTransactionCount(owner_address)
        contract = cls.get_instance(ledger_api, contract_address)

        tx = contract.functions.removeLiquidityETHWithPermit(
            token,
            liquidity,
            amount_token_min,
            amount_ETH_min,
            to_address,
            deadline,
            approve_max,
            v,
            r,
            s,
        ).buildTransaction(
            {
                "gas": gas,
                "gasPrice": ledger_api.api.toWei("50", "gwei"),
                "nonce": nonce,
            }
        )
        tx = ledger_api.update_with_gas_estimate(tx)

        return tx

    @classmethod
    def remove_liquidity_ETH_Supporting_fee_on_transfer_tokens(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        owner_address: str,
        token: str,
        liquidity: int,
        amount_token_min: int,
        amount_ETH_min: int,
        to_address: str,
        deadline: int,
        gas: int = 300000,
    ) -> Optional[JSONLike]:
        """Remove liquidity ETH supportinmg fee on transfer tokens."""

        nonce = ledger_api.api.eth.getTransactionCount(owner_address)
        contract = cls.get_instance(ledger_api, contract_address)

        tx = contract.functions.removeLiquidityETHSupportingFeeOnTransferTokens(
            token, liquidity, amount_token_min, amount_ETH_min, to_address, deadline
        ).buildTransaction(
            {
                "gas": gas,
                "gasPrice": ledger_api.api.toWei("50", "gwei"),
                "nonce": nonce,
            }
        )
        tx = ledger_api.update_with_gas_estimate(tx)

        return tx

    @classmethod
    def remove_liquidity_ETH_with_permit_supporting_fee_on_transfer_tokens(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        owner_address: str,
        token: str,
        liquidity: int,
        amount_token_min: int,
        amount_ETH_min: int,
        to_address: str,
        deadline: int,
        approve_max: bool,
        v: int,
        r: bytes,
        s: bytes,
        gas: int = 300000,
    ) -> Optional[JSONLike]:
        """Remove liquidity ETH with permit supportinmg fee on transfer tokens."""

        nonce = ledger_api.api.eth.getTransactionCount(owner_address)
        contract = cls.get_instance(ledger_api, contract_address)

        tx = contract.functions.removeLiquidityETHWithPermitSupportingFeeOnTransferTokens(
            token,
            liquidity,
            amount_token_min,
            amount_ETH_min,
            to_address,
            deadline,
            approve_max,
            v,
            r,
            s,
        ).buildTransaction(
            {
                "gas": gas,
                "gasPrice": ledger_api.api.toWei("50", "gwei"),
                "nonce": nonce,
            }
        )
        tx = ledger_api.update_with_gas_estimate(tx)

        return tx

    @classmethod
    def swap_exact_tokens_for_tokens(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        owner_address: str,
        amount_in: int,
        amount_out_min: int,
        path: list,
        to_address: str,
        deadline: int,
        gas: int = 300000,
    ) -> Optional[JSONLike]:
        """Swap exact tokens for tokens."""

        nonce = ledger_api.api.eth.getTransactionCount(owner_address)
        contract = cls.get_instance(ledger_api, contract_address)

        tx = contract.functions.swapExactTokensForTokens(
            amount_in, amount_out_min, path, to_address, deadline
        ).buildTransaction(
            {
                "gas": gas,
                "gasPrice": ledger_api.api.toWei("50", "gwei"),
                "nonce": nonce,
            }
        )
        tx = ledger_api.update_with_gas_estimate(tx)

        return tx

    @classmethod
    def swap_tokens_for_exact_tokens(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        owner_address: str,
        amount_out: int,
        amount_in_max: int,
        path: list,
        to_address: str,
        deadline: int,
        gas: int = 300000,
    ) -> Optional[JSONLike]:
        """Swap tokens for exact tokens."""

        nonce = ledger_api.api.eth.getTransactionCount(owner_address)
        contract = cls.get_instance(ledger_api, contract_address)

        tx = contract.functions.swapTokensForExactTokens(
            amount_out, amount_in_max, path, to_address, deadline
        ).buildTransaction(
            {
                "gas": gas,
                "gasPrice": ledger_api.api.toWei("50", "gwei"),
                "nonce": nonce,
            }
        )
        tx = ledger_api.update_with_gas_estimate(tx)

        return tx

    @classmethod
    def swap_exact_ETH_for_tokens(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        owner_address: str,
        amount_out_min: int,
        path: list,
        to_address: str,
        deadline: int,
        gas: int = 300000,
    ) -> Optional[JSONLike]:
        """Swap exact ETH for tokens."""

        nonce = ledger_api.api.eth.getTransactionCount(owner_address)
        contract = cls.get_instance(ledger_api, contract_address)

        tx = contract.functions.swapExactETHForTokens(
            amount_out_min, path, to_address, deadline
        ).buildTransaction(
            {
                "gas": gas,
                "gasPrice": ledger_api.api.toWei("50", "gwei"),
                "nonce": nonce,
            }
        )
        tx = ledger_api.update_with_gas_estimate(tx)

        return tx

    @classmethod
    def swap_tokens_for_exact_ETH(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        owner_address: str,
        amount_out: int,
        amount_in_max: int,
        path: list,
        to_address: str,
        deadline: int,
        gas: int = 300000,
    ) -> Optional[JSONLike]:
        """Swap tokens for exact ETH."""

        nonce = ledger_api.api.eth.getTransactionCount(owner_address)
        contract = cls.get_instance(ledger_api, contract_address)

        tx = contract.functions.swapTokensForExactETH(
            amount_out, amount_in_max, path, to_address, deadline
        ).buildTransaction(
            {
                "gas": gas,
                "gasPrice": ledger_api.api.toWei("50", "gwei"),
                "nonce": nonce,
            }
        )
        tx = ledger_api.update_with_gas_estimate(tx)

        return tx

    @classmethod
    def swap_exact_tokens_for_ETH(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        owner_address: str,
        amount_in: int,
        amount_out_min: int,
        path: list,
        to_address: str,
        deadline: int,
        gas: int = 300000,
    ) -> Optional[JSONLike]:
        """Swap exact tokens for ETH."""

        nonce = ledger_api.api.eth.getTransactionCount(owner_address)
        contract = cls.get_instance(ledger_api, contract_address)

        tx = contract.functions.swapExactTokensForETH(
            amount_in, amount_out_min, path, to_address, deadline
        ).buildTransaction(
            {
                "gas": gas,
                "gasPrice": ledger_api.api.toWei("50", "gwei"),
                "nonce": nonce,
            }
        )
        tx = ledger_api.update_with_gas_estimate(tx)

        return tx

    @classmethod
    def swap_ETH_for_exact_tokens(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        owner_address: str,
        amount_out: int,
        path: list,
        to_address: str,
        deadline: int,
        gas: int = 300000,
    ) -> Optional[JSONLike]:
        """Swap ETH tokens for exact tokens."""

        nonce = ledger_api.api.eth.getTransactionCount(owner_address)
        contract = cls.get_instance(ledger_api, contract_address)

        tx = contract.functions.swapETHExactTokens(
            amount_out, path, to_address, deadline
        ).buildTransaction(
            {
                "gas": gas,
                "gasPrice": ledger_api.api.toWei("50", "gwei"),
                "nonce": nonce,
            }
        )
        tx = ledger_api.update_with_gas_estimate(tx)

        return tx

    @classmethod
    def swap_exact_tokens_for_tokens_supporting_fee_on_transfer_tokens(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        owner_address: str,
        amount_in: int,
        amount_out_min: int,
        path: list,
        to_address: str,
        deadline: int,
        gas: int = 300000,
    ) -> Optional[JSONLike]:
        """Swap exact tokens for tokens supporting fee on transfer tokens."""

        nonce = ledger_api.api.eth.getTransactionCount(owner_address)
        contract = cls.get_instance(ledger_api, contract_address)

        tx = contract.functions.swapExactTokensForTokensSupportingFeeOnTransferTokens(
            amount_in, amount_out_min, path, to_address, deadline
        ).buildTransaction(
            {
                "gas": gas,
                "gasPrice": ledger_api.api.toWei("50", "gwei"),
                "nonce": nonce,
            }
        )
        tx = ledger_api.update_with_gas_estimate(tx)

        return tx

    @classmethod
    def swap_exact_ETH_for_tokens_supporting_fee_on_transfer_tokens(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        owner_address: str,
        amount_out_min: int,
        path: list,
        to_address: str,
        deadline: int,
        gas: int = 300000,
    ) -> Optional[JSONLike]:
        """Swap exact ETH for tokens supporting fee on transfer tokens."""

        nonce = ledger_api.api.eth.getTransactionCount(owner_address)
        contract = cls.get_instance(ledger_api, contract_address)

        tx = contract.functions.swapExactETHForTokensSupportingFeeOnTransferTokens(
            amount_out_min, path, to_address, deadline
        ).buildTransaction(
            {
                "gas": gas,
                "gasPrice": ledger_api.api.toWei("50", "gwei"),
                "nonce": nonce,
            }
        )
        tx = ledger_api.update_with_gas_estimate(tx)

        return tx

    @classmethod
    def swap_exact_tokens_for_ETH_supporting_fee_on_transfer_tokens(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        owner_address: str,
        amount_in: int,
        amount_out_min: int,
        path: list,
        to_address: str,
        deadline: int,
        gas: int = 300000,
    ) -> Optional[JSONLike]:
        """Swap exact tokens for ETH supporting fee on transfer tokens."""

        nonce = ledger_api.api.eth.getTransactionCount(owner_address)
        contract = cls.get_instance(ledger_api, contract_address)

        tx = contract.functions.swapExactTokensForETHSupportingFeeOnTransferTokens(
            amount_in, amount_out_min, path, to_address, deadline
        ).buildTransaction(
            {
                "gas": gas,
                "gasPrice": ledger_api.api.toWei("50", "gwei"),
                "nonce": nonce,
            }
        )
        tx = ledger_api.update_with_gas_estimate(tx)

        return tx

    @classmethod
    def quote(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        amount_a: int,
        reserve_a: int,
        reserve_b: int,
    ) -> Optional[JSONLike]:
        """Quote."""

        contract = cls.get_instance(ledger_api, contract_address)

        tx = contract.functions.quote(amount_a, reserve_a, reserve_b).buildTransaction()
        tx = ledger_api.update_with_gas_estimate(tx)

        return tx

    @classmethod
    def get_amount_out(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        amount_in: int,
        reserve_in,
        reserve_out: int,
    ) -> Optional[JSONLike]:
        """Get amount out."""

        contract = cls.get_instance(ledger_api, contract_address)

        tx = contract.functions.getAmountOut(
            amount_in, reserve_in, reserve_out
        ).buildTransaction()
        tx = ledger_api.update_with_gas_estimate(tx)

        return tx

    @classmethod
    def get_amount_in(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        amount_out: int,
        reserve_in,
        reserve_out: int,
    ) -> Optional[JSONLike]:
        """Get amount in."""

        contract = cls.get_instance(ledger_api, contract_address)

        tx = contract.functions.getAmountIn(
            amount_out, reserve_in, reserve_out
        ).buildTransaction()
        tx = ledger_api.update_with_gas_estimate(tx)

        return tx

    @classmethod
    def get_amounts_out(
        cls, ledger_api: LedgerApi, contract_address: str, amount_in: int, path: list
    ) -> Optional[JSONLike]:
        """Get amounts out."""

        contract = cls.get_instance(ledger_api, contract_address)

        tx = contract.functions.getAmountsOut(amount_in, path).buildTransaction()
        tx = ledger_api.update_with_gas_estimate(tx)

        return tx

    @classmethod
    def get_amounts_in(
        cls, ledger_api: LedgerApi, contract_address: str, amount_out: int, path: list
    ) -> Optional[JSONLike]:
        """Get amounts in."""

        contract = cls.get_instance(ledger_api, contract_address)

        tx = contract.functions.getAmountsIn(amount_out, path).buildTransaction()
        tx = ledger_api.update_with_gas_estimate(tx)

        return tx
