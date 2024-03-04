# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022-2024 Valory AG
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

"""Test the rounds of the skill."""

from copy import deepcopy
from typing import FrozenSet, cast
from unittest.mock import MagicMock

import pytest

from packages.valory.skills.abstract_round_abci.base import (
    ABCIAppInternalError,
    AbciAppDB,
    TransactionNotValidError,
)
from packages.valory.skills.termination_abci.payloads import BackgroundPayload
from packages.valory.skills.termination_abci.rounds import (
    BackgroundRound,
    Event,
    SynchronizedData,
    TerminationRound,
)


MAX_PARTICIPANTS: int = 4


def get_participants() -> FrozenSet[str]:
    """Participants"""
    return frozenset([f"agent_{i}" for i in range(MAX_PARTICIPANTS)])


class BaseRoundTestClass:  # pylint: disable=too-few-public-methods
    """Base test class for Rounds."""

    synchronized_data: SynchronizedData
    participants: FrozenSet[str]

    def setup(
        self,
    ) -> None:
        """Setup the test class."""

        self.participants = get_participants()
        self.synchronized_data = SynchronizedData(
            AbciAppDB(
                setup_data=dict(
                    participants=[tuple(self.participants)],
                    all_participants=[tuple(self.participants)],
                    consensus_threshold=[3],
                ),
            )
        )


class TestBackgroundRound(BaseRoundTestClass):
    """Tests for BackgroundRound."""

    def test_run(
        self,
    ) -> None:
        """Run tests."""

        test_round = BackgroundRound(
            synchronized_data=deepcopy(self.synchronized_data),
            context=MagicMock(
                params=MagicMock(
                    default_chain_id=1,
                )
            ),
        )
        payload_data = "0xdata"
        first_payload, *payloads = [
            BackgroundPayload(sender=participant, background_data=payload_data)
            for participant in self.participants
        ]

        test_round.process_payload(first_payload)
        assert test_round.collection == {first_payload.sender: first_payload}
        assert test_round.end_block() is None

        for payload in payloads:
            test_round.process_payload(payload)

        expected_state = self.synchronized_data.update(
            most_voted_tx_hash=payload_data,
            termination_majority_reached=True,
        )

        res = test_round.end_block()
        assert res is not None
        actual_state, event = res

        assert (
            cast(SynchronizedData, actual_state).termination_majority_reached
            == cast(  # pylint: disable=no-member
                SynchronizedData, expected_state
            ).termination_majority_reached
        )

        assert event == Event.TERMINATE

    def test_bad_payloads(self) -> None:
        """Tests the background round when bad payloads are sent."""
        test_round = BackgroundRound(
            synchronized_data=deepcopy(self.synchronized_data),
            context=MagicMock(),
        )
        payload_data = "0xdata"
        bad_participant = "non_existent"
        bad_participant_payload = BackgroundPayload(
            sender=bad_participant, background_data=payload_data
        )
        first_payload, *_ = [
            BackgroundPayload(sender=participant, background_data=payload_data)
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


class TestTerminationRound(BaseRoundTestClass):
    """Tests for TerminationRound."""

    def test_run(
        self,
    ) -> None:
        """Run tests."""

        test_round = TerminationRound(
            synchronized_data=deepcopy(self.synchronized_data),
            context=MagicMock(),
        )
        res = test_round.end_block()  # pylint: disable=assignment-from-none
        assert res is None
