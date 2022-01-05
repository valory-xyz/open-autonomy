# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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


def snake_to_camel(string: str) -> str:
    """Convert snake_case to camelCase"""

    if "_" in string:
        camel_case = string.split("_")
        for i in range(1, len(camel_case)):
            camel_case[i] = camel_case[i][0].upper() + camel_case[i][1:]
        string = ("").join(camel_case)
    return string


# pylint: disable=too-many-arguments,invalid-name,too-many-locals,too-many-public-methods
class UniswapV2Router02Contract(Contract):
    """The Uniswap V2 Router02 contract."""

    contract_id = PUBLIC_ID

    @classmethod
    def get_method_data(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        method_name: str,
        **kwargs: Any,
    ) -> Optional[JSONLike]:
        """
        Get a contract call encoded data.

        :param ledger_api: the ledger apis.
        :param contract_address: the contract address.
        :param method_name: the contract method name
        :param kwargs: the contract method args
        :return: the tx  # noqa: DAR202
        """
        instance = cls.get_instance(ledger_api, contract_address)

        method_name = snake_to_camel(method_name)
        kwargs = {snake_to_camel(key): value for key, value in kwargs.items()}

        try:
            # Get an ordered argument list from the method's abi
            method = instance.get_function_by_name(method_name)
            input_names = [i["name"] for i in method.abi["inputs"]]

            args = [kwargs[i] for i in input_names]
            # Encode and return the contract call
            data = instance.encodeABI(fn_name=method_name, args=args)
        except KeyError:  # pragma: nocover # TOFIX catch other exceptions which can occur
            return None
        return {"data": bytes.fromhex(data[2:])}  # type: ignore

    @classmethod
    def add_liquidity(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        sender_address: str,
        token_a: str,
        token_b: str,
        amount_a_desired: int,
        amount_b_desired: int,
        amount_a_min: int,
        amount_b_min: int,
        to_address: str,
        deadline: int,
        **kwargs: int,
    ) -> Optional[JSONLike]:
        """Add liquidity."""
        return cls._prepare_tx(
            ledger_api,
            contract_address,
            sender_address,
            "addLiquidity",
            token_a,
            token_b,
            amount_a_desired,
            amount_b_desired,
            amount_a_min,
            amount_b_min,
            to_address,
            deadline,
            **kwargs,
        )

    @classmethod
    def add_liquidity_ETH(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        sender_address: str,
        token: str,
        amount_token_desired: int,
        amount_token_min: int,
        amount_ETH_min: int,
        to_address: str,
        deadline: int,
        **kwargs: int,
    ) -> Optional[JSONLike]:
        """Add liquidity ETH."""
        return cls._prepare_tx(
            ledger_api,
            contract_address,
            sender_address,
            "addLiquidityETH",
            token,
            amount_token_desired,
            amount_token_min,
            amount_ETH_min,
            to_address,
            deadline,
            **kwargs,
        )

    @classmethod
    def remove_liquidity(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        sender_address: str,
        token_a: str,
        token_b: str,
        liquidity: int,
        amount_a_min: int,
        amount_b_min: int,
        to_address: str,
        deadline: int,
        **kwargs: int,
    ) -> Optional[JSONLike]:
        """Remove liquidity."""
        return cls._prepare_tx(
            ledger_api,
            contract_address,
            sender_address,
            "removeLiquidity",
            token_a,
            token_b,
            liquidity,
            amount_a_min,
            amount_b_min,
            to_address,
            deadline,
            **kwargs,
        )

    @classmethod
    def remove_liquidity_ETH(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        sender_address: str,
        token: str,
        liquidity: int,
        amount_token_min: int,
        amount_ETH_min: int,
        to_address: str,
        deadline: int,
        **kwargs: int,
    ) -> Optional[JSONLike]:
        """Remove liquidity ETH."""
        return cls._prepare_tx(
            ledger_api,
            contract_address,
            sender_address,
            "removeLiquidityETH",
            token,
            liquidity,
            amount_token_min,
            amount_ETH_min,
            to_address,
            deadline,
            **kwargs,
        )

    @classmethod
    def remove_liquidity_with_permit(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        sender_address: str,
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
        **kwargs: int,
    ) -> Optional[JSONLike]:
        """Remove liquidity with permit."""
        return cls._prepare_tx(
            ledger_api,
            contract_address,
            sender_address,
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
            **kwargs,
        )

    @classmethod
    def remove_liquidity_ETH_with_permit(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        sender_address: str,
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
        **kwargs: int,
    ) -> Optional[JSONLike]:
        """Remove liquidity ETH with permit."""
        return cls._prepare_tx(
            ledger_api,
            contract_address,
            sender_address,
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
            **kwargs,
        )

    @classmethod
    def remove_liquidity_ETH_Supporting_fee_on_transfer_tokens(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        sender_address: str,
        token: str,
        liquidity: int,
        amount_token_min: int,
        amount_ETH_min: int,
        to_address: str,
        deadline: int,
        **kwargs: int,
    ) -> Optional[JSONLike]:
        """Remove liquidity ETH supportinmg fee on transfer tokens."""
        return cls._prepare_tx(
            ledger_api,
            contract_address,
            sender_address,
            "removeLiquidityETHSupportingFeeOnTransferTokens",
            token,
            liquidity,
            amount_token_min,
            amount_ETH_min,
            to_address,
            deadline,
            **kwargs,
        )

    @classmethod
    def remove_liquidity_ETH_with_permit_supporting_fee_on_transfer_tokens(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        sender_address: str,
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
        **kwargs: int,
    ) -> Optional[JSONLike]:
        """Remove liquidity ETH with permit supportinmg fee on transfer tokens."""
        return cls._prepare_tx(
            ledger_api,
            contract_address,
            sender_address,
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
            **kwargs,
        )

    @classmethod
    def swap_exact_tokens_for_tokens(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        sender_address: str,
        amount_in: int,
        amount_out_min: int,
        path: list,
        to_address: str,
        deadline: int,
        **kwargs: int,
    ) -> Optional[JSONLike]:
        """Swap exact tokens for tokens."""
        return cls._prepare_tx(
            ledger_api,
            contract_address,
            sender_address,
            "swapExactTokensForTokens",
            amount_in,
            amount_out_min,
            path,
            to_address,
            deadline,
            **kwargs,
        )

    @classmethod
    def swap_tokens_for_exact_tokens(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        sender_address: str,
        amount_out: int,
        amount_in_max: int,
        path: list,
        to_address: str,
        deadline: int,
        **kwargs: int,
    ) -> Optional[JSONLike]:
        """Swap tokens for exact tokens."""
        return cls._prepare_tx(
            ledger_api,
            contract_address,
            sender_address,
            "swapTokensForExactTokens",
            amount_out,
            amount_in_max,
            path,
            to_address,
            deadline,
            **kwargs,
        )

    @classmethod
    def swap_exact_ETH_for_tokens(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        sender_address: str,
        amount_out_min: int,
        path: list,
        to_address: str,
        deadline: int,
        **kwargs: int,
    ) -> Optional[JSONLike]:
        """Swap exact ETH for tokens."""
        return cls._prepare_tx(
            ledger_api,
            contract_address,
            sender_address,
            "swapExactETHForTokens",
            amount_out_min,
            path,
            to_address,
            deadline,
            **kwargs,
        )

    @classmethod
    def swap_tokens_for_exact_ETH(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        sender_address: str,
        amount_out: int,
        amount_in_max: int,
        path: list,
        to_address: str,
        deadline: int,
        **kwargs: int,
    ) -> Optional[JSONLike]:
        """Swap tokens for exact ETH."""
        return cls._prepare_tx(
            ledger_api,
            contract_address,
            sender_address,
            "swapTokensForExactETH",
            amount_out,
            amount_in_max,
            path,
            to_address,
            deadline,
            **kwargs,
        )

    @classmethod
    def swap_exact_tokens_for_ETH(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        sender_address: str,
        amount_in: int,
        amount_out_min: int,
        path: list,
        to_address: str,
        deadline: int,
        **kwargs: int,
    ) -> Optional[JSONLike]:
        """Swap exact tokens for ETH."""
        return cls._prepare_tx(
            ledger_api,
            contract_address,
            sender_address,
            "swapExactTokensForETH",
            amount_in,
            amount_out_min,
            path,
            to_address,
            deadline,
            **kwargs,
        )

    @classmethod
    def swap_ETH_for_exact_tokens(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        sender_address: str,
        amount_out: int,
        path: list,
        to_address: str,
        deadline: int,
        **kwargs: int,
    ) -> Optional[JSONLike]:
        """Swap ETH tokens for exact tokens."""
        return cls._prepare_tx(
            ledger_api,
            contract_address,
            sender_address,
            "swapETHForExactTokens",
            amount_out,
            path,
            to_address,
            deadline,
            **kwargs,
        )

    @classmethod
    def swap_exact_tokens_for_tokens_supporting_fee_on_transfer_tokens(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        sender_address: str,
        amount_in: int,
        amount_out_min: int,
        path: list,
        to_address: str,
        deadline: int,
        **kwargs: int,
    ) -> Optional[JSONLike]:
        """Swap exact tokens for tokens supporting fee on transfer tokens."""
        return cls._prepare_tx(
            ledger_api,
            contract_address,
            sender_address,
            "swapExactTokensForTokensSupportingFeeOnTransferTokens",
            amount_in,
            amount_out_min,
            path,
            to_address,
            deadline,
            **kwargs,
        )

    @classmethod
    def swap_exact_ETH_for_tokens_supporting_fee_on_transfer_tokens(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        sender_address: str,
        amount_out_min: int,
        path: list,
        to_address: str,
        deadline: int,
        **kwargs: int,
    ) -> Optional[JSONLike]:
        """Swap exact ETH for tokens supporting fee on transfer tokens."""
        return cls._prepare_tx(
            ledger_api,
            contract_address,
            sender_address,
            "swapExactETHForTokensSupportingFeeOnTransferTokens",
            amount_out_min,
            path,
            to_address,
            deadline,
            **kwargs,
        )

    @classmethod
    def swap_exact_tokens_for_ETH_supporting_fee_on_transfer_tokens(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        sender_address: str,
        amount_in: int,
        amount_out_min: int,
        path: list,
        to_address: str,
        deadline: int,
        **kwargs: int,
    ) -> Optional[JSONLike]:
        """Swap exact tokens for ETH supporting fee on transfer tokens."""
        return cls._prepare_tx(
            ledger_api,
            contract_address,
            sender_address,
            "swapExactTokensForETHSupportingFeeOnTransferTokens",
            amount_in,
            amount_out_min,
            path,
            to_address,
            deadline,
            **kwargs,
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
    def _prepare_tx(  # pylint: disable=too-many-arguments
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        sender_address: str,
        method_name: str,
        *method_args: Any,
        eth_value: int = 0,
        gas: Optional[int] = None,
        gas_price: Optional[int] = None,
        max_fee_per_gas: Optional[int] = None,
        max_priority_fee_per_gas: Optional[int] = None,
    ) -> Optional[JSONLike]:
        """Prepare tx method."""
        contract = cls.get_instance(ledger_api, contract_address)
        method = getattr(contract.functions, method_name)
        tx = method(*method_args)
        tx = cls._build_transaction(
            ledger_api,
            sender_address,
            tx,
            eth_value,
            gas,
            gas_price,
            max_fee_per_gas,
            max_priority_fee_per_gas,
        )
        return tx

    @classmethod
    def _build_transaction(  # pylint: disable=too-many-arguments
        cls,
        ledger_api: LedgerApi,
        sender_address: str,
        tx: Any,
        eth_value: int = 0,
        gas: Optional[int] = None,
        gas_price: Optional[int] = None,
        max_fee_per_gas: Optional[int] = None,
        max_priority_fee_per_gas: Optional[int] = None,
    ) -> Optional[JSONLike]:
        """Build transaction method."""
        nonce = ledger_api.api.eth.get_transaction_count(sender_address)
        tx_params = {
            "nonce": nonce,
            "value": eth_value,
        }
        if gas is not None:
            tx_params["gas"] = gas
        if gas_price is not None:
            tx_params["gasPrice"] = gas_price
        if max_fee_per_gas is not None:
            tx_params["maxFeePerGas"] = max_fee_per_gas  # pragma: nocover
        if max_priority_fee_per_gas is not None:
            tx_params[
                "maxPriorityFeePerGas"
            ] = max_priority_fee_per_gas  # pragma: nocover
        tx = tx.buildTransaction(tx_params)
        return tx
