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
from typing import Any, Optional

from aea.common import JSONLike
from aea.configurations.base import PublicId
from aea.contracts.base import Contract
from aea.crypto.base import LedgerApi


PUBLIC_ID = PublicId.from_str("valory/uniswap_v2_router_02:0.1.0")

_logger = logging.getLogger(
    f"aea.packages.{PUBLIC_ID.author}.contracts.{PUBLIC_ID.name}.contract"
)


# pylint: disable=too-many-arguments,invalid-name,too-many-locals,too-many-public-methods
class UniswapV2Router02Contract(Contract):
    """The Uniswap V2 Router02 contract."""

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
        data = instance.encodeABI(fn_name=method_name, args=list(kwargs.values()))
        return {"data": bytes.fromhex(data[2:])}  # type: ignore

    @classmethod
    def add_liquidity(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        sender_address: str,
        gas: int,
        gas_price: int,
        token_a: str,
        token_b: str,
        amount_a_desired: int,
        amount_b_desired: int,
        amount_a_min: int,
        amount_b_min: int,
        to_address: str,
        deadline: int,
    ) -> Optional[JSONLike]:
        """Add liquidity."""
        return cls._prepare_tx(
            ledger_api,
            contract_address,
            sender_address,
            gas,
            gas_price,
            "addLiquidity",
            token_a,
            token_b,
            amount_a_desired,
            amount_b_desired,
            amount_a_min,
            amount_b_min,
            to_address,
            deadline,
        )

    @classmethod
    def add_liquidity_ETH(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        sender_address: str,
        gas: int,
        gas_price: int,
        token: str,
        amount_token_desired: int,
        amount_token_min: int,
        amount_ETH_min: int,
        to_address: str,
        deadline: int,
    ) -> Optional[JSONLike]:
        """Add liquidity ETH."""
        return cls._prepare_tx(
            ledger_api,
            contract_address,
            sender_address,
            gas,
            gas_price,
            "addLiquidityETH",
            token,
            amount_token_desired,
            amount_token_min,
            amount_ETH_min,
            to_address,
            deadline,
        )

    @classmethod
    def remove_liquidity(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        sender_address: str,
        gas: int,
        gas_price: int,
        token_a: str,
        token_b: str,
        liquidity: int,
        amount_a_min: int,
        amount_b_min: int,
        to_address: str,
        deadline: int,
    ) -> Optional[JSONLike]:
        """Remove liquidity."""
        return cls._prepare_tx(
            ledger_api,
            contract_address,
            sender_address,
            gas,
            gas_price,
            "removeLiquidity",
            token_a,
            token_b,
            liquidity,
            amount_a_min,
            amount_b_min,
            to_address,
            deadline,
        )

    @classmethod
    def remove_liquidity_ETH(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        sender_address: str,
        gas: int,
        gas_price: int,
        token: str,
        liquidity: int,
        amount_token_min: int,
        amount_ETH_min: int,
        to_address: str,
        deadline: int,
    ) -> Optional[JSONLike]:
        """Remove liquidity ETH."""
        return cls._prepare_tx(
            ledger_api,
            contract_address,
            sender_address,
            gas,
            gas_price,
            "removeLiquidityETH",
            token,
            liquidity,
            amount_token_min,
            amount_ETH_min,
            to_address,
            deadline,
        )

    @classmethod
    def remove_liquidity_with_permit(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        sender_address: str,
        gas: int,
        gas_price: int,
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
    ) -> Optional[JSONLike]:
        """Remove liquidity with permit."""
        return cls._prepare_tx(
            ledger_api,
            contract_address,
            sender_address,
            gas,
            gas_price,
            "removeLiquidityWithPermit",
            token_a,
            token_b,
            liquidity,
            amount_a_min,
            amount_b_min,
            to_address,
            deadline,
            approve_max,
            v,
            r,
            s,
        )

    @classmethod
    def remove_liquidity_ETH_with_permit(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        sender_address: str,
        gas: int,
        gas_price: int,
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
    ) -> Optional[JSONLike]:
        """Remove liquidity ETH with permit."""
        return cls._prepare_tx(
            ledger_api,
            contract_address,
            sender_address,
            gas,
            gas_price,
            "removeLiquidityETHWithPermit",
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
        )

    @classmethod
    def remove_liquidity_ETH_Supporting_fee_on_transfer_tokens(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        sender_address: str,
        gas: int,
        gas_price: int,
        token: str,
        liquidity: int,
        amount_token_min: int,
        amount_ETH_min: int,
        to_address: str,
        deadline: int,
    ) -> Optional[JSONLike]:
        """Remove liquidity ETH supportinmg fee on transfer tokens."""
        return cls._prepare_tx(
            ledger_api,
            contract_address,
            sender_address,
            gas,
            gas_price,
            "removeLiquidityETHSupportingFeeOnTransferTokens",
            token,
            liquidity,
            amount_token_min,
            amount_ETH_min,
            to_address,
            deadline,
        )

    @classmethod
    def remove_liquidity_ETH_with_permit_supporting_fee_on_transfer_tokens(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        sender_address: str,
        gas: int,
        gas_price: int,
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
    ) -> Optional[JSONLike]:
        """Remove liquidity ETH with permit supportinmg fee on transfer tokens."""
        return cls._prepare_tx(
            ledger_api,
            contract_address,
            sender_address,
            gas,
            gas_price,
            "removeLiquidityETHWithPermitSupportingFeeOnTransferTokens",
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
        )

    @classmethod
    def swap_exact_tokens_for_tokens(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        sender_address: str,
        gas: int,
        gas_price: int,
        amount_in: int,
        amount_out_min: int,
        path: list,
        to_address: str,
        deadline: int,
    ) -> Optional[JSONLike]:
        """Swap exact tokens for tokens."""
        return cls._prepare_tx(
            ledger_api,
            contract_address,
            sender_address,
            gas,
            gas_price,
            "swapExactTokensForTokens",
            amount_in,
            amount_out_min,
            path,
            to_address,
            deadline,
        )

    @classmethod
    def swap_tokens_for_exact_tokens(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        sender_address: str,
        gas: int,
        gas_price: int,
        amount_out: int,
        amount_in_max: int,
        path: list,
        to_address: str,
        deadline: int,
    ) -> Optional[JSONLike]:
        """Swap tokens for exact tokens."""
        return cls._prepare_tx(
            ledger_api,
            contract_address,
            sender_address,
            gas,
            gas_price,
            "swapTokensForExactTokens",
            amount_out,
            amount_in_max,
            path,
            to_address,
            deadline,
        )

    @classmethod
    def swap_exact_ETH_for_tokens(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        sender_address: str,
        gas: int,
        gas_price: int,
        amount_out_min: int,
        path: list,
        to_address: str,
        deadline: int,
    ) -> Optional[JSONLike]:
        """Swap exact ETH for tokens."""
        return cls._prepare_tx(
            ledger_api,
            contract_address,
            sender_address,
            gas,
            gas_price,
            "swapExactETHForTokens",
            amount_out_min,
            path,
            to_address,
            deadline,
        )

    @classmethod
    def swap_tokens_for_exact_ETH(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        sender_address: str,
        gas: int,
        gas_price: int,
        amount_out: int,
        amount_in_max: int,
        path: list,
        to_address: str,
        deadline: int,
    ) -> Optional[JSONLike]:
        """Swap tokens for exact ETH."""
        return cls._prepare_tx(
            ledger_api,
            contract_address,
            sender_address,
            gas,
            gas_price,
            "swapTokensForExactETH",
            amount_out,
            amount_in_max,
            path,
            to_address,
            deadline,
        )

    @classmethod
    def swap_exact_tokens_for_ETH(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        sender_address: str,
        gas: int,
        gas_price: int,
        amount_in: int,
        amount_out_min: int,
        path: list,
        to_address: str,
        deadline: int,
    ) -> Optional[JSONLike]:
        """Swap exact tokens for ETH."""
        return cls._prepare_tx(
            ledger_api,
            contract_address,
            sender_address,
            gas,
            gas_price,
            "swapExactTokensForETH",
            amount_in,
            amount_out_min,
            path,
            to_address,
            deadline,
        )

    @classmethod
    def swap_ETH_for_exact_tokens(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        sender_address: str,
        gas: int,
        gas_price: int,
        amount_out: int,
        path: list,
        to_address: str,
        deadline: int,
    ) -> Optional[JSONLike]:
        """Swap ETH tokens for exact tokens."""
        return cls._prepare_tx(
            ledger_api,
            contract_address,
            sender_address,
            gas,
            gas_price,
            "swapETHForExactTokens",
            amount_out,
            path,
            to_address,
            deadline,
        )

    @classmethod
    def swap_exact_tokens_for_tokens_supporting_fee_on_transfer_tokens(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        sender_address: str,
        gas: int,
        gas_price: int,
        amount_in: int,
        amount_out_min: int,
        path: list,
        to_address: str,
        deadline: int,
    ) -> Optional[JSONLike]:
        """Swap exact tokens for tokens supporting fee on transfer tokens."""
        return cls._prepare_tx(
            ledger_api,
            contract_address,
            sender_address,
            gas,
            gas_price,
            "swapExactTokensForTokensSupportingFeeOnTransferTokens",
            amount_in,
            amount_out_min,
            path,
            to_address,
            deadline,
        )

    @classmethod
    def swap_exact_ETH_for_tokens_supporting_fee_on_transfer_tokens(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        sender_address: str,
        gas: int,
        gas_price: int,
        amount_out_min: int,
        path: list,
        to_address: str,
        deadline: int,
    ) -> Optional[JSONLike]:
        """Swap exact ETH for tokens supporting fee on transfer tokens."""
        return cls._prepare_tx(
            ledger_api,
            contract_address,
            sender_address,
            gas,
            gas_price,
            "swapExactETHForTokensSupportingFeeOnTransferTokens",
            amount_out_min,
            path,
            to_address,
            deadline,
        )

    @classmethod
    def swap_exact_tokens_for_ETH_supporting_fee_on_transfer_tokens(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        sender_address: str,
        gas: int,
        gas_price: int,
        amount_in: int,
        amount_out_min: int,
        path: list,
        to_address: str,
        deadline: int,
    ) -> Optional[JSONLike]:
        """Swap exact tokens for ETH supporting fee on transfer tokens."""
        return cls._prepare_tx(
            ledger_api,
            contract_address,
            sender_address,
            gas,
            gas_price,
            "swapExactTokensForETHSupportingFeeOnTransferTokens",
            amount_in,
            amount_out_min,
            path,
            to_address,
            deadline,
        )

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
        return cls._call(
            ledger_api, contract_address, "quote", amount_a, reserve_a, reserve_b
        )

    @classmethod
    def get_amount_out(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        amount_in: int,
        reserve_in: int,
        reserve_out: int,
    ) -> Optional[JSONLike]:
        """Get amount out."""
        return cls._call(
            ledger_api,
            contract_address,
            "getAmountOut",
            amount_in,
            reserve_in,
            reserve_out,
        )

    @classmethod
    def get_amount_in(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        amount_out: int,
        reserve_in: int,
        reserve_out: int,
    ) -> Optional[JSONLike]:
        """Get amount in."""
        return cls._call(
            ledger_api,
            contract_address,
            "getAmountIn",
            amount_out,
            reserve_in,
            reserve_out,
        )

    @classmethod
    def get_amounts_out(
        cls, ledger_api: LedgerApi, contract_address: str, amount_in: int, path: list
    ) -> Optional[JSONLike]:
        """Get amounts out."""
        return cls._call(ledger_api, contract_address, "getAmountsOut", amount_in, path)

    @classmethod
    def get_amounts_in(
        cls, ledger_api: LedgerApi, contract_address: str, amount_out: int, path: list
    ) -> Optional[JSONLike]:
        """Get amounts in."""
        return cls._call(ledger_api, contract_address, "getAmountsIn", amount_out, path)

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
