# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023-2024 Valory AG
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
import json
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, cast

from packages.valory.skills.abstract_round_abci.base import (
    AbciApp,
    AbciAppTransitionFunction,
    AppState,
    BaseSynchronizedData,
    CollectSameUntilThresholdRound,
    DegenerateRound,
    get_name,
)
from packages.valory.skills.test_solana_tx_abci.payloads import SolanaTransactionPayload


class Event(Enum):
    """Event enumeration for the solana test skill."""

    DONE = "done"
    ROUND_TIMEOUT = "round_timeout"
    ERROR = "error"
    NO_MAJORITY = "no_majority"


class SynchronizedData(BaseSynchronizedData):
    """
    Class to represent the synchronized data.

    This data is replicated by the tendermint application.
    """

    @property
    def most_voted_instruction_set(self) -> List[Dict[str, Any]]:
        """Return the list of instructions selected for execution on the multisig."""
        return cast(
            List[Dict[str, Any]], self.db.get_strict("most_voted_instruction_set")
        )


class SolanaRound(CollectSameUntilThresholdRound):
    """Dummy solana round."""

    payload_class = SolanaTransactionPayload
    synchronized_data_class = BaseSynchronizedData

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Enum]]:
        """End block."""
        if self.threshold_reached:  # pragma: no cover
            payload = cast(str, self.most_voted_payload)
            instructions = json.loads(payload)
            synchronized_data = self.synchronized_data.update(
                synchronized_data_class=SynchronizedData,
                **{
                    get_name(SynchronizedData.most_voted_instruction_set): instructions,
                }
            )

            return synchronized_data, Event.DONE
        if not self.is_majority_possible(
            self.collection, self.synchronized_data.nb_participants
        ):
            return self.synchronized_data, Event.NO_MAJORITY

        return None


class FinishedWithTransactionRound(DegenerateRound):
    """Finished with transaction round."""


class SolanaTestAbciApp(AbciApp[Event]):
    """SolanaTestAbciApp

    Initial round: SolanaRound

    Initial states: {SolanaRound}

    Transition states:
        0. SolanaRound
            - done: 1.
            - no majority: 0.
            - round timeout: 0.
        1. FinishedWithTransactionRound

    Final states: {FinishedWithTransactionRound}

    Timeouts:
        round timeout: 30.0
        error: 30.0
    """

    initial_round_cls: AppState = SolanaRound
    transition_function: AbciAppTransitionFunction = {
        SolanaRound: {
            Event.DONE: FinishedWithTransactionRound,
            Event.NO_MAJORITY: SolanaRound,
            Event.ROUND_TIMEOUT: SolanaRound,
        },
        FinishedWithTransactionRound: {},
    }
    final_states = {
        FinishedWithTransactionRound,
    }
    db_pre_conditions = {SolanaRound: set()}
    db_post_conditions = {
        FinishedWithTransactionRound: {
            get_name(SynchronizedData.most_voted_instruction_set)
        }
    }
    event_to_timeout: Dict[Event, float] = {
        Event.ROUND_TIMEOUT: 30.0,
        Event.ERROR: 30.0,
    }
