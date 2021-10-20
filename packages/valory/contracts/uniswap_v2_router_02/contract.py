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

from aea.common import Optional[JSONLike]
from aea.configurations.base import PublicId
from aea.contracts.base import Contract


PUBLIC_ID = PublicId.from_str("valory/uniswap_v2_router02:0.1.0")

_logger = logging.getLogger(
    f"aea.packages.{PUBLIC_ID.author}.contracts.{PUBLIC_ID.name}.contract"
)


class UniswapV2Router02(Contract):
    """The Uniswap V2 Router02 contract."""

    @classmethod
    def add_liquidity(
        cls,
        token_a: str,
        token_b: str,
        amount_a_desired: int,
        amount_b_desired: int,
        amount_a_min: int,
        amount_b_min: int,
        to: str,
        deadline,
    ) -> Optional[JSONLike]:
        """Add liquidity."""
        pass

    @classmethod
    def add_liquidity_ETH(
        cls,
        token: str,
        amount_token_desired: int,
        amount_token_min: int,
        amount_ETH_min: int,
        to: str,
        deadline,
    ) -> Optional[JSONLike]:
        """Add liquidity ETH."""
        pass

    @classmethod
    def remove_liquidity(
        cls,
        token_a: str,
        token_b: str,
        liquidity: int,
        amount_a_min: int,
        amount_b_min: int,
        to: str,
        deadline: int,
    ) -> Optional[JSONLike]:
        """Remove liquidity."""
        pass

    @classmethod
    def remove_liquidity_ETH(
        cls,
        token: str,
        liquidity: int,
        amount_token_min: int,
        amount_ETH_min: int,
        to: str,
        deadline: int,
    ) -> Optional[JSONLike]:
        """Remove liquidity ETH."""
        pass

    @classmethod
    def remove_liquidity_with_permit(
        cls,
        token_a: str,
        token_b: str,
        liquidity: int,
        amount_a_min: int,
        amount_b_min: int,
        to: str,
        deadline: int,
        approve_max: bool,
        v: int,
        r: bytes,
        s: bytes,
    ) -> Optional[JSONLike]:
        """Remove liquidity with permit."""
        pass

    @classmethod
    def remove_liquidity_ETH_with_permit(
        cls,
        token: str,
        liquidity: int,
        amount_token_min: int,
        amount_ETH_min: int,
        to: str,
        deadline: int,
        approve_max: bool,
        v: int,
        r: bytes,
        s: bytes,
    ) -> Optional[JSONLike]:
        """Remove liquidity ETH with permit."""
        pass

    @classmethod
    def remove_liquidity_ETH_Supporting_fee_on_transfer_tokens(
        cls,
        token: str,
        liquidity: int,
        amount_token_min: int,
        amount_ETH_min: int,
        to: str,
        deadline: int,
    ) -> Optional[JSONLike]:
        """Remove liquidity ETH supportinmg fee on transfer tokens."""
        pass

    @classmethod
    def remove_liquidity_ETH_with_permit_supporting_fee_on_transfer_tokens(
        cls,
        token: str,
        liquidity: int,
        amount_token_min: int,
        amount_ETH_min: int,
        to: str,
        deadline: int,
        approve_max: bool,
        v: int,
        r: bytes,
        s: bytes,
    ) -> Optional[JSONLike]:
        """Remove liquidity ETH with permit supportinmg fee on transfer tokens."""
        pass

    @classmethod
    def swap_exact_tokens_for_tokens(
        cls, amount_in: int, amount_out_min: int, path: list, to: str, deadline: int
    ) -> Optional[JSONLike]:
        """Swap exact tokens for tokens."""
        pass

    @classmethod
    def swap_tokens_for_exact_tokens(
        cls, amount_out: int, amount_in_max: int, path: list, to: str, deadline: int
    ) -> Optional[JSONLike]:
        """Swap tokens for exact tokens."""
        pass

    @classmethod
    def swap_exact_ETH_for_tokens(
        cls, amount_out_min: int, path: list, to: str, deadline: int
    ) -> Optional[JSONLike]:
        """Swap exact ETH for tokens."""
        pass

    @classmethod
    def swap_tokens_for_exact_ETH(
        cls, amount_out: int, amount_in_max: int, path: list, to: str, deadline: int
    ) -> Optional[JSONLike]:
        """Swap tokens for exact ETH."""
        pass

    @classmethod
    def swap_exact_tokens_for_ETH(
        cls, amount_in: int, amount_out_min: int, path: list, to: str, deadline: int
    ) -> Optional[JSONLike]:
        """Swap exact tokens for ETH."""
        pass

    @classmethod
    def swap_ETH_for_exact_tokens(
        cls, amount_out: int, path: list, to: str, deadline: int
    ) -> Optional[JSONLike]:
        """Swap ETH tokens for exact tokens."""
        pass

    @classmethod
    def swap_exact_tokens_for_tokens_supporting_fee_on_transfer_tokens(
        cls, amount_in: int, amount_out_min: int, path: list, to: str, deadline: int
    ) -> Optional[JSONLike]:
        """Swap exact tokens for tokens supporting fee on transfer tokens."""
        pass

    @classmethod
    def swap_exact_ETH_for_tokens_supporting_fee_on_transfer_tokens(
        cls, amount_out_min: int, path: list, to: str, deadline: int
    ) -> Optional[JSONLike]:
        """Swap exact ETH for tokens supporting fee on transfer tokens."""
        pass

    @classmethod
    def swap_exact_tokens_for_ETH_supporting_fee_on_transfer_tokens(
        cls, amount_in: int, amount_out_min: int, path: list, to: str, deadline: int
    ) -> Optional[JSONLike]:
        """Swap exact tokens for ETH supporting fee on transfer tokens."""
        pass

    @classmethod
    def quote(cls, amount_a: int, reserve_a: int, reserve_b: int) -> Optional[JSONLike]:
        """Quote."""
        pass

    @classmethod
    def get_amount_out(cls, amount_in: int, reserve_in, reserve_out: int) -> Optional[JSONLike]:
        """Get amount out."""
        pass

    @classmethod
    def get_amount_in(cls, amount_out: int, reserve_in, reserve_out: int) -> Optional[JSONLike]:
        """Get amount in."""
        pass

    @classmethod
    def get_amounts_out(cls, amount_in: int, path: list) -> Optional[JSONLike]:
        """Get amounts out."""
        pass

    @classmethod
    def get_amounts_in(cls, amount_out: int, path: list) -> Optional[JSONLike]:
        """Get amounts in."""
        pass
