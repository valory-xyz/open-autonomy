# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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

from packages.valory.skills.abstract_round_abci.base import AbciAppDB, ConsensusParams
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
    consensus_params: ConsensusParams
    participants: FrozenSet[str]

    @classmethod
    def setup(
        cls,
    ) -> None:
        """Setup the test class."""

        cls.participants = get_participants()
        cls.synchronized_data = SynchronizedData(
            AbciAppDB(
                setup_data=dict(
                    participants=[cls.participants], all_participants=[cls.participants]
                ),
            )
        )
        cls.consensus_params = ConsensusParams(max_participants=MAX_PARTICIPANTS)


class TestBackgroundRound(BaseRoundTestClass):
    """Tests for BackgroundRound."""

    def test_run(
        self,
    ) -> None:
        """Run tests."""

        test_round = BackgroundRound(
            synchronized_data=deepcopy(self.synchronized_data),
            consensus_params=self.consensus_params,
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
            == cast(SynchronizedData, expected_state).termination_majority_reached
        )

        assert event == Event.TERMINATE


class TestTerminationRound(BaseRoundTestClass):
    """Tests for TerminationRound."""

    def test_run(
        self,
    ) -> None:
        """Run tests."""

        test_round = TerminationRound(
            synchronized_data=deepcopy(self.synchronized_data),
            consensus_params=self.consensus_params,
        )
        res = test_round.end_block()  # pylint: disable=assignment-from-none
        assert res is None
