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

"""This module contains the behaviours for the 'liquidity_rebalancing_abci' skill."""
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
    BaseBehaviour,
)
from packages.valory.skills.liquidity_rebalancing_abci.models import Params, SharedState
from packages.valory.skills.liquidity_rebalancing_abci.payloads import (
    SleepPayload,
    StrategyEvaluationPayload,
    StrategyType,
    TransactionHashPayload,
)
from packages.valory.skills.liquidity_rebalancing_abci.rounds import (
    EnterPoolTransactionHashRound,
    ExitPoolTransactionHashRound,
    LiquidityRebalancingAbciApp,
    SleepRound,
    StrategyEvaluationRound,
    SwapBackTransactionHashRound,
    SynchronizedData,
)
from packages.valory.skills.transaction_settlement_abci.payload_tools import (
    hash_payload_to_hex,
)


# These safeTxGas values are calculated from experimental values plus
# a 10% buffer and rounded up. The Gnosis safe default value is 0 (max gas)
# https://help.gnosis-safe.io/en/articles/4738445-advanced-transaction-parameters
# More on gas estimation: https://help.gnosis-safe.io/en/articles/4933491-gas-estimation
SAFE_TX_GAS_ENTER = 553000
SAFE_TX_GAS_EXIT = 248000
SAFE_TX_GAS_SWAP_BACK = 268000


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
    return sum(event["value"] for event in token_events)


class LiquidityRebalancingBaseBehaviour(BaseBehaviour, ABC):
    """Base behaviour for the liquidity rebalancing skill."""

    @property
    def synchronized_data(self) -> SynchronizedData:
        """Return the synchronized data."""
        return cast(SynchronizedData, super().synchronized_data)

    @property
    def params(self) -> Params:
        """Return the params."""
        return cast(Params, self.context.params)

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
            to=self.synchronized_data.safe_contract_address,
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
            contract_address=self.synchronized_data.router_contract_address,
            contract_id=str(UniswapV2Router02Contract.contract_id),
            contract_callable="get_method_data",
            **contract_api_kwargs,
        )
        swap_data = cast(bytes, contract_api_msg.raw_transaction.body["data"])

        return {
            "operation": MultiSendOperation.CALL,
            "to": self.synchronized_data.router_contract_address,
            "value": eth_value
            if is_input_native
            else 0,  # Input amount for native tokens
            "data": HexBytes(swap_data.hex()),
        }

    def get_swap_data(
        self, strategy: dict, token: str, is_swap_back: bool
    ) -> Generator[None, None, Optional[Dict]]:
        """
        Return the swap tx data for swaps, particularized for swaps base->token and token->base.

        :param strategy: the strategy
        :param token: "token_a" or "token_b"
        :param is_swap_back: True for token[a,b] -> token_base, False for token_base -> token[a,b]
        :return: the tx data
        """

        token_letter = token[-1]  # a or b
        input_token = token if is_swap_back else "token_base"
        output_token = "token_base" if is_swap_back else token

        kwargs = dict(
            deadline=strategy["deadline"],
            is_input_native=strategy[input_token]["is_native"],
            is_output_native=strategy[output_token]["is_native"],
            exact_input=is_swap_back,
            path=[strategy[t]["address"] for t in (input_token, output_token)],
        )

        if not is_swap_back:
            kwargs["amount_out"] = strategy[token]["amount_after_swap"]
            kwargs["amount_in_max"] = strategy["token_base"][
                f"amount_in_max_{token_letter}"
            ]
            kwargs["eth_value"] = (
                strategy["token_base"][f"amount_in_max_{token_letter}"]
                if strategy["token_base"]["is_native"]
                else 0
            )

        else:
            kwargs["amount_in"] = strategy[token]["amount_received"]
            kwargs["amount_out_min"] = strategy["token_base"][
                f"amount_min_after_swap_back_{token_letter}"
            ]
            kwargs["eth_value"] = (
                strategy[token]["amount_received"]
                if strategy[token]["is_native"]
                else 0
            )

        return self.get_swap_tx_data(**kwargs)

    def get_tx_result(self) -> Generator[None, None, list]:
        """Transaction transfer result."""
        strategy = json.loads(self.synchronized_data.most_voted_strategy)
        contract_api_msg = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_STATE,  # type: ignore
            contract_address=strategy["token_LP"]["address"],
            contract_id=str(UniswapV2ERC20Contract.contract_id),
            contract_callable="get_transaction_transfer_logs",
            tx_hash=self.synchronized_data.final_tx_hash,
            target_address=self.synchronized_data.safe_contract_address,
        )
        if contract_api_msg.performative != ContractApiMessage.Performative.STATE:
            self.context.logger.info(
                f"Error retrieving the transaction logs for hash: {self.synchronized_data.final_tx_hash}"
            )
            return []  # pragma: nocover
        transfers = cast(list, contract_api_msg.state.body["logs"])

        transfer_log_message = (
            f"The tx with hash {self.synchronized_data.final_tx_hash} ended with the following transfers.\n"
            f"Transfers: {str(transfers)}\n"
        )
        self.context.logger.info(transfer_log_message)
        return transfers

    def get_allowance_data(
        self, token_address: str, value: int
    ) -> Generator[None, None, dict]:
        """
        Return the swap tx data for swaps, particularized for swaps base->token and token->base.

        :param token_address: the spender's address
        :param value: the allowance value to set
        :return: the tx data
        :yield: the tx data
        """

        contract_api_msg = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
            contract_address=token_address,
            contract_id=str(UniswapV2ERC20Contract.contract_id),
            contract_callable="get_method_data",
            method_name="approve",
            spender=self.synchronized_data.router_contract_address,
            value=value,
        )

        return {
            "operation": MultiSendOperation.CALL,
            "to": token_address,
            "value": 0,
            "data": HexBytes(
                cast(bytes, contract_api_msg.raw_transaction.body["data"]).hex()
            ),
        }


class StrategyEvaluationBehaviour(LiquidityRebalancingBaseBehaviour):
    """Evaluate the financial strategy."""

    behaviour_id = "strategy_evaluation"
    matching_round = StrategyEvaluationRound

    def async_act(self) -> Generator:
        """Do the action."""

        with self.context.benchmark_tool.measure(self.behaviour_id).local():

            # Get the previous strategy or use the dummy one
            # For now, the app will loop between enter-exit-swap_back,
            # unless we start with WAIT. Then it will keep waiting.
            strategy: dict = {}
            try:
                strategy = json.loads(self.synchronized_data.most_voted_strategy)

                if strategy["action"] == StrategyType.ENTER.value:
                    strategy["action"] = StrategyType.EXIT.value

                elif strategy["action"] == StrategyType.EXIT.value:
                    strategy["action"] = StrategyType.SWAP_BACK.value

                elif strategy["action"] == StrategyType.SWAP_BACK.value:
                    strategy["action"] = StrategyType.ENTER.value

            # An exception will occur during the first run as no strategy was set
            except ValueError:
                strategy = self.get_dummy_strategy()

            # Log the new strategy
            if strategy["action"] == StrategyType.WAIT.value:  # pragma: nocover
                self.context.logger.info("Current strategy is still optimal. Waiting.")

            if strategy["action"] == StrategyType.ENTER.value:
                self.context.logger.info(
                    "Performing strategy update: moving into "
                    + f"{strategy['token_a']['ticker']}-{strategy['token_b']['ticker']} (pool {self.synchronized_data.router_contract_address})"
                )

            if strategy["action"] == StrategyType.EXIT.value:  # pragma: nocover
                self.context.logger.info(
                    "Performing strategy update: moving out of "
                    + f"{strategy['token_a']['ticker']}-{strategy['token_b']['ticker']} (pool {self.synchronized_data.router_contract_address})"
                )

            if strategy["action"] == StrategyType.SWAP_BACK.value:  # pragma: nocover
                self.context.logger.info(
                    f"Performing strategy update: swapping back {strategy['token_a']['ticker']}, {strategy['token_b']['ticker']}"
                )

            payload = StrategyEvaluationPayload(
                self.context.agent_address, json.dumps(strategy, sort_keys=True)
            )

        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()

    def get_dummy_strategy(self) -> dict:
        """Get a dummy strategy."""
        last_timestamp = cast(
            SharedState, self.context.state
        ).round_sequence.abci_app.last_timestamp.timestamp()

        strategy = {
            "action": StrategyType.ENTER.value,
            "safe_nonce": 0,
            "safe_tx_gas": {
                "enter": SAFE_TX_GAS_ENTER,
                "exit": SAFE_TX_GAS_EXIT,
                "swap_back": SAFE_TX_GAS_SWAP_BACK,
            },
            "deadline": int(last_timestamp)
            + self.params.rebalancing_params["deadline"],
            "chain": self.params.rebalancing_params["chain"],
            "token_base": {
                "ticker": self.params.rebalancing_params["token_base_ticker"],
                "address": self.params.rebalancing_params["token_base_address"],
                "amount_in_max_a": int(1e4),
                "amount_min_after_swap_back_a": int(1e2),
                "amount_in_max_b": int(1e4),
                "amount_min_after_swap_back_b": int(1e2),
                "is_native": False,
                "set_allowance": self.params.rebalancing_params["max_allowance"],
                "remove_allowance": 0,
            },
            "token_LP": {
                "address": self.params.rebalancing_params["lp_token_address"],
                "set_allowance": self.params.rebalancing_params["max_allowance"],
                "remove_allowance": 0,
            },
            "token_a": {
                "ticker": self.params.rebalancing_params["token_a_ticker"],
                "address": self.params.rebalancing_params["token_a_address"],
                "amount_after_swap": int(1e3),
                "amount_min_after_add_liq": int(0.5e3),
                "is_native": False,  # if one of the two tokens is native, A must be the one
                "set_allowance": self.params.rebalancing_params["max_allowance"],
                "remove_allowance": 0,
                "amount_received_after_exit": 0,
            },
            "token_b": {
                "ticker": self.params.rebalancing_params["token_b_ticker"],
                "address": self.params.rebalancing_params["token_b_address"],
                "amount_after_swap": int(1e3),
                "amount_min_after_add_liq": int(0.5e3),
                "is_native": False,  # if one of the two tokens is native, A must be the one
                "set_allowance": self.params.rebalancing_params["max_allowance"],
                "remove_allowance": 0,
                "amount_received_after_exit": 0,
            },
        }
        return strategy


class SleepBehaviour(LiquidityRebalancingBaseBehaviour):
    """Wait for a predefined amount of time."""

    behaviour_id = "sleep"
    matching_round = SleepRound

    def async_act(self) -> Generator:
        """Do the action."""

        with self.context.benchmark_tool.measure(self.behaviour_id).local():

            yield from self.sleep(self.params.rebalancing_params["sleep_seconds"])
            payload = SleepPayload(self.context.agent_address)

        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class EnterPoolTransactionHashBehaviour(LiquidityRebalancingBaseBehaviour):
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

    behaviour_id = "enter_pool_tx_hash"
    matching_round = EnterPoolTransactionHashRound

    def async_act(self) -> Generator:
        """
        Do the action.

        Steps:
        - Request the transaction hash for the safe transaction. This is the
          hash that needs to be signed by a threshold of agents.
        - Send the transaction hash as a transaction and wait for it to be mined.
        - Wait until ABCI application transitions to the next round.
        - Go to the next behaviour (set done event).
        """

        with self.context.benchmark_tool.measure(self.behaviour_id).local():

            strategy = json.loads(self.synchronized_data.most_voted_strategy)

            # Prepare a uniswap tx list. We should check what token balances we have at this point.
            # It is possible that we don't need to swap. For now let's assume we have just USDT
            # and always swap back to it.
            multi_send_txs = []

            # Add allowance for base token
            if (
                not strategy["token_base"]["is_native"]
                and "set_allowance" in strategy["token_base"]
            ):
                allowance_base_data = yield from self.get_allowance_data(
                    token_address=strategy["token_base"]["address"],
                    value=strategy["token_base"]["set_allowance"],
                )

                multi_send_txs.append(allowance_base_data)

            # Swap first token
            if strategy["token_a"]["address"] != strategy["token_base"]["address"]:

                swap_tx_data = yield from self.get_swap_data(  # nosec
                    strategy=strategy, token="token_a", is_swap_back=False
                )
                if swap_tx_data:
                    multi_send_txs.append(swap_tx_data)

            # Swap second token
            if strategy["token_b"]["address"] != strategy["token_base"]["address"]:

                swap_tx_data = yield from self.get_swap_data(  # nosec
                    strategy=strategy, token="token_b", is_swap_back=False
                )
                if swap_tx_data:
                    multi_send_txs.append(swap_tx_data)

            # Add allowance for token A (only if not native)
            if (
                not strategy["token_a"]["is_native"]
                and "set_allowance" in strategy["token_a"]
            ):
                allowance_a_data = yield from self.get_allowance_data(
                    token_address=strategy["token_a"]["address"],
                    value=strategy["token_a"]["set_allowance"],
                )

                multi_send_txs.append(allowance_a_data)

            # Add allowance for token B (only if not native)
            if (
                not strategy["token_b"]["is_native"]
                and "set_allowance" in strategy["token_b"]
            ):
                allowance_b_data = yield from self.get_allowance_data(
                    token_address=strategy["token_b"]["address"],
                    value=strategy["token_b"]["set_allowance"],
                )

                multi_send_txs.append(allowance_b_data)

            # Add liquidity
            if strategy["token_a"]["is_native"]:
                contract_api_msg = yield from self.get_contract_api_response(
                    performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                    contract_address=self.synchronized_data.router_contract_address,
                    contract_id=str(UniswapV2Router02Contract.contract_id),
                    contract_callable="get_method_data",
                    method_name="add_liquidity_ETH",
                    token=strategy["token_b"]["address"],
                    amount_token_desired=int(strategy["token_b"]["amount_after_swap"]),
                    amount_token_min=int(
                        strategy["token_b"]["amount_min_after_add_liq"]
                    ),
                    amount_ETH_min=int(strategy["token_a"]["amount_min_after_add_liq"]),
                    to=self.synchronized_data.safe_contract_address,
                    deadline=strategy["deadline"],
                )
                liquidity_data = cast(
                    bytes, contract_api_msg.raw_transaction.body["data"]
                )
                multi_send_txs.append(
                    {
                        "operation": MultiSendOperation.CALL,
                        "to": self.synchronized_data.router_contract_address,
                        "value": int(strategy["token_a"]["amount_min_after_add_liq"]),
                        "data": HexBytes(liquidity_data.hex()),
                    }
                )

            else:
                contract_api_msg = yield from self.get_contract_api_response(
                    performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                    contract_address=self.synchronized_data.router_contract_address,
                    contract_id=str(UniswapV2Router02Contract.contract_id),
                    contract_callable="get_method_data",
                    method_name="add_liquidity",
                    token_a=strategy["token_a"]["address"],
                    token_b=strategy["token_b"]["address"],
                    amount_a_desired=int(strategy["token_a"]["amount_after_swap"]),
                    amount_b_desired=int(strategy["token_b"]["amount_after_swap"]),
                    amount_a_min=int(strategy["token_a"]["amount_min_after_add_liq"]),
                    amount_b_min=int(strategy["token_b"]["amount_min_after_add_liq"]),
                    to=self.synchronized_data.safe_contract_address,
                    deadline=strategy["deadline"],  # 5 min into the future
                )
                liquidity_data = cast(
                    bytes, contract_api_msg.raw_transaction.body["data"]
                )
                multi_send_txs.append(
                    {
                        "operation": MultiSendOperation.CALL,
                        "to": self.synchronized_data.router_contract_address,
                        "value": 0,
                        "data": HexBytes(liquidity_data.hex()),
                    }
                )

            # Get the tx list data from multisend contract
            contract_api_msg = yield from self.get_contract_api_response(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=self.synchronized_data.safe_contract_address,
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
                contract_address=self.synchronized_data.safe_contract_address,
                contract_id=str(GnosisSafeContract.contract_id),
                contract_callable="get_raw_safe_transaction_hash",
                to_address=self.synchronized_data.multisend_contract_address,
                value=0,
                data=bytes.fromhex(multisend_data),
                operation=SafeOperation.DELEGATE_CALL.value,
                safe_tx_gas=strategy["safe_tx_gas"]["enter"],
                safe_nonce=strategy["safe_nonce"],
            )
            safe_tx_hash = cast(str, contract_api_msg.raw_transaction.body["tx_hash"])
            safe_tx_hash = safe_tx_hash[2:]
            self.context.logger.info(f"Hash of the Safe transaction: {safe_tx_hash}")

            payload_string = hash_payload_to_hex(
                safe_tx_hash=safe_tx_hash,
                ether_value=0,
                safe_tx_gas=strategy["safe_tx_gas"]["enter"],
                to_address=self.synchronized_data.multisend_contract_address,
                data=bytes.fromhex(multisend_data),
                operation=SafeOperation.DELEGATE_CALL.value,
            )

            payload = TransactionHashPayload(
                sender=self.context.agent_address, tx_hash=payload_string
            )

        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class ExitPoolTransactionHashBehaviour(LiquidityRebalancingBaseBehaviour):
    """Prepare the transaction hash for exiting the liquidity pool

    The expected transfers derived from this behaviour are
    Safe         ->  A-B-pool    : AB_LP tokens
    AB_LP        ->  Safe        : A tokens
    AB_LP        ->  Safe        : B tokens
    """

    behaviour_id = "exit_pool_tx_hash"
    matching_round = ExitPoolTransactionHashRound

    def async_act(self) -> Generator:  # pylint: disable=too-many-statements
        """
        Do the action.

        Steps:
        - Request the transaction hash for the safe transaction. This is the
          hash that needs to be signed by a threshold of agents.
        - Send the transaction hash as a transaction and wait for it to be mined.
        - Wait until ABCI application transitions to the next round.
        - Go to the next behaviour (set done event).
        """

        with self.context.benchmark_tool.measure(self.behaviour_id).local():

            strategy = json.loads(self.synchronized_data.most_voted_strategy)

            # Get previous transaction's results
            transfers = yield from self.get_tx_result()

            amount_a_sent: int = parse_tx_token_balance(
                transfer_logs=transfers,
                token_address=strategy["token_a"]["address"],
                source_address=self.synchronized_data.safe_contract_address,
                destination_address=self.synchronized_data.router_contract_address,
            )
            amount_b_sent: int = parse_tx_token_balance(
                transfer_logs=transfers,
                token_address=strategy["token_b"]["address"],
                source_address=self.synchronized_data.safe_contract_address,
                destination_address=self.synchronized_data.router_contract_address,
            )
            amount_liquidity_received: int = parse_tx_token_balance(
                transfer_logs=transfers,
                token_address=strategy["token_LP"]["address"],
                source_address=self.params.rebalancing_params["default_minter"],
                destination_address=self.synchronized_data.safe_contract_address,
            )

            # Prepare a uniswap tx list. We should check what token balances we have at this point.
            # It is possible that we don't need to swap. For now let's assume we have just USDT
            # and always swap back to it.
            multi_send_txs = []

            # Add allowance for LP token to be spent by the router
            allowance_lp_data = yield from self.get_allowance_data(
                token_address=strategy["token_LP"]["address"],
                value=strategy["token_LP"]["set_allowance"],
            )

            multi_send_txs.append(allowance_lp_data)

            # Remove liquidity
            if strategy["token_a"]["is_native"]:

                contract_api_msg = yield from self.get_contract_api_response(
                    performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                    contract_address=self.synchronized_data.router_contract_address,
                    contract_id=str(UniswapV2Router02Contract.contract_id),
                    contract_callable="get_method_data",
                    method_name="remove_liquidity_ETH",
                    token=strategy["token_b"]["address"],
                    liquidity=amount_liquidity_received,
                    amount_token_min=int(amount_b_sent),
                    amount_ETH_min=int(amount_a_sent),
                    to=self.synchronized_data.safe_contract_address,
                    deadline=strategy["deadline"],
                )
                liquidity_data = cast(
                    bytes, contract_api_msg.raw_transaction.body["data"]
                )

            else:

                contract_api_msg = yield from self.get_contract_api_response(
                    performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                    contract_address=self.synchronized_data.router_contract_address,
                    contract_id=str(UniswapV2Router02Contract.contract_id),
                    contract_callable="get_method_data",
                    method_name="remove_liquidity",
                    token_a=strategy["token_a"]["address"],
                    token_b=strategy["token_b"]["address"],
                    liquidity=amount_liquidity_received,
                    amount_a_min=int(amount_a_sent),
                    amount_b_min=int(amount_b_sent),
                    to=self.synchronized_data.safe_contract_address,
                    deadline=strategy["deadline"],
                )
                liquidity_data = cast(
                    bytes, contract_api_msg.raw_transaction.body["data"]
                )

            multi_send_txs.append(
                {
                    "operation": MultiSendOperation.CALL,
                    "to": self.synchronized_data.router_contract_address,
                    "value": 0,
                    "data": HexBytes(liquidity_data.hex()),
                }
            )

            # Remove allowance for LP token
            if "remove_allowance" in strategy["token_LP"]:
                allowance_lp_data = yield from self.get_allowance_data(
                    token_address=strategy["token_LP"]["address"],
                    value=strategy["token_LP"]["remove_allowance"],
                )

                multi_send_txs.append(allowance_lp_data)

            # Get the tx list data from multisend contract
            contract_api_msg = yield from self.get_contract_api_response(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=self.synchronized_data.safe_contract_address,
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
                contract_address=self.synchronized_data.safe_contract_address,
                contract_id=str(GnosisSafeContract.contract_id),
                contract_callable="get_raw_safe_transaction_hash",
                to_address=self.synchronized_data.multisend_contract_address,
                value=0,
                data=bytes.fromhex(multisend_data),
                operation=SafeOperation.DELEGATE_CALL.value,
                safe_tx_gas=strategy["safe_tx_gas"]["exit"],
                safe_nonce=strategy["safe_nonce"],
            )
            safe_tx_hash = cast(str, contract_api_msg.raw_transaction.body["tx_hash"])
            safe_tx_hash = safe_tx_hash[2:]
            self.context.logger.info(f"Hash of the Safe transaction: {safe_tx_hash}")

            payload_string = hash_payload_to_hex(
                safe_tx_hash=safe_tx_hash,
                ether_value=0,
                safe_tx_gas=strategy["safe_tx_gas"]["enter"],
                to_address=self.synchronized_data.multisend_contract_address,
                data=bytes.fromhex(multisend_data),
                operation=SafeOperation.DELEGATE_CALL.value,
            )

            payload = TransactionHashPayload(
                sender=self.context.agent_address, tx_hash=payload_string
            )

        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class SwapBackTransactionHashBehaviour(LiquidityRebalancingBaseBehaviour):
    """Prepare the transaction hash for swapping back assets

    The expected transfers derived from this behaviour are
    Safe         ->  A-Base-pool    : A tokens
    A-Base-pool  ->  Safe           : Base tokens
    Safe         ->  B-Base-pool    : B tokens
    B-Base-pool  ->  Safe           : Base tokens
    """

    behaviour_id = "swap_back_tx_hash"
    matching_round = SwapBackTransactionHashRound

    def async_act(self) -> Generator:  # pylint: disable=too-many-statements
        """
        Do the action.

        Steps:
        - Request the transaction hash for the safe transaction. This is the
          hash that needs to be signed by a threshold of agents.
        - Send the transaction hash as a transaction and wait for it to be mined.
        - Wait until ABCI application transitions to the next round.
        - Go to the next behaviour (set done event).
        """

        with self.context.benchmark_tool.measure(self.behaviour_id).local():

            strategy = json.loads(self.synchronized_data.most_voted_strategy)

            transfers = yield from self.get_tx_result()
            transfers = transfers if transfers else []

            strategy["token_a"]["amount_received"] = parse_tx_token_balance(
                transfer_logs=transfers,
                token_address=strategy["token_a"]["address"],
                source_address=strategy["token_LP"]["address"],
                destination_address=self.synchronized_data.safe_contract_address,
            )
            strategy["token_b"]["amount_received"] = parse_tx_token_balance(
                transfer_logs=transfers,
                token_address=strategy["token_b"]["address"],
                source_address=strategy["token_LP"]["address"],
                destination_address=self.synchronized_data.safe_contract_address,
            )

            # Prepare a uniswap tx list. We should check what token balances we have at this point.
            # It is possible that we don't need to swap. For now let's assume we have just USDT
            # and always swap back to it.
            multi_send_txs = []

            # Swap first token back
            swap_tx_data = yield from self.get_swap_data(  # nosec
                strategy=strategy, token="token_a", is_swap_back=True
            )
            if swap_tx_data:
                multi_send_txs.append(swap_tx_data)

            # Swap second token back
            swap_tx_data = yield from self.get_swap_data(  # nosec
                strategy=strategy, token="token_b", is_swap_back=True
            )
            if swap_tx_data:
                multi_send_txs.append(swap_tx_data)

            # Remove allowance for base token
            if (
                not strategy["token_base"]["is_native"]
                and "remove_allowance" in strategy["token_base"]
            ):
                allowance_base_data = yield from self.get_allowance_data(
                    token_address=strategy["token_base"]["address"],
                    value=strategy["token_base"]["remove_allowance"],
                )

                multi_send_txs.append(allowance_base_data)

            # Remove allowance for the first token
            if (
                not strategy["token_a"]["is_native"]
                and "remove_allowance" in strategy["token_a"]
            ):
                allowance_base_data = yield from self.get_allowance_data(
                    token_address=strategy["token_a"]["address"],
                    value=strategy["token_a"]["remove_allowance"],
                )

                multi_send_txs.append(allowance_base_data)

            # Remove allowance for the second token
            if (
                not strategy["token_b"]["is_native"]
                and "remove_allowance" in strategy["token_b"]
            ):
                allowance_b_data = yield from self.get_allowance_data(
                    token_address=strategy["token_b"]["address"],
                    value=strategy["token_b"]["remove_allowance"],
                )

                multi_send_txs.append(allowance_b_data)

            # Get the tx list data from multisend contract
            contract_api_msg = yield from self.get_contract_api_response(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=self.synchronized_data.safe_contract_address,
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
                contract_address=self.synchronized_data.safe_contract_address,
                contract_id=str(GnosisSafeContract.contract_id),
                contract_callable="get_raw_safe_transaction_hash",
                to_address=self.synchronized_data.multisend_contract_address,
                value=0,
                data=bytes.fromhex(multisend_data),
                operation=SafeOperation.DELEGATE_CALL.value,
                safe_tx_gas=strategy["safe_tx_gas"]["swap_back"],
                safe_nonce=strategy["safe_nonce"],
            )
            safe_tx_hash = cast(str, contract_api_msg.raw_transaction.body["tx_hash"])
            safe_tx_hash = safe_tx_hash[2:]
            self.context.logger.info(f"Hash of the Safe transaction: {safe_tx_hash}")

            payload_string = hash_payload_to_hex(
                safe_tx_hash=safe_tx_hash,
                ether_value=0,
                safe_tx_gas=strategy["safe_tx_gas"]["enter"],
                to_address=self.synchronized_data.multisend_contract_address,
                data=bytes.fromhex(multisend_data),
                operation=SafeOperation.DELEGATE_CALL.value,
            )

            payload = TransactionHashPayload(
                sender=self.context.agent_address, tx_hash=payload_string
            )

        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class LiquidityRebalancingConsensusBehaviour(AbstractRoundBehaviour):
    """This behaviour manages the consensus stages for the rebalancing behaviour."""

    initial_behaviour_cls = StrategyEvaluationBehaviour
    abci_app_cls = LiquidityRebalancingAbciApp  # type: ignore
    behaviours: Set[Type[BaseBehaviour]] = {  # type: ignore
        StrategyEvaluationBehaviour,  # type: ignore
        SleepBehaviour,  # type: ignore
        EnterPoolTransactionHashBehaviour,  # type: ignore
        ExitPoolTransactionHashBehaviour,  # type: ignore
        SwapBackTransactionHashBehaviour,  # type: ignore
    }
