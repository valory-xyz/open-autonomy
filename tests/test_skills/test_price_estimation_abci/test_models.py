# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021 Valory AG
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

"""Test the models.py module of the skill."""
from datetime import datetime
from typing import Optional, Tuple

from packages.valory.skills.abstract_round_abci.base import (
    AbstractRound,
    BasePeriodState,
)
from packages.valory.skills.price_estimation_abci.models import SharedState


DEPLOY_SAFE_STATE = "deploy_safe"
FINALIZE_STATE = "finalize"


class DummyContext:
    """Dummy Context class for shared state."""

    class params:
        """Dummy param variable."""

        keeper_timeout_seconds: float = 1.0


class ConcreteRound(AbstractRound):
    """A ConcreteRound for testing purposes."""

    def end_block(self) -> Optional[Tuple[BasePeriodState, "AbstractRound"]]:
        """Handle the end of the block."""


class TestSharedState:
    """Test SharedState(Model) class."""

    def test_initialization(
        self,
    ):
        """Test initialization."""
        SharedState(name="", skill_context=DummyContext())

    def test_reset_state_time(
        self,
    ):
        """Test `reset_state_time` method."""

        shared_state = SharedState(name="", skill_context=DummyContext())

        shared_state.reset_state_time(DEPLOY_SAFE_STATE)
        assert shared_state._state_start_times[DEPLOY_SAFE_STATE] is None

        shared_state.reset_state_time(FINALIZE_STATE)
        assert shared_state._state_start_times[FINALIZE_STATE] is None

    def test_set_state_time(
        self,
    ):
        """Test `set_state_time`."""

        shared_state = SharedState(name="", skill_context=DummyContext())

        shared_state.set_state_time(DEPLOY_SAFE_STATE)
        assert shared_state._state_start_times[DEPLOY_SAFE_STATE] is not None
        assert isinstance(shared_state._state_start_times[DEPLOY_SAFE_STATE], datetime)

        shared_state.set_state_time(FINALIZE_STATE)
        assert shared_state._state_start_times[FINALIZE_STATE] is not None
        assert isinstance(shared_state._state_start_times[FINALIZE_STATE], datetime)

    def test_has_keeper_timed_out(
        self,
    ):
        """Test `has_keeper_timed_out` method."""

        shared_state = SharedState(name="", skill_context=DummyContext())

        shared_state.set_state_time(DEPLOY_SAFE_STATE)
        assert not shared_state.has_keeper_timed_out(DEPLOY_SAFE_STATE)

        shared_state.set_state_time(FINALIZE_STATE)
        assert not shared_state.has_keeper_timed_out(FINALIZE_STATE)
