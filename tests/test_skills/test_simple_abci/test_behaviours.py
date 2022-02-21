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

"""Tests for valory/simple_abci skill's behaviours."""
import json
import time
from pathlib import Path
from typing import cast
from unittest import mock

from packages.valory.skills.abstract_round_abci.base import StateDB
from packages.valory.skills.abstract_round_abci.behaviour_utils import BaseState
from packages.valory.skills.reset_pause_abci.behaviours import ResetAndPauseBehaviour
from packages.valory.skills.simple_abci.behaviours import (
    RandomnessAtStartupBehaviour,
    RegistrationBehaviour,
    SelectKeeperAtStartupBehaviour,
)
from packages.valory.skills.simple_abci.rounds import Event
from packages.valory.skills.simple_abci.rounds import PeriodState
from packages.valory.skills.simple_abci.rounds import (
    PeriodState as SimpleAbciPeriodState,
)

from tests.conftest import ROOT_DIR
from tests.test_skills.base import FSMBehaviourBaseCase


class DummyRoundId:
    """Dummy class for setting round_id for exit condition."""

    round_id: str

    def __init__(self, round_id: str) -> None:
        """Dummy class for setting round_id for exit condition."""
        self.round_id = round_id


class SimpleAbciFSMBehaviourBaseCase(FSMBehaviourBaseCase):
    """Base case for testing PriceEstimation FSMBehaviour."""

    path_to_skill = Path(ROOT_DIR, "packages", "valory", "skills", "simple_abci")


class TestRandomnessBehaviourTest(SimpleAbciFSMBehaviourBaseCase):
    """Test RandomnessBehaviour."""

    def test_randomness_behaviour(
        self,
    ) -> None:
        """Test RandomnessBehaviour."""

        self.fast_forward_to_state(
            self.behaviour,
            RandomnessAtStartupBehaviour.state_id,
            SimpleAbciPeriodState(
                StateDB(initial_period=0, initial_data=dict()),
            ),
        )
        assert (
            cast(
                BaseState,
                cast(BaseState, self.behaviour.current_state),
            ).state_id
            == RandomnessAtStartupBehaviour.state_id
        )
        self.behaviour.act_wrapper()
        self.mock_http_request(
            request_kwargs=dict(
                method="GET",
                headers="",
                version="",
                body=b"",
                url="https://drand.cloudflare.com/public/latest",
            ),
            response_kwargs=dict(
                version="",
                status_code=200,
                status_text="",
                headers="",
                body=json.dumps(
                    {
                        "round": 1283255,
                        "randomness": "04d4866c26e03347d2431caa82ab2d7b7bdbec8b58bca9460c96f5265d878feb",
                    }
                ).encode("utf-8"),
            ),
        )

        self.behaviour.act_wrapper()
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round(Event.DONE)

        state = cast(BaseState, self.behaviour.current_state)
        assert state.state_id == SelectKeeperAtStartupBehaviour.state_id

    def test_invalid_response(
        self,
    ) -> None:
        """Test invalid json response."""
        self.fast_forward_to_state(
            self.behaviour,
            RandomnessAtStartupBehaviour.state_id,
            SimpleAbciPeriodState(
                StateDB(initial_period=0, initial_data=dict()),
            ),
        )
        assert (
            cast(
                BaseState,
                cast(BaseState, self.behaviour.current_state),
            ).state_id
            == RandomnessAtStartupBehaviour.state_id
        )
        self.behaviour.act_wrapper()

        self.mock_http_request(
            request_kwargs=dict(
                method="GET",
                headers="",
                version="",
                body=b"",
                url="https://drand.cloudflare.com/public/latest",
            ),
            response_kwargs=dict(
                version="", status_code=200, status_text="", headers="", body=b""
            ),
        )
        self.behaviour.act_wrapper()
        time.sleep(1)
        self.behaviour.act_wrapper()

    def test_max_retries_reached(
        self,
    ) -> None:
        """Test with max retries reached."""
        self.fast_forward_to_state(
            self.behaviour,
            RandomnessAtStartupBehaviour.state_id,
            SimpleAbciPeriodState(
                StateDB(initial_period=0, initial_data=dict()),
            ),
        )
        assert (
            cast(
                BaseState,
                cast(BaseState, self.behaviour.current_state),
            ).state_id
            == RandomnessAtStartupBehaviour.state_id
        )
        with mock.patch.object(
            self.behaviour.context.randomness_api,
            "is_retries_exceeded",
            return_value=True,
        ):
            self.behaviour.act_wrapper()
            state = cast(BaseState, self.behaviour.current_state)
            assert state.state_id == RandomnessAtStartupBehaviour.state_id
            self._test_done_flag_set()

    def test_clean_up(
        self,
    ) -> None:
        """Test when `observed` value is none."""
        self.fast_forward_to_state(
            self.behaviour,
            RandomnessAtStartupBehaviour.state_id,
            SimpleAbciPeriodState(
                StateDB(initial_period=0, initial_data=dict()),
            ),
        )
        assert (
            cast(
                BaseState,
                cast(BaseState, self.behaviour.current_state),
            ).state_id
            == RandomnessAtStartupBehaviour.state_id
        )
        self.behaviour.context.randomness_api._retries_attempted = 1
        assert self.behaviour.current_state is not None
        self.behaviour.current_state.clean_up()
        assert self.behaviour.context.randomness_api._retries_attempted == 0


class TestSelectKeeperBehaviourTest(SimpleAbciFSMBehaviourBaseCase):
    """Test SelectKeeperBehaviour."""

    def test_select_keeper(
        self,
    ) -> None:
        """Test select keeper agent."""
        participants = frozenset({self.skill.skill_context.agent_address, "a_1", "a_2"})
        self.fast_forward_to_state(
            behaviour=self.behaviour,
            state_id=SelectKeeperAtStartupBehaviour.state_id,
            period_state=PeriodState(
                StateDB(
                    initial_period=0,
                    initial_data=dict(
                        participants=participants,
                        most_voted_randomness="56cbde9e9bbcbdcaf92f183c678eaa5288581f06b1c9c7f884ce911776727688",
                    ),
                )
            ),
        )
        assert (
            cast(
                BaseState,
                cast(BaseState, self.behaviour.current_state),
            ).state_id
            == SelectKeeperAtStartupBehaviour.state_id
        )
        self.behaviour.act_wrapper()
        self.mock_a2a_transaction()
        self._test_done_flag_set()

        statex = cast(
            BaseState,
            cast(BaseState, self.behaviour.current_state),
        ).state_id
        print(f"\n\n{statex}\n\n")

        self.end_round(Event.DONE)
        state = cast(BaseState, self.behaviour.current_state)
        assert state.state_id == ResetAndPauseBehaviour.state_id


class TestRegistrationBehaviour(SimpleAbciFSMBehaviourBaseCase):
    """Test case to test RegistrationBehaviour."""

    def test_registration(self) -> None:
        """Test registration."""
        self.fast_forward_to_state(
            self.behaviour,
            RegistrationBehaviour.state_id,
            SimpleAbciPeriodState(
                StateDB(initial_period=0, initial_data=dict()),
            ),
        )
        assert (
            cast(
                BaseState,
                cast(BaseState, self.behaviour.current_state),
            ).state_id
            == RegistrationBehaviour.state_id
        )
        self.behaviour.act_wrapper()
        self.mock_a2a_transaction()
        self._test_done_flag_set()

        self.end_round(Event.DONE)
        state = cast(BaseState, self.behaviour.current_state)
        assert state.state_id == RandomnessAtStartupBehaviour.state_id
