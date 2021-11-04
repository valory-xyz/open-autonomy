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

"""This module contains the behaviours for the 'liquidity_provision' skill."""
from typing import Generator, Set, Type

from packages.valory.skills.abstract_round_abci.behaviours import AbstractRoundBehaviour
from packages.valory.skills.abstract_round_abci.utils import BenchmarkTool
from packages.valory.skills.liquidity_provision.payloads import (
    StrategyEvaluationPayload,
    StrategyType,
)
from packages.valory.skills.liquidity_provision.rounds import (
    LiquidityProvisionAbciApp,
    SelectKeeperAddAllowanceRound,
    SelectKeeperAddLiquidityRound,
    SelectKeeperDeployRound,
    SelectKeeperMainRound,
    SelectKeeperRemoveAllowanceRound,
    SelectKeeperRemoveLiquidityRound,
    SelectKeeperSwapBackRound,
    SelectKeeperSwapRound,
)
from packages.valory.skills.price_estimation_abci.behaviours import (
    DeploySafeBehaviour,
    EndBehaviour,
    PriceEstimationBaseState,
    RandomnessBehaviour,
    RegistrationBehaviour,
    SelectKeeperBehaviour,
    TendermintHealthcheckBehaviour,
    ValidateSafeBehaviour,
)


benchmark_tool = BenchmarkTool()


class LiquidityProvisionBaseState(PriceEstimationBaseState):
    """Base state behaviour for the liquidity provision skill."""


def get_strategy_update() -> dict:
    """Get a strategy update."""
    strategy = {
        "action": StrategyType.GO,
        "pair": ["FTM", "BOO"],
        "pool": "0x0000000000000000000000000000",
        "amountETH": 0.1,  # Be careful with floats and determinism here
    }
    return strategy


class StrategyEvaluationBehaviour(LiquidityProvisionBaseState):
    """Evaluate the financial strategy."""

    def async_act(self) -> Generator:
        """
        Do the action.

        Steps:
        - Select a keeper randomly.
        - Send the transaction with the keeper and wait for it to be mined.
        - Wait until ABCI application transitions to the next round.
        - Go to the next behaviour state (set done event).
        """

        with benchmark_tool.measure(
            self,
        ).local():

            strategy = get_strategy_update()
            payload = StrategyEvaluationPayload(self.context.agent_address, strategy)

            if strategy["action"] == StrategyType.WAIT:
                self.context.logger.info("Current strategy is still optimal. Waiting.")

            if strategy["action"] == StrategyType.GO:
                self.context.logger.info(
                    f"Performing strategy update: moving {strategy['amountETH']} into "
                    "{strategy['pair'][0]}-{strategy['pair'][1]} (pool {strategy['pool']})"
                )

        with benchmark_tool.measure(
            self,
        ).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class WaitBehaviour(LiquidityProvisionBaseState):
    """Wait until next strategy evaluation."""


class SwapBehaviour(LiquidityProvisionBaseState):
    """Swap tokens."""


class ValidateSwapBehaviour(LiquidityProvisionBaseState):
    """Validate the token swap tx."""


class AllowanceCheckBehaviour(LiquidityProvisionBaseState):
    """Check the current token allowance."""


class AddAllowanceBehaviour(LiquidityProvisionBaseState):
    """Increase the current allowance."""


class ValidateAddAllowanceBehaviour(LiquidityProvisionBaseState):
    """Validate the approve tx."""


class AddLiquidityBehaviour(LiquidityProvisionBaseState):
    """Enter a liquidity pool."""


class ValidateAddLiquidityBehaviour(LiquidityProvisionBaseState):
    """Validate the enter pool tx."""


class RemoveLiquidityBehaviour(LiquidityProvisionBaseState):
    """Leave a liquidity pool."""


class ValidateRemoveLiquidityBehaviour(LiquidityProvisionBaseState):
    """Validate the leave pool tx."""


class RemoveAllowanceBehaviour(LiquidityProvisionBaseState):
    """Remove the token's allowance."""


class ValidateRemoveAllowanceBehaviour(LiquidityProvisionBaseState):
    """Validate the approve tx."""


class SwapBackBehaviour(LiquidityProvisionBaseState):
    """Swap tokens back to the initial holdings."""


class ValidateSwapBackBehaviour(LiquidityProvisionBaseState):
    """Validate the swap tx."""


class SelectKeeperMainBehaviour(SelectKeeperBehaviour):
    """Select the keeper agent."""

    state_id = "select_keeper_main"
    matching_round = SelectKeeperMainRound


class SelectKeeperDeployBehaviour(SelectKeeperBehaviour):
    """Select the keeper agent."""

    state_id = "select_keeper_deploy"
    matching_round = SelectKeeperDeployRound


class SelectKeeperSwapBehaviour(SelectKeeperBehaviour):
    """Select the keeper agent."""

    state_id = "select_keeper_swap"
    matching_round = SelectKeeperSwapRound


class SelectKeeperAddAllowanceBehaviour(SelectKeeperBehaviour):
    """Select the keeper agent."""

    state_id = "select_keeper_approve"
    matching_round = SelectKeeperAddAllowanceRound


class SelectKeeperAddLiquidityBehaviour(SelectKeeperBehaviour):
    """Select the keeper agent."""

    state_id = "select_keeper_add_liquidity"
    matching_round = SelectKeeperAddLiquidityRound


class SelectKeeperRemoveLiquidityBehaviour(SelectKeeperBehaviour):
    """Select the keeper agent."""

    state_id = "select_keeper_remove_liquidity"
    matching_round = SelectKeeperRemoveLiquidityRound


class SelectKeeperRemoveAllowanceBehaviour(SelectKeeperBehaviour):
    """Select the keeper agent."""

    state_id = "select_keeper_remove_allowance"
    matching_round = SelectKeeperRemoveAllowanceRound


class SelectKeeperSwapBackBehaviour(SelectKeeperBehaviour):
    """Select the keeper agent."""

    state_id = "select_keeper_swap_back"
    matching_round = SelectKeeperSwapBackRound


class LiquidityProvisionConsensusBehaviour(AbstractRoundBehaviour):
    """This behaviour manages the consensus stages for the price estimation."""

    initial_state_cls = TendermintHealthcheckBehaviour
    abci_app_cls: LiquidityProvisionAbciApp  # type: ignore
    behaviour_states: Set[Type[PriceEstimationBaseState]] = {  # type: ignore
        TendermintHealthcheckBehaviour,  # type: ignore
        RegistrationBehaviour,  # type: ignore
        RandomnessBehaviour,  # type: ignore
        SelectKeeperMainBehaviour,  # type: ignore
        DeploySafeBehaviour,  # type: ignore
        ValidateSafeBehaviour,  # type: ignore
        StrategyEvaluationBehaviour,  # type: ignore
        SwapBehaviour,  # type: ignore
        ValidateSwapBehaviour,  # type: ignore
        AllowanceCheckBehaviour,  # type: ignore
        AddAllowanceBehaviour,  # type: ignore
        ValidateAddAllowanceBehaviour,  # type: ignore
        AddLiquidityBehaviour,  # type: ignore
        ValidateAddLiquidityBehaviour,  # type: ignore
        RemoveLiquidityBehaviour,  # type: ignore
        ValidateRemoveLiquidityBehaviour,  # type: ignore
        RemoveAllowanceBehaviour,  # type: ignore
        ValidateRemoveAllowanceBehaviour,  # type: ignore
        SwapBackBehaviour,  # type: ignore
        ValidateSwapBackBehaviour,  # type: ignore
        EndBehaviour,  # type: ignore
    }
