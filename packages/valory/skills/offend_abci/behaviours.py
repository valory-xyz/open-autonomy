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

"""This module contains the behaviours for the 'offend_abci' skill."""

import json
from copy import deepcopy
from typing import Dict, Generator, Set, Type, cast

from packages.valory.skills.abstract_round_abci.base import (
    NUMBER_OF_BLOCKS_TRACKED,
    NUMBER_OF_ROUNDS_TRACKED,
    OffenceStatus,
    OffenseStatusEncoder,
)
from packages.valory.skills.abstract_round_abci.behaviours import (
    AbstractRoundBehaviour,
    BaseBehaviour,
)
from packages.valory.skills.offend_abci.models import OffendParams, SharedState
from packages.valory.skills.offend_abci.payloads import OffencesPayload
from packages.valory.skills.offend_abci.rounds import OffendAbciApp, OffendRound


class OffendBehaviour(BaseBehaviour):
    """Simulate offences."""

    matching_round = OffendRound

    @property
    def shared_state(self) -> SharedState:
        """Get the round sequence from the shared state."""
        return cast(SharedState, self.context.state)

    @property
    def offence_status(self) -> Dict[str, OffenceStatus]:
        """Get the offence status from the round sequence."""
        return self.shared_state.round_sequence.offence_status

    @property
    def first_agent(self) -> str:
        """Short the agents' addresses and get the first address."""
        return sorted(self.shared_state.synchronized_data.all_participants)[0]

    @property
    def params(self) -> OffendParams:
        """Return the params."""
        return cast(OffendParams, self.context.params)

    def _updated_status(self) -> Dict[str, OffenceStatus]:
        """Return the offense status updated."""
        status_per_agent = deepcopy(self.offence_status)
        affected_agent = self.first_agent
        status = status_per_agent[affected_agent]

        if self.params.validator_downtime:
            for _ in range(NUMBER_OF_BLOCKS_TRACKED):
                status.validator_downtime.add(True)

        for _ in range(NUMBER_OF_ROUNDS_TRACKED):
            if self.params.invalid_payload:
                status.invalid_payload.add(True)
            if self.params.blacklisted:
                status.blacklisted.add(True)
            if self.params.suspected:
                status.suspected.add(True)

        status.num_unknown_offenses = self.params.num_unknown
        status.num_double_signed = self.params.num_double_signed
        status.num_light_client_attack = self.params.num_light_client_attack

        return status_per_agent

    def async_act(self) -> Generator:
        """Create offences."""
        updated_status = self._updated_status()
        serialized_status = json.dumps(
            updated_status, cls=OffenseStatusEncoder, sort_keys=True
        )
        payload = OffencesPayload(self.context.agent_address, serialized_status)
        yield from self.send_a2a_transaction(payload)
        yield from self.wait_until_round_end()
        self.set_done()


class OffendRoundBehaviour(AbstractRoundBehaviour):
    """This behaviour manages the consensus stages for the Offend abci app."""

    initial_behaviour_cls = OffendBehaviour
    abci_app_cls = OffendAbciApp
    behaviours: Set[Type[BaseBehaviour]] = {
        OffendBehaviour,  # type: ignore
    }
