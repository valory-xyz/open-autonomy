# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022-2023 Valory AG
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

"""This package contains the rounds of DummyAbciApp."""

from abc import ABC
from enum import Enum
from typing import FrozenSet, Optional, Set, Tuple, cast

from packages.valory.skills.abstract_round_abci.base import (
    AbciApp,
    AbciAppTransitionFunction,
    AbstractRound,
    AppState,
    BaseSynchronizedData,
    CollectSameUntilAllRound,
    CollectSameUntilThresholdRound,
    EventToTimeout,
    OnlyKeeperSendsRound,
)
from packages.valory.skills.abstract_round_abci.tests.data.dummy_abci.payloads import (
    DummyFinalPayload,
    DummyKeeperSelectionPayload,
    DummyRandomnessPayload,
    DummyStartingPayload,
)


class Event(Enum):
    """DummyAbciApp Events"""

    ROUND_TIMEOUT = "round_timeout"
    NO_MAJORITY = "no_majority"
    DONE = "done"


class SynchronizedData(BaseSynchronizedData):
    """
    Class to represent the synchronized data.

    This data is replicated by the tendermint application.
    """


class DummyMixinRound(AbstractRound, ABC):
    """DummyMixinRound"""

    done_event = Event.DONE
    no_majority_event = Event.NO_MAJORITY

    @property
    def synchronized_data(self) -> SynchronizedData:
        """Return the synchronized data."""
        return cast(SynchronizedData, self._synchronized_data)


class DummyStartingRound(CollectSameUntilAllRound, DummyMixinRound):
    """DummyStartingRound"""

    round_id: str = "dummy_starting"
    payload_class = DummyStartingPayload
    payload_attribute: str = "dummy_starting"
    synchronized_data_class = SynchronizedData

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""

        if self.collection_threshold_reached:
            synchronized_data = self.synchronized_data.update(
                participants=tuple(sorted(self.collection)),
                synchronized_data_class=SynchronizedData,
            )
            return synchronized_data, Event.DONE
        return None


class DummyRandomnessRound(CollectSameUntilThresholdRound, DummyMixinRound):
    """DummyRandomnessRound"""

    round_id: str = "dummy_randomness"
    payload_class = DummyRandomnessPayload
    payload_attribute: str = "dummy_randomness"
    collection_key = "participant_to_randomness"
    selection_key = "most_voted_randomness"
    synchronized_data_class = SynchronizedData


class DummyKeeperSelectionRound(CollectSameUntilThresholdRound, DummyMixinRound):
    """DummyKeeperSelectionRound"""

    round_id: str = "dummy_keeper_selection"
    payload_class = DummyKeeperSelectionPayload
    payload_attribute: str = "dummy_keeper_selection"
    collection_key = "participant_to_keeper"
    selection_key = "most_voted_keeper"
    synchronized_data_class = SynchronizedData


class DummyFinalRound(OnlyKeeperSendsRound, DummyMixinRound):
    """DummyFinalRound"""

    round_id: str = "dummy_final"
    payload_class = DummyFinalPayload
    payload_attribute: str = "dummy_final"
    synchronized_data_class = SynchronizedData


class DummyAbciApp(AbciApp[Event]):
    """DummyAbciApp"""

    initial_round_cls: AppState = DummyStartingRound
    transition_function: AbciAppTransitionFunction = {
        DummyStartingRound: {
            Event.DONE: DummyRandomnessRound,
            Event.ROUND_TIMEOUT: DummyStartingRound,
            Event.NO_MAJORITY: DummyStartingRound,
        },
        DummyRandomnessRound: {
            Event.DONE: DummyKeeperSelectionRound,
            Event.ROUND_TIMEOUT: DummyRandomnessRound,
            Event.NO_MAJORITY: DummyRandomnessRound,
        },
        DummyKeeperSelectionRound: {
            Event.DONE: DummyFinalRound,
            Event.ROUND_TIMEOUT: DummyKeeperSelectionRound,
            Event.NO_MAJORITY: DummyKeeperSelectionRound,
        },
        DummyFinalRound: {
            Event.DONE: DummyStartingRound,
            Event.ROUND_TIMEOUT: DummyFinalRound,
            Event.NO_MAJORITY: DummyFinalRound,
        },
    }
    final_states: Set[AppState] = set()
    event_to_timeout: EventToTimeout = {}
    cross_period_persisted_keys: FrozenSet[str] = frozenset()
