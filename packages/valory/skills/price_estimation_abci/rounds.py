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
import struct
from abc import ABC
from types import MappingProxyType
from typing import Dict, Mapping, Optional, Set, Tuple, Type, cast

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
    TransactionType,
)
from packages.valory.skills.common_apps.rounds import Event, FinishedRound
from packages.valory.skills.common_apps.tools import aggregate


def encode_float(value: float) -> bytes:
    """Encode a float value."""
    return struct.pack("d", value)


class PeriodState(BasePeriodState):
    """
    Class to represent a period state.

    This state is replicated by the tendermint application.
    """

    @property
    def safe_contract_address(self) -> str:
        """Get the safe contract address."""
        return cast(str, self.db.get_strict("safe_contract_address"))

    @property
    def oracle_contract_address(self) -> str:
        """Get the oracle contract address."""
        return cast(str, self.db.get_strict("oracle_contract_address"))

    @property
    def participant_to_observations(self) -> Mapping[str, ObservationPayload]:
        """Get the participant_to_observations."""
        return cast(
            Mapping[str, ObservationPayload],
            self.db.get_strict("participant_to_observations"),
        )

    @property
    def participant_to_estimate(self) -> Mapping[str, EstimatePayload]:
        """Get the participant_to_estimate."""
        return cast(
            Mapping[str, EstimatePayload], self.db.get_strict("participant_to_estimate")
        )

    @property
    def final_tx_hash(self) -> str:
        """Get the final_tx_hash."""
        return cast(str, self.db.get_strict("final_tx_hash"))

    @property
    def is_final_tx_hash_set(self) -> bool:
        """Check if final_tx_hash is set."""
        return self.db.get("final_tx_hash", None) is not None

    @property
    def estimate(self) -> float:
        """Get the estimate."""
        return cast(float, self.db.get_strict("estimate"))

    @property
    def most_voted_estimate(self) -> float:
        """Get the most_voted_estimate."""
        return cast(float, self.db.get_strict("most_voted_estimate"))

    @property
    def encoded_most_voted_estimate(self) -> bytes:
        """Get the encoded (most voted) estimate."""
        return encode_float(self.most_voted_estimate)

    @property
    def most_voted_tx_hash(self) -> str:
        """Get the most_voted_tx_hash."""
        return cast(str, self.db.get_strict("most_voted_tx_hash"))


class PriceEstimationAbstractRound(AbstractRound[Event, TransactionType], ABC):
    """Abstract round for the agent registration skill."""

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


class CollectObservationRound(
    CollectDifferentUntilThresholdRound, PriceEstimationAbstractRound
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
                period_state_class=PeriodState,
            )
            return state, Event.DONE
        return None


class EstimateConsensusRound(
    CollectSameUntilThresholdRound, PriceEstimationAbstractRound
):
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


class TxHashRound(CollectSameUntilThresholdRound, PriceEstimationAbstractRound):
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


class FinishedPriceAggregationRound(FinishedRound):
    """This class represents the finished round of the price aggreagation."""

    round_id = "finished_price_aggregation"


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
            Event.DONE: FinishedPriceAggregationRound,
            Event.NONE: CollectObservationRound,  # if the agents cannot produce the hash we reset the period
            Event.ROUND_TIMEOUT: CollectObservationRound,  # if the round times out we reset the period
            Event.NO_MAJORITY: CollectObservationRound,  # if there is no majority we reset the period
        },
        FinishedPriceAggregationRound: {},
    }
    final_states: Set[AppState] = {FinishedPriceAggregationRound}
    event_to_timeout: Dict[Event, float] = {
        Event.ROUND_TIMEOUT: 30.0,
        Event.VALIDATE_TIMEOUT: 30.0,
        Event.RESET_TIMEOUT: 30.0,
    }
