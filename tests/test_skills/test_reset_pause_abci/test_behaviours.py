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

"""Tests for valory/reset_pause_abci skill's behaviours."""
import datetime
import time
from pathlib import Path
from typing import cast
from unittest import mock

from packages.valory.skills.abstract_round_abci.base import (
    BasePeriodState as ResetPeriodState,
)
from packages.valory.skills.abstract_round_abci.base import StateDB
from packages.valory.skills.abstract_round_abci.behaviour_utils import (
    BaseState,
    make_degenerate_state,
)
from packages.valory.skills.reset_pause_abci.behaviours import ResetAndPauseBehaviour
from packages.valory.skills.reset_pause_abci.rounds import Event as ResetEvent
from packages.valory.skills.reset_pause_abci.rounds import FinishedResetAndPauseRound

from tests.conftest import ROOT_DIR
from tests.test_skills.base import FSMBehaviourBaseCase


class ResetPauseAbciFSMBehaviourBaseCase(FSMBehaviourBaseCase):
    """Base case for testing PauseReset FSMBehaviour."""

    path_to_skill = Path(ROOT_DIR, "packages", "valory", "skills", "reset_pause_abci")


class TestResetAndPauseBehaviour(ResetPauseAbciFSMBehaviourBaseCase):
    """Test ResetBehaviour."""

    behaviour_class = ResetAndPauseBehaviour
    next_behaviour_class = make_degenerate_state(FinishedResetAndPauseRound.round_id)

    def test_reset_behaviour(
        self,
    ) -> None:
        """Test reset behaviour."""
        self.fast_forward_to_state(
            behaviour=self.behaviour,
            state_id=self.behaviour_class.state_id,
            period_state=ResetPeriodState(
                StateDB(
                    initial_period=0,
                    initial_data=dict(
                        most_voted_estimate=0.1,
                        tx_hashes_history=["68656c6c6f776f726c64"],
                    ),
                )
            ),
        )
        assert (
            cast(
                BaseState,
                cast(BaseState, self.behaviour.current_state),
            ).state_id
            == self.behaviour_class.state_id
        )
        with mock.patch(
            "packages.valory.skills.abstract_round_abci.base.AbciApp.last_timestamp",
            new_callable=mock.PropertyMock,
        ) as pmock:
            pmock.return_value = datetime.datetime.now()
            self.behaviour.context.params.observation_interval = 0.1
            self.behaviour.act_wrapper()
            time.sleep(0.3)
            self.behaviour.act_wrapper()
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round(ResetEvent.DONE)
        state = cast(BaseState, self.behaviour.current_state)
        assert state.state_id == self.next_behaviour_class.state_id
