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

"""Tests for valory/registration_abci skill's behaviours."""
from unittest.mock import MagicMock

from packages.valory.skills.register_reset_abci.behaviours import (
    RegisterResetAbciAppConsensusBehaviour,
)
from packages.valory.skills.register_reset_abci.composition import RegisterResetAbciApp
from packages.valory.skills.registration_abci.behaviours import (
    AgentRegistrationRoundBehaviour,
    RegistrationStartupBehaviour,
)
from packages.valory.skills.reset_pause_abci.behaviours import (
    ResetPauseABCIConsensusBehaviour,
)


def test_RegisterResetAbciAppConsensusBehaviour() -> None:
    """Test RegisterResetAbciAppConsensusBehaviour"""
    behaviour = RegisterResetAbciAppConsensusBehaviour(
        name="dummy_name", skill_context=MagicMock()
    )
    assert behaviour.initial_behaviour_cls == RegistrationStartupBehaviour
    assert behaviour.abci_app_cls == RegisterResetAbciApp
    assert behaviour.behaviours == {
        *AgentRegistrationRoundBehaviour.behaviours,
        *ResetPauseABCIConsensusBehaviour.behaviours,
    }
