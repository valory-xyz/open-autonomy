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

"""Tests for valory/termination_abci skill's behaviours."""

from pathlib import Path
from unittest.mock import MagicMock

from packages.valory.skills.register_termination_abci import PUBLIC_ID
from packages.valory.skills.register_termination_abci.behaviours import (
    RegisterTerminationAbciAppConsensusBehaviour,
)
from packages.valory.skills.register_termination_abci.composition import (
    RegisterTerminateAbciApp,
)
from packages.valory.skills.registration_abci.behaviours import (
    AgentRegistrationRoundBehaviour,
    RegistrationStartupBehaviour,
)
from packages.valory.skills.reset_pause_abci.behaviours import (
    ResetPauseABCIConsensusBehaviour,
)
from packages.valory.skills.termination_abci.behaviours import (
    BackgroundBehaviour,
    TerminationAbciBehaviours,
)


def test_skill_public_id() -> None:
    """Test skill module public ID"""

    # pylint: disable=no-member
    assert PUBLIC_ID.name == Path(__file__).parents[1].name
    assert PUBLIC_ID.author == Path(__file__).parents[3].name


def test_RegisterSafeTerminationAbciAppConsensusBehaviour() -> None:
    """Test RegisterSafeTerminationAbciAppConsensusBehaviour"""
    behaviour = RegisterTerminationAbciAppConsensusBehaviour(
        name="dummy_name", skill_context=MagicMock()
    )
    assert behaviour.initial_behaviour_cls == RegistrationStartupBehaviour
    assert behaviour.abci_app_cls == RegisterTerminateAbciApp
    assert behaviour.behaviours == {
        *AgentRegistrationRoundBehaviour.behaviours,
        *ResetPauseABCIConsensusBehaviour.behaviours,
        *TerminationAbciBehaviours.behaviours,
    }
    assert behaviour.background_behaviour_cls == BackgroundBehaviour
