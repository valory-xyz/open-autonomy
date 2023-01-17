# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023 Valory AG
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
"""This module contains the data classes for the Hello World ABCI application."""

from enum import Enum
from typing import Dict, Optional, Tuple

from packages.valory.skills.abstract_round_abci.base import (
    AbciApp,
    AbciAppTransitionFunction,
    AppState,
    BaseSynchronizedData,
    CollectDifferentUntilAllRound,
)
from packages.valory.skills.test_ipfs_abci.payloads import DummyPayload


class Event(Enum):
    """Event enumeration for the ipfs test skill."""

    DONE = "done"
    ROUND_TIMEOUT = "round_timeout"


class IpfsRound(CollectDifferentUntilAllRound):
    """Dummy ipfs round."""

    payload_class = DummyPayload
    payload_attribute = "sender"
    synchronized_data_class = BaseSynchronizedData

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Enum]]:
        """End block. This is a dummy round, we don't care about payloads."""
        if self.collection_threshold_reached:  # pragma: no cover
            # added to satisfy fsm-spec checks,
            # the following will never be executed
            return self.synchronized_data, Event.DONE
        return None


class IpfsTestAbciApp(AbciApp[Event]):
    """IpfsTestAbciApp

    Initial round: IpfsRound

    Initial states: {IpfsRound}

    Transition states:
        0. IpfsRound
            - done: 0.
            - round timeout: 0.

    Final states: {}

    Timeouts:
        round timeout: 30.0
    """

    initial_round_cls: AppState = IpfsRound
    transition_function: AbciAppTransitionFunction = {
        IpfsRound: {
            Event.DONE: IpfsRound,
            Event.ROUND_TIMEOUT: IpfsRound,
        },
    }
    event_to_timeout: Dict[Event, float] = {
        Event.ROUND_TIMEOUT: 30.0,
    }
