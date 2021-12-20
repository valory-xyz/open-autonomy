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

"""This module contains the data classes for the price estimation ABCI application."""
from types import MappingProxyType
from typing import Dict, Optional, Set, Tuple, Type

from packages.valory.skills.abstract_round_abci.abci_app_chain import (
    AbciAppTransitionMapping,
    chain,
)
from packages.valory.skills.abstract_round_abci.base import (
    AbciApp,
    AbciAppTransitionFunction,
    AbstractRound,
    AppState,
    BasePeriodState,
    CollectDifferentUntilThresholdRound,
    CollectSameUntilThresholdRound,
)
from packages.valory.skills.common_apps.payloads import (
    EstimatePayload,
    ObservationPayload,
    TransactionHashPayload,
)
from packages.valory.skills.common_apps.rounds import (
    AgentRegistrationAbciApp,
    CommonAppsAbstractRound,
    Event,
    FailedRound,
    FinishedARound,
    FinishedBRound,
    FinishedCRound,
    FinishedDRound,
    FinishedERound,
    FinishedFRound,
    RandomnessAStartupRound,
    RandomnessBStartupRound,
    RandomnessRound,
    RegistrationRound,
    TransactionSubmissionAbciApp,
)
from packages.valory.skills.common_apps.tools import aggregate
from packages.valory.skills.oracle_deployment_abci.rounds import OracleDeploymentAbciApp
from packages.valory.skills.safe_deployment_abci.rounds import SafeDeploymentAbciApp


class CollectObservationRound(
    CollectDifferentUntilThresholdRound, CommonAppsAbstractRound
):
    """
    This class represents the 'collect-observation' round.

    Input: a period state with the prior round data
    Ouptut: a new period state with the prior round data and the observations

    It schedules the EstimateConsensusRound.
    """

    round_id = "collect_observation"
    allowed_tx_type = ObservationPayload.transaction_type
    payload_attribute = "observation"

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        # if reached observation threshold, set the result
        if self.collection_threshold_reached:
            observations = [
                getattr(payload, self.payload_attribute)
                for payload in self.collection.values()
            ]
            estimate = aggregate(*observations)
            state = self.period_state.update(
                participant_to_observations=MappingProxyType(self.collection),
                estimate=estimate,
            )
            return state, Event.DONE
        return None


class EstimateConsensusRound(CollectSameUntilThresholdRound, CommonAppsAbstractRound):
    """
    This class represents the 'estimate_consensus' round.

    Input: a period state with the prior round data
    Ouptut: a new period state with the prior round data and the votes for each estimate

    It schedules the TxHashRound.
    """

    round_id = "estimate_consensus"
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


class TxHashRound(CollectSameUntilThresholdRound, CommonAppsAbstractRound):
    """
    This class represents the 'tx-hash' round.

    Input: a period state with the prior round data
    Ouptut: a new period state with the prior round data and the votes for each tx hash

    It schedules the CollectSignatureRound.
    """

    round_id = "tx_hash"
    allowed_tx_type = TransactionHashPayload.transaction_type
    payload_attribute = "tx_hash"

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        if self.threshold_reached and self.most_voted_payload is not None:
            state = self.period_state.update(
                participant_to_tx_hash=MappingProxyType(self.collection),
                most_voted_tx_hash=self.most_voted_payload,
            )
            return state, Event.DONE
        if self.threshold_reached and self.most_voted_payload is None:
            return self.period_state, Event.NONE
        if not self.is_majority_possible(
            self.collection, self.period_state.nb_participants
        ):
            return self._return_no_majority_event()
        return None


class PriceAggregationAbciApp(AbciApp[Event]):
    """Price estimation ABCI application."""

    initial_round_cls: Type[AbstractRound] = CollectObservationRound
    transition_function: AbciAppTransitionFunction = {
        CollectObservationRound: {
            Event.DONE: EstimateConsensusRound,
            Event.ROUND_TIMEOUT: CollectObservationRound,  # if the round times out we reset the period
        },
        EstimateConsensusRound: {
            Event.DONE: TxHashRound,
            Event.ROUND_TIMEOUT: CollectObservationRound,  # if the round times out we reset the period
            Event.NO_MAJORITY: CollectObservationRound,  # if there is no majority we reset the period
        },
        TxHashRound: {
            Event.DONE: FinishedCRound,
            Event.NONE: CollectObservationRound,  # if the agents cannot produce the hash we reset the period
            Event.ROUND_TIMEOUT: CollectObservationRound,  # if the round times out we reset the period
            Event.NO_MAJORITY: CollectObservationRound,  # if there is no majority we reset the period
        },
        FinishedCRound: {},
    }
    final_states: Set[AppState] = {FinishedCRound}
    event_to_timeout: Dict[Event, float] = {
        Event.ROUND_TIMEOUT: 30.0,
        Event.VALIDATE_TIMEOUT: 30.0,
        Event.RESET_TIMEOUT: 30.0,
    }


abci_app_transition_mapping: AbciAppTransitionMapping = {
    FinishedERound: RandomnessAStartupRound,
    FinishedFRound: CollectObservationRound,
    FinishedARound: RandomnessBStartupRound,
    FinishedBRound: CollectObservationRound,
    FinishedCRound: RandomnessRound,
    FinishedDRound: CollectObservationRound,
    FailedRound: RegistrationRound,
}

PriceEstimationAbciApp = chain(
    (
        AgentRegistrationAbciApp,
        SafeDeploymentAbciApp,
        OracleDeploymentAbciApp,
        PriceAggregationAbciApp,
        TransactionSubmissionAbciApp,
    ),
    abci_app_transition_mapping,
)
