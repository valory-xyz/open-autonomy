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
from typing import Dict, FrozenSet

from packages.valory.skills.abstract_round_abci.base import (
    BaseSynchronizedData as ResetSynchronizedSata,
)
from packages.valory.skills.abstract_round_abci.test_tools.rounds import (
    BaseCollectSameUntilThresholdRoundTest,
)
from packages.valory.skills.reset_pause_abci.payloads import ResetPausePayload
from packages.valory.skills.reset_pause_abci.rounds import Event as ResetEvent
from packages.valory.skills.reset_pause_abci.rounds import ResetAndPauseRound


MAX_PARTICIPANTS: int = 4
DUMMY_RANDOMNESS = 0.1  # for coverage purposes


def get_participant_to_period_count(
    participants: FrozenSet[str], period_count: int
) -> Dict[str, ResetPausePayload]:
    """participant_to_selection"""
    return {
        participant: ResetPausePayload(sender=participant, period_count=period_count)
        for participant in participants
    }


class TestResetAndPauseRound(BaseCollectSameUntilThresholdRoundTest):
    """Test ResetRound."""

    _synchronized_data_class = ResetSynchronizedSata
    _event_class = ResetEvent

    def test_runs(
        self,
    ) -> None:
        """Runs tests."""

        synchronized_data = self.synchronized_data.update(
            keeper_randomness=DUMMY_RANDOMNESS,
        )
        synchronized_data._db._cross_period_persisted_keys = ["keeper_randomness"]
        test_round = ResetAndPauseRound(
            synchronized_data=synchronized_data, consensus_params=self.consensus_params
        )
        next_period_count = 1
        self._complete_run(
            self._test_round(
                test_round=test_round,
                round_payloads=get_participant_to_period_count(
                    self.participants, next_period_count
                ),
                synchronized_data_update_fn=lambda _synchronized_data, _: _synchronized_data.create(
                    participants=[self.participants],
                    all_participants=[self.participants],
                    keeper_randomness=[DUMMY_RANDOMNESS],
                ),
                synchronized_data_attr_checks=[],  # [lambda _synchronized_data: _synchronized_data.participants],
                most_voted_payload=next_period_count,
                exit_event=self._event_class.DONE,
            )
        )

    def test_accepting_payloads_from(self) -> None:
        """Test accepting payloads from"""

        alice, *others = self.participants
        participants = list(others)
        all_participants = participants + [alice]

        synchronized_data = self.synchronized_data.update(
            participants=participants, all_participants=all_participants
        )

        test_round = ResetAndPauseRound(
            synchronized_data=synchronized_data, consensus_params=self.consensus_params
        )

        assert test_round.accepting_payloads_from is not participants
        assert test_round.accepting_payloads_from is all_participants
