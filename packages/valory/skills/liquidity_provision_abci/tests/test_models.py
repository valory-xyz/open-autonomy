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

"""Test the models.py module of the skill."""

# pylint: skip-file

from unittest.mock import MagicMock

from packages.valory.skills.abstract_round_abci.test_tools.base import DummyContext
from packages.valory.skills.liquidity_provision_abci.composition import (
    LiquidityProvisionAbciApp,
)
from packages.valory.skills.liquidity_provision_abci.models import SharedState
from packages.valory.skills.liquidity_rebalancing_abci.rounds import Event


class TestSharedState:
    """Test SharedState(Model) class."""

    def test_initialization(
        self,
    ) -> None:
        """Test initialization."""
        SharedState(name="", skill_context=DummyContext())

    def test_setup(
        self,
        shared_state: SharedState,
    ) -> None:
        """Test setup."""
        shared_state.context.params.setup_params = {"test": []}
        shared_state.context.params.consensus_params = MagicMock()
        shared_state.setup()
        assert (
            LiquidityProvisionAbciApp.event_to_timeout[Event.ROUND_TIMEOUT]
            == shared_state.context.params.round_timeout_seconds
        )
