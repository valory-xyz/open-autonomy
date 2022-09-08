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
"""Tests for valory/liquidity_rebalancing_behaviour skill's behaviours."""

# pylint: skip-file

import binascii
import datetime
import json
import time
from pathlib import Path
from typing import Dict, cast
from unittest import mock

import pytest
from aea.exceptions import AEAActException
from aea.helpers.transaction.base import RawTransaction, State

from packages.valory.contracts.gnosis_safe.contract import SafeOperation
from packages.valory.contracts.multisend.contract import MultiSendContract
from packages.valory.contracts.uniswap_v2_erc20.contract import UniswapV2ERC20Contract
from packages.valory.contracts.uniswap_v2_router_02.contract import (
    UniswapV2Router02Contract,
)
from packages.valory.protocols.contract_api.custom_types import Kwargs
from packages.valory.protocols.contract_api.message import ContractApiMessage
from packages.valory.skills.abstract_round_abci.base import AbciApp, AbciAppDB
from packages.valory.skills.abstract_round_abci.behaviour_utils import BaseBehaviour
from packages.valory.skills.abstract_round_abci.test_tools.base import (
    FSMBehaviourBaseCase,
)
from packages.valory.skills.liquidity_rebalancing_abci.behaviours import (
    EnterPoolTransactionHashBehaviour,
    ExitPoolTransactionHashBehaviour,
    GnosisSafeContract,
    SAFE_TX_GAS_ENTER,
    SAFE_TX_GAS_EXIT,
    SAFE_TX_GAS_SWAP_BACK,
    SleepBehaviour,
    StrategyEvaluationBehaviour,
    SwapBackTransactionHashBehaviour,
    parse_tx_token_balance,
)
from packages.valory.skills.liquidity_rebalancing_abci.payloads import StrategyType
from packages.valory.skills.liquidity_rebalancing_abci.rounds import Event
from packages.valory.skills.liquidity_rebalancing_abci.rounds import (
    SynchronizedData as LiquidityRebalancingSynchronizedSata,
)


PACKAGE_DIR = Path(__file__).parent.parent


MAX_ALLOWANCE = 2 ** 256 - 1
WETH_ADDRESS = "0xDc64a140Aa3E981100a9becA4E685f962f0cF6C9"  # nosec
TOKEN_A_ADDRESS = "0x0DCd1Bf9A1b36cE34237eEaFef220932846BCD82"  # nosec
TOKEN_B_ADDRESS = "0x9A676e781A523b5d0C0e43731313A708CB607508"  # nosec
LP_TOKEN_ADDRESS = "0x50CD56fb094F8f06063066a619D898475dD3EedE"  # nosec
DEFAULT_MINTER = "0x0000000000000000000000000000000000000000"  # nosec
A_B_POOL_ADDRESS = "0x86A6C37D3E868580a65C723AAd7E0a945E170416"  # nosec
A_WETH_POOL_ADDRESS = "0x86A6C37D3E868580a65C723AAd7E0a945E170416"  # nosec
B_WETH_POOL_ADDRESS = "0x3430fe46bfE23b1fafDe4F7c78481051F7c0E01F"  # nosec
SLEEP_SECONDS = 1
DEADLINE = int(time.time()) + 300


def get_default_strategy(
    is_base_native: bool, is_a_native: bool, is_b_native: bool
) -> Dict:
    """Returns default strategy."""
    strategy = {
        "action": StrategyType.ENTER.value,
        "safe_nonce": 0,
        "safe_tx_gas": {
            "enter": SAFE_TX_GAS_ENTER,
            "exit": SAFE_TX_GAS_EXIT,
            "swap_back": SAFE_TX_GAS_SWAP_BACK,
        },
        "deadline": DEADLINE,  # 5 min into future
        "chain": "Ethereum",
        "token_base": {
            "ticker": "WETH",
            "address": WETH_ADDRESS,
            "amount_in_max_a": int(1e4),
            "amount_min_after_swap_back_a": int(1e2),
            "amount_in_max_b": int(1e4),
            "amount_min_after_swap_back_b": int(1e2),
            "is_native": is_base_native,
            "set_allowance": MAX_ALLOWANCE,
            "remove_allowance": 0,
        },
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
            "is_native": is_a_native,  # if one of the two tokens is native, A must be the one
            "set_allowance": MAX_ALLOWANCE,
            "remove_allowance": 0,
            "amount_received_after_exit": 0,
        },
        "token_b": {
            "ticker": "TKB",
            "address": TOKEN_B_ADDRESS,
            "amount_after_swap": int(1e3),
            "amount_min_after_add_liq": int(0.5e3),
            "is_native": is_b_native,  # if one of the two tokens is native, A must be the one
            "set_allowance": MAX_ALLOWANCE,
            "remove_allowance": 0,
            "amount_received_after_exit": 0,
        },
    }

    return strategy


class LiquidityRebalancingBehaviourBaseCase(FSMBehaviourBaseCase):
    """Base case for testing LiquidityRebalancing FSMBehaviour."""

    path_to_skill = PACKAGE_DIR


class TestStrategyEvaluationBehaviour(LiquidityRebalancingBehaviourBaseCase):
    """Test StrategyEvaluationBehaviour."""

    def test_transaction_hash_enter(
        self,
    ) -> None:
        """Run tests."""

        strategy = get_default_strategy(
            is_base_native=False, is_a_native=True, is_b_native=False
        )
        synchronized_data = LiquidityRebalancingSynchronizedSata(
            AbciAppDB(
                setup_data=AbciAppDB.data_to_lists(
                    dict(
                        most_voted_tx_hash="0x",
                        safe_contract_address="safe_contract_address",
                        most_voted_keeper_address="most_voted_keeper_address",
                        most_voted_strategy=json.dumps(strategy),
                        multisend_contract_address="0xb0e6add595e00477cf347d09797b156719dc5233",
                        router_contract_address="router_contract_address",
                    )
                ),
            )
        )
        self.fast_forward_to_behaviour(
            behaviour=self.behaviour,
            behaviour_id=StrategyEvaluationBehaviour.behaviour_id,
            synchronized_data=synchronized_data,
        )
        assert (
            cast(
                BaseBehaviour,
                cast(BaseBehaviour, self.behaviour.current_behaviour),
            ).behaviour_id
            == StrategyEvaluationBehaviour.behaviour_id
        )
        self.behaviour.act_wrapper()

        self.mock_a2a_transaction()
        self._test_done_flag_set()

    def test_transaction_hash_exit(
        self,
    ) -> None:
        """Run tests."""

        strategy = get_default_strategy(
            is_base_native=False, is_a_native=True, is_b_native=False
        )
        strategy["action"] = StrategyType.EXIT.value
        synchronized_data = LiquidityRebalancingSynchronizedSata(
            AbciAppDB(
                setup_data=AbciAppDB.data_to_lists(
                    dict(
                        most_voted_tx_hash="0x",
                        safe_contract_address="safe_contract_address",
                        most_voted_keeper_address="most_voted_keeper_address",
                        most_voted_strategy=json.dumps(strategy),
                        multisend_contract_address="0xb0e6add595e00477cf347d09797b156719dc5233",
                        router_contract_address="router_contract_address",
                    )
                ),
            )
        )
        self.fast_forward_to_behaviour(
            behaviour=self.behaviour,
            behaviour_id=StrategyEvaluationBehaviour.behaviour_id,
            synchronized_data=synchronized_data,
        )
        assert (
            cast(
                BaseBehaviour,
                cast(BaseBehaviour, self.behaviour.current_behaviour),
            ).behaviour_id
            == StrategyEvaluationBehaviour.behaviour_id
        )
        self.behaviour.act_wrapper()

        self.mock_a2a_transaction()
        self._test_done_flag_set()

    def test_no_strategy(
        self,
    ) -> None:
        """Run tests."""

        synchronized_data = LiquidityRebalancingSynchronizedSata(
            AbciAppDB(
                setup_data=AbciAppDB.data_to_lists(
                    dict(
                        most_voted_tx_hash="0x",
                        safe_contract_address="safe_contract_address",
                        most_voted_keeper_address="most_voted_keeper_address",
                        multisend_contract_address="0xb0e6add595e00477cf347d09797b156719dc5233",
                        router_contract_address="router_contract_address",
                    )
                ),
            )
        )
        self.fast_forward_to_behaviour(
            behaviour=self.behaviour,
            behaviour_id=StrategyEvaluationBehaviour.behaviour_id,
            synchronized_data=synchronized_data,
        )
        assert (
            cast(
                BaseBehaviour,
                cast(BaseBehaviour, self.behaviour.current_behaviour),
            ).behaviour_id
            == StrategyEvaluationBehaviour.behaviour_id
        )
        with mock.patch.object(
            AbciApp,
            "last_timestamp",
            return_value=datetime.datetime.now(),
        ):
            self.behaviour.act_wrapper()

            self.mock_a2a_transaction()
            self._test_done_flag_set()

    def test_transaction_hash_swap_back(
        self,
    ) -> None:
        """Run tests."""

        strategy = get_default_strategy(
            is_base_native=False, is_a_native=True, is_b_native=False
        )
        strategy["action"] = StrategyType.SWAP_BACK.value
        synchronized_data = LiquidityRebalancingSynchronizedSata(
            AbciAppDB(
                setup_data=AbciAppDB.data_to_lists(
                    dict(
                        most_voted_tx_hash="0x",
                        safe_contract_address="safe_contract_address",
                        most_voted_keeper_address="most_voted_keeper_address",
                        most_voted_strategy=json.dumps(strategy),
                        multisend_contract_address="0xb0e6add595e00477cf347d09797b156719dc5233",
                        router_contract_address="router_contract_address",
                    )
                ),
            )
        )
        self.fast_forward_to_behaviour(
            behaviour=self.behaviour,
            behaviour_id=StrategyEvaluationBehaviour.behaviour_id,
            synchronized_data=synchronized_data,
        )
        assert (
            cast(
                BaseBehaviour,
                cast(BaseBehaviour, self.behaviour.current_behaviour),
            ).behaviour_id
            == StrategyEvaluationBehaviour.behaviour_id
        )
        self.behaviour.act_wrapper()

        self.mock_a2a_transaction()
        self._test_done_flag_set()


class TestEnterPoolTransactionHashBehaviour(LiquidityRebalancingBehaviourBaseCase):
    """Test EnterPoolTransactionHashBehaviour."""

    def test_transaction_hash(
        self,
    ) -> None:
        """Test tx hash behaviour."""

        strategy = get_default_strategy(
            is_base_native=False, is_a_native=True, is_b_native=False
        )
        synchronized_data = LiquidityRebalancingSynchronizedSata(
            AbciAppDB(
                setup_data=AbciAppDB.data_to_lists(
                    dict(
                        most_voted_tx_hash="0x",
                        safe_contract_address="safe_contract_address",
                        most_voted_keeper_address="most_voted_keeper_address",
                        most_voted_strategy=json.dumps(strategy),
                        multisend_contract_address="0xb0e6add595e00477cf347d09797b156719dc5233",
                        router_contract_address="router_contract_address",
                    )
                ),
            )
        )
        self.fast_forward_to_behaviour(
            behaviour=self.behaviour,
            behaviour_id=EnterPoolTransactionHashBehaviour.behaviour_id,
            synchronized_data=synchronized_data,
        )
        assert (
            cast(
                BaseBehaviour,
                cast(BaseBehaviour, self.behaviour.current_behaviour),
            ).behaviour_id
            == EnterPoolTransactionHashBehaviour.behaviour_id
        )
        self.behaviour.act_wrapper()

        # Add allowance for base token
        self.mock_contract_api_request(
            contract_id=str(UniswapV2ERC20Contract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=strategy["token_base"]["address"],
                kwargs=Kwargs(
                    dict(
                        method_name="approve",
                        # sender=synchronized_data.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        spender=synchronized_data.router_contract_address,
                        value=MAX_ALLOWANCE,
                    )
                ),
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_method_data",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"data": b"dummy_tx"},  # type: ignore
                ),
            ),
        )

        # Swap first token
        method_name = (
            "swap_tokens_for_exact_ETH"
            if strategy["token_a"]["is_native"]
            else "swap_tokens_for_exact_tokens"
        )

        self.mock_contract_api_request(
            contract_id=str(UniswapV2Router02Contract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=synchronized_data.router_contract_address,
                kwargs=Kwargs(
                    dict(
                        method_name=method_name,
                        # sender=synchronized_data.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        amount_out=int(strategy["token_a"]["amount_after_swap"]),
                        amount_in_max=int(strategy["token_base"]["amount_in_max_a"]),
                        path=[
                            strategy["token_base"]["address"],
                            strategy["token_a"]["address"],
                        ],
                        to=synchronized_data.safe_contract_address,
                        deadline=DEADLINE,
                    )
                ),
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_swap_tokens_for_exact_ETH_data",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"data": b"dummy_tx"},  # type: ignore  # type: ignore
                ),
            ),
        )

        # Swap second token
        self.mock_contract_api_request(
            contract_id=str(UniswapV2Router02Contract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=synchronized_data.router_contract_address,
                kwargs=Kwargs(
                    dict(
                        method_name="swap_tokens_for_exact_tokens",
                        # sender=synchronized_data.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        amount_out=int(strategy["token_b"]["amount_after_swap"]),
                        amount_in_max=int(strategy["token_base"]["amount_in_max_b"]),
                        path=[
                            strategy["token_base"]["address"],
                            strategy["token_b"]["address"],
                        ],
                        to=synchronized_data.safe_contract_address,
                        deadline=DEADLINE,
                    )
                ),
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_swap_exact_tokens_for_tokens_data",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"data": b"dummy_tx"},  # type: ignore
                ),
            ),
        )

        # Add allowance for token B
        self.mock_contract_api_request(
            contract_id=str(UniswapV2ERC20Contract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=strategy["token_b"]["address"],
                kwargs=Kwargs(
                    dict(
                        method_name="approve",
                        # sender=synchronized_data.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        spender=synchronized_data.router_contract_address,
                        value=MAX_ALLOWANCE,
                    )
                ),
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_method_data",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"data": b"dummy_tx"},  # type: ignore
                ),
            ),
        )

        # Add liquidity
        self.mock_contract_api_request(
            contract_id=str(UniswapV2Router02Contract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=synchronized_data.router_contract_address,
                kwargs=Kwargs(
                    dict(
                        method_name="add_liquidity_ETH",
                        # sender=synchronized_data.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        token=strategy["token_b"]["address"],
                        amount_token_desired=int(
                            strategy["token_b"]["amount_after_swap"]
                        ),
                        amount_token_min=int(
                            strategy["token_b"]["amount_min_after_add_liq"]
                        ),
                        amount_ETH_min=int(
                            strategy["token_a"]["amount_min_after_add_liq"]
                        ),
                        to=synchronized_data.safe_contract_address,
                        deadline=DEADLINE,
                    )
                ),
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_method_data",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"data": b"dummy_tx"},  # type: ignore
                ),
            ),
        )

        # Get the tx list data from multisend contract
        self.mock_contract_api_request(
            contract_id=str(MultiSendContract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=synchronized_data.safe_contract_address,
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_tx_data",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"data": b"dummy_tx".hex()},
                ),
            ),
        )

        # Get the tx hash from Gnosis Safe contract
        self.mock_contract_api_request(
            contract_id=str(GnosisSafeContract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=synchronized_data.safe_contract_address,
                kwargs=Kwargs(
                    dict(
                        to_address=synchronized_data.multisend_contract_address,
                        value=0,
                        data=b"ummy_tx",  # type: ignore
                        operation=SafeOperation.DELEGATE_CALL.value,
                        safe_tx_gas=strategy["safe_tx_gas"]["enter"],
                        safe_nonce=strategy["safe_nonce"],
                    )
                ),
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_raw_safe_transaction_hash",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"tx_hash": "0xb0e6add595e00477cf347d09797b156719dc5233283ac76e4efce2a674fe72d9"},  # type: ignore
                ),
            ),
        )

        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round(Event.DONE)

    def test_transaction_hash_when_strategy_is_not_native(
        self,
    ) -> None:
        """Test tx hash behaviour."""

        strategy = get_default_strategy(
            is_base_native=False, is_a_native=False, is_b_native=False
        )
        synchronized_data = LiquidityRebalancingSynchronizedSata(
            AbciAppDB(
                setup_data=AbciAppDB.data_to_lists(
                    dict(
                        most_voted_tx_hash="0x",
                        safe_contract_address="safe_contract_address",
                        most_voted_keeper_address="most_voted_keeper_address",
                        most_voted_strategy=json.dumps(strategy),
                        multisend_contract_address="0xb0e6add595e00477cf347d09797b156719dc5233",
                        router_contract_address="router_contract_address",
                    )
                ),
            )
        )
        self.fast_forward_to_behaviour(
            behaviour=self.behaviour,
            behaviour_id=EnterPoolTransactionHashBehaviour.behaviour_id,
            synchronized_data=synchronized_data,
        )
        assert (
            cast(
                BaseBehaviour,
                cast(BaseBehaviour, self.behaviour.current_behaviour),
            ).behaviour_id
            == EnterPoolTransactionHashBehaviour.behaviour_id
        )
        self.behaviour.act_wrapper()

        # Add allowance for base token
        method_name = (
            "swap_tokens_for_exact_ETH"
            if strategy["token_a"]["is_native"]
            else "swap_tokens_for_exact_tokens"
        )

        self.mock_contract_api_request(
            contract_id=str(UniswapV2ERC20Contract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=strategy["token_base"]["address"],
                kwargs=Kwargs(
                    dict(
                        method_name="approve",
                        # sender=synchronized_data.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        spender=synchronized_data.router_contract_address,
                        value=MAX_ALLOWANCE,
                    )
                ),
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_method_data",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"data": b"dummy_tx"},  # type: ignore
                ),
            ),
        )

        # Swap first token
        self.mock_contract_api_request(
            contract_id=str(UniswapV2Router02Contract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=synchronized_data.router_contract_address,
                kwargs=Kwargs(
                    dict(
                        method_name=method_name,
                        # sender=synchronized_data.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        amount_out=int(strategy["token_a"]["amount_after_swap"]),
                        amount_in_max=int(strategy["token_base"]["amount_in_max_a"]),
                        path=[
                            strategy["token_base"]["address"],
                            strategy["token_a"]["address"],
                        ],
                        to=synchronized_data.safe_contract_address,
                        deadline=DEADLINE,
                    )
                ),
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_swap_tokens_for_exact_tokens_data",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"data": b"dummy_tx"},  # type: ignore
                ),
            ),
        )

        # Swap second token
        self.mock_contract_api_request(
            contract_id=str(UniswapV2Router02Contract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=synchronized_data.router_contract_address,
                kwargs=Kwargs(
                    dict(
                        method_name="swap_tokens_for_exact_tokens",
                        # sender=synchronized_data.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        amount_out=int(strategy["token_b"]["amount_after_swap"]),
                        amount_in_max=int(strategy["token_base"]["amount_in_max_b"]),
                        path=[
                            strategy["token_base"]["address"],
                            strategy["token_b"]["address"],
                        ],
                        to=synchronized_data.safe_contract_address,
                        deadline=DEADLINE,
                    )
                ),
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_swap_tokens_for_exact_tokens_data",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"data": b"dummy_tx"},  # type: ignore
                ),
            ),
        )

        # Add allowance for token A
        self.mock_contract_api_request(
            contract_id=str(UniswapV2ERC20Contract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=strategy["token_a"]["address"],
                kwargs=Kwargs(
                    dict(
                        method_name="approve",
                        # sender=synchronized_data.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        spender=synchronized_data.router_contract_address,
                        value=MAX_ALLOWANCE,
                    )
                ),
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_method_data",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"data": b"dummy_tx"},  # type: ignore
                ),
            ),
        )

        # Add allowance for token B
        self.mock_contract_api_request(
            contract_id=str(UniswapV2ERC20Contract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=strategy["token_b"]["address"],
                kwargs=Kwargs(
                    dict(
                        method_name="approve",
                        # sender=synchronized_data.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        spender=synchronized_data.router_contract_address,
                        value=MAX_ALLOWANCE,
                    )
                ),
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_method_data",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"data": b"dummy_tx"},  # type: ignore
                ),
            ),
        )

        # Add liquidity
        self.mock_contract_api_request(
            contract_id=str(UniswapV2Router02Contract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=synchronized_data.router_contract_address,
                kwargs=Kwargs(
                    dict(
                        method_name="add_liquidity",
                        # sender=synchronized_data.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        token_a=strategy["token_a"]["address"],
                        token_b=strategy["token_b"]["address"],
                        amount_a_desired=int(strategy["token_a"]["amount_after_swap"]),
                        amount_b_desired=int(strategy["token_b"]["amount_after_swap"]),
                        amount_a_min=int(
                            strategy["token_a"]["amount_min_after_add_liq"]
                        ),
                        amount_b_min=int(
                            strategy["token_b"]["amount_min_after_add_liq"]
                        ),
                        to=synchronized_data.safe_contract_address,
                        deadline=DEADLINE,
                    )
                ),
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_method_data",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"data": b"dummy_tx"},  # type: ignore
                ),
            ),
        )

        # Get the tx list data from multisend contract
        self.mock_contract_api_request(
            contract_id=str(MultiSendContract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=synchronized_data.safe_contract_address,
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_tx_data",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"data": b"dummy_tx".hex()},  # type: ignore
                ),
            ),
        )

        # Get the tx hash from Gnosis Safe contract
        self.mock_contract_api_request(
            contract_id=str(GnosisSafeContract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=synchronized_data.safe_contract_address,
                kwargs=Kwargs(
                    dict(
                        to_address=synchronized_data.multisend_contract_address,
                        value=0,
                        data=b"ummy_tx",  # type: ignore
                        operation=SafeOperation.DELEGATE_CALL.value,
                        safe_tx_gas=strategy["safe_tx_gas"]["enter"],
                        safe_nonce=strategy["safe_nonce"],
                    )
                ),
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_raw_safe_transaction_hash",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"tx_hash": "0xb0e6add595e00477cf347d09797b156719dc5233283ac76e4efce2a674fe72d9"},  # type: ignore
                ),
            ),
        )

        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round(Event.DONE)

    def test_transaction_hash_bad_swap_parameters(
        self,
    ) -> None:
        """Test tx hash behaviour."""

        strategy = get_default_strategy(
            is_base_native=True, is_a_native=True, is_b_native=False
        )
        synchronized_data = LiquidityRebalancingSynchronizedSata(
            AbciAppDB(
                setup_data=AbciAppDB.data_to_lists(
                    dict(
                        most_voted_tx_hash="0x",
                        safe_contract_address="safe_contract_address",
                        most_voted_keeper_address="most_voted_keeper_address",
                        most_voted_strategy=json.dumps(strategy),
                        multisend_contract_address="0xb0e6add595e00477cf347d09797b156719dc5233",
                        router_contract_address="router_contract_address",
                    )
                ),
            )
        )
        self.fast_forward_to_behaviour(
            behaviour=self.behaviour,
            behaviour_id=EnterPoolTransactionHashBehaviour.behaviour_id,
            synchronized_data=synchronized_data,
        )
        assert (
            cast(
                BaseBehaviour,
                cast(BaseBehaviour, self.behaviour.current_behaviour),
            ).behaviour_id
            == EnterPoolTransactionHashBehaviour.behaviour_id
        )

        with pytest.raises(AEAActException):

            self.behaviour.act_wrapper()

            # Add allowance for base token
            self.mock_contract_api_request(
                contract_id=str(UniswapV2ERC20Contract.contract_id),
                request_kwargs=dict(
                    performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                    contract_address=strategy["token_base"]["address"],
                    kwargs=Kwargs(
                        dict(
                            method_name="approve",
                            spender=synchronized_data.router_contract_address,
                            value=MAX_ALLOWANCE,
                        )
                    ),
                ),
                response_kwargs=dict(
                    performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                    callable="get_method_data",
                    raw_transaction=RawTransaction(
                        ledger_id="ethereum",
                        body={"data": b"dummy_tx"},  # type: ignore
                    ),
                ),
            )


class TestExitPoolTransactionHashBehaviour(LiquidityRebalancingBehaviourBaseCase):
    """Test ExitPoolTransactionHashBehaviour."""

    def test_transaction_hash(
        self,
    ) -> None:
        """Test tx hash behaviour."""

        strategy = get_default_strategy(
            is_base_native=False, is_a_native=True, is_b_native=False
        )
        synchronized_data = LiquidityRebalancingSynchronizedSata(
            AbciAppDB(
                setup_data=AbciAppDB.data_to_lists(
                    dict(
                        most_voted_tx_hash="0x",
                        safe_contract_address="safe_contract_address",
                        most_voted_keeper_address="most_voted_keeper_address",
                        most_voted_strategy=json.dumps(strategy),
                        multisend_contract_address="0xb0e6add595e00477cf347d09797b156719dc5233",
                        router_contract_address="router_contract_address",
                        final_tx_hash=binascii.hexlify(b"dummy_tx").decode(),
                    )
                ),
            )
        )

        amount_base_sent = 0
        amount_b_sent = 0
        amount_liquidity_received = 0

        self.fast_forward_to_behaviour(
            behaviour=self.behaviour,
            behaviour_id=ExitPoolTransactionHashBehaviour.behaviour_id,
            synchronized_data=synchronized_data,
        )
        assert (
            cast(
                BaseBehaviour,
                cast(BaseBehaviour, self.behaviour.current_behaviour),
            ).behaviour_id
            == ExitPoolTransactionHashBehaviour.behaviour_id
        )
        self.behaviour.act_wrapper()

        # Get previous transaction's results
        self.mock_contract_api_request(
            contract_id=str(UniswapV2ERC20Contract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_STATE,  # type: ignore
                contract_address=strategy["token_LP"]["address"],
                kwargs=Kwargs(
                    dict(
                        tx_hash=synchronized_data.final_tx_hash,
                        target_address=synchronized_data.safe_contract_address,
                    )
                ),
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.STATE,
                callable="verify_tx",
                state=State(
                    ledger_id="ethereum",
                    body={"logs": []},
                ),
            ),
        )

        # Add allowance for LP token to be spent by the router
        self.mock_contract_api_request(
            contract_id=str(UniswapV2ERC20Contract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=strategy["token_LP"]["address"],
                kwargs=Kwargs(
                    dict(
                        method_name="approve",
                        # sender=synchronized_data.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        spender=synchronized_data.router_contract_address,
                        value=strategy["token_LP"]["set_allowance"],
                    )
                ),
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_method_data",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"data": b"dummy_tx"},  # type: ignore
                ),
            ),
        )

        # Remove liquidity
        self.mock_contract_api_request(
            contract_id=str(UniswapV2Router02Contract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=synchronized_data.router_contract_address,
                kwargs=Kwargs(
                    dict(
                        method_name="remove_liquidity_ETH",
                        # sender=synchronized_data.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        token=strategy["token_b"]["address"],
                        liquidity=amount_liquidity_received,
                        amount_token_min=int(amount_b_sent),
                        amount_ETH_min=int(amount_base_sent),
                        to=synchronized_data.safe_contract_address,
                        deadline=DEADLINE,
                    )
                ),
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_method_data",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"data": b"dummy_tx"},  # type: ignore
                ),
            ),
        )

        # Remove allowance for LP token
        self.mock_contract_api_request(
            contract_id=str(UniswapV2ERC20Contract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=strategy["token_LP"]["address"],
                kwargs=Kwargs(
                    dict(
                        method_name="approve",
                        # sender=synchronized_data.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        spender=synchronized_data.router_contract_address,
                        value=strategy["token_LP"]["remove_allowance"],
                    )
                ),
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_method_data",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"data": b"dummy_tx"},  # type: ignore
                ),
            ),
        )

        # Get the tx list data from multisend contract
        self.mock_contract_api_request(
            contract_id=str(MultiSendContract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=synchronized_data.safe_contract_address,
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_tx_data",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"data": b"dummy_tx".hex()},  # type: ignore
                ),
            ),
        )

        # Get the tx hash from Gnosis Safe contract
        self.mock_contract_api_request(
            contract_id=str(GnosisSafeContract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=synchronized_data.safe_contract_address,
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_raw_safe_transaction_hash",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"tx_hash": "0xb0e6add595e00477cf347d09797b156719dc5233283ac76e4efce2a674fe72d9"},  # type: ignore
                ),
            ),
        )

        self.mock_a2a_transaction()
        self.end_round(Event.DONE)

    def test_transaction_hash_when_strategy_is_not_native(
        self,
    ) -> None:
        """Test tx hash behaviour."""

        strategy = get_default_strategy(
            is_base_native=False, is_a_native=False, is_b_native=False
        )
        synchronized_data = LiquidityRebalancingSynchronizedSata(
            AbciAppDB(
                setup_data=AbciAppDB.data_to_lists(
                    dict(
                        most_voted_tx_hash="0x",
                        safe_contract_address="safe_contract_address",
                        most_voted_keeper_address="most_voted_keeper_address",
                        most_voted_strategy=json.dumps(strategy),
                        multisend_contract_address="0xb0e6add595e00477cf347d09797b156719dc5233",
                        router_contract_address="router_contract_address",
                        final_tx_hash=binascii.hexlify(b"dummy_tx").decode(),
                    )
                ),
            )
        )

        amount_a_sent = 0
        amount_b_sent = 0
        amount_liquidity_received = 0

        self.fast_forward_to_behaviour(
            behaviour=self.behaviour,
            behaviour_id=ExitPoolTransactionHashBehaviour.behaviour_id,
            synchronized_data=synchronized_data,
        )
        assert (
            cast(
                BaseBehaviour,
                cast(BaseBehaviour, self.behaviour.current_behaviour),
            ).behaviour_id
            == ExitPoolTransactionHashBehaviour.behaviour_id
        )
        self.behaviour.act_wrapper()

        # Get previous transaction's results
        self.mock_contract_api_request(
            contract_id=str(UniswapV2ERC20Contract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_STATE,  # type: ignore
                contract_address=strategy["token_LP"]["address"],
                kwargs=Kwargs(
                    dict(
                        tx_hash=synchronized_data.final_tx_hash,
                        target_address=synchronized_data.safe_contract_address,
                    )
                ),
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.STATE,
                callable="verify_tx",
                state=State(
                    ledger_id="ethereum",
                    body={"logs": []},
                ),
            ),
        )

        # Add allowance for LP token to be spent by the router
        self.mock_contract_api_request(
            contract_id=str(UniswapV2ERC20Contract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=strategy["token_LP"]["address"],
                kwargs=Kwargs(
                    dict(
                        method_name="approve",
                        # sender=synchronized_data.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        spender=synchronized_data.router_contract_address,
                        value=MAX_ALLOWANCE,
                    )
                ),
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_method_data",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"data": b"dummy_tx"},  # type: ignore
                ),
            ),
        )

        # Remove liquidity
        self.mock_contract_api_request(
            contract_id=str(UniswapV2Router02Contract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=synchronized_data.router_contract_address,
                kwargs=Kwargs(
                    dict(
                        method_name="remove_liquidity",
                        # sender=synchronized_data.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        token_a=strategy["token_a"]["address"],
                        token_b=strategy["token_b"]["address"],
                        liquidity=amount_liquidity_received,
                        amount_a_min=int(amount_a_sent),
                        amount_b_min=int(amount_b_sent),
                        to=synchronized_data.safe_contract_address,
                        deadline=DEADLINE,
                    )
                ),
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_method_data",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"data": b"dummy_tx"},  # type: ignore
                ),
            ),
        )

        # Remove allowance for LP token
        self.mock_contract_api_request(
            contract_id=str(UniswapV2ERC20Contract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=strategy["token_LP"]["address"],
                kwargs=Kwargs(
                    dict(
                        method_name="approve",
                        # sender=synchronized_data.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        spender=synchronized_data.router_contract_address,
                        value=strategy["token_LP"]["remove_allowance"],
                    )
                ),
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_method_data",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"data": b"dummy_tx"},  # type: ignore
                ),
            ),
        )

        # Get the tx list data from multisend contract
        self.mock_contract_api_request(
            contract_id=str(MultiSendContract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=synchronized_data.safe_contract_address,
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_tx_data",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"data": b"dummy_tx".hex()},  # type: ignore
                ),
            ),
        )

        # Get the tx hash from Gnosis Safe contract
        self.mock_contract_api_request(
            contract_id=str(GnosisSafeContract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=synchronized_data.safe_contract_address,
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_raw_safe_transaction_hash",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"tx_hash": "0xb0e6add595e00477cf347d09797b156719dc5233283ac76e4efce2a674fe72d9"},  # type: ignore
                ),
            ),
        )

        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round(Event.DONE)

    def test_log_no_tx_results(
        self,
    ) -> None:
        """Test tx hash behaviour."""

        strategy = get_default_strategy(
            is_base_native=False, is_a_native=True, is_b_native=False
        )
        synchronized_data = LiquidityRebalancingSynchronizedSata(
            AbciAppDB(
                setup_data=AbciAppDB.data_to_lists(
                    dict(
                        most_voted_tx_hash="0x",
                        safe_contract_address="safe_contract_address",
                        most_voted_keeper_address="most_voted_keeper_address",
                        most_voted_strategy=json.dumps(strategy),
                        multisend_contract_address="0xb0e6add595e00477cf347d09797b156719dc5233",
                        router_contract_address="router_contract_address",
                        final_tx_hash=binascii.hexlify(b"dummy_tx").decode(),
                    )
                ),
            )
        )

        self.fast_forward_to_behaviour(
            behaviour=self.behaviour,
            behaviour_id=ExitPoolTransactionHashBehaviour.behaviour_id,
            synchronized_data=synchronized_data,
        )
        assert (
            cast(
                BaseBehaviour,
                cast(BaseBehaviour, self.behaviour.current_behaviour),
            ).behaviour_id
            == ExitPoolTransactionHashBehaviour.behaviour_id
        )
        self.behaviour.act_wrapper()

        # Get previous transaction's results
        self.mock_contract_api_request(
            contract_id=str(UniswapV2ERC20Contract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_STATE,  # type: ignore
                contract_address=strategy["token_LP"]["address"],
                kwargs=Kwargs(
                    dict(
                        tx_hash=synchronized_data.final_tx_hash,
                        target_address=synchronized_data.safe_contract_address,
                    )
                ),
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.ERROR,
                callable="verify_tx",
                state=State(
                    ledger_id="ethereum",
                    body={"logs": []},
                ),
            ),
        )

        assert (
            cast(
                BaseBehaviour,
                cast(BaseBehaviour, self.behaviour.current_behaviour),
            ).behaviour_id
            == ExitPoolTransactionHashBehaviour.behaviour_id
        )


class TestSwapBackTransactionHashBehaviour(LiquidityRebalancingBehaviourBaseCase):
    """Test SwapBackTransactionHashBehaviour."""

    def test_transaction_hash(
        self,
    ) -> None:
        """Test tx hash behaviour."""

        strategy = get_default_strategy(
            is_base_native=False, is_a_native=True, is_b_native=False
        )
        synchronized_data = LiquidityRebalancingSynchronizedSata(
            AbciAppDB(
                setup_data=AbciAppDB.data_to_lists(
                    dict(
                        most_voted_tx_hash="0x",
                        safe_contract_address="safe_contract_address",
                        most_voted_keeper_address="most_voted_keeper_address",
                        most_voted_strategy=json.dumps(strategy),
                        multisend_contract_address="0xb0e6add595e00477cf347d09797b156719dc5233",
                        router_contract_address="router_contract_address",
                        final_tx_hash=binascii.hexlify(b"dummy_tx").decode(),
                    )
                ),
            )
        )
        self.fast_forward_to_behaviour(
            behaviour=self.behaviour,
            behaviour_id=SwapBackTransactionHashBehaviour.behaviour_id,
            synchronized_data=synchronized_data,
        )
        assert (
            cast(
                BaseBehaviour,
                cast(BaseBehaviour, self.behaviour.current_behaviour),
            ).behaviour_id
            == SwapBackTransactionHashBehaviour.behaviour_id
        )
        self.behaviour.act_wrapper()

        # Get previous transaction's results
        self.mock_contract_api_request(
            contract_id=str(UniswapV2ERC20Contract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_STATE,  # type: ignore
                contract_address=strategy["token_LP"]["address"],
                kwargs=Kwargs(
                    dict(
                        tx_hash=synchronized_data.final_tx_hash,
                        target_address=synchronized_data.safe_contract_address,
                    )
                ),
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.STATE,
                callable="verify_tx",
                state=State(
                    ledger_id="ethereum",
                    body={"logs": []},
                ),
            ),
        )

        # Swap first token back
        self.mock_contract_api_request(
            contract_id=str(UniswapV2Router02Contract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=synchronized_data.router_contract_address,
                kwargs=Kwargs(
                    dict(
                        method_name="swap_exact_ETH_for_tokens",
                        # sender=synchronized_data.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        amount_out_min=int(
                            strategy["token_base"]["amount_min_after_swap_back_a"]
                        ),
                        path=[
                            strategy["token_a"]["address"],
                            strategy["token_base"]["address"],
                        ],
                        to=synchronized_data.safe_contract_address,
                        deadline=DEADLINE,
                    )
                ),
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_method_data",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"data": b"dummy_tx"},  # type: ignore
                ),
            ),
        )

        # Swap second token back
        amount_b_received = 0
        self.mock_contract_api_request(
            contract_id=str(UniswapV2Router02Contract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=synchronized_data.router_contract_address,
                kwargs=Kwargs(
                    dict(
                        method_name="swap_exact_tokens_for_tokens",
                        # sender=synchronized_data.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        amount_in=int(
                            amount_b_received,
                        ),
                        amount_out_min=int(
                            strategy["token_base"]["amount_min_after_swap_back_b"]
                        ),
                        path=[
                            strategy["token_b"]["address"],
                            strategy["token_base"]["address"],
                        ],
                        to=synchronized_data.safe_contract_address,
                        deadline=DEADLINE,
                    )
                ),
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_method_data",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"data": b"dummy_tx"},  # type: ignore
                ),
            ),
        )

        # Remove allowance for base token
        self.mock_contract_api_request(
            contract_id=str(UniswapV2ERC20Contract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=strategy["token_base"]["address"],
                kwargs=Kwargs(
                    dict(
                        method_name="approve",
                        # sender=synchronized_data.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        spender=synchronized_data.router_contract_address,
                        value=0,
                    )
                ),
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_method_data",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"data": b"dummy_tx"},  # type: ignore
                ),
            ),
        )

        # Remove allowance for the second token
        self.mock_contract_api_request(
            contract_id=str(UniswapV2ERC20Contract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=strategy["token_b"]["address"],
                kwargs=Kwargs(
                    dict(
                        method_name="approve",
                        # sender=synchronized_data.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        spender=synchronized_data.router_contract_address,
                        value=0,
                    )
                ),
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_method_data",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"data": b"dummy_tx"},  # type: ignore
                ),
            ),
        )

        # Get the tx list data from multisend contract
        self.mock_contract_api_request(
            contract_id=str(MultiSendContract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=synchronized_data.safe_contract_address,
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_tx_data",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"data": b"dummy_tx".hex()},  # type: ignore
                ),
            ),
        )

        # Get the tx hash from Gnosis Safe contract
        self.mock_contract_api_request(
            contract_id=str(GnosisSafeContract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=synchronized_data.safe_contract_address,
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_raw_safe_transaction_hash",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"tx_hash": "0xb0e6add595e00477cf347d09797b156719dc5233283ac76e4efce2a674fe72d9"},  # type: ignore
                ),
            ),
        )

        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round(Event.DONE)

    def test_transaction_hash_when_strategy_is_not_native(
        self,
    ) -> None:
        """Test tx hash behaviour."""

        strategy = get_default_strategy(
            is_base_native=False, is_a_native=False, is_b_native=False
        )
        synchronized_data = LiquidityRebalancingSynchronizedSata(
            AbciAppDB(
                setup_data=AbciAppDB.data_to_lists(
                    dict(
                        most_voted_tx_hash="0x",
                        safe_contract_address="safe_contract_address",
                        most_voted_keeper_address="most_voted_keeper_address",
                        most_voted_strategy=json.dumps(strategy),
                        multisend_contract_address="0xb0e6add595e00477cf347d09797b156719dc5233",
                        router_contract_address="router_contract_address",
                        final_tx_hash=binascii.hexlify(b"dummy_tx").decode(),
                    )
                ),
            )
        )
        self.fast_forward_to_behaviour(
            behaviour=self.behaviour,
            behaviour_id=SwapBackTransactionHashBehaviour.behaviour_id,
            synchronized_data=synchronized_data,
        )
        assert (
            cast(
                BaseBehaviour,
                cast(BaseBehaviour, self.behaviour.current_behaviour),
            ).behaviour_id
            == SwapBackTransactionHashBehaviour.behaviour_id
        )
        self.behaviour.act_wrapper()

        # Get previous transaction's results
        self.mock_contract_api_request(
            contract_id=str(UniswapV2ERC20Contract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_STATE,  # type: ignore
                contract_address=strategy["token_LP"]["address"],
                kwargs=Kwargs(
                    dict(
                        tx_hash=synchronized_data.final_tx_hash,
                        target_address=synchronized_data.safe_contract_address,
                    )
                ),
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.STATE,
                callable="verify_tx",
                state=State(
                    ledger_id="ethereum",
                    body={"logs": []},
                ),
            ),
        )

        # Swap first token back
        amount_a_received = 0
        self.mock_contract_api_request(
            contract_id=str(UniswapV2Router02Contract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=synchronized_data.router_contract_address,
                kwargs=Kwargs(
                    dict(
                        method_name="swap_exact_tokens_for_tokens",
                        # sender=synchronized_data.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        amount_in=int(amount_a_received),
                        amount_out_min=int(
                            strategy["token_base"]["amount_min_after_swap_back_a"]
                        ),
                        path=[
                            strategy["token_a"]["address"],
                            strategy["token_base"]["address"],
                        ],
                        to=synchronized_data.safe_contract_address,
                        deadline=DEADLINE,
                    )
                ),
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_method_data",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"data": b"dummy_tx"},  # type: ignore
                ),
            ),
        )

        # Swap second token back
        amount_b_received = 0
        self.mock_contract_api_request(
            contract_id=str(UniswapV2Router02Contract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=synchronized_data.router_contract_address,
                kwargs=Kwargs(
                    dict(
                        method_name="swap_exact_tokens_for_tokens",
                        # sender=synchronized_data.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        amount_in=int(amount_b_received),
                        amount_out_min=int(
                            strategy["token_base"]["amount_min_after_swap_back_b"]
                        ),
                        path=[
                            strategy["token_b"]["address"],
                            strategy["token_base"]["address"],
                        ],
                        to=synchronized_data.safe_contract_address,
                        deadline=DEADLINE,
                    )
                ),
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_method_data",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"data": b"dummy_tx"},  # type: ignore
                ),
            ),
        )

        # Remove allowance for base token
        self.mock_contract_api_request(
            contract_id=str(UniswapV2ERC20Contract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=strategy["token_base"]["address"],
                kwargs=Kwargs(
                    dict(
                        method_name="approve",
                        # sender=synchronized_data.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        spender=synchronized_data.router_contract_address,
                        value=0,
                    )
                ),
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_method_data",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"data": b"dummy_tx"},  # type: ignore
                ),
            ),
        )

        # Remove allowance for the first token
        self.mock_contract_api_request(
            contract_id=str(UniswapV2ERC20Contract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=strategy["token_a"]["address"],
                kwargs=Kwargs(
                    dict(
                        method_name="approve",
                        # sender=synchronized_data.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        spender=synchronized_data.router_contract_address,
                        value=0,
                    )
                ),
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_method_data",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"data": b"dummy_tx"},  # type: ignore
                ),
            ),
        )

        # Remove allowance for the second token
        self.mock_contract_api_request(
            contract_id=str(UniswapV2ERC20Contract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=strategy["token_b"]["address"],
                kwargs=Kwargs(
                    dict(
                        method_name="approve",
                        # sender=synchronized_data.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        spender=synchronized_data.router_contract_address,
                        value=0,
                    )
                ),
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_method_data",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"data": b"dummy_tx"},  # type: ignore
                ),
            ),
        )

        # Get the tx list data from multisend contract
        self.mock_contract_api_request(
            contract_id=str(MultiSendContract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=synchronized_data.safe_contract_address,
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_tx_data",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"data": b"dummy_tx".hex()},  # type: ignore
                ),
            ),
        )

        # Get the tx hash from Gnosis Safe contract
        self.mock_contract_api_request(
            contract_id=str(GnosisSafeContract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=synchronized_data.safe_contract_address,
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_raw_safe_transaction_hash",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"tx_hash": "0xb0e6add595e00477cf347d09797b156719dc5233283ac76e4efce2a674fe72d9"},  # type: ignore
                ),
            ),
        )

        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round(Event.DONE)


def test_parse_tx_token_balance() -> None:
    """Test test_parse_tx_token_balance"""

    transfer_logs = [
        {"from": "from", "to": "to", "token_address": "token_address", "value": 1},
        {"from": "from", "to": "to", "token_address": "token_address", "value": 1},
        {
            "from": "from_2",
            "to": "to_2",
            "token_address": "token_address_2",
            "value": 1,
        },
    ]

    amount_1 = parse_tx_token_balance(  # nosec
        transfer_logs=transfer_logs,
        token_address="token_address",
        source_address="from",
        destination_address="to",
    )
    amount_2 = parse_tx_token_balance(  # nosec
        transfer_logs=transfer_logs,
        token_address="token_address_2",
        source_address="from_2",
        destination_address="to_2",
    )
    assert amount_1 == 2, "The transfered amount is not correct"
    assert amount_2 == 1, "The transfered amount is not correct"


class TestSleepBehaviour(LiquidityRebalancingBehaviourBaseCase):
    """Test SleepBehaviour."""

    def test_sleep(
        self,
    ) -> None:
        """Run tests."""

        synchronized_data = LiquidityRebalancingSynchronizedSata(
            AbciAppDB(
                setup_data=AbciAppDB.data_to_lists(
                    dict(
                        most_voted_tx_hash="0x",
                        safe_contract_address="safe_contract_address",
                        most_voted_keeper_address="most_voted_keeper_address",
                        multisend_contract_address="0xb0e6add595e00477cf347d09797b156719dc5233",
                        router_contract_address="router_contract_address",
                    )
                ),
            )
        )
        self.fast_forward_to_behaviour(
            behaviour=self.behaviour,
            behaviour_id=SleepBehaviour.behaviour_id,
            synchronized_data=synchronized_data,
        )
        assert (
            cast(
                BaseBehaviour,
                cast(BaseBehaviour, self.behaviour.current_behaviour),
            ).behaviour_id
            == SleepBehaviour.behaviour_id
        )
        self.behaviour.act_wrapper()
        time.sleep(SLEEP_SECONDS)
        self.behaviour.act_wrapper()
        self.mock_a2a_transaction()
        self._test_done_flag_set()
