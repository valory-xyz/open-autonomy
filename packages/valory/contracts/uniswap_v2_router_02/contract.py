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

"""This module contains the class to connect to a Uniswap V2 Router02 contract."""
import logging
from typing import Any, Optional

from aea.common import JSONLike
from aea.configurations.base import PublicId
from aea.contracts.base import Contract
from aea_ledger_ethereum import EthereumApi


PUBLIC_ID = PublicId.from_str("valory/uniswap_v2_router_02:0.1.0")

_logger = logging.getLogger(
    f"aea.packages.{PUBLIC_ID.author}.contracts.{PUBLIC_ID.name}.contract"
)


# pylint: disable=too-many-arguments,invalid-name,too-many-locals,too-many-public-methods
class UniswapV2Router02Contract(Contract):
    """The Uniswap V2 Router02 contract."""

    contract_id = PUBLIC_ID

    @classmethod
    def add_liquidity(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        token_a: str,
        token_b: str,
        amount_a_desired: int,
        amount_b_desired: int,
        amount_a_min: int,
        amount_b_min: int,
        to_address: str,
        deadline: int,
        **kwargs: Any,
    ) -> Optional[JSONLike]:
        """Add liquidity."""
        contract_instance = cls.get_instance(ledger_api, contract_address)

        return ledger_api.build_transaction(
            contract_instance,
            "addLiquidity",
            method_args=dict(
                tokenA=token_a,
                tokenB=token_b,
                amountADesired=amount_a_desired,
                amountBDesired=amount_b_desired,
                amountAMin=amount_a_min,
                amountBMin=amount_b_min,
                to=to_address,
                deadline=deadline,
            ),
            tx_args=kwargs,
        )

    @classmethod
    def add_liquidity_ETH(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        token: str,
        amount_token_desired: int,
        amount_token_min: int,
        amount_ETH_min: int,
        to_address: str,
        deadline: int,
        **kwargs: Any,
    ) -> Optional[JSONLike]:
        """Add liquidity ETH."""
        contract_instance = cls.get_instance(ledger_api, contract_address)

        return ledger_api.build_transaction(
            contract_instance,
            "addLiquidityETH",
            method_args=dict(
                token=token,
                amountTokenDesired=amount_token_desired,
                amountTokenMin=amount_token_min,
                amountETHMin=amount_ETH_min,
                to=to_address,
                deadline=deadline,
            ),
            tx_args=kwargs,
        )

    @classmethod
    def remove_liquidity(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        token_a: str,
        token_b: str,
        liquidity: int,
        amount_a_min: int,
        amount_b_min: int,
        to_address: str,
        deadline: int,
        **kwargs: Any,
    ) -> Optional[JSONLike]:
        """Remove liquidity."""
        contract_instance = cls.get_instance(ledger_api, contract_address)

        return ledger_api.build_transaction(
            contract_instance,
            "removeLiquidity",
            method_args=dict(
                tokenA=token_a,
                tokenB=token_b,
                liquidity=liquidity,
                amountAMin=amount_a_min,
                amountBMin=amount_b_min,
                to=to_address,
                deadline=deadline,
            ),
            tx_args=kwargs,
        )

    @classmethod
    def remove_liquidity_ETH(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        token: str,
        liquidity: int,
        amount_token_min: int,
        amount_ETH_min: int,
        to_address: str,
        deadline: int,
        **kwargs: Any,
    ) -> Optional[JSONLike]:
        """Remove liquidity ETH."""
        contract_instance = cls.get_instance(ledger_api, contract_address)

        return ledger_api.build_transaction(
            contract_instance,
            "removeLiquidityETH",
            method_args=dict(
                token=token,
                liquidity=liquidity,
                amountTokenMin=amount_token_min,
                amountETHMin=amount_ETH_min,
                to=to_address,
                deadline=deadline,
            ),
            tx_args=kwargs,
        )

    @classmethod
    def remove_liquidity_with_permit(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
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
        **kwargs: Any,
    ) -> Optional[JSONLike]:
        """Remove liquidity with permit."""
        contract_instance = cls.get_instance(ledger_api, contract_address)

        return ledger_api.build_transaction(
            contract_instance,
            "removeLiquidityWithPermit",
            method_args=dict(
                tokenA=token_a,
                tokenB=token_b,
                liquidity=liquidity,
                amountAMin=amount_a_min,
                amountBMin=amount_b_min,
                to=to_address,
                deadline=deadline,
                approveMax=approve_max,
                v=v,
                r=r,
                s=s,
            ),
            tx_args=kwargs,
        )

    @classmethod
    def remove_liquidity_ETH_with_permit(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
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
        **kwargs: Any,
    ) -> Optional[JSONLike]:
        """Remove liquidity ETH with permit."""
        contract_instance = cls.get_instance(ledger_api, contract_address)

        return ledger_api.build_transaction(
            contract_instance,
            "removeLiquidityETHWithPermit",
            method_args=dict(
                token=token,
                liquidity=liquidity,
                amountTokenMin=amount_token_min,
                amountETHMin=amount_ETH_min,
                to=to_address,
                deadline=deadline,
                approveMax=approve_max,
                v=v,
                r=r,
                s=s,
            ),
            tx_args=kwargs,
        )

    @classmethod
    def remove_liquidity_ETH_Supporting_fee_on_transfer_tokens(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        token: str,
        liquidity: int,
        amount_token_min: int,
        amount_ETH_min: int,
        to_address: str,
        deadline: int,
        **kwargs: Any,
    ) -> Optional[JSONLike]:
        """Remove liquidity ETH supportinmg fee on transfer tokens."""
        contract_instance = cls.get_instance(ledger_api, contract_address)

        return ledger_api.build_transaction(
            contract_instance,
            "removeLiquidityETHSupportingFeeOnTransferTokens",
            method_args=dict(
                token=token,
                liquidity=liquidity,
                amountTokenMin=amount_token_min,
                amountETHMin=amount_ETH_min,
                to=to_address,
                deadline=deadline,
            ),
            tx_args=kwargs,
        )

    @classmethod
    def remove_liquidity_ETH_with_permit_supporting_fee_on_transfer_tokens(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
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
        **kwargs: Any,
    ) -> Optional[JSONLike]:
        """Remove liquidity ETH with permit supportinmg fee on transfer tokens."""
        contract_instance = cls.get_instance(ledger_api, contract_address)

        return ledger_api.build_transaction(
            contract_instance,
            "removeLiquidityETHWithPermitSupportingFeeOnTransferTokens",
            method_args=dict(
                token=token,
                liquidity=liquidity,
                amountTokenMin=amount_token_min,
                amountETHMin=amount_ETH_min,
                to=to_address,
                deadline=deadline,
                approveMax=approve_max,
                v=v,
                r=r,
                s=s,
            ),
            tx_args=kwargs,
        )

    @classmethod
    def swap_exact_tokens_for_tokens(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        amount_in: int,
        amount_out_min: int,
        path: list,
        to_address: str,
        deadline: int,
        **kwargs: Any,
    ) -> Optional[JSONLike]:
        """Swap exact tokens for tokens."""
        contract_instance = cls.get_instance(ledger_api, contract_address)

        return ledger_api.build_transaction(
            contract_instance,
            "swapExactTokensForTokens",
            method_args=dict(
                amountIn=amount_in,
                amountOutMin=amount_out_min,
                path=path,
                to=to_address,
                deadline=deadline,
            ),
            tx_args=kwargs,
        )

    @classmethod
    def swap_tokens_for_exact_tokens(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        amount_out: int,
        amount_in_max: int,
        path: list,
        to_address: str,
        deadline: int,
        **kwargs: Any,
    ) -> Optional[JSONLike]:
        """Swap tokens for exact tokens."""
        contract_instance = cls.get_instance(ledger_api, contract_address)

        return ledger_api.build_transaction(
            contract_instance,
            "swapTokensForExactTokens",
            method_args=dict(
                amountOut=amount_out,
                amountInMax=amount_in_max,
                path=path,
                to=to_address,
                deadline=deadline,
            ),
            tx_args=kwargs,
        )

    @classmethod
    def swap_exact_ETH_for_tokens(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        amount_out_min: int,
        path: list,
        to_address: str,
        deadline: int,
        **kwargs: Any,
    ) -> Optional[JSONLike]:
        """Swap exact ETH for tokens."""
        contract_instance = cls.get_instance(ledger_api, contract_address)

        return ledger_api.build_transaction(
            contract_instance,
            "swapExactETHForTokens",
            method_args=dict(
                amountOutMin=amount_out_min,
                path=path,
                to=to_address,
                deadline=deadline,
            ),
            tx_args=kwargs,
        )

    @classmethod
    def swap_tokens_for_exact_ETH(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        amount_out: int,
        amount_in_max: int,
        path: list,
        to_address: str,
        deadline: int,
        **kwargs: Any,
    ) -> Optional[JSONLike]:
        """Swap tokens for exact ETH."""
        contract_instance = cls.get_instance(ledger_api, contract_address)

        return ledger_api.build_transaction(
            contract_instance,
            "swapTokensForExactETH",
            method_args=dict(
                amountOut=amount_out,
                amountInMax=amount_in_max,
                path=path,
                to=to_address,
                deadline=deadline,
            ),
            tx_args=kwargs,
        )

    @classmethod
    def swap_exact_tokens_for_ETH(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        amount_in: int,
        amount_out_min: int,
        path: list,
        to_address: str,
        deadline: int,
        **kwargs: Any,
    ) -> Optional[JSONLike]:
        """Swap exact tokens for ETH."""
        contract_instance = cls.get_instance(ledger_api, contract_address)

        return ledger_api.build_transaction(
            contract_instance,
            "swapExactTokensForETH",
            method_args=dict(
                amountIn=amount_in,
                amountOutMin=amount_out_min,
                path=path,
                to=to_address,
                deadline=deadline,
            ),
            tx_args=kwargs,
        )

    @classmethod
    def swap_ETH_for_exact_tokens(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        amount_out: int,
        path: list,
        to_address: str,
        deadline: int,
        **kwargs: Any,
    ) -> Optional[JSONLike]:
        """Swap ETH tokens for exact tokens."""
        contract_instance = cls.get_instance(ledger_api, contract_address)

        return ledger_api.build_transaction(
            contract_instance,
            "swapETHForExactTokens",
            method_args=dict(
                amountOut=amount_out,
                path=path,
                to=to_address,
                deadline=deadline,
            ),
            tx_args=kwargs,
        )

    @classmethod
    def swap_exact_tokens_for_tokens_supporting_fee_on_transfer_tokens(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        amount_in: int,
        amount_out_min: int,
        path: list,
        to_address: str,
        deadline: int,
        **kwargs: Any,
    ) -> Optional[JSONLike]:
        """Swap exact tokens for tokens supporting fee on transfer tokens."""
        contract_instance = cls.get_instance(ledger_api, contract_address)

        return ledger_api.build_transaction(
            contract_instance,
            "swapExactTokensForTokensSupportingFeeOnTransferTokens",
            method_args=dict(
                amountIn=amount_in,
                amountOutMin=amount_out_min,
                path=path,
                to=to_address,
                deadline=deadline,
            ),
            tx_args=kwargs,
        )

    @classmethod
    def swap_exact_ETH_for_tokens_supporting_fee_on_transfer_tokens(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        amount_out_min: int,
        path: list,
        to_address: str,
        deadline: int,
        **kwargs: Any,
    ) -> Optional[JSONLike]:
        """Swap exact ETH for tokens supporting fee on transfer tokens."""
        contract_instance = cls.get_instance(ledger_api, contract_address)

        return ledger_api.build_transaction(
            contract_instance,
            "swapExactETHForTokensSupportingFeeOnTransferTokens",
            method_args=dict(
                amountOutMin=amount_out_min,
                path=path,
                to=to_address,
                deadline=deadline,
            ),
            tx_args=kwargs,
        )

    @classmethod
    def swap_exact_tokens_for_ETH_supporting_fee_on_transfer_tokens(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        amount_in: int,
        amount_out_min: int,
        path: list,
        to_address: str,
        deadline: int,
        **kwargs: Any,
    ) -> Optional[JSONLike]:
        """Swap exact tokens for ETH supporting fee on transfer tokens."""
        contract_instance = cls.get_instance(ledger_api, contract_address)

        return ledger_api.build_transaction(
            contract_instance,
            "swapExactTokensForETHSupportingFeeOnTransferTokens",
            method_args=dict(
                amountIn=amount_in,
                amountOutMin=amount_out_min,
                path=path,
                to=to_address,
                deadline=deadline,
            ),
            tx_args=kwargs,
        )

    @classmethod
    def quote(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        amount_a: int,
        reserve_a: int,
        reserve_b: int,
    ) -> Optional[JSONLike]:
        """Quote."""
        contract_instance = cls.get_instance(ledger_api, contract_address)

        return ledger_api.contract_method_call(
            contract_instance,
            "quote",
            amountA=amount_a,
            reserveA=reserve_a,
            reserveB=reserve_b,
        )

    @classmethod
    def get_amount_out(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        amount_in: int,
        reserve_in: int,
        reserve_out: int,
    ) -> Optional[JSONLike]:
        """Get amount out."""
        contract_instance = cls.get_instance(ledger_api, contract_address)

        return ledger_api.contract_method_call(
            contract_instance,
            "getAmountOut",
            amountIn=amount_in,
            reserveIn=reserve_in,
            reserveOut=reserve_out,
        )

    @classmethod
    def get_amount_in(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        amount_out: int,
        reserve_in: int,
        reserve_out: int,
    ) -> Optional[JSONLike]:
        """Get amount in."""
        contract_instance = cls.get_instance(ledger_api, contract_address)

        return ledger_api.contract_method_call(
            contract_instance,
            "getAmountIn",
            amountOut=amount_out,
            reserveIn=reserve_in,
            reserveOut=reserve_out,
        )

    @classmethod
    def get_amounts_out(
        cls, ledger_api: EthereumApi, contract_address: str, amount_in: int, path: list
    ) -> Optional[JSONLike]:
        """Get amounts out."""
        contract_instance = cls.get_instance(ledger_api, contract_address)

        return ledger_api.contract_method_call(
            contract_instance, "getAmountsOut", amountIn=amount_in, path=path
        )

    @classmethod
    def get_amounts_in(
        cls, ledger_api: EthereumApi, contract_address: str, amount_out: int, path: list
    ) -> Optional[JSONLike]:
        """Get amounts in."""
        contract_instance = cls.get_instance(ledger_api, contract_address)

        return ledger_api.contract_method_call(
            contract_instance, "getAmountsIn", amountOut=amount_out, path=path
        )
