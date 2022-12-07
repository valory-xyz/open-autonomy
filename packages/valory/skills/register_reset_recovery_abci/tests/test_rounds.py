# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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
from typing import FrozenSet

from packages.valory.skills.abstract_round_abci.base import (
    AbciAppDB,
    BaseSynchronizedData,
    ConsensusParams,
)
from packages.valory.skills.register_reset_recovery_abci.payloads import (
    RoundCountPayload,
)
from packages.valory.skills.register_reset_recovery_abci.rounds import (
    Event,
    RoundCountRound,
)


MAX_PARTICIPANTS: int = 4


def get_participants() -> FrozenSet[str]:
    """Participants"""
    return frozenset([f"agent_{i}" for i in range(MAX_PARTICIPANTS)])


class BaseRoundTestClass:  # pylint: disable=too-few-public-methods
    """Base test class for Rounds."""

    synchronized_data: BaseSynchronizedData
    consensus_params: ConsensusParams
    participants: FrozenSet[str]

    def setup(
        self,
    ) -> None:
        """Setup the test class."""

        self.participants = get_participants()
        self.synchronized_data = BaseSynchronizedData(
            AbciAppDB(
                setup_data=dict(
                    participants=[self.participants],
                    all_participants=[self.participants],
                ),
            )
        )
        self.consensus_params = ConsensusParams(max_participants=MAX_PARTICIPANTS)


class TestTerminationRound(BaseRoundTestClass):
    """Tests for TerminationRound."""

    def test_run(
        self,
    ) -> None:
        """Run tests."""

        test_round = RoundCountRound(
            synchronized_data=deepcopy(self.synchronized_data),
            consensus_params=self.consensus_params,
        )
        payload_data = 1
        first_payload, *payloads = [
            RoundCountPayload(sender=participant, current_round_count=payload_data)
            for participant in self.participants
        ]

        test_round.process_payload(first_payload)
        assert test_round.collection == {first_payload.sender: first_payload}
        assert test_round.end_block() is None

        for payload in payloads:
            test_round.process_payload(payload)

        res = test_round.end_block()
        assert res is not None
        _, event = res

        assert event == Event.DONE
