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

"""This module contains the rounds for the APY estimation ABCI application."""
from abc import ABC
from enum import Enum
from types import MappingProxyType
from typing import AbstractSet, Dict, Mapping, Optional, Tuple, Type, cast, Any, List

from aea.exceptions import enforce

from packages.valory.skills.abstract_round_abci.base import (
    AbciApp,
    AbciAppTransitionFunction,
    AbstractRound,
    BasePeriodState,
    EventType,
    TransactionType, CollectSameUntilThresholdRound,
)
from packages.valory.skills.apy_estimation.payloads import TransformationPayload, ResetPayload, FetchingPayload, \
    EstimatePayload
from packages.valory.skills.simple_abci.rounds import RegistrationRound


class Event(Enum):
    """Event enumeration for the APY estimation demo."""
    DONE = "done"
    ROUND_TIMEOUT = "round_timeout"
    NO_MAJORITY = "no_majority"
    RESET_TIMEOUT = "reset_timeout"
    FULLY_TRAINED = "fully_trained"


class PeriodState(BasePeriodState):
    """Class to represent a period state. This state is replicated by the tendermint application."""

    def __init__(  # pylint: disable=too-many-arguments,too-many-locals
        self,
        participants: Optional[AbstractSet[str]] = None,
        period_count: Optional[int] = None,
        period_setup_params: Optional[Dict] = None,
        participant_to_fetching: Optional[Mapping[str, FetchingPayload]] = None,
        most_voted_history: Optional[str] = None,
        participant_to_transformation: Optional[
            Mapping[str, TransformationPayload]
        ] = None,
        most_voted_transformation: Optional[str] = None,
        participant_to_estimate: Optional[Mapping[str, EstimatePayload]] = None,
        most_voted_estimate: Optional[List[float]] = None,
        best_params: Optional[Dict[str, Any]] = None,
        full_training: Optional[bool] = False,
        pair_name: Optional[str] = None
    ) -> None:
        """Initialize the state."""
        super().__init__(participants, period_count, period_setup_params)
        self. _participant_to_fetching = participant_to_fetching
        self._most_voted_history = most_voted_history
        self._participant_to_transformation = participant_to_transformation
        self._most_voted_transformation = most_voted_transformation
        self._participant_to_estimate = participant_to_estimate
        self._most_voted_estimate = most_voted_estimate
        self._best_params = best_params
        self._full_training = full_training
        self._pair_name = pair_name

    @property
    def participant_to_fetching(self) -> Mapping[str, FetchingPayload]:
        """Get the participant_to_fetching."""
        enforce(
            self._participant_to_fetching is not None,
            "'participant_to_fetching' field is None",
        )
        return self._participant_to_fetching

    @property
    def most_voted_history(self) -> str:
        """Get the most_voted_history."""
        enforce(
            self._most_voted_history is not None,
            "'most_voted_history' field is None",
        )
        return self._most_voted_history

    @property
    def participant_to_transformation(self) -> Mapping[str, TransformationPayload]:
        """Get the participant_to_transformation."""
        enforce(
            self._participant_to_transformation is not None,
            "'participant_to_transformation' field is None",
        )
        return self._participant_to_transformation

    @property
    def most_voted_transformation(self) -> str:
        """Get the most_voted_transformation."""
        enforce(
            self._most_voted_transformation is not None,
            "'most_voted_transformation' field is None",
        )
        return self._most_voted_transformation

    @property
    def participant_to_estimate(self) -> Mapping[str, EstimatePayload]:
        """Get the participant_to_estimate."""
        enforce(
            self._participant_to_estimate is not None,
            "'participant_to_estimate' field is None",
        )
        return self._participant_to_estimate

    @property
    def most_voted_estimate(self) -> Optional[List[float]]:
        """Get the most_voted_estimate."""
        enforce(
            self._most_voted_estimate is not None,
            "'most_voted_estimate' field is None",
        )
        return self._most_voted_estimate

    @property
    def best_params(self) -> Dict[str, Any]:
        """Get the best_params."""
        enforce(
            self._best_params is not None,
            "'best_params' field is None",
        )
        return self._best_params

    @property
    def full_training(self) -> bool:
        """Get the full_training flag."""
        return self._full_training

    @property
    def pair_name(self) -> str:
        """Get the pair_name."""
        enforce(
            self._pair_name is not None,
            "'pair_name' field is None",
        )
        return self._pair_name


class APYEstimationAbstractRound(AbstractRound[Event, TransactionType], ABC):
    """Abstract round for the APY estimation skill."""

    @property
    def period_state(self) -> PeriodState:
        """Return the period state."""
        return cast(PeriodState, self._state)

    def _return_no_majority_event(self) -> Tuple[PeriodState, Event]:
        """
        Trigger the NO_MAJORITY event.

        :return: a new period state and a NO_MAJORITY event
        """
        return self.period_state, Event.NO_MAJORITY


class CollectHistoryRound(
    CollectSameUntilThresholdRound, APYEstimationAbstractRound
):
    """
    This class represents the 'collect-history' round.

    Input: a period state with the prior round data.
    Output: a new period state with the prior round data and the votes for the historical data.

    It schedules the TransformRound.
    """

    round_id = "collect_history"
    allowed_tx_type = FetchingPayload.transaction_type
    payload_attribute = "history"

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        state = event = None

        if self.threshold_reached:
            updated_state = self.period_state.update(
                participant_to_fetching=MappingProxyType(self.collection),
                most_voted_history=self.most_voted_payload,
            )
            state, event = updated_state, Event.DONE

        elif not self.is_majority_possible(
            self.collection, self.period_state.nb_participants
        ):
            state, event = self._return_no_majority_event()

        return state, event


class TransformRound(CollectSameUntilThresholdRound, APYEstimationAbstractRound):
    """
    This class represents the 'Transform' round.

    Input: a period state with the prior round data.
    Output: a new period state with the prior round data and the votes for the transformed data.

    It schedules the PreprocessRound.
    """

    def end_block(self) -> Optional[Tuple[BasePeriodState, EventType]]:
        """Process the end of the block."""
        raise NotImplementedError()


class PreprocessRound(CollectSameUntilThresholdRound, APYEstimationAbstractRound):
    """
    This class represents the 'Preprocess' round.

    Input: a period state with the prior round data.
    Output: a new period state with the prior round data and the votes for the preprocessed data.

    It schedules the Optimize.
    """

    def end_block(self) -> Optional[Tuple[BasePeriodState, EventType]]:
        """Process the end of the block."""
        raise NotImplementedError()


class OptimizeRound(CollectSameUntilThresholdRound, APYEstimationAbstractRound):
    """
    This class represents the 'Optimize' round.

    Input: a period state with the prior round data.
    Output: a new period state with the prior round data and the votes for the hyperparameters.

    It schedules the TrainRound.
    """

    def end_block(self) -> Optional[Tuple[BasePeriodState, EventType]]:
        """Process the end of the block."""
        raise NotImplementedError()


class TrainRound(CollectSameUntilThresholdRound, APYEstimationAbstractRound):
    """
    This class represents the 'Train' round.

    Input: a period state with the prior round data.
    Output: a new period state with the prior round data and the votes for the model.

    It schedules the TestRound.
    """

    def end_block(self) -> Optional[Tuple[BasePeriodState, EventType]]:
        """Process the end of the block."""
        raise NotImplementedError()


class TestRound(CollectSameUntilThresholdRound, APYEstimationAbstractRound):
    """
    This class represents the 'Test' round.

    Input: a period state with the prior round data.
    Output: a new period state with the prior round data and the votes for the results.

    It schedules the EstimateConsensusRound.
    """

    def end_block(self) -> Optional[Tuple[BasePeriodState, EventType]]:
        """Process the end of the block."""
        # TODO full_training -> True
        raise NotImplementedError()


class EstimateRound(
    CollectSameUntilThresholdRound, APYEstimationAbstractRound
):
    """
    This class represents the 'estimate' round.

    Input: a period state with the prior round data.
    Output: a new period state with the prior round data and the votes for each estimate.

    It schedules the .
    """

    round_id = "estimate"
    allowed_tx_type = EstimatePayload.transaction_type
    payload_attribute = "estimate"

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            state = self.period_state.update(
                participant_to_estimate=MappingProxyType(self.collection),
                most_voted_estimate=self.most_voted_payload,
            )
            return state, Event.DONE
        if not self.is_majority_possible(
            self.collection, self.period_state.nb_participants
        ):
            return self._return_no_majority_event()
        return None


class ResetRound(CollectSameUntilThresholdRound, APYEstimationAbstractRound):
    """This class represents the base reset round."""

    round_id = "reset"
    allowed_tx_type = ResetPayload.transaction_type
    payload_attribute = "period_count"

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            state = self.period_state.update(
                period_count=self.most_voted_payload,
                participant_to_randomness=None,
                most_voted_randomness=None,
                participant_to_selection=None,
                most_voted_keeper_address=None,
                participant_to_votes=None,
                participant_to_fetching=None,
                participant_to_estimate=None,
                estimate=None,
                most_voted_estimate=None,
                participant_to_tx_hash=None,
                most_voted_tx_hash=None,
                participant_to_signature=None,
                final_tx_hash=None,
                transformation=None,
                participant_to_transformation=None,
                most_voted_history=None,
            )
            return state, Event.DONE
        if not self.is_majority_possible(
            self.collection, self.period_state.nb_participants
        ):
            return self._return_no_majority_event()
        return None


class APYEstimationAbciApp(AbciApp[Event]):  # pylint: disable=too-few-public-methods
    """APY estimation ABCI application."""

    initial_round_cls: Type[AbstractRound] = RegistrationRound
    transition_function: AbciAppTransitionFunction = {
        RegistrationRound: {
            Event.DONE: CollectHistoryRound,
        },
        CollectHistoryRound: {
            Event.DONE: TransformRound,
            Event.NO_MAJORITY: ResetRound,  # if there is no majority we reset the period
            Event.ROUND_TIMEOUT: ResetRound,  # if the round times out we reset the period
        },
        TransformRound: {
            Event.DONE: PreprocessRound,
            Event.NO_MAJORITY: ResetRound,  # if there is no majority we reset the period
            Event.ROUND_TIMEOUT: ResetRound,  # if the round times out we reset the period
        },
        PreprocessRound: {
            Event.DONE: OptimizeRound,
            Event.NO_MAJORITY: ResetRound,  # if there is no majority we reset the period
            Event.ROUND_TIMEOUT: ResetRound,  # if the round times out we reset the period
        },
        OptimizeRound: {
            Event.DONE: TrainRound,
            Event.NO_MAJORITY: ResetRound,  # if there is no majority we reset the period
            Event.ROUND_TIMEOUT: ResetRound,  # if the round times out we reset the period
        },
        TrainRound: {
            Event.FULLY_TRAINED: EstimateRound,
            Event.DONE: TestRound,
            Event.NO_MAJORITY: ResetRound,  # if there is no majority we reset the period
            Event.ROUND_TIMEOUT: ResetRound,  # if the round times out we reset the period
        },
        TestRound: {
            Event.DONE: TrainRound,
            Event.NO_MAJORITY: ResetRound,  # if there is no majority we reset the period
            Event.ROUND_TIMEOUT: ResetRound,  # if the round times out we reset the period
        },
        EstimateRound: {
            Event.DONE: ResetRound,
            Event.ROUND_TIMEOUT: ResetRound,  # if the round times out we reset the period
            Event.NO_MAJORITY: ResetRound,  # if there is no majority we reset the period
        },
        ResetRound: {
            Event.DONE: RegistrationRound,  # TODO change this to APY estimation when implemented.
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
    }
    event_to_timeout: Dict[Event, float] = {
        Event.ROUND_TIMEOUT: 30.0,
        Event.RESET_TIMEOUT: 30.0,
    }
