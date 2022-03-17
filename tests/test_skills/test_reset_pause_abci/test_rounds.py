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

"""Test the base.py module of the skill."""
import logging  # noqa: F401
from typing import Dict, FrozenSet

from packages.valory.skills.abstract_round_abci.base import (
    BasePeriodState as ResetPeriodState,
)
from packages.valory.skills.reset_pause_abci.payloads import ResetPausePayload
from packages.valory.skills.reset_pause_abci.rounds import Event as ResetEvent
from packages.valory.skills.reset_pause_abci.rounds import ResetAndPauseRound

from tests.test_skills.test_abstract_round_abci.test_base_rounds import (
    BaseCollectSameUntilThresholdRoundTest,
)


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

    _period_state_class = ResetPeriodState
    _event_class = ResetEvent

    def test_runs(
        self,
    ) -> None:
        """Runs tests."""

        period_state = self.period_state.update(
            keeper_randomness=DUMMY_RANDOMNESS,
        )
        period_state._db._cross_period_persisted_keys = ["keeper_randomness"]
        test_round = ResetAndPauseRound(
            state=period_state, consensus_params=self.consensus_params
        )
        next_period_count = 1
        self._complete_run(
            self._test_round(
                test_round=test_round,
                round_payloads=get_participant_to_period_count(
                    self.participants, next_period_count
                ),
                state_update_fn=lambda _period_state, _: _period_state.update(
                    period_count=next_period_count,
                    participants=self.participants,
                    all_participants=self.participants,
                    keeper_randomness=DUMMY_RANDOMNESS,
                ),
                state_attr_checks=[],  # [lambda state: state.participants],
                most_voted_payload=next_period_count,
                exit_event=self._event_class.DONE,
            )
        )
