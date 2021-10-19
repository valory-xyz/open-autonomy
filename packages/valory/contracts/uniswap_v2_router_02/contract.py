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

from aea.contracts.base import Contract
from aea.configurations.base import PublicId

PUBLIC_ID = PublicId.from_str("valory/uniswap_v2_router02:0.1.0")

_logger = logging.getLogger(
    f"aea.packages.{PUBLIC_ID.author}.contracts.{PUBLIC_ID.name}.contract"
)

class UniswapV2Router02(Contract):
    """The Uniswap V2 Router02 contract."""

    @classmethod
    def addLiquidity(
        cls,
        tokenA: str,
        tokenB: str,
        amountADesired: int,
        amountBDesired: int,
        amountAMin: int,
        amountBMin: int,
        to: str,
        deadline
    ):
        """Add liquidity."""
        pass

    @classmethod
    def addLiquidityETH(
        cls,
        token: str,
        amountTokenDesired: int,
        amountTokenMin: int,
        amountETHMin: int,
        to: str,
        deadline
    ):
        """Add liquidity ETH."""
        pass

    @classmethod
    def removeLiquidity(
        cls,
        tokenA: str,
        tokenB: str,
        liquidity: int,
        amountAMin: int,
        amountBMin: int,
        to: str,
        deadline: int
    ):
        """Remove liquidity."""
        pass

    @classmethod
    def removeLiquidityETH(
        cls,
        token: str,
        liquidity: int,
        amountTokenMin: int,
        amountETHMin: int,
        to: str,
        deadline: int
    ):
        """Remove liquidity ETH."""
        pass

    @classmethod
    def removeLiquidityWithPermit(
        cls,
        tokenA: str,
        tokenB: str,
        liquidity: int,
        amountAMin: int,
        amountBMin: int,
        to: str,
        deadline: int,
        approveMax: bool,
        v: int,
        r: bytes,
        s: bytes
    ):
        """Remove liquidity with permit."""
        pass

    @classmethod
    def removeLiquidityETHWithPermit(
        cls,
        token: str,
        liquidity: int,
        amountTokenMin: int,
        amountETHMin: int,
        to: str,
        deadline: int,
        approveMax: bool,
        v: int,
        r: bytes,
        s: bytes
    ):
        """Remove liquidity ETH with permit."""
        pass

    @classmethod
    def removeLiquidityETHSupportingFeeOnTransferTokens(
        cls,
        token: str,
        liquidity: int,
        amountTokenMin: int,
        amountETHMin: int,
        to: str,
        deadline: int
    ):
        """Remove liquidity ETH supportinmg fee on transfer tokens."""
        pass

    @classmethod
    def removeLiquidityETHWithPermitSupportingFeeOnTransferTokens(
        cls,
        token: str,
        liquidity: int,
        amountTokenMin: int,
        amountETHMin: int,
        to: str,
        deadline: int,
        approveMax: bool,
        v: int,
        r: bytes,
        s: bytes
    ):
        """Remove liquidity ETH with permit supportinmg fee on transfer tokens."""
        pass

    @classmethod
    def swapExactTokensForTokens(
        cls,
        amountIn: int,
        amountOutMin: int,
        path: list,
        to: str,
        deadline: int
    ):
        """Swap exact tokens for tokens."""
        pass

    @classmethod
    def swapTokensForExactTokens(
        cls,
        amountOut: int,
        amountInMax: int,
        path: list,
        to: str,
        deadline: int
    ):
        """Swap tokens for exact tokens."""
        pass

    @classmethod
    def swapExactETHForTokens(
        cls,amountOutMin: int,
        path: list,
        to: str,
        deadline: int):
            """Swap exact ETH for tokens."""
            pass

    @classmethod
    def swapTokensForExactETH(
        cls,amountOut: int,
        amountInMax: int,
        path: list,
        to: str,
        deadline: int):
            """Swap tokens for exact ETH."""
            pass

    @classmethod
    def swapExactTokensForETH(
        cls,amountIn: int,
        amountOutMin: int,
        path: list,
        to: str,
        deadline: int):
            """Swap exact tokens for ETH."""
            pass

    @classmethod
    def swapETHForExactTokens(
        cls,amountOut: int,
        path: list,
        to: str,
        deadline: int):
            """Swap ETH tokens for exact tokens."""
            pass

    @classmethod
    def swapExactTokensForTokensSupportingFeeOnTransferTokens(
        cls,
        amountIn: int,
        amountOutMin: int,
        path: list,
        to: str,
        deadline: int
    ):
        """Swap exact tokens for tokens supporting fee on transfer tokens."""
        pass

    @classmethod
    def swapExactETHForTokensSupportingFeeOnTransferTokens(
        cls,
        amountOutMin: int,
        path: list,
        to: str,
        deadline: int
    ):
        """Swap exact ETH for tokens supporting fee on transfer tokens."""
        pass

    @classmethod
    def swapExactTokensForETHSupportingFeeOnTransferTokens(
        cls,
        amountIn: int,
        amountOutMin: int,
        path: list,
        to: str,
        deadline: int
    ):
        """Swap exact tokens for ETH supporting fee on transfer tokens."""
        pass

    @classmethod
    def quote(
        cls, amountA: int, reserveA: int, reserveB: int):
            """Quote."""
            pass

    @classmethod
    def getAmountOut(
        cls, amountIn: int, reserveIn, reserveOut: int):
            """Get amount out."""
            pass

    @classmethod
    def getAmountIn(
        cls, amountOut: int, reserveIn, reserveOut: int):
            """Get amount in."""
            pass

    @classmethod
    def getAmountsOut(
        cls, amountIn: int, path: list):
            """Get amounts out."""
            pass

    @classmethod
    def getAmountsIn(
        cls, amountOut: int, path: list):
            """Get amounts in."""
            pass