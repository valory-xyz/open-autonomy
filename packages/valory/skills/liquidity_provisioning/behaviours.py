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

"""This module contains the behaviours for the 'liquidity_provisioning' skill."""
from typing import Set, Type

from packages.valory.skills.abstract_round_abci.behaviours import AbstractRoundBehaviour
from packages.valory.skills.liquidity_provisioning.rounds import (
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


class LiquidityProvisionBaseState(PriceEstimationBaseState):
    """Base state behaviour for the liquidity provision skill."""

    pass


class StrategyEvaluationBehaviour(LiquidityProvisionBaseState):
    """Evaluate the financial strategy."""

    pass


class WaitBehaviour(LiquidityProvisionBaseState):
    """Wait until next strategy evaluation."""

    pass


class SwapBehaviour(LiquidityProvisionBaseState):
    """Swap tokens."""

    pass


class ValidateSwapBehaviour(LiquidityProvisionBaseState):
    """Validate the token swap tx."""

    pass


class AllowanceCheckBehaviour(LiquidityProvisionBaseState):
    """Check the current token allowance."""

    pass


class AddAllowanceBehaviour(LiquidityProvisionBaseState):
    """Increase the current allowance."""

    pass


class ValidateAddAllowanceBehaviour(LiquidityProvisionBaseState):
    """Validate the approve tx."""

    pass


class AddLiquidityBehaviour(LiquidityProvisionBaseState):
    """Enter a liquidity pool."""

    pass


class ValidateAddLiquidityBehaviour(LiquidityProvisionBaseState):
    """Validate the enter pool tx."""

    pass


class RemoveLiquidityBehaviour(LiquidityProvisionBaseState):
    """Leave a liquidity pool."""

    pass


class ValidateRemoveLiquidityBehaviour(LiquidityProvisionBaseState):
    """Validate the leave pool tx."""

    pass


class RemoveAllowanceBehaviour(LiquidityProvisionBaseState):
    """Remove the token's allowance."""

    pass


class ValidateRemoveAllowanceBehaviour(LiquidityProvisionBaseState):
    """Validate the approve tx."""

    pass


class SwapBackBehaviour(LiquidityProvisionBaseState):
    """Swap tokens back to the initial holdings."""

    pass


class ValidateSwapBackBehaviour(LiquidityProvisionBaseState):
    """Validate the swap tx."""

    pass


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
        StrategyEvaluationBehaviour,
        SwapBehaviour,  # type: ignore
        ValidateSwapBehaviour,  # type: ignore
        AllowanceCheckBehaviour,  # type: ignore
        AddAllowanceBehaviour,  # type: ignore
        ValidateAddAllowanceBehaviour,
        AddLiquidityBehaviour,  # type: ignore
        ValidateAddLiquidityBehaviour,
        RemoveLiquidityBehaviour,  # type: ignore
        ValidateRemoveLiquidityBehaviour,  # type: ignore
        RemoveAllowanceBehaviour,  # type: ignore
        ValidateRemoveAllowanceBehaviour,  # type: ignore
        SwapBackBehaviour,  # type: ignore
        ValidateSwapBackBehaviour,
        EndBehaviour,  # type: ignore
    }
