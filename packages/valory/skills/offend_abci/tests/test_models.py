# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023 Valory AG
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

from unittest.mock import MagicMock

from hypothesis import given, settings
from hypothesis import strategies as st

from packages.valory.skills.abstract_round_abci.tests.conftest import (
    irrelevant_config,
    profile_name,
)
from packages.valory.skills.offend_abci.models import OffendParams, SharedState
from packages.valory.skills.offend_abci.rounds import Event, OffendAbciApp


settings.load_profile(profile_name)


class TestModels:
    """Test the models."""

    @staticmethod
    def test_setup() -> None:
        """Test `SharedState`'s `setup`."""
        shared_state = SharedState(name="", skill_context=MagicMock())
        shared_state.context.params.setup_params = {"test": []}
        shared_state.setup()
        assert (
            OffendAbciApp.event_to_timeout[Event.ROUND_TIMEOUT]
            == shared_state.context.params.round_timeout_seconds
        )

    @staticmethod
    @given(
        offend_config=st.fixed_dictionaries(
            dict(
                validator_downtime=st.booleans(),
                invalid_payload=st.booleans(),
                blacklisted=st.booleans(),
                suspected=st.booleans(),
                num_unknown=st.integers(),
                num_double_signed=st.integers(),
                num_light_client_attack=st.integers(),
            )
        )
    )
    def test_init(offend_config: dict) -> None:
        """Test the initialization of the `OffendParams`."""
        base_config = dict(
            name="test",
            skill_context=MagicMock(),
            service_id="test",
        )
        params = OffendParams(
            **base_config,
            **offend_config,
            **irrelevant_config,
        )
        assert all(getattr(params, name) == val for name, val in offend_config.items())
