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

"""This module contains the behaviours for the 'liquidity_provision' skill."""
import json
from abc import ABC
from typing import Any, Dict, Generator, List, Optional, Set, Type, cast

from hexbytes import HexBytes

from packages.valory.contracts.gnosis_safe.contract import (
    GnosisSafeContract,
    SafeOperation,
)
from packages.valory.contracts.multisend.contract import (
    MultiSendContract,
    MultiSendOperation,
)
from packages.valory.contracts.uniswap_v2_erc20.contract import UniswapV2ERC20Contract
from packages.valory.contracts.uniswap_v2_router_02.contract import (
    UniswapV2Router02Contract,
)
from packages.valory.protocols.contract_api import ContractApiMessage
from packages.valory.skills.abstract_round_abci.behaviours import (
    AbstractRoundBehaviour,
    BaseState,
)
from packages.valory.skills.abstract_round_abci.utils import BenchmarkTool
from packages.valory.skills.liquidity_provision.composition import (
    LiquidityProvisionAbciApp,
)
from packages.valory.skills.liquidity_provision.models import Params
from packages.valory.skills.liquidity_provision.payloads import (
    StrategyEvaluationPayload,
    StrategyType,
    TransactionHashPayload,
)
from packages.valory.skills.liquidity_provision.rounds import (
    EnterPoolTransactionHashRound,
    ExitPoolTransactionHashRound,
    LiquidityRebalancingAbciApp,
    PeriodState,
    SleepRound,
    StrategyEvaluationRound,
    SwapBackTransactionHashRound,
)
from packages.valory.skills.registration_abci.behaviours import (
    AgentRegistrationRoundBehaviour,
    TendermintHealthcheckBehaviour,
)
from packages.valory.skills.safe_deployment_abci.behaviours import (
    SafeDeploymentRoundBehaviour,
)
from packages.valory.skills.transaction_settlement_abci.behaviours import (
    TransactionSettlementRoundBehaviour,
)


ETHER_VALUE = 0  # TOFIX
SAFE_TX_GAS = 4000000  # TOFIX
MAX_ALLOWANCE = 2 ** 256 - 1
CURRENT_BLOCK_TIMESTAMP = 0  # TOFIX
WETH_ADDRESS = "0xDc64a140Aa3E981100a9becA4E685f962f0cF6C9"  # nosec
TOKEN_A_ADDRESS = "0x0DCd1Bf9A1b36cE34237eEaFef220932846BCD82"  # nosec
TOKEN_B_ADDRESS = "0x9A676e781A523b5d0C0e43731313A708CB607508"  # nosec
LP_TOKEN_ADDRESS = "0x50CD56fb094F8f06063066a619D898475dD3EedE"  # nosec
DEFAULT_MINTER = "0x0000000000000000000000000000000000000000"  # nosec
AB_POOL_ADDRESS = "0x86A6C37D3E868580a65C723AAd7E0a945E170416"  # nosec
SLEEP_SECONDS = 60

benchmark_tool = BenchmarkTool()


def parse_tx_token_balance(
    transfer_logs: List[Dict],
    token_address: str,
    source_address: str,
    destination_address: str,
) -> int:
    """
    Returns the transfered token amount from one address to another given a list of transactions.

    :param transfer_logs: a list of transactions.
    :param token_address: the token address.
    :param source_address: the source address.
    :param destination_address: the destination address.
    :return: the transfered amount
    """

    token_events = list(
        filter(
            lambda log: log["token_address"] == token_address
            and log["from"] == source_address
            and log["to"] == destination_address,
            transfer_logs,
        )
    )
    return sum([event["value"] for event in token_events])


class LiquidityProvisionBaseBehaviour(BaseState, ABC):
    """Base state behaviour for the liquidity provision skill."""

    @property
    def period_state(self) -> PeriodState:
        """Return the period state."""
        return cast(PeriodState, super().period_state)

    @property
    def params(self) -> Params:
        """Return the params."""
        return cast(Params, super().params)

    def get_swap_tx_data(  # pylint: disable=too-many-arguments
        self,
        is_input_native: bool,
        is_output_native: bool,
        exact_input: bool,
        path: List[str],
        deadline: int,
        amount_in: Optional[int] = None,
        amount_out: Optional[int] = None,
        amount_in_max: Optional[int] = None,
        amount_out_min: Optional[int] = None,
        eth_value: Optional[int] = None,
    ) -> Generator[None, None, Optional[Dict]]:
        """
        Return the swap tx data.

        :param is_input_native: flag to check if the first token is native
        :param is_output_native: flag to check if the second token is native
        :param exact_input: flag to check if the exact amount belongs to the input or the output
        :param path: the swap path
        :param deadline: the tx deadline
        :param amount_in: the amount in
        :param amount_out: the amount out
        :param amount_in_max: the max amount in
        :param amount_out_min: the min amount out
        :param eth_value: the tx value, also used as amount_or amount_in_max in for some cases
        :return: None if required parameters are missing
        :yield: the tx data
        """

        if (  # pylint: disable=too-many-boolean-expressions
            (is_input_native and is_output_native)
            or (is_input_native and eth_value is None)
            or (not is_input_native and exact_input and amount_in is None)
            or (not is_input_native and not exact_input and amount_in_max is None)
            or (exact_input and amount_out_min is None)
            or (not exact_input and amount_out is None)
        ):
            self.context.logger.error("Swap data is not correct.")
            raise RuntimeError("Swap has been called with incorrect/missing parameters")
        method_name = (
            f'swap_exact_{"ETH" if is_input_native else "tokens"}_for_{"ETH" if is_output_native else "tokens"}'
            if exact_input
            else f'swap_{"ETH" if is_input_native else "tokens"}_for_exact_{"ETH" if is_output_native else "tokens"}'
        )

        contract_api_kwargs: Dict[str, Any] = dict(
            method_name=method_name,
            path=path,
            to=self.period_state.safe_contract_address,
            deadline=deadline,
        )

        # Input amounts for native tokens are read from the msg.value field.
        # We only need to specify them here for not native tokens.
        if not is_input_native and exact_input:
            contract_api_kwargs["amount_in"] = int(amount_in)  # type: ignore

        if not is_input_native and not exact_input:
            contract_api_kwargs["amount_in_max"] = int(amount_in_max)  # type: ignore

        # Output amounts
        if exact_input:
            contract_api_kwargs["amount_out_min"] = int(amount_out_min)  # type: ignore
        else:
            contract_api_kwargs["amount_out"] = int(amount_out)  # type: ignore

        contract_api_msg = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
            contract_address=self.period_state.router_contract_address,
            contract_id=str(UniswapV2Router02Contract.contract_id),
            contract_callable="get_method_data",
            **contract_api_kwargs,
        )
        swap_data = cast(bytes, contract_api_msg.raw_transaction.body["data"])

        return {
            "operation": MultiSendOperation.CALL,
            "to": self.period_state.router_contract_address,
            "value": eth_value
            if is_input_native
            else 0,  # Input amount for native tokens
            "data": HexBytes(swap_data.hex()),
        }

    def get_tx_result(self) -> Generator[None, None, Optional[list]]:
        """Transaction transfer result."""
        strategy = self.period_state.most_voted_strategy
        contract_api_msg = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_STATE,  # type: ignore
            contract_address=strategy["pair"]["token_LP"]["address"],
            contract_id=str(UniswapV2ERC20Contract.contract_id),
            contract_callable="get_transaction_transfer_logs",
            tx_hash=self.period_state.final_tx_hash,
            target_address=self.period_state.safe_contract_address,
        )
        if contract_api_msg.performative != ContractApiMessage.Performative.STATE:
            return []  # pragma: nocover
        transfers = cast(list, contract_api_msg.state.body["logs"])

        transfer_log_message = (
            f"The tx with hash {self.period_state.final_tx_hash} ended with the following transfers.\n"
            f"Transfers: {str(transfers)}\n"
        )
        self.context.logger.info(transfer_log_message)
        return transfers


def get_dummy_strategy() -> dict:
    """Get a dummy strategy."""
    strategy = {
        "action": StrategyType.ENTER.value,
        "safe_nonce": 0,
        "safe_tx_gas": SAFE_TX_GAS,
        "deadline": CURRENT_BLOCK_TIMESTAMP + 300,  # 5 min into future
        "chain": "Ethereum",
        "base": {
            "ticker": "WETH",
            "address": WETH_ADDRESS,
            "amount_in_max_a": int(1e4),
            "amount_min_after_swap_back_a": int(1e2),
            "amount_in_max_b": int(1e4),
            "amount_min_after_swap_back_b": int(1e2),
            "is_native": False,
            "set_allowance": MAX_ALLOWANCE,
            "remove_allowance": 0,
        },
        "pair": {
            "token_LP": {
                "address": LP_TOKEN_ADDRESS,
                "set_allowance": MAX_ALLOWANCE,
                "remove_allowance": 0,
            },
            "token_a": {
                "ticker": "TKA",
                "address": TOKEN_A_ADDRESS,
                "amount_after_swap": int(1e3),
                "amount_min_after_add_liq": int(0.5e3),
                "is_native": False,  # if one of the two tokens is native, A must be the one
                "set_allowance": MAX_ALLOWANCE,
                "remove_allowance": 0,
            },
            "token_b": {
                "ticker": "TKB",
                "address": TOKEN_B_ADDRESS,
                "amount_after_swap": int(1e3),
                "amount_min_after_add_liq": int(0.5e3),
                "is_native": False,  # if one of the two tokens is native, A must be the one
                "set_allowance": MAX_ALLOWANCE,
                "remove_allowance": 0,
            },
        },
    }
    return strategy


class StrategyEvaluationBehaviour(LiquidityProvisionBaseBehaviour):
    """Evaluate the financial strategy."""

    state_id = "strategy_evaluation"
    matching_round = StrategyEvaluationRound

    def async_act(self) -> Generator:
        """Do the action."""

        with benchmark_tool.measure(
            self,
        ).local():

            # Get the previous strategy or use the dummy one
            # For now, the app will loop between enter-exit-swap_back,
            # unless we start with WAIT. Then it will keep waiting.
            strategy: dict = {}
            try:
                strategy = self.period_state.most_voted_strategy

                if strategy["action"] == StrategyType.ENTER.value:
                    strategy["action"] = StrategyType.EXIT.value

                elif strategy["action"] == StrategyType.EXIT.value:
                    strategy["action"] = StrategyType.SWAP_BACK.value

                elif strategy["action"] == StrategyType.SWAP_BACK.value:
                    strategy["action"] = StrategyType.ENTER.value

            # An exception will occur during the first run as no strategy was set
            except ValueError:
                strategy = get_dummy_strategy()

            # Log the new strategy
            if strategy["action"] == StrategyType.WAIT.value:  # pragma: nocover
                self.context.logger.info("Current strategy is still optimal. Waiting.")

            if strategy["action"] == StrategyType.ENTER.value:
                self.context.logger.info(
                    "Performing strategy update: moving into "
                    + f"{strategy['pair']['token_a']['ticker']}-{strategy['pair']['token_b']['ticker']} (pool {self.period_state.router_contract_address})"
                )

            if strategy["action"] == StrategyType.EXIT.value:  # pragma: nocover
                self.context.logger.info(
                    "Performing strategy update: moving out of "
                    + f"{strategy['pair']['token_a']['ticker']}-{strategy['pair']['token_b']['ticker']} (pool {self.period_state.router_contract_address})"
                )

            if strategy["action"] == StrategyType.SWAP_BACK.value:  # pragma: nocover
                self.context.logger.info(
                    f"Performing strategy update: swapping back {strategy['pair']['token_a']['ticker']}, {strategy['pair']['token_b']['ticker']}"
                )

            payload = StrategyEvaluationPayload(self.context.agent_address, strategy)

        with benchmark_tool.measure(
            self,
        ).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class SleepBehaviour(LiquidityProvisionBaseBehaviour):
    """Wait for a predefined amount of time."""

    state_id = "sleep"
    matching_round = SleepRound

    def async_act(self) -> Generator:
        """Do the action."""

        with benchmark_tool.measure(
            self,
        ).local():

            yield from self.sleep(SLEEP_SECONDS)

        with benchmark_tool.measure(
            self,
        ).consensus():
            yield from self.wait_until_round_end()

        self.set_done()


class EnterPoolTransactionHashBehaviour(LiquidityProvisionBaseBehaviour):
    """Prepare the transaction hash for entering the liquidity pool

    The expected transfers derived from this behaviour are
    Safe         ->  A-Base-pool : Base tokens
    A-Base-pool  ->  Safe        : A tokens
    Safe         ->  B-Base-pool : Base tokens
    B-Base-pool  ->  Safe        : B tokens
    Safe         ->  A-B-pool    : A tokens
    Safe         ->  A-B-pool    : B tokens
    A-B-pool Minter       ->  Safe        : AB_LP tokens
    """

    state_id = "enter_pool_tx_hash"
    matching_round = EnterPoolTransactionHashRound

    def async_act(self) -> Generator:
        """
        Do the action.

        Steps:
        - Request the transaction hash for the safe transaction. This is the
          hash that needs to be signed by a threshold of agents.
        - Send the transaction hash as a transaction and wait for it to be mined.
        - Wait until ABCI application transitions to the next round.
        - Go to the next behaviour state (set done event).
        """

        with benchmark_tool.measure(
            self,
        ).local():

            strategy = self.period_state.most_voted_strategy

            # Prepare a uniswap tx list. We should check what token balances we have at this point.
            # It is possible that we don't need to swap. For now let's assume we have just USDT
            # and always swap back to it.
            multi_send_txs = []

            # Add allowance for base token
            if (
                not strategy["base"]["is_native"]
                and "set_allowance" in strategy["base"]
            ):
                contract_api_msg = yield from self.get_contract_api_response(
                    performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                    contract_address=strategy["base"]["address"],
                    contract_id=str(UniswapV2ERC20Contract.contract_id),
                    contract_callable="get_method_data",
                    method_name="approve",
                    spender=self.period_state.router_contract_address,
                    value=strategy["base"]["set_allowance"],
                )
                allowance_base_data = cast(
                    bytes, contract_api_msg.raw_transaction.body["data"]
                )
                multi_send_txs.append(
                    {
                        "operation": MultiSendOperation.CALL,
                        "to": strategy["base"]["address"],
                        "value": 0,
                        "data": HexBytes(allowance_base_data.hex()),
                    }
                )

            # Swap first token
            if strategy["pair"]["token_a"]["ticker"] != strategy["base"]["ticker"]:

                swap_tx_data = yield from self.get_swap_tx_data(
                    is_input_native=strategy["base"]["is_native"],
                    is_output_native=strategy["pair"]["token_a"]["is_native"],
                    exact_input=False,
                    amount_out=strategy["pair"]["token_a"]["amount_after_swap"],
                    amount_in_max=strategy["base"]["amount_in_max_a"],
                    eth_value=strategy["base"]["amount_in_max_a"]
                    if strategy["base"]["is_native"]
                    else 0,
                    path=[
                        strategy["base"]["address"],
                        strategy["pair"]["token_a"]["address"],
                    ],
                    deadline=strategy["deadline"],
                )

                if swap_tx_data:
                    multi_send_txs.append(swap_tx_data)

            # Swap second token
            if strategy["pair"]["token_b"]["ticker"] != strategy["base"]["ticker"]:

                swap_tx_data = yield from self.get_swap_tx_data(
                    is_input_native=strategy["base"]["is_native"],
                    is_output_native=strategy["pair"]["token_b"]["is_native"],
                    exact_input=False,
                    amount_out=strategy["pair"]["token_b"]["amount_after_swap"],
                    amount_in_max=strategy["base"]["amount_in_max_b"],
                    eth_value=strategy["base"]["amount_in_max_b"]
                    if strategy["base"]["is_native"]
                    else 0,
                    path=[
                        strategy["base"]["address"],
                        strategy["pair"]["token_b"]["address"],
                    ],
                    deadline=strategy["deadline"],
                )

                if swap_tx_data:
                    multi_send_txs.append(swap_tx_data)

            # Add allowance for token A (only if not native)
            if (
                not strategy["pair"]["token_a"]["is_native"]
                and "set_allowance" in strategy["pair"]["token_a"]
            ):
                contract_api_msg = yield from self.get_contract_api_response(
                    performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                    contract_address=strategy["pair"]["token_a"]["address"],
                    contract_id=str(UniswapV2ERC20Contract.contract_id),
                    contract_callable="get_method_data",
                    method_name="approve",
                    spender=self.period_state.router_contract_address,
                    value=strategy["pair"]["token_a"]["set_allowance"],
                )
                allowance_a_data = cast(
                    bytes, contract_api_msg.raw_transaction.body["data"]
                )
                multi_send_txs.append(
                    {
                        "operation": MultiSendOperation.CALL,
                        "to": strategy["pair"]["token_a"]["address"],
                        "value": 0,
                        "data": HexBytes(allowance_a_data.hex()),
                    }
                )

            # Add allowance for token B (only if not native)
            if (
                not strategy["pair"]["token_b"]["is_native"]
                and "set_allowance" in strategy["pair"]["token_b"]
            ):
                contract_api_msg = yield from self.get_contract_api_response(
                    performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                    contract_address=strategy["pair"]["token_b"]["address"],
                    contract_id=str(UniswapV2ERC20Contract.contract_id),
                    contract_callable="get_method_data",
                    method_name="approve",
                    spender=self.period_state.router_contract_address,
                    value=strategy["pair"]["token_b"]["set_allowance"],
                )
                allowance_b_data = cast(
                    bytes, contract_api_msg.raw_transaction.body["data"]
                )
                multi_send_txs.append(
                    {
                        "operation": MultiSendOperation.CALL,
                        "to": strategy["pair"]["token_b"]["address"],
                        "value": 0,
                        "data": HexBytes(allowance_b_data.hex()),
                    }
                )

            # Add liquidity
            if strategy["pair"]["token_a"]["is_native"]:
                contract_api_msg = yield from self.get_contract_api_response(
                    performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                    contract_address=self.period_state.router_contract_address,
                    contract_id=str(UniswapV2Router02Contract.contract_id),
                    contract_callable="get_method_data",
                    method_name="add_liquidity_ETH",
                    token=strategy["pair"]["token_b"]["address"],
                    amount_token_desired=int(
                        strategy["pair"]["token_b"]["amount_after_swap"]
                    ),
                    amount_token_min=int(
                        strategy["pair"]["token_b"]["amount_min_after_add_liq"]
                    ),
                    amount_ETH_min=int(
                        strategy["pair"]["token_a"]["amount_min_after_add_liq"]
                    ),
                    to=self.period_state.safe_contract_address,
                    deadline=strategy["deadline"],
                )
                liquidity_data = cast(
                    bytes, contract_api_msg.raw_transaction.body["data"]
                )
                multi_send_txs.append(
                    {
                        "operation": MultiSendOperation.CALL,
                        "to": self.period_state.router_contract_address,
                        "value": int(
                            strategy["pair"]["token_a"]["amount_min_after_add_liq"]
                        ),
                        "data": HexBytes(liquidity_data.hex()),
                    }
                )

            else:
                contract_api_msg = yield from self.get_contract_api_response(
                    performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                    contract_address=self.period_state.router_contract_address,
                    contract_id=str(UniswapV2Router02Contract.contract_id),
                    contract_callable="get_method_data",
                    method_name="add_liquidity",
                    token_a=strategy["pair"]["token_a"]["address"],
                    token_b=strategy["pair"]["token_b"]["address"],
                    amount_a_desired=int(
                        strategy["pair"]["token_a"]["amount_after_swap"]
                    ),
                    amount_b_desired=int(
                        strategy["pair"]["token_b"]["amount_after_swap"]
                    ),
                    amount_a_min=int(
                        strategy["pair"]["token_a"]["amount_min_after_add_liq"]
                    ),
                    amount_b_min=int(
                        strategy["pair"]["token_b"]["amount_min_after_add_liq"]
                    ),
                    to=self.period_state.safe_contract_address,
                    deadline=strategy["deadline"],  # 5 min into the future
                )
                liquidity_data = cast(
                    bytes, contract_api_msg.raw_transaction.body["data"]
                )
                multi_send_txs.append(
                    {
                        "operation": MultiSendOperation.CALL,
                        "to": self.period_state.router_contract_address,
                        "value": 0,
                        "data": HexBytes(liquidity_data.hex()),
                    }
                )

            # Get the tx list data from multisend contract
            contract_api_msg = yield from self.get_contract_api_response(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=self.period_state.safe_contract_address,
                contract_id=str(MultiSendContract.contract_id),
                contract_callable="get_tx_data",
                multi_send_txs=multi_send_txs,
            )
            multisend_data = cast(str, contract_api_msg.raw_transaction.body["data"])
            multisend_data = multisend_data[2:]
            self.context.logger.info(f"Multisend data: {multisend_data}")
            # Get the tx hash from Gnosis Safe contract
            contract_api_msg = yield from self.get_contract_api_response(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=self.period_state.safe_contract_address,
                contract_id=str(GnosisSafeContract.contract_id),
                contract_callable="get_raw_safe_transaction_hash",
                to_address=self.period_state.multisend_contract_address,
                value=ETHER_VALUE,
                data=bytes.fromhex(multisend_data),
                operation=SafeOperation.DELEGATE_CALL.value,
                safe_tx_gas=strategy["safe_tx_gas"],
                safe_nonce=strategy["safe_nonce"],
            )
            safe_tx_hash = cast(str, contract_api_msg.raw_transaction.body["tx_hash"])
            safe_tx_hash = safe_tx_hash[2:]
            self.context.logger.info(f"Hash of the Safe transaction: {safe_tx_hash}")
            payload = TransactionHashPayload(
                sender=self.context.agent_address,
                tx_hash=json.dumps(
                    {"tx_hash": safe_tx_hash, "tx_data": multisend_data}
                ),  # TOFIX
            )

        with benchmark_tool.measure(
            self,
        ).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class ExitPoolTransactionHashBehaviour(LiquidityProvisionBaseBehaviour):
    """Prepare the transaction hash for exiting the liquidity pool

    The expected transfers derived from this behaviour are
    Safe         ->  A-B-pool    : AB_LP tokens
    AB_LP        ->  Safe        : A tokens
    AB_LP        ->  Safe        : B tokens
    """

    state_id = "exit_pool_tx_hash"
    matching_round = ExitPoolTransactionHashRound

    def async_act(self) -> Generator:  # pylint: disable=too-many-statements
        """
        Do the action.

        Steps:
        - Request the transaction hash for the safe transaction. This is the
          hash that needs to be signed by a threshold of agents.
        - Send the transaction hash as a transaction and wait for it to be mined.
        - Wait until ABCI application transitions to the next round.
        - Go to the next behaviour state (set done event).
        """

        with benchmark_tool.measure(
            self,
        ).local():

            strategy = self.period_state.most_voted_strategy

            # Get previous transaction's results
            transfers = yield from self.get_tx_result()
            transfers = transfers if transfers else []

            amount_a_sent: int = parse_tx_token_balance(
                transfer_logs=transfers,
                token_address=strategy["pair"]["token_a"]["address"],
                source_address=self.period_state.safe_contract_address,
                destination_address=self.period_state.router_contract_address,
            )
            amount_b_sent: int = parse_tx_token_balance(
                transfer_logs=transfers,
                token_address=strategy["pair"]["token_b"]["address"],
                source_address=self.period_state.safe_contract_address,
                destination_address=self.period_state.router_contract_address,
            )
            amount_liquidity_received: int = parse_tx_token_balance(
                transfer_logs=transfers,
                token_address=strategy["pair"]["token_LP"]["address"],
                source_address=DEFAULT_MINTER,
                destination_address=self.period_state.safe_contract_address,
            )

            # Prepare a uniswap tx list. We should check what token balances we have at this point.
            # It is possible that we don't need to swap. For now let's assume we have just USDT
            # and always swap back to it.
            multi_send_txs = []

            # Add allowance for LP token to be spent by the router
            contract_api_msg = yield from self.get_contract_api_response(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=strategy["pair"]["token_LP"]["address"],
                contract_id=str(UniswapV2ERC20Contract.contract_id),
                contract_callable="get_method_data",
                method_name="approve",
                spender=self.period_state.router_contract_address,
                value=strategy["pair"]["token_LP"]["set_allowance"],
            )
            allowance_lp_data = cast(
                bytes, contract_api_msg.raw_transaction.body["data"]
            )
            multi_send_txs.append(
                {
                    "operation": MultiSendOperation.CALL,
                    "to": strategy["pair"]["token_LP"]["address"],
                    "value": 0,
                    "data": HexBytes(allowance_lp_data.hex()),
                }
            )

            # Remove liquidity
            if strategy["pair"]["token_a"]["is_native"]:

                contract_api_msg = yield from self.get_contract_api_response(
                    performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                    contract_address=self.period_state.router_contract_address,
                    contract_id=str(UniswapV2Router02Contract.contract_id),
                    contract_callable="get_method_data",
                    method_name="remove_liquidity_ETH",
                    token=strategy["pair"]["token_b"]["address"],
                    liquidity=amount_liquidity_received,
                    amount_token_min=int(amount_b_sent),
                    amount_ETH_min=int(amount_a_sent),
                    to=self.period_state.safe_contract_address,
                    deadline=strategy["deadline"],
                )
                liquidity_data = cast(
                    bytes, contract_api_msg.raw_transaction.body["data"]
                )
                multi_send_txs.append(
                    {
                        "operation": MultiSendOperation.CALL,
                        "to": self.period_state.router_contract_address,
                        "value": 0,
                        "data": HexBytes(liquidity_data.hex()),
                    }
                )

            else:

                contract_api_msg = yield from self.get_contract_api_response(
                    performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                    contract_address=self.period_state.router_contract_address,
                    contract_id=str(UniswapV2Router02Contract.contract_id),
                    contract_callable="get_method_data",
                    method_name="remove_liquidity",
                    token_a=strategy["pair"]["token_a"]["address"],
                    token_b=strategy["pair"]["token_b"]["address"],
                    liquidity=amount_liquidity_received,
                    amount_a_min=int(amount_a_sent),
                    amount_b_min=int(amount_b_sent),
                    to=self.period_state.safe_contract_address,
                    deadline=strategy["deadline"],
                )
                liquidity_data = cast(
                    bytes, contract_api_msg.raw_transaction.body["data"]
                )
                multi_send_txs.append(
                    {
                        "operation": MultiSendOperation.CALL,
                        "to": self.period_state.router_contract_address,
                        "value": 0,
                        "data": HexBytes(liquidity_data.hex()),
                    }
                )

            # Remove allowance for LP token
            if "remove_allowance" in strategy["pair"]["token_LP"]:
                contract_api_msg = yield from self.get_contract_api_response(
                    performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                    contract_address=strategy["pair"]["token_LP"]["address"],
                    contract_id=str(UniswapV2ERC20Contract.contract_id),
                    contract_callable="get_method_data",
                    method_name="approve",
                    spender=self.period_state.router_contract_address,
                    value=strategy["pair"]["token_LP"]["remove_allowance"],
                )
                allowance_lp_data = cast(
                    bytes, contract_api_msg.raw_transaction.body["data"]
                )
                multi_send_txs.append(
                    {
                        "operation": MultiSendOperation.CALL,
                        "to": strategy["pair"]["token_LP"]["address"],
                        "value": 0,
                        "data": HexBytes(allowance_lp_data.hex()),
                    }
                )

            # Get the tx list data from multisend contract
            contract_api_msg = yield from self.get_contract_api_response(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=self.period_state.safe_contract_address,
                contract_id=str(MultiSendContract.contract_id),
                contract_callable="get_tx_data",
                multi_send_txs=multi_send_txs,
            )
            multisend_data = cast(str, contract_api_msg.raw_transaction.body["data"])
            multisend_data = multisend_data[2:]
            self.context.logger.info(f"Multisend data: {multisend_data}")
            # Get the tx hash from Gnosis Safe contract
            contract_api_msg = yield from self.get_contract_api_response(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=self.period_state.safe_contract_address,
                contract_id=str(GnosisSafeContract.contract_id),
                contract_callable="get_raw_safe_transaction_hash",
                to_address=self.period_state.multisend_contract_address,
                value=ETHER_VALUE,
                data=bytes.fromhex(multisend_data),
                operation=SafeOperation.DELEGATE_CALL.value,
                safe_tx_gas=strategy["safe_tx_gas"],
                safe_nonce=strategy["safe_nonce"],
            )
            safe_tx_hash = cast(str, contract_api_msg.raw_transaction.body["tx_hash"])
            safe_tx_hash = safe_tx_hash[2:]
            self.context.logger.info(f"Hash of the Safe transaction: {safe_tx_hash}")
            payload = TransactionHashPayload(
                sender=self.context.agent_address,
                tx_hash=json.dumps(
                    {"tx_hash": safe_tx_hash, "tx_data": multisend_data}
                ),  # TOFIX
            )

        with benchmark_tool.measure(
            self,
        ).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class SwapBackTransactionHashBehaviour(LiquidityProvisionBaseBehaviour):
    """Prepare the transaction hash for swapping back assets

    The expected transfers derived from this behaviour are
    Safe         ->  A-Base-pool    : A tokens
    A-Base-pool  ->  Safe           : Base tokens
    Safe         ->  B-Base-pool    : B tokens
    B-Base-pool  ->  Safe           : Base tokens
    """

    state_id = "swap_back_tx_hash"
    matching_round = SwapBackTransactionHashRound

    def async_act(self) -> Generator:  # pylint: disable=too-many-statements
        """
        Do the action.

        Steps:
        - Request the transaction hash for the safe transaction. This is the
          hash that needs to be signed by a threshold of agents.
        - Send the transaction hash as a transaction and wait for it to be mined.
        - Wait until ABCI application transitions to the next round.
        - Go to the next behaviour state (set done event).
        """

        with benchmark_tool.measure(
            self,
        ).local():

            strategy = self.period_state.most_voted_strategy

            transfers = yield from self.get_tx_result()
            transfers = transfers if transfers else []

            amount_a_received: int = parse_tx_token_balance(
                transfer_logs=transfers,
                token_address=strategy["pair"]["token_a"]["address"],
                source_address=self.period_state.router_contract_address,
                destination_address=self.period_state.safe_contract_address,
            )
            amount_b_received: int = parse_tx_token_balance(
                transfer_logs=transfers,
                token_address=strategy["pair"]["token_b"]["address"],
                source_address=self.period_state.router_contract_address,
                destination_address=self.period_state.safe_contract_address,
            )

            # Prepare a uniswap tx list. We should check what token balances we have at this point.
            # It is possible that we don't need to swap. For now let's assume we have just USDT
            # and always swap back to it.
            multi_send_txs = []

            # Swap first token back
            swap_tx_data = yield from self.get_swap_tx_data(
                is_input_native=strategy["pair"]["token_a"]["is_native"],
                is_output_native=strategy["base"]["is_native"],
                exact_input=True,
                amount_in=int(amount_a_received),
                amount_out_min=int(strategy["base"]["amount_min_after_swap_back_a"]),
                eth_value=amount_a_received
                if strategy["pair"]["token_a"]["is_native"]
                else 0,
                path=[
                    strategy["pair"]["token_a"]["address"],
                    strategy["base"]["address"],
                ],
                deadline=strategy["deadline"],
            )

            if swap_tx_data:
                multi_send_txs.append(swap_tx_data)

            # Swap second token back
            swap_tx_data = yield from self.get_swap_tx_data(
                is_input_native=strategy["pair"]["token_b"]["is_native"],
                is_output_native=strategy["base"]["is_native"],
                exact_input=True,
                amount_in=int(amount_b_received),
                amount_out_min=int(strategy["base"]["amount_min_after_swap_back_b"]),
                eth_value=amount_b_received
                if strategy["pair"]["token_b"]["is_native"]
                else 0,
                path=[
                    strategy["pair"]["token_b"]["address"],
                    strategy["base"]["address"],
                ],
                deadline=strategy["deadline"],
            )

            if swap_tx_data:
                multi_send_txs.append(swap_tx_data)

            # Remove allowance for base token
            if (
                not strategy["base"]["is_native"]
                and "remove_allowance" in strategy["base"]
            ):
                contract_api_msg = yield from self.get_contract_api_response(
                    performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                    contract_address=strategy["base"]["address"],
                    contract_id=str(UniswapV2ERC20Contract.contract_id),
                    contract_callable="get_method_data",
                    method_name="approve",
                    spender=self.period_state.router_contract_address,
                    value=strategy["base"]["remove_allowance"],
                )
                allowance_base_data = cast(
                    bytes, contract_api_msg.raw_transaction.body["data"]
                )
                multi_send_txs.append(
                    {
                        "operation": MultiSendOperation.CALL,
                        "to": strategy["base"]["address"],
                        "value": 0,
                        "data": HexBytes(allowance_base_data.hex()),
                    }
                )

            # Remove allowance for the first token
            if (
                not strategy["pair"]["token_a"]["is_native"]
                and "remove_allowance" in strategy["pair"]["token_a"]
            ):
                contract_api_msg = yield from self.get_contract_api_response(
                    performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                    contract_address=strategy["pair"]["token_a"]["address"],
                    contract_id=str(UniswapV2ERC20Contract.contract_id),
                    contract_callable="get_method_data",
                    method_name="approve",
                    spender=self.period_state.router_contract_address,
                    value=strategy["pair"]["token_a"]["remove_allowance"],
                )
                allowance_base_data = cast(
                    bytes, contract_api_msg.raw_transaction.body["data"]
                )
                multi_send_txs.append(
                    {
                        "operation": MultiSendOperation.CALL,
                        "to": strategy["pair"]["token_a"]["address"],
                        "value": 0,
                        "data": HexBytes(allowance_base_data.hex()),
                    }
                )

            # Remove allowance for the second token
            if (
                not strategy["pair"]["token_b"]["is_native"]
                and "remove_allowance" in strategy["pair"]["token_b"]
            ):
                contract_api_msg = yield from self.get_contract_api_response(
                    performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                    contract_address=strategy["pair"]["token_b"]["address"],
                    contract_id=str(UniswapV2ERC20Contract.contract_id),
                    contract_callable="get_method_data",
                    method_name="approve",
                    spender=self.period_state.router_contract_address,
                    value=0,
                )
                allowance_base_data = cast(
                    bytes, contract_api_msg.raw_transaction.body["data"]
                )
                multi_send_txs.append(
                    {
                        "operation": MultiSendOperation.CALL,
                        "to": strategy["pair"]["token_b"]["address"],
                        "value": strategy["pair"]["token_b"]["remove_allowance"],
                        "data": HexBytes(allowance_base_data.hex()),
                    }
                )

            # Get the tx list data from multisend contract
            contract_api_msg = yield from self.get_contract_api_response(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=self.period_state.safe_contract_address,
                contract_id=str(MultiSendContract.contract_id),
                contract_callable="get_tx_data",
                multi_send_txs=multi_send_txs,
            )
            multisend_data = cast(str, contract_api_msg.raw_transaction.body["data"])
            multisend_data = multisend_data[2:]
            self.context.logger.info(f"Multisend data: {multisend_data}")
            # Get the tx hash from Gnosis Safe contract
            contract_api_msg = yield from self.get_contract_api_response(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=self.period_state.safe_contract_address,
                contract_id=str(GnosisSafeContract.contract_id),
                contract_callable="get_raw_safe_transaction_hash",
                to_address=self.period_state.multisend_contract_address,
                value=ETHER_VALUE,
                data=bytes.fromhex(multisend_data),
                operation=SafeOperation.DELEGATE_CALL.value,
                safe_tx_gas=strategy["safe_tx_gas"],
                safe_nonce=strategy["safe_nonce"],
            )
            safe_tx_hash = cast(str, contract_api_msg.raw_transaction.body["tx_hash"])
            safe_tx_hash = safe_tx_hash[2:]
            self.context.logger.info(f"Hash of the Safe transaction: {safe_tx_hash}")
            payload = TransactionHashPayload(
                sender=self.context.agent_address,
                tx_hash=json.dumps(
                    {"tx_hash": safe_tx_hash, "tx_data": multisend_data}
                ),  # TOFIX
            )

        with benchmark_tool.measure(
            self,
        ).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class StrategyRoundBehaviour(AbstractRoundBehaviour):
    """This behaviour manages the consensus stages for the rebalancing behaviour."""

    initial_state_cls = StrategyEvaluationBehaviour
    abci_app_cls = LiquidityRebalancingAbciApp  # type: ignore
    behaviour_states: Set[Type[BaseState]] = {  # type: ignore
        StrategyEvaluationBehaviour,  # type: ignore
        SleepBehaviour,  # type: ignore
        EnterPoolTransactionHashBehaviour,  # type: ignore
        ExitPoolTransactionHashBehaviour,  # type: ignore
        SwapBackTransactionHashBehaviour,  # type: ignore
    }


class LiquidityProvisionConsensusBehaviour(AbstractRoundBehaviour):
    """This behaviour manages the consensus stages for the price estimation."""

    initial_state_cls = TendermintHealthcheckBehaviour
    abci_app_cls = LiquidityProvisionAbciApp  # type: ignore
    behaviour_states: Set[Type[BaseState]] = {
        *AgentRegistrationRoundBehaviour.behaviour_states,
        *SafeDeploymentRoundBehaviour.behaviour_states,
        *TransactionSettlementRoundBehaviour.behaviour_states,
        *StrategyRoundBehaviour.behaviour_states,
    }

    def setup(self) -> None:
        """Set up the behaviour."""
        super().setup()
        benchmark_tool.logger = self.context.logger
