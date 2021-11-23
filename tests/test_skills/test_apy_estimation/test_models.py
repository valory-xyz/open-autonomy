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

from packages.valory.skills.apy_estimation.models import MARGIN
from packages.valory.skills.apy_estimation.rounds import APYEstimationAbciApp
from packages.valory.skills.price_estimation_abci.rounds import Event


class TestSharedState:
    """Test SharedState(Model) class."""

    def test_setup(
            self,
            shared_state,
    ):
        """Test setup."""
        shared_state.setup()
        assert APYEstimationAbciApp.event_to_timeout[
                   Event.ROUND_TIMEOUT] == shared_state.context.params.round_timeout_seconds
        assert APYEstimationAbciApp.event_to_timeout[
                   Event.RESET_TIMEOUT] == shared_state.context.params.observation_interval + MARGIN
