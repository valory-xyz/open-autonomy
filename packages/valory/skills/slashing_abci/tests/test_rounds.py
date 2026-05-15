# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023-2026 Valory AG
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

"""Tests the slashing background rounds."""

import json
from copy import deepcopy
from typing import Dict, FrozenSet, cast
from unittest.mock import MagicMock

import pytest
from hypothesis import settings

from packages.valory.skills.abstract_round_abci.base import (
    ABCIAppInternalError,
    TransactionNotValidError,
)
from packages.valory.skills.abstract_round_abci.test_tools.rounds import (
    BaseCollectSameUntilThresholdRoundTest,
    BaseRoundTestClass,
)
from packages.valory.skills.abstract_round_abci.tests.conftest import profile_name
from packages.valory.skills.slashing_abci.payloads import (
    SlashingTxPayload,
    StatusResetPayload,
)
from packages.valory.skills.slashing_abci.rounds import (
    Event,
    SlashingCheckRound,
    StatusResetRound,
)
from packages.valory.skills.slashing_abci.rounds import (
    SynchronizedData as SlashingSyncedData,
)
from packages.valory.skills.transaction_settlement_abci.rounds import (
    SynchronizedData as TxSettlementSyncedData,
)

settings.load_profile(profile_name)


class TestSlashingCheckRound(BaseRoundTestClass):
    """Tests for `SlashingCheckRound`."""

    _synchronized_data_class = SlashingSyncedData
    _event_class = Event

    def test_run(self) -> None:
        """Run tests."""

        test_round = SlashingCheckRound(
            synchronized_data=self.synchronized_data,
            context=MagicMock(),
        )

        first_payload, *payloads = [
            SlashingTxPayload(
                sender,
                "tx_hex",
            )
            for sender in self.participants
        ]

        test_round.process_payload(first_payload)
        assert test_round.collection == {first_payload.sender: first_payload}
        res = test_round.end_block()
        assert res is None

        for payload in payloads[:2]:
            test_round.process_payload(payload)
            res = test_round.end_block()

        expected_state = cast(
            SlashingSyncedData,
            self.synchronized_data.update(
                termination_majority_reached=True,
            ),
        )

        assert res is not None
        actual_state, event = res
        actual_state = cast(SlashingSyncedData, actual_state)

        assert actual_state.slashing_in_flight == expected_state.slashing_in_flight
        assert (
            actual_state.slashing_majority_reached
            == expected_state.slashing_majority_reached
        )
        assert (
            TxSettlementSyncedData(actual_state.db).most_voted_tx_hash
            == TxSettlementSyncedData(expected_state.db).most_voted_tx_hash
        )
        assert event == Event.SLASH_START
        assert not test_round.collection

    def test_bad_payloads(self) -> None:
        """Tests the slashing check round when bad payloads are sent."""
        test_round = SlashingCheckRound(
            synchronized_data=deepcopy(self.synchronized_data),
            context=MagicMock(),
        )
        payload_data = "0xdata"
        bad_participant = "non_existent"
        bad_participant_payload = SlashingTxPayload(bad_participant, payload_data)
        first_payload, *_ = [
            SlashingTxPayload(participant, payload_data)
            for participant in self.participants
        ]

        with pytest.raises(
            TransactionNotValidError,
            match=f"{bad_participant} not in list of participants",
        ):
            test_round.check_payload(bad_participant_payload)

        with pytest.raises(
            ABCIAppInternalError,
            match=f"{bad_participant} not in list of participants",
        ):
            test_round.process_payload(bad_participant_payload)

        # a valid payload gets sent for the first time and it goes through
        test_round.process_payload(first_payload)

        # a duplicate (valid) payload will not go through
        with pytest.raises(
            TransactionNotValidError,
            match=f"sender {first_payload.sender} has already sent value for round",
        ):
            test_round.check_payload(first_payload)

        with pytest.raises(
            ABCIAppInternalError,
            match=f"sender {first_payload.sender} has already sent value for round",
        ):
            test_round.process_payload(first_payload)


def _participant_to_status_reset(
    participants: FrozenSet[str],
    operators_mapping: str,
    slash_timestamps: str,
    slashing_in_flight: bool,
    slash_tx_sent: bool,
) -> Dict[str, StatusResetPayload]:
    """Build participant-to-payload mapping for the status reset round."""
    return {
        participant: StatusResetPayload(
            sender=participant,
            operators_mapping=operators_mapping,
            slash_timestamps=slash_timestamps,
            slashing_in_flight=slashing_in_flight,
            slash_tx_sent=slash_tx_sent,
        )
        for participant in participants
    }


class TestStatusResetRound(BaseCollectSameUntilThresholdRoundTest):
    """Exercise StatusResetRound through the framework base test."""

    _synchronized_data_class = SlashingSyncedData
    _event_class = Event

    def test_slash_end_event(self) -> None:
        """A threshold of identical payloads writes the 4-tuple selection_key into the DB and yields ``SLASH_END``.

        The 4th payload field ``slash_tx_sent`` maps positionally to the 4th
        selection_key ``slashing_majority_reached``; this test pins that
        mapping so a future reorder of either tuple is caught.
        """
        operators_mapping = json.dumps({"operator_a": ["agent_a"]}, sort_keys=True)
        slash_timestamps = json.dumps({"agent_a": 1700000000}, sort_keys=True)
        slashing_in_flight = False
        slash_tx_sent = True

        test_round = StatusResetRound(
            synchronized_data=self.synchronized_data,
            context=MagicMock(),
        )

        def _expected(
            data: SlashingSyncedData, _round: StatusResetRound
        ) -> SlashingSyncedData:
            return cast(
                SlashingSyncedData,
                data.update(
                    synchronized_data_class=SlashingSyncedData,
                    operators_mapping=operators_mapping,
                    slash_timestamps=slash_timestamps,
                    slashing_in_flight=slashing_in_flight,
                    slashing_majority_reached=slash_tx_sent,
                ),
            )

        self._complete_run(
            self._test_round(
                test_round=test_round,
                round_payloads=_participant_to_status_reset(
                    self.participants,
                    operators_mapping,
                    slash_timestamps,
                    slashing_in_flight,
                    slash_tx_sent,
                ),
                synchronized_data_update_fn=_expected,
                synchronized_data_attr_checks=[
                    lambda data: data.operators_mapping,
                    lambda data: data.slash_timestamps,
                    lambda data: data.slashing_in_flight,
                    lambda data: data.slashing_majority_reached,
                ],
                most_voted_payload=operators_mapping,
                exit_event=Event.SLASH_END,
            )
        )

    def test_no_majority_event(self) -> None:
        """A round in which majority is impossible yields ``Event.NO_MAJORITY``."""
        test_round = StatusResetRound(
            synchronized_data=self.synchronized_data,
            context=MagicMock(),
        )
        self._test_no_majority_event(test_round)
