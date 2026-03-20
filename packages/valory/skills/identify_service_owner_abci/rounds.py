# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2026 Valory AG
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

"""This module contains the rounds of the IdentifyServiceOwnerAbciApp."""

from enum import Enum
from typing import Dict, FrozenSet, Set, Type, cast

from packages.valory.skills.abstract_round_abci.base import (
    AbciApp,
    AbciAppTransitionFunction,
    AppState,
    BaseSynchronizedData,
    CollectSameUntilThresholdRound,
    DegenerateRound,
    get_name,
)
from packages.valory.skills.identify_service_owner_abci.payloads import (
    IdentifyServiceOwnerPayload,
)


class Event(Enum):
    """IdentifyServiceOwnerAbciApp Events"""

    DONE = "done"
    ERROR = "error"
    NO_MAJORITY = "no_majority"
    ROUND_TIMEOUT = "round_timeout"


class SynchronizedData(BaseSynchronizedData):
    """Class to represent the synchronized data.

    This data is replicated by the tendermint application.
    """

    @property
    def service_owner(self) -> str:
        """Get the resolved service owner address."""
        return cast(str, self.db.get_strict("service_owner"))


class IdentifyServiceOwnerRound(CollectSameUntilThresholdRound):
    """A round for resolving the real service owner."""

    payload_class = IdentifyServiceOwnerPayload
    synchronized_data_class = SynchronizedData
    done_event = Event.DONE
    none_event = Event.ERROR
    no_majority_event = Event.NO_MAJORITY
    selection_key = get_name(SynchronizedData.service_owner)
    collection_key = "participant_to_service_owner"


class FinishedIdentifyServiceOwnerRound(DegenerateRound):
    """A round representing the successful resolution of the service owner."""


class FinishedIdentifyServiceOwnerErrorRound(DegenerateRound):
    """A round representing a failure in resolving the service owner."""


class IdentifyServiceOwnerAbciApp(AbciApp[Event]):
    """IdentifyServiceOwnerAbciApp

    Initial round: IdentifyServiceOwnerRound

    Initial states: {IdentifyServiceOwnerRound}

    Transition states:
        0. IdentifyServiceOwnerRound
            - done: 1.
            - error: 2.
            - no majority: 0.
            - round timeout: 0.
        1. FinishedIdentifyServiceOwnerRound
        2. FinishedIdentifyServiceOwnerErrorRound

    Final states: {FinishedIdentifyServiceOwnerErrorRound, FinishedIdentifyServiceOwnerRound}

    Timeouts:
        round timeout: 30.0
    """

    initial_round_cls: Type[AppState] = IdentifyServiceOwnerRound
    initial_states: Set[AppState] = {IdentifyServiceOwnerRound}
    transition_function: AbciAppTransitionFunction = {
        IdentifyServiceOwnerRound: {
            Event.DONE: FinishedIdentifyServiceOwnerRound,
            Event.ERROR: FinishedIdentifyServiceOwnerErrorRound,
            Event.NO_MAJORITY: IdentifyServiceOwnerRound,
            Event.ROUND_TIMEOUT: IdentifyServiceOwnerRound,
        },
        FinishedIdentifyServiceOwnerRound: {},
        FinishedIdentifyServiceOwnerErrorRound: {},
    }
    final_states: Set[AppState] = {
        FinishedIdentifyServiceOwnerRound,
        FinishedIdentifyServiceOwnerErrorRound,
    }
    event_to_timeout: Dict[Event, float] = {
        Event.ROUND_TIMEOUT: 30.0,
    }
    cross_period_persisted_keys: FrozenSet[str] = frozenset({"service_owner"})
    db_pre_conditions: Dict[AppState, Set[str]] = {
        IdentifyServiceOwnerRound: set(),
    }
    db_post_conditions: Dict[AppState, Set[str]] = {
        FinishedIdentifyServiceOwnerRound: {"service_owner"},
        FinishedIdentifyServiceOwnerErrorRound: set(),
    }
