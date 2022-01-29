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
"""Tests for valory/liquidity_provision_behaviour skill's behaviours."""
from pathlib import Path
from typing import Dict, cast

import pytest
from aea.exceptions import AEAActException
from aea.helpers.transaction.base import RawTransaction

from packages.valory.contracts.gnosis_safe.contract import SafeOperation
from packages.valory.contracts.multisend.contract import MultiSendContract
from packages.valory.contracts.uniswap_v2_erc20.contract import UniswapV2ERC20Contract
from packages.valory.contracts.uniswap_v2_router_02.contract import (
    UniswapV2Router02Contract,
)
from packages.valory.protocols.contract_api.custom_types import Kwargs
from packages.valory.protocols.contract_api.message import ContractApiMessage
from packages.valory.skills.abstract_round_abci.base import StateDB
from packages.valory.skills.abstract_round_abci.behaviour_utils import BaseState
from packages.valory.skills.liquidity_provision.behaviours import (
    CURRENT_BLOCK_TIMESTAMP,
    ETHER_VALUE,
    EnterPoolTransactionHashBehaviour,
    ExitPoolTransactionHashBehaviour,
    GnosisSafeContract,
    LP_TOKEN_ADDRESS,
    MAX_ALLOWANCE,
    SAFE_TX_GAS,
    StrategyEvaluationBehaviour,
    SwapBackTransactionHashBehaviour,
    parse_tx_token_balance,
)
from packages.valory.skills.liquidity_provision.payloads import StrategyType
from packages.valory.skills.liquidity_provision.rounds import Event, PeriodState

from tests.conftest import ROOT_DIR
from tests.test_skills.base import FSMBehaviourBaseCase


def get_default_strategy(
    is_base_native: bool, is_a_native: bool, is_b_native: bool
) -> Dict:
    """Returns default strategy."""
    return {
        "action": StrategyType.ENTER.value,
        "safe_nonce": 0,
        "chain": "Ethereum",
        "safe_tx_gas": SAFE_TX_GAS,
        "deadline": CURRENT_BLOCK_TIMESTAMP + 300,  # 5 min into future
        "base": {
            "ticker": "WETH",
            "address": "0xWETH_ADDRESS",
            "amount_in_max_a": int(1e4),
            "amount_min_after_swap_back_a": int(1e2),
            "amount_in_max_b": int(1e4),
            "amount_min_after_swap_back_b": int(1e2),
            "is_native": is_base_native,
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
                "address": "0xTKA_ADDRESS",
                "amount_after_swap": int(1e3),
                "amount_min_after_add_liq": int(0.5e3),
                "is_native": is_a_native,
                "set_allowance": MAX_ALLOWANCE,
                "remove_allowance": 0,
            },
            "token_b": {
                "ticker": "TKB",
                "address": "0xTKB_ADDRESS",
                "amount_after_swap": int(1e3),
                "amount_min_after_add_liq": int(0.5e3),
                "is_native": is_b_native,
                "set_allowance": MAX_ALLOWANCE,
                "remove_allowance": 0,
            },
        },
    }


class LiquidityProvisionBehaviourBaseCase(FSMBehaviourBaseCase):
    """Base case for testing PriceEstimation FSMBehaviour."""

    path_to_skill = Path(
        ROOT_DIR, "packages", "valory", "skills", "liquidity_provision"
    )


class TestStrategyEvaluationBehaviour(LiquidityProvisionBehaviourBaseCase):
    """Test StrategyEvaluationBehaviour."""

    def test_transaction_hash(
        self,
    ) -> None:
        """Test tx hash behaviour."""

        strategy = get_default_strategy(
            is_base_native=False, is_a_native=True, is_b_native=False
        )
        period_state = PeriodState(
            StateDB(
                initial_period=0,
                initial_data=dict(
                    most_voted_tx_hash="0x",
                    safe_contract_address="safe_contract_address",
                    most_voted_keeper_address="most_voted_keeper_address",
                    most_voted_strategy=strategy,
                    multisend_contract_address="multisend_contract_address",
                    router_contract_address="router_contract_address",
                ),
            )
        )
        self.fast_forward_to_state(
            behaviour=self.behaviour,
            state_id=StrategyEvaluationBehaviour.state_id,
            period_state=period_state,
        )
        assert (
            cast(
                BaseState,
                cast(BaseState, self.behaviour.current_state),
            ).state_id
            == StrategyEvaluationBehaviour.state_id
        )
        self.behaviour.act_wrapper()

        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round(Event.DONE)


class TestEnterPoolTransactionHashBehaviour(LiquidityProvisionBehaviourBaseCase):
    """Test EnterPoolTransactionHashBehaviour."""

    def test_transaction_hash(
        self,
    ) -> None:
        """Test tx hash behaviour."""

        strategy = get_default_strategy(
            is_base_native=False, is_a_native=True, is_b_native=False
        )
        period_state = PeriodState(
            StateDB(
                initial_period=0,
                initial_data=dict(
                    most_voted_tx_hash="0x",
                    safe_contract_address="safe_contract_address",
                    most_voted_keeper_address="most_voted_keeper_address",
                    most_voted_strategy=strategy,
                    multisend_contract_address="multisend_contract_address",
                    router_contract_address="router_contract_address",
                ),
            )
        )
        self.fast_forward_to_state(
            behaviour=self.behaviour,
            state_id=EnterPoolTransactionHashBehaviour.state_id,
            period_state=period_state,
        )
        assert (
            cast(
                BaseState,
                cast(BaseState, self.behaviour.current_state),
            ).state_id
            == EnterPoolTransactionHashBehaviour.state_id
        )
        self.behaviour.act_wrapper()

        # Add allowance for base token
        self.mock_contract_api_request(
            contract_id=str(UniswapV2ERC20Contract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=strategy["base"]["address"],
                kwargs=Kwargs(
                    dict(
                        method_name="approve",
                        # sender=period_state.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        spender=period_state.router_contract_address,
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
            if strategy["pair"]["token_a"]["is_native"]
            else "swap_tokens_for_exact_tokens"
        )

        self.mock_contract_api_request(
            contract_id=str(UniswapV2Router02Contract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=period_state.router_contract_address,
                kwargs=Kwargs(
                    dict(
                        method_name=method_name,
                        # sender=period_state.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        amount_out=int(
                            strategy["pair"]["token_a"]["amount_after_swap"]
                        ),
                        amount_in_max=int(strategy["base"]["amount_in_max_a"]),
                        path=[
                            strategy["base"]["address"],
                            strategy["pair"]["token_a"]["address"],
                        ],
                        to=period_state.safe_contract_address,
                        deadline=CURRENT_BLOCK_TIMESTAMP + 300,
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
                contract_address=period_state.router_contract_address,
                kwargs=Kwargs(
                    dict(
                        method_name="swap_tokens_for_exact_tokens",
                        # sender=period_state.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        amount_out=int(
                            strategy["pair"]["token_b"]["amount_after_swap"]
                        ),
                        amount_in_max=int(strategy["base"]["amount_in_max_b"]),
                        path=[
                            strategy["base"]["address"],
                            strategy["pair"]["token_b"]["address"],
                        ],
                        to=period_state.safe_contract_address,
                        deadline=CURRENT_BLOCK_TIMESTAMP + 300,  # 5 min into the future
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
                contract_address=strategy["pair"]["token_b"]["address"],
                kwargs=Kwargs(
                    dict(
                        method_name="approve",
                        # sender=period_state.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        spender=period_state.router_contract_address,
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
                contract_address=period_state.router_contract_address,
                kwargs=Kwargs(
                    dict(
                        method_name="add_liquidity_ETH",
                        # sender=period_state.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
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
                        to=period_state.safe_contract_address,
                        deadline=CURRENT_BLOCK_TIMESTAMP + 300,
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
                contract_address=period_state.safe_contract_address,
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
                contract_address=period_state.safe_contract_address,
                kwargs=Kwargs(
                    dict(
                        to_address=period_state.multisend_contract_address,
                        value=ETHER_VALUE,
                        data=b"ummy_tx",  # type: ignore
                        operation=SafeOperation.DELEGATE_CALL.value,
                        safe_tx_gas=4000000,
                        safe_nonce=strategy["safe_nonce"],
                    )
                ),
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_raw_safe_transaction_hash",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"tx_hash": b"dummy_tx".hex()},  # type: ignore
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
        period_state = PeriodState(
            StateDB(
                initial_period=0,
                initial_data=dict(
                    most_voted_tx_hash="0x",
                    safe_contract_address="safe_contract_address",
                    most_voted_keeper_address="most_voted_keeper_address",
                    most_voted_strategy=strategy,
                    multisend_contract_address="multisend_contract_address",
                    router_contract_address="router_contract_address",
                ),
            )
        )
        self.fast_forward_to_state(
            behaviour=self.behaviour,
            state_id=EnterPoolTransactionHashBehaviour.state_id,
            period_state=period_state,
        )
        assert (
            cast(
                BaseState,
                cast(BaseState, self.behaviour.current_state),
            ).state_id
            == EnterPoolTransactionHashBehaviour.state_id
        )
        self.behaviour.act_wrapper()

        # Add allowance for base token
        method_name = (
            "swap_tokens_for_exact_ETH"
            if strategy["pair"]["token_a"]["is_native"]
            else "swap_tokens_for_exact_tokens"
        )

        self.mock_contract_api_request(
            contract_id=str(UniswapV2ERC20Contract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=strategy["base"]["address"],
                kwargs=Kwargs(
                    dict(
                        method_name="approve",
                        # sender=period_state.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        spender=period_state.router_contract_address,
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
                contract_address=period_state.router_contract_address,
                kwargs=Kwargs(
                    dict(
                        method_name=method_name,
                        # sender=period_state.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        amount_out=int(
                            strategy["pair"]["token_a"]["amount_after_swap"]
                        ),
                        amount_in_max=int(strategy["base"]["amount_in_max_a"]),
                        path=[
                            strategy["base"]["address"],
                            strategy["pair"]["token_a"]["address"],
                        ],
                        to=period_state.safe_contract_address,
                        deadline=CURRENT_BLOCK_TIMESTAMP + 300,
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
                contract_address=period_state.router_contract_address,
                kwargs=Kwargs(
                    dict(
                        method_name="swap_tokens_for_exact_tokens",
                        # sender=period_state.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        amount_out=int(
                            strategy["pair"]["token_b"]["amount_after_swap"]
                        ),
                        amount_in_max=int(strategy["base"]["amount_in_max_b"]),
                        path=[
                            strategy["base"]["address"],
                            strategy["pair"]["token_b"]["address"],
                        ],
                        to=period_state.safe_contract_address,
                        deadline=CURRENT_BLOCK_TIMESTAMP + 300,  # 5 min into the future
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
                contract_address=strategy["pair"]["token_a"]["address"],
                kwargs=Kwargs(
                    dict(
                        method_name="approve",
                        # sender=period_state.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        spender=period_state.router_contract_address,
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
                contract_address=strategy["pair"]["token_b"]["address"],
                kwargs=Kwargs(
                    dict(
                        method_name="approve",
                        # sender=period_state.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        spender=period_state.router_contract_address,
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
                contract_address=period_state.router_contract_address,
                kwargs=Kwargs(
                    dict(
                        method_name="add_liquidity",
                        # sender=period_state.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
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
                        to=period_state.safe_contract_address,
                        deadline=CURRENT_BLOCK_TIMESTAMP + 300,
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
                contract_address=period_state.safe_contract_address,
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
                contract_address=period_state.safe_contract_address,
                kwargs=Kwargs(
                    dict(
                        to_address=period_state.multisend_contract_address,
                        value=ETHER_VALUE,
                        data=b"ummy_tx",  # type: ignore
                        operation=SafeOperation.DELEGATE_CALL.value,
                        safe_tx_gas=4000000,
                        safe_nonce=strategy["safe_nonce"],
                    )
                ),
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_raw_safe_transaction_hash",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"tx_hash": b"dummy_tx".hex()},  # type: ignore
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
        period_state = PeriodState(
            StateDB(
                initial_period=0,
                initial_data=dict(
                    most_voted_tx_hash="0x",
                    safe_contract_address="safe_contract_address",
                    most_voted_keeper_address="most_voted_keeper_address",
                    most_voted_strategy=strategy,
                    multisend_contract_address="multisend_contract_address",
                    router_contract_address="router_contract_address",
                ),
            )
        )
        self.fast_forward_to_state(
            behaviour=self.behaviour,
            state_id=EnterPoolTransactionHashBehaviour.state_id,
            period_state=period_state,
        )
        assert (
            cast(
                BaseState,
                cast(BaseState, self.behaviour.current_state),
            ).state_id
            == EnterPoolTransactionHashBehaviour.state_id
        )

        with pytest.raises(AEAActException):

            self.behaviour.act_wrapper()

            # Add allowance for base token
            self.mock_contract_api_request(
                contract_id=str(UniswapV2ERC20Contract.contract_id),
                request_kwargs=dict(
                    performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                    contract_address=strategy["base"]["address"],
                    kwargs=Kwargs(
                        dict(
                            method_name="approve",
                            spender=period_state.router_contract_address,
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


class TestExitPoolTransactionHashBehaviour(LiquidityProvisionBehaviourBaseCase):
    """Test ExitPoolTransactionHashBehaviour."""

    def test_transaction_hash(
        self,
    ) -> None:
        """Test tx hash behaviour."""

        strategy = get_default_strategy(
            is_base_native=False, is_a_native=True, is_b_native=False
        )
        period_state = PeriodState(
            StateDB(
                initial_period=0,
                initial_data=dict(
                    most_voted_tx_hash="0x",
                    safe_contract_address="safe_contract_address",
                    most_voted_keeper_address="most_voted_keeper_address",
                    most_voted_strategy=strategy,
                    multisend_contract_address="multisend_contract_address",
                    router_contract_address="router_contract_address",
                    most_voted_transfers='{"transfers":[]}',
                ),
            )
        )

        amount_base_sent = 0
        amount_b_sent = 0
        amount_liquidity_received = 0

        self.fast_forward_to_state(
            behaviour=self.behaviour,
            state_id=ExitPoolTransactionHashBehaviour.state_id,
            period_state=period_state,
        )
        assert (
            cast(
                BaseState,
                cast(BaseState, self.behaviour.current_state),
            ).state_id
            == ExitPoolTransactionHashBehaviour.state_id
        )
        self.behaviour.act_wrapper()

        # Add allowance for LP token to be spent by the router
        self.mock_contract_api_request(
            contract_id=str(UniswapV2ERC20Contract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=strategy["pair"]["token_LP"]["address"],
                kwargs=Kwargs(
                    dict(
                        method_name="approve",
                        # sender=period_state.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        spender=period_state.router_contract_address,
                        value=strategy["pair"]["token_LP"]["set_allowance"],
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
                contract_address=period_state.router_contract_address,
                kwargs=Kwargs(
                    dict(
                        method_name="remove_liquidity_ETH",
                        # sender=period_state.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        token=strategy["pair"]["token_b"]["address"],
                        liquidity=amount_liquidity_received,
                        amount_token_min=int(amount_b_sent),
                        amount_ETH_min=int(amount_base_sent),
                        to=period_state.safe_contract_address,
                        deadline=CURRENT_BLOCK_TIMESTAMP + 300,
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
                contract_address=strategy["pair"]["token_LP"]["address"],
                kwargs=Kwargs(
                    dict(
                        method_name="approve",
                        # sender=period_state.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        spender=period_state.router_contract_address,
                        value=strategy["pair"]["token_LP"]["remove_allowance"],
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
                contract_address=period_state.safe_contract_address,
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
                contract_address=period_state.safe_contract_address,
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_raw_safe_transaction_hash",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"tx_hash": b"dummy_tx".hex()},  # type: ignore
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
        period_state = PeriodState(
            StateDB(
                initial_period=0,
                initial_data=dict(
                    most_voted_tx_hash="0x",
                    safe_contract_address="safe_contract_address",
                    most_voted_keeper_address="most_voted_keeper_address",
                    most_voted_strategy=strategy,
                    multisend_contract_address="multisend_contract_address",
                    router_contract_address="router_contract_address",
                    most_voted_transfers='{"transfers":[]}',
                ),
            )
        )

        amount_a_sent = 0
        amount_b_sent = 0
        amount_liquidity_received = 0

        self.fast_forward_to_state(
            behaviour=self.behaviour,
            state_id=ExitPoolTransactionHashBehaviour.state_id,
            period_state=period_state,
        )
        assert (
            cast(
                BaseState,
                cast(BaseState, self.behaviour.current_state),
            ).state_id
            == ExitPoolTransactionHashBehaviour.state_id
        )
        self.behaviour.act_wrapper()

        # Add allowance for LP token to be spent by the router
        self.mock_contract_api_request(
            contract_id=str(UniswapV2ERC20Contract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=strategy["pair"]["token_LP"]["address"],
                kwargs=Kwargs(
                    dict(
                        method_name="approve",
                        # sender=period_state.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        spender=period_state.router_contract_address,
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
                contract_address=period_state.router_contract_address,
                kwargs=Kwargs(
                    dict(
                        method_name="remove_liquidity",
                        # sender=period_state.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        token_a=strategy["pair"]["token_a"]["address"],
                        token_b=strategy["pair"]["token_b"]["address"],
                        liquidity=amount_liquidity_received,
                        amount_a_min=int(amount_a_sent),
                        amount_b_min=int(amount_b_sent),
                        to=period_state.safe_contract_address,
                        deadline=CURRENT_BLOCK_TIMESTAMP + 300,
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
                contract_address=strategy["pair"]["token_LP"]["address"],
                kwargs=Kwargs(
                    dict(
                        method_name="approve",
                        # sender=period_state.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        spender=period_state.router_contract_address,
                        value=strategy["pair"]["token_LP"]["remove_allowance"],
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
                contract_address=period_state.safe_contract_address,
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
                contract_address=period_state.safe_contract_address,
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_raw_safe_transaction_hash",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"tx_hash": b"dummy_tx".hex()},  # type: ignore
                ),
            ),
        )

        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round(Event.DONE)


class TestSwapBackTransactionHashBehaviour(LiquidityProvisionBehaviourBaseCase):
    """Test SwapBackTransactionHashBehaviour."""

    def test_transaction_hash(
        self,
    ) -> None:
        """Test tx hash behaviour."""

        strategy = get_default_strategy(
            is_base_native=False, is_a_native=True, is_b_native=False
        )
        period_state = PeriodState(
            StateDB(
                initial_period=0,
                initial_data=dict(
                    most_voted_tx_hash="0x",
                    safe_contract_address="safe_contract_address",
                    most_voted_keeper_address="most_voted_keeper_address",
                    most_voted_strategy=strategy,
                    multisend_contract_address="multisend_contract_address",
                    router_contract_address="router_contract_address",
                    most_voted_transfers='{"transfers":[]}',
                ),
            )
        )
        self.fast_forward_to_state(
            behaviour=self.behaviour,
            state_id=SwapBackTransactionHashBehaviour.state_id,
            period_state=period_state,
        )
        assert (
            cast(
                BaseState,
                cast(BaseState, self.behaviour.current_state),
            ).state_id
            == SwapBackTransactionHashBehaviour.state_id
        )
        self.behaviour.act_wrapper()

        # Swap first token back
        self.mock_contract_api_request(
            contract_id=str(UniswapV2Router02Contract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=period_state.router_contract_address,
                kwargs=Kwargs(
                    dict(
                        method_name="swap_exact_ETH_for_tokens",
                        # sender=period_state.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        amount_out_min=int(
                            strategy["base"]["amount_min_after_swap_back_a"]
                        ),
                        path=[
                            strategy["pair"]["token_a"]["address"],
                            strategy["base"]["address"],
                        ],
                        to=period_state.safe_contract_address,
                        deadline=CURRENT_BLOCK_TIMESTAMP + 300,
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
                contract_address=period_state.router_contract_address,
                kwargs=Kwargs(
                    dict(
                        method_name="swap_exact_tokens_for_tokens",
                        # sender=period_state.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        amount_in=int(
                            amount_b_received,
                        ),
                        amount_out_min=int(
                            strategy["base"]["amount_min_after_swap_back_b"]
                        ),
                        path=[
                            strategy["pair"]["token_b"]["address"],
                            strategy["base"]["address"],
                        ],
                        to=period_state.safe_contract_address,
                        deadline=CURRENT_BLOCK_TIMESTAMP + 300,
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
                contract_address=strategy["base"]["address"],
                kwargs=Kwargs(
                    dict(
                        method_name="approve",
                        # sender=period_state.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        spender=period_state.router_contract_address,
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
                contract_address=strategy["pair"]["token_b"]["address"],
                kwargs=Kwargs(
                    dict(
                        method_name="approve",
                        # sender=period_state.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        spender=period_state.router_contract_address,
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
                contract_address=period_state.safe_contract_address,
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
                contract_address=period_state.safe_contract_address,
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_raw_safe_transaction_hash",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"tx_hash": b"dummy_tx".hex()},  # type: ignore
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
        period_state = PeriodState(
            StateDB(
                initial_period=0,
                initial_data=dict(
                    most_voted_tx_hash="0x",
                    safe_contract_address="safe_contract_address",
                    most_voted_keeper_address="most_voted_keeper_address",
                    most_voted_strategy=strategy,
                    multisend_contract_address="multisend_contract_address",
                    router_contract_address="router_contract_address",
                    most_voted_transfers='{"transfers":[]}',
                ),
            )
        )
        self.fast_forward_to_state(
            behaviour=self.behaviour,
            state_id=SwapBackTransactionHashBehaviour.state_id,
            period_state=period_state,
        )
        assert (
            cast(
                BaseState,
                cast(BaseState, self.behaviour.current_state),
            ).state_id
            == SwapBackTransactionHashBehaviour.state_id
        )
        self.behaviour.act_wrapper()

        # Swap first token back
        amount_a_received = 0
        self.mock_contract_api_request(
            contract_id=str(UniswapV2Router02Contract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=period_state.router_contract_address,
                kwargs=Kwargs(
                    dict(
                        method_name="swap_exact_tokens_for_tokens",
                        # sender=period_state.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        amount_in=int(amount_a_received),
                        amount_out_min=int(
                            strategy["base"]["amount_min_after_swap_back_a"]
                        ),
                        path=[
                            strategy["pair"]["token_a"]["address"],
                            strategy["base"]["address"],
                        ],
                        to=period_state.safe_contract_address,
                        deadline=CURRENT_BLOCK_TIMESTAMP + 300,
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
                contract_address=period_state.router_contract_address,
                kwargs=Kwargs(
                    dict(
                        method_name="swap_exact_tokens_for_tokens",
                        # sender=period_state.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        amount_in=int(amount_b_received),
                        amount_out_min=int(
                            strategy["base"]["amount_min_after_swap_back_b"]
                        ),
                        path=[
                            strategy["pair"]["token_b"]["address"],
                            strategy["base"]["address"],
                        ],
                        to=period_state.safe_contract_address,
                        deadline=CURRENT_BLOCK_TIMESTAMP + 300,
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
                contract_address=strategy["base"]["address"],
                kwargs=Kwargs(
                    dict(
                        method_name="approve",
                        # sender=period_state.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        spender=period_state.router_contract_address,
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
                contract_address=strategy["pair"]["token_a"]["address"],
                kwargs=Kwargs(
                    dict(
                        method_name="approve",
                        # sender=period_state.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        spender=period_state.router_contract_address,
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
                contract_address=strategy["pair"]["token_b"]["address"],
                kwargs=Kwargs(
                    dict(
                        method_name="approve",
                        # sender=period_state.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        spender=period_state.router_contract_address,
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
                contract_address=period_state.safe_contract_address,
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
                contract_address=period_state.safe_contract_address,
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_raw_safe_transaction_hash",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"tx_hash": b"dummy_tx".hex()},  # type: ignore
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
