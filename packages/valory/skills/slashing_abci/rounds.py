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

"""This module contains the slashing rounds."""

import json
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, cast

from packages.valory.skills.abstract_round_abci.base import (
    ABCIAppInternalError,
    AbciApp,
    AppState,
    BaseSynchronizedData,
    BaseTxPayload,
    CollectSameUntilThresholdRound,
    CollectionRound,
    DeserializedCollection,
    TransactionNotValidError,
    get_name,
)
from packages.valory.skills.slashing_abci.payloads import (
    SlashingTxPayload,
    StatusResetPayload,
)
from packages.valory.skills.transaction_settlement_abci.rounds import (
    SynchronizedData as TxSettlementSyncedData,
)


class Event(Enum):
    """Defines the round events."""

    SLASH_START = "slash_start"
    SLASH_END = "slash_end"
    NO_MAJORITY = "no_majority"
    ROUND_TIMEOUT = "round_timeout"
    NONE = "none"


class SynchronizedData(BaseSynchronizedData):
    """
    Class to represent the synchronized data.

    This data is replicated by the tendermint application.
    """

    @property
    def slashing_bg_init(self) -> bool:
        """Get if the slashing background round has been initialized."""
        return bool(self.db.get("slashing_bg_init", False))

    @property
    def slashing_in_flight(self) -> bool:
        """Get if there is a slashing operation in progress."""
        return bool(self.db.get("slashing_in_flight", False))

    @property
    def slashing_majority_reached(self) -> bool:
        """Get if the slashing majority has been reached."""
        return bool(self.db.get("slashing_majority_reached", False))

    @property
    def operators_mapping(self) -> Optional[Dict[str, List[str]]]:
        """Get a mapping of the operators mapped to their agent instances."""
        mapping = self.db.get("operators_mapping", None)

        if mapping is None:
            return None

        return json.loads(mapping)

    @property
    def slash_timestamps(self) -> Dict[str, int]:
        """Get the timestamp in which each agent instance was slashed at."""
        timestamps = str(self.db.get("slash_timestamps", ""))

        if timestamps == "":
            return {}

        return json.loads(timestamps)

    @property
    def participant_to_offence_reset(
        self,
    ) -> DeserializedCollection:  # pragma: no cover
        """The participants mapped to the status reset payloads."""
        serialized = self.db.get_strict("participant_to_randomness")
        deserialized = CollectionRound.deserialize_collection(serialized)
        return cast(DeserializedCollection, deserialized)


class SlashingCheckRound(CollectSameUntilThresholdRound):
    """Defines the slashing check background round, which runs concurrently with other rounds to send the slash tx."""

    payload_class = SlashingTxPayload
    synchronized_data_class = SynchronizedData
    selection_key = (
        get_name(TxSettlementSyncedData.most_voted_tx_hash),
        get_name(SynchronizedData.slashing_in_flight),
        get_name(SynchronizedData.slashing_majority_reached),
    )

    def process_payload(self, payload: BaseTxPayload) -> None:
        """Process payload."""
        # for background round payloads, we don't need to check the round_count, as round_count is irrelevant for the
        # background since it's running concurrently in the background.
        sender = payload.sender
        if sender not in self.accepting_payloads_from:
            raise ABCIAppInternalError(
                f"{sender} not in list of participants: {sorted(self.accepting_payloads_from)}"
            )

        if sender in self.collection:
            raise ABCIAppInternalError(
                f"sender {sender} has already sent value for round: {self.round_id}"
            )

        self.collection[sender] = payload

    def check_payload(self, payload: BaseTxPayload) -> None:
        """Check Payload"""
        # NOTE: the TransactionNotValidError is intercepted in ABCIRoundHandler.deliver_tx
        #  which means it will be logged instead of raised
        # for background round payloads, we don't need to check the round_count, as round_count is irrelevant for the
        # background since it's running concurrently in the background.
        sender_in_participant_set = payload.sender in self.accepting_payloads_from
        if not sender_in_participant_set:
            raise TransactionNotValidError(
                f"{payload.sender} not in list of participants: {sorted(self.accepting_payloads_from)}"
            )

        if payload.sender in self.collection:
            raise TransactionNotValidError(
                f"sender {payload.sender} has already sent value for round: {self.round_id}"
            )

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""
        synced_data = SynchronizedData(db=self.synchronized_data.db)
        if not synced_data.slashing_bg_init:
            # we set the cross-period values because the period will most probably be increased
            # before this background round ever returns a `SLASH_START` event.
            # if this happens, and we do not set them here, then the db creation for the new period will fail
            # because the values are in the cross-period persisted keys.
            self.synchronized_data.update(
                synchronized_data_class=self.synchronized_data_class,
                slashing_bg_init=True,
                operators_mapping=None,
                slash_timestamps="",
                slashing_in_flight=synced_data.slashing_in_flight,
                slashing_majority_reached=synced_data.slashing_majority_reached,
            )

        if not self.threshold_reached or synced_data.slashing_in_flight:
            return None

        majority_data = dict(zip(self.selection_key, self.most_voted_payload_values))
        state = synced_data.update(
            synchronized_data_class=self.synchronized_data_class,
            **majority_data,
        )
        # we need to reset the collection before returning the slash start event,
        # because this round is continuously and concurrently run in the background
        self.collection = {}
        return state, Event.SLASH_START


class StatusResetRound(CollectSameUntilThresholdRound):
    """Defines the slashing check background round, which runs after a slash tx has been verified."""

    payload_class = StatusResetPayload
    synchronized_data_class = SynchronizedData
    collection_key = get_name(SynchronizedData.participant_to_offence_reset)
    selection_key = (
        get_name(SynchronizedData.operators_mapping),
        get_name(SynchronizedData.slash_timestamps),
        get_name(SynchronizedData.slashing_in_flight),
        get_name(SynchronizedData.slashing_majority_reached),
    )
    done_event = Event.SLASH_END
    no_majority_event = Event.NO_MAJORITY
    none_event = Event.NONE


class PostSlashingTxAbciApp(AbciApp[Event]):
    """PostSlashingTxAbciApp

    Initial round: StatusResetRound

    Initial states: {StatusResetRound}

    Transition states:
        0. StatusResetRound
            - slash end: 0.
            - no majority: 0.
            - round timeout: 0.
            - none: 0.

    Final states: {}

    Timeouts:
        round timeout: 30.0
    """

    initial_round_cls = StatusResetRound
    initial_states = {StatusResetRound}
    transition_function = {
        StatusResetRound: {
            # the following is not needed, it is added to satisfy the round check.
            # the `SLASH_END` event is the end event of the slashing background app,
            # which signals the app to return to the main transition function
            # for more information, see `BackgroundApp` and `AbciApp` implementation
            Event.SLASH_END: StatusResetRound,
            Event.NO_MAJORITY: StatusResetRound,
            Event.ROUND_TIMEOUT: StatusResetRound,
            # none event cannot occur
            Event.NONE: StatusResetRound,
        },
    }
    cross_period_persisted_keys = frozenset(
        {
            get_name(SynchronizedData.operators_mapping),
            get_name(SynchronizedData.slash_timestamps),
            get_name(SynchronizedData.slashing_in_flight),
            get_name(SynchronizedData.slashing_majority_reached),
        }
    )
    event_to_timeout: Dict[Event, float] = {Event.ROUND_TIMEOUT: 30.0}
    db_pre_conditions: Dict[AppState, Set[str]] = {StatusResetRound: set()}
