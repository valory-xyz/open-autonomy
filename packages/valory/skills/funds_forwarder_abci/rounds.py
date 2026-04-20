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

"""This module contains the rounds of the FundsForwarderAbciApp."""

from enum import Enum
from typing import Dict, FrozenSet, Set, Tuple, cast

from packages.valory.skills.abstract_round_abci.base import (
    AbciApp,
    AbciAppTransitionFunction,
    AppState,
    CollectSameUntilThresholdRound,
    DegenerateRound,
    get_name,
)
from packages.valory.skills.funds_forwarder_abci.payloads import FundsForwarderPayload
from packages.valory.skills.transaction_settlement_abci.rounds import (
    SynchronizedData as TxSynchronizedData,
)


class Event(Enum):
    """FundsForwarderAbciApp Events"""

    DONE = "done"
    NONE = "none"
    NO_MAJORITY = "no_majority"
    ROUND_TIMEOUT = "round_timeout"


class SynchronizedData(TxSynchronizedData):
    """Class to represent the synchronized data.

    This data is replicated by the tendermint application.
    """

    @property
    def service_owner(self) -> str:
        """Get the resolved service owner address."""
        return cast(str, self.db.get_strict("service_owner"))

    @property
    def most_voted_tx_hash(self) -> str:
        """Get the most_voted_tx_hash."""
        return cast(str, self.db.get_strict("most_voted_tx_hash"))

    @property
    def tx_submitter(self) -> str:
        """Get the round that submitted the transaction."""
        return cast(str, self.db.get_strict("tx_submitter"))

    @property
    def participant_to_funds_forwarder(self) -> dict:
        """Get the participant_to_funds_forwarder."""
        return cast(dict, self.db.get_strict("participant_to_funds_forwarder"))


class FundsForwarderRound(CollectSameUntilThresholdRound):
    """A round for sweeping excess funds to the service owner."""

    payload_class = FundsForwarderPayload
    synchronized_data_class = SynchronizedData
    done_event = Event.DONE
    none_event = Event.NONE
    no_majority_event = Event.NO_MAJORITY
    selection_key: Tuple[str, ...] = (
        get_name(SynchronizedData.tx_submitter),
        get_name(SynchronizedData.most_voted_tx_hash),
    )
    collection_key = get_name(SynchronizedData.participant_to_funds_forwarder)


class FinishedFundsForwarderWithTxRound(DegenerateRound):
    """A round representing a successful fund sweep with a transaction."""


class FinishedFundsForwarderNoTxRound(DegenerateRound):
    """A round representing a fund sweep with no transaction needed."""


class FundsForwarderAbciApp(AbciApp[Event]):
    """FundsForwarderAbciApp

    Initial round: FundsForwarderRound

    Initial states: {FundsForwarderRound}

    Transition states:
        0. FundsForwarderRound
            - done: 1.
            - none: 2.
            - no majority: 0.
            - round timeout: 0.
        1. FinishedFundsForwarderWithTxRound
        2. FinishedFundsForwarderNoTxRound

    Final states: {FinishedFundsForwarderNoTxRound, FinishedFundsForwarderWithTxRound}

    Timeouts:
        round timeout: 30.0
    """

    initial_round_cls: AppState = FundsForwarderRound
    initial_states: Set[AppState] = {FundsForwarderRound}
    transition_function: AbciAppTransitionFunction = {
        FundsForwarderRound: {
            Event.DONE: FinishedFundsForwarderWithTxRound,
            Event.NONE: FinishedFundsForwarderNoTxRound,
            Event.NO_MAJORITY: FundsForwarderRound,
            Event.ROUND_TIMEOUT: FundsForwarderRound,
        },
        FinishedFundsForwarderWithTxRound: {},
        FinishedFundsForwarderNoTxRound: {},
    }
    final_states: Set[AppState] = {
        FinishedFundsForwarderWithTxRound,
        FinishedFundsForwarderNoTxRound,
    }
    event_to_timeout: Dict[Event, float] = {
        Event.ROUND_TIMEOUT: 30.0,
    }
    cross_period_persisted_keys: FrozenSet[str] = frozenset()
    db_pre_conditions: Dict[AppState, Set[str]] = {
        FundsForwarderRound: {
            get_name(SynchronizedData.service_owner),
        },
    }
    db_post_conditions: Dict[AppState, Set[str]] = {
        FinishedFundsForwarderWithTxRound: {
            get_name(SynchronizedData.most_voted_tx_hash),
            get_name(SynchronizedData.tx_submitter),
        },
        FinishedFundsForwarderNoTxRound: set(),
    }
