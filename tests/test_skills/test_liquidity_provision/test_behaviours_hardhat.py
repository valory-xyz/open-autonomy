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
"""Tests for valory/liquidity_provision skill behaviours with Hardhat."""
import time
from typing import Dict, cast

from packages.valory.contracts.uniswap_v2_router_02.contract import (
    UniswapV2Router02Contract,
)
from packages.valory.protocols.contract_api.message import ContractApiMessage
from packages.valory.skills.abstract_round_abci.behaviour_utils import BaseState
from packages.valory.skills.liquidity_provision.behaviours import (
    EnterPoolTransactionHashBehaviour,
)
from packages.valory.skills.liquidity_provision.payloads import StrategyType
from packages.valory.skills.liquidity_provision.rounds import PeriodState

from tests.fixture_helpers import HardHatAMMBaseTest
from tests.test_skills.test_liquidity_provision.test_behaviours import (
    LiquidityProvisionBehaviourBaseCase,
)


DEFAULT_GAS = 1000000
DEFAULT_GAS_PRICE = 1000000


def get_default_strategy(is_native: bool = True) -> Dict:
    """Returns default strategy."""
    return {
        "action": StrategyType.GO.value,
        "chain": "Fantom",
        "base": {"address": "0xUSDT_ADDRESS", "balance": 100},
        "pair": {
            "token_a": {
                "ticker": "FTM",
                "address": "0xFTM_ADDRESS",
                "amount": 1,
                "amount_min": 1,
                # If any, only token_a can be the native one (ETH, FTM...)
                "is_native": is_native,
            },
            "token_b": {
                "ticker": "BOO",
                "address": "0xBOO_ADDRESS",
                "amount": 1,
                "amount_min": 1,
            },
        },
        "router_address": "router_address",
        "liquidity_to_remove": 1,
    }


class TestEnterPoolTransactionHashBehaviourHardhat(
    LiquidityProvisionBehaviourBaseCase, HardHatAMMBaseTest
):
    """Test liquidity pool behaviours in a Hardhat environment."""

    def test_swap(self):
        """Test a swap tx: WETH for token A."""

        strategy = get_default_strategy()
        period_state = PeriodState(
            most_voted_tx_hash="0x",
            safe_contract_address="safe_contract_address",
            most_voted_keeper_address="most_voted_keeper_address",
            most_voted_strategy=strategy,
            multisend_contract_address="multisend_contract_address",
        )
        self.fast_forward_to_state(
            behaviour=self.liquidity_provision_behaviour,
            state_id=EnterPoolTransactionHashBehaviour.state_id,
            period_state=period_state,
        )
        assert (
            cast(
                BaseState,
                cast(BaseState, self.liquidity_provision_behaviour.current_state),
            ).state_id
            == EnterPoolTransactionHashBehaviour.state_id
        )
        self.liquidity_provision_behaviour.act_wrapper()

        amount_in = 10
        amount_out_min = 1

        contract_address = "0xCf7Ed3AccA5a467e9e704C703E8D87F634fB0Fc9"
        weth_address = "0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512"
        tokenA_address = "0xDc64a140Aa3E981100a9becA4E685f962f0cF6C9"
        account_1_address = "0xBcd4042DE499D14e55001CcbB24a551F3b954096"

        contract_api_msg = yield from self.liquidity_provision_behaviour.current_state.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
            contract_address=contract_address,
            contract_id=str(UniswapV2Router02Contract.contract_id),
            contract_callable="swap_exact_tokens_for_tokens",
            amount_in=amount_in,
            amount_out_min=amount_out_min,
            path=[
                weth_address,
                tokenA_address,
            ],
            to=account_1_address,
            deadline=int(time.time()) + 300,  # 5 min into the future
        )

        # Send the tx
        tx_hash = yield from self.liquidity_provision_behaviour.current_state.send_raw_transaction(
            contract_api_msg.raw_transaction
        )

        # Verify the tx
        assert tx_hash is not None
