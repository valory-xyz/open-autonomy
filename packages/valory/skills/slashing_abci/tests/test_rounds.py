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

"""Tests the slashing background rounds."""
from copy import deepcopy
from typing import cast
from unittest.mock import MagicMock

import pytest
from hypothesis import settings

from packages.valory.skills.abstract_round_abci.base import (
    ABCIAppInternalError,
    TransactionNotValidError,
)
from packages.valory.skills.abstract_round_abci.test_tools.rounds import (
    BaseRoundTestClass,
)
from packages.valory.skills.abstract_round_abci.tests.conftest import profile_name
from packages.valory.skills.slashing_abci.payloads import SlashingTxPayload
from packages.valory.skills.slashing_abci.rounds import Event, SlashingCheckRound
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
