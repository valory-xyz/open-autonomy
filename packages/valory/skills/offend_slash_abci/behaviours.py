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

"""This module contains the behaviours for the 'offend_slash_abci' skill."""

from typing import Set, Type

from packages.valory.skills.abstract_round_abci.behaviours import (
    AbstractRoundBehaviour,
    BaseBehaviour,
)
from packages.valory.skills.offend_abci.behaviours import OffendRoundBehaviour
from packages.valory.skills.offend_slash_abci.composition import OffendSlashAbciApp
from packages.valory.skills.registration_abci.behaviours import (
    AgentRegistrationRoundBehaviour,
    RegistrationStartupBehaviour,
)
from packages.valory.skills.reset_pause_abci.behaviours import (
    ResetPauseABCIConsensusBehaviour,
)
from packages.valory.skills.slashing_abci.behaviours import (
    SlashingAbciBehaviours,
    SlashingCheckBehaviour,
)


class OffendSlashAbciAppConsensusBehaviour(AbstractRoundBehaviour):
    """This behaviour manages the consensus stages for the offend_slash_abci."""

    initial_behaviour_cls = RegistrationStartupBehaviour
    abci_app_cls = OffendSlashAbciApp
    behaviours: Set[Type[BaseBehaviour]] = {
        *AgentRegistrationRoundBehaviour.behaviours,
        *OffendRoundBehaviour.behaviours,
        *ResetPauseABCIConsensusBehaviour.behaviours,
        *SlashingAbciBehaviours.behaviours,
    }
    background_behaviours_cls = {SlashingCheckBehaviour}
