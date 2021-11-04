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

"""This module contains the data classes for the liquidity provision ABCI application."""
from abc import ABC
from enum import Enum
from types import MappingProxyType
from typing import AbstractSet, Dict, Mapping, Optional, Tuple, Type, cast

from aea.exceptions import enforce

from packages.valory.skills.abstract_round_abci.base import (
    AbciApp,
    AbciAppTransitionFunction,
    AbstractRound,
    BasePeriodState,
)
from packages.valory.skills.liquidity_provision.payloads import (
    StrategyEvaluationPayload,
    StrategyType,
)
from packages.valory.skills.price_estimation_abci.payloads import TransactionType
from packages.valory.skills.price_estimation_abci.rounds import (
    CollectDifferentUntilAllRound,
    CollectSameUntilThresholdRound,
    ConsensusReachedRound,
    DeploySafeRound,
    RandomnessRound,
    RegistrationRound,
)
from packages.valory.skills.price_estimation_abci.rounds import (
    ValidateSafeRound as DeploySafeValidationRound,
)


class Event(Enum):
    """Event enumeration for the liquidity provision demo."""

    DONE = "done"
    EXIT = "exit"
    ROUND_TIMEOUT = "round_timeout"
    NO_MAJORITY = "no_majority"
    WAIT = "wait"
    NO_ALLOWANCE = "no_allowance"


class PeriodState(BasePeriodState):  # pylint: disable=too-many-instance-attributes
    """
    Class to represent a period state.

    This state is replicated by the tendermint application.
    """

    def __init__(  # pylint: disable=too-many-arguments,too-many-locals
        self,
        participants: Optional[AbstractSet[str]] = None,
        participant_to_strategy: Optional[
            Mapping[str, StrategyEvaluationPayload]
        ] = None,
        most_voted_strategy: Optional[dict] = None,
    ) -> None:
        """Initialize a period state."""
        super().__init__(participants=participants)
        self._participant_to_strategy = participant_to_strategy
        self._most_voted_strategy = most_voted_strategy

    @property
    def most_voted_strategy(self) -> dict:
        """Get the most_voted_strategy."""
        enforce(
            self._most_voted_strategy is not None,
            "'most_voted_strategy' field is None",
        )
        return cast(dict, self._most_voted_strategy)

    def reset(self) -> "PeriodState":
        """Return the initial period state."""
        return PeriodState(self.participants)


class LiquidityProvisionAbstractRound(AbstractRound[Event, TransactionType], ABC):
    """Abstract round for the liquidity provision skill."""

    @property
    def period_state(self) -> PeriodState:
        """Return the period state."""
        return cast(PeriodState, self._state)

    def _return_no_majority_event(self) -> Tuple[PeriodState, Event]:
        """
        Trigger the NO_MAJORITY event.

        :return: a new period state and a NO_MAJORITY event
        """
        return self.period_state.reset(), Event.NO_MAJORITY


class SelectKeeperMainRound(
    CollectDifferentUntilAllRound, LiquidityProvisionAbstractRound
):
    """This class represents the select keeper main round."""

    round_id = "select_keeper_main"


class DeploySelectKeeperRound(
    CollectSameUntilThresholdRound, LiquidityProvisionAbstractRound
):
    """This class represents the select keeper deploy round."""

    round_id = "select_keeper_deploy"


class StrategyEvaluationRound(
    CollectSameUntilThresholdRound, LiquidityProvisionAbstractRound
):
    """This class represents the strategy evaluation round.

    Input: a set of participants (addresses)
    Output: a set of participants (addresses) and the strategy

    It schedules the WaitRound or the SwapRound.
    """

    round_id = "strategy_evaluation"
    allowed_tx_type = StrategyEvaluationPayload.transaction_type
    payload_attribute = "strategy"

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            state = self.period_state.update(
                participant_to_strategy=MappingProxyType(self.collection),
                most_voted_strategy=self.most_voted_payload,
            )
            event = (
                Event.DONE
                if self.period_state.most_voted_strategy["action"] == StrategyType.GO
                else Event.WAIT
            )
            return state, event
        if not self.is_majority_possible(
            self.collection, self.period_state.nb_participants
        ):
            return self._return_no_majority_event()
        return None


class WaitRound(LiquidityProvisionAbstractRound):
    """This class represents the wait round."""


class SwapSelectKeeperRound(
    CollectSameUntilThresholdRound, LiquidityProvisionAbstractRound
):
    """This class represents the swap select keeper round."""

    round_id = "swap_select_keeper"


class SwapTransactionHashRound(LiquidityProvisionAbstractRound):
    """This class represents the swap transaction hash round."""


class SwapSignatureRound(LiquidityProvisionAbstractRound):
    """This class represents the swap signature round."""


class SwapSendRound(LiquidityProvisionAbstractRound):
    """This class represents the swap send round."""


class SwapValidationRound(LiquidityProvisionAbstractRound):
    """This class represents the swap validation round."""


class AllowanceCheckRound(LiquidityProvisionAbstractRound):
    """This class represents the AllowanceCheck round."""


class AddAllowanceSelectKeeperRound(
    CollectSameUntilThresholdRound, LiquidityProvisionAbstractRound
):
    """This class represents the AddAllowance select keeper round."""

    round_id = "add_allowance_select_keeper"


class AddAllowanceTransactionHashRound(LiquidityProvisionAbstractRound):
    """This class represents the AddAllowance transaction hash round."""


class AddAllowanceSignatureRound(LiquidityProvisionAbstractRound):
    """This class represents the AddAllowance signature round."""


class AddAllowanceSendRound(LiquidityProvisionAbstractRound):
    """This class represents the AddAllowance send round."""


class AddAllowanceValidationRound(LiquidityProvisionAbstractRound):
    """This class represents the AddAllowance validation round."""


class AddLiquiditySelectKeeperRound(
    CollectSameUntilThresholdRound, LiquidityProvisionAbstractRound
):
    """This class represents the AddLiquidity select keeper round."""

    round_id = "add_allowance_select_keeper"


class AddLiquidityTransactionHashRound(LiquidityProvisionAbstractRound):
    """This class represents the AddLiquidity transaction hash round."""


class AddLiquiditySignatureRound(LiquidityProvisionAbstractRound):
    """This class represents the AddLiquidity signature round."""


class AddLiquiditySendRound(LiquidityProvisionAbstractRound):
    """This class represents the AddLiquidity send round."""


class AddLiquidityValidationRound(LiquidityProvisionAbstractRound):
    """This class represents the AddLiquidity validation round."""


class RemoveLiquiditySelectKeeperRound(
    CollectSameUntilThresholdRound, LiquidityProvisionAbstractRound
):
    """This class represents the RemoveLiquidity select keeper round."""

    round_id = "add_allowance_select_keeper"


class RemoveLiquidityTransactionHashRound(LiquidityProvisionAbstractRound):
    """This class represents the RemoveLiquidity transaction hash round."""


class RemoveLiquiditySignatureRound(LiquidityProvisionAbstractRound):
    """This class represents the RemoveLiquidity signature round."""


class RemoveLiquiditySendRound(LiquidityProvisionAbstractRound):
    """This class represents the RemoveLiquidity send round."""


class RemoveLiquidityValidationRound(LiquidityProvisionAbstractRound):
    """This class represents the RemoveLiquidity validation round."""


class RemoveAllowanceSelectKeeperRound(
    CollectSameUntilThresholdRound, LiquidityProvisionAbstractRound
):
    """This class represents the RemoveAllowance select keeper round."""

    round_id = "add_allowance_select_keeper"


class RemoveAllowanceTransactionHashRound(LiquidityProvisionAbstractRound):
    """This class represents the RemoveAllowance transaction hash round."""


class RemoveAllowanceSignatureRound(LiquidityProvisionAbstractRound):
    """This class represents the RemoveAllowance signature round."""


class RemoveAllowanceSendRound(LiquidityProvisionAbstractRound):
    """This class represents the RemoveAllowance send round."""


class RemoveAllowanceValidationRound(LiquidityProvisionAbstractRound):
    """This class represents the RemoveAllowance validation round."""


class SwapBackSelectKeeperRound(
    CollectSameUntilThresholdRound, LiquidityProvisionAbstractRound
):
    """This class represents the SwapBack select keeper round."""

    round_id = "add_allowance_select_keeper"


class SwapBackTransactionHashRound(LiquidityProvisionAbstractRound):
    """This class represents the SwapBack transaction hash round."""


class SwapBackSignatureRound(LiquidityProvisionAbstractRound):
    """This class represents the SwapBack signature round."""


class SwapBackSendRound(LiquidityProvisionAbstractRound):
    """This class represents the SwapBack send round."""


class SwapBackValidationRound(LiquidityProvisionAbstractRound):
    """This class represents the SwapBack validation round."""


class LiquidityProvisionAbciApp(AbciApp[Event]):
    """Liquidity Provision ABCI application."""

    initial_round_cls: Type[AbstractRound] = RegistrationRound
    transition_function: AbciAppTransitionFunction = {
        RegistrationRound: {Event.DONE: RandomnessRound},
        RandomnessRound: {
            Event.DONE: SelectKeeperMainRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
        SelectKeeperMainRound: {
            Event.DONE: DeploySafeRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
        DeploySafeRound: {
            Event.DONE: DeploySafeValidationRound,
            Event.EXIT: DeploySelectKeeperRound,
        },
        DeploySelectKeeperRound: {
            Event.DONE: DeploySafeRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
        DeploySafeValidationRound: {
            Event.DONE: StrategyEvaluationRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
        StrategyEvaluationRound: {
            Event.DONE: SwapTransactionHashRound,
            Event.WAIT: WaitRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
        WaitRound: {
            Event.DONE: StrategyEvaluationRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
        SwapSelectKeeperRound: {
            Event.DONE: SwapTransactionHashRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
        SwapTransactionHashRound: {
            Event.DONE: SwapSignatureRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
            Event.EXIT: SwapSelectKeeperRound,
        },
        SwapSignatureRound: {
            Event.DONE: SwapSendRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
            Event.EXIT: SwapSelectKeeperRound,
        },
        SwapSendRound: {
            Event.DONE: SwapValidationRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
            Event.EXIT: SwapSelectKeeperRound,
        },
        SwapValidationRound: {
            Event.DONE: AllowanceCheckRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
        AllowanceCheckRound: {
            Event.NO_ALLOWANCE: AddAllowanceTransactionHashRound,
            Event.DONE: AddLiquidityTransactionHashRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
        AddAllowanceSelectKeeperRound: {
            Event.DONE: AddAllowanceTransactionHashRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
        AddAllowanceTransactionHashRound: {
            Event.DONE: AddAllowanceSignatureRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
            Event.EXIT: AddAllowanceSelectKeeperRound,
        },
        AddAllowanceSignatureRound: {
            Event.DONE: AddAllowanceSendRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
            Event.EXIT: AddAllowanceSelectKeeperRound,
        },
        AddAllowanceSendRound: {
            Event.DONE: AddAllowanceValidationRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
            Event.EXIT: AddAllowanceSelectKeeperRound,
        },
        AddAllowanceValidationRound: {
            Event.DONE: AddLiquidityTransactionHashRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
        AddLiquiditySelectKeeperRound: {
            Event.DONE: AddLiquidityTransactionHashRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
        AddLiquidityTransactionHashRound: {
            Event.DONE: AddLiquiditySignatureRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
            Event.EXIT: AddLiquiditySelectKeeperRound,
        },
        AddLiquiditySignatureRound: {
            Event.DONE: AddLiquiditySendRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
            Event.EXIT: AddLiquiditySelectKeeperRound,
        },
        AddLiquiditySendRound: {
            Event.DONE: AddLiquidityValidationRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
            Event.EXIT: AddLiquiditySelectKeeperRound,
        },
        AddLiquidityValidationRound: {
            Event.DONE: RemoveLiquidityTransactionHashRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
        RemoveLiquiditySelectKeeperRound: {
            Event.DONE: RemoveLiquidityTransactionHashRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
        RemoveLiquidityTransactionHashRound: {
            Event.DONE: RemoveLiquiditySignatureRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
            Event.EXIT: RemoveLiquiditySelectKeeperRound,
        },
        RemoveLiquiditySignatureRound: {
            Event.DONE: RemoveLiquiditySendRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
            Event.EXIT: RemoveLiquiditySelectKeeperRound,
        },
        RemoveLiquiditySendRound: {
            Event.DONE: RemoveLiquidityValidationRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
            Event.EXIT: RemoveLiquiditySelectKeeperRound,
        },
        RemoveLiquidityValidationRound: {
            Event.DONE: RemoveAllowanceTransactionHashRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
        RemoveAllowanceSelectKeeperRound: {
            Event.DONE: RemoveAllowanceTransactionHashRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
        RemoveAllowanceTransactionHashRound: {
            Event.DONE: RemoveAllowanceSignatureRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
            Event.EXIT: RemoveAllowanceSelectKeeperRound,
        },
        RemoveAllowanceSignatureRound: {
            Event.DONE: RemoveAllowanceSendRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
            Event.EXIT: RemoveAllowanceSelectKeeperRound,
        },
        RemoveAllowanceSendRound: {
            Event.DONE: RemoveAllowanceValidationRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
            Event.EXIT: RemoveAllowanceSelectKeeperRound,
        },
        RemoveAllowanceValidationRound: {
            Event.DONE: SwapBackTransactionHashRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
        SwapBackSelectKeeperRound: {
            Event.DONE: SwapBackTransactionHashRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
        SwapBackTransactionHashRound: {
            Event.DONE: SwapBackSignatureRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
            Event.EXIT: SwapBackSelectKeeperRound,
        },
        SwapBackSignatureRound: {
            Event.DONE: SwapBackSendRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
            Event.EXIT: SwapBackSelectKeeperRound,
        },
        SwapBackSendRound: {
            Event.DONE: SwapBackValidationRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
            Event.EXIT: SwapBackSelectKeeperRound,
        },
        SwapBackValidationRound: {
            Event.DONE: ConsensusReachedRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
    }
    event_to_timeout: Dict[Event, float] = {
        Event.EXIT: 5.0,
        Event.ROUND_TIMEOUT: 30.0,
    }
