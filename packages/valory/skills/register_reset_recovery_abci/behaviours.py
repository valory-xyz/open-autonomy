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

"""This module contains the behaviours for the 'abci' skill."""

from typing import Set, Type, Generator, cast

from packages.valory.skills.abstract_round_abci.behaviours import (
    AbstractRoundBehaviour,
    BaseBehaviour,
)
from packages.valory.skills.register_reset_recovery_abci.composition import RegisterResetRecoveryAbciApp
from packages.valory.skills.register_reset_recovery_abci.models import SharedState
from packages.valory.skills.register_reset_recovery_abci.payloads import RoundCountPayload
from packages.valory.skills.register_reset_recovery_abci.rounds import RoundCountRound
from packages.valory.skills.registration_abci.behaviours import (
    AgentRegistrationRoundBehaviour,
    RegistrationStartupBehaviour,
)


class ShareRoundCountBehaviour(BaseBehaviour):
    """A dummy behaviour that sync the round count."""

    state_id = "share_round"
    behaviour_id = "share_round_behaviour"
    matching_round = RoundCountRound

    def async_act(self) -> Generator:
        """Simply logs the round count, and share it."""
        round_count: int = cast(
            SharedState, self.context.state
        ).synchronized_data.round_count

        self.context.logger.info(f"Current round count is {round_count}. ")
        payload = RoundCountPayload(sender=self.context.agent_address, current_round_count=round_count)

        yield from self.send_a2a_transaction(payload)
        yield from self.wait_until_round_end()
        self.set_done()


class RegisterResetRecoveryAbciAppConsensusBehaviour(AbstractRoundBehaviour):
    """This behaviour manages the consensus stages for the register-reset-recovery."""

    initial_behaviour_cls = RegistrationStartupBehaviour
    abci_app_cls = RegisterResetRecoveryAbciApp
    behaviours: Set[Type[BaseBehaviour]] = {
        *AgentRegistrationRoundBehaviour.behaviours,
        ShareRoundCountBehaviour,
    }
