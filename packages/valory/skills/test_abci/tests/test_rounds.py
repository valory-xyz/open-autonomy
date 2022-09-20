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

# pylint: skip-file

import logging  # noqa: F401
from typing import FrozenSet, cast

from packages.valory.skills.abstract_round_abci.base import (
    AbciAppDB,
    BaseSynchronizedData,
    ConsensusParams,
)
from packages.valory.skills.test_abci.payloads import DummyPayload
from packages.valory.skills.test_abci.rounds import DummyRound, Event


MAX_PARTICIPANTS: int = 4


def get_participants() -> FrozenSet[str]:
    """Participants"""
    return frozenset([f"agent_{i}" for i in range(MAX_PARTICIPANTS)])


class BaseRoundTestClass:
    """Base test class for Rounds."""

    synchronized_data: BaseSynchronizedData
    consensus_params: ConsensusParams
    participants: FrozenSet[str]

    @classmethod
    def setup(
        cls,
    ) -> None:
        """Setup the test class."""

        cls.participants = get_participants()
        cls.synchronized_data = BaseSynchronizedData(
            AbciAppDB(
                setup_data=dict(
                    participants=[cls.participants], all_participants=[cls.participants]
                ),
            )
        )
        cls.consensus_params = ConsensusParams(max_participants=MAX_PARTICIPANTS)


class TestDummyRound(BaseRoundTestClass):
    """Tests for DummyRound."""

    def test_run(
        self,
    ) -> None:
        """Run tests."""

        test_round = DummyRound(
            synchronized_data=self.synchronized_data,
            consensus_params=self.consensus_params,
        )

        first_payload, *payloads = [
            DummyPayload(sender=participant) for participant in self.participants
        ]

        test_round.process_payload(first_payload)
        assert test_round.collection == {first_payload.sender: first_payload}
        assert test_round.end_block() == (self.synchronized_data, Event.DONE)

        for payload in payloads:
            test_round.process_payload(payload)

        actual_next_behaviour = BaseSynchronizedData(
            AbciAppDB(
                setup_data=dict(participants=[frozenset(test_round.collection.keys())]),
            )
        )

        res = test_round.end_block()
        assert res is not None
        synchronized_data, event = res
        assert (
            cast(BaseSynchronizedData, synchronized_data).participants
            == cast(BaseSynchronizedData, actual_next_behaviour).participants
        )
        assert event == Event.DONE
