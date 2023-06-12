# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022-2023 Valory AG
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

"""This module contains the pending offences ever-running background behaviour."""

from dataclasses import asdict
from typing import Generator, Set, cast

from packages.valory.skills.abstract_round_abci.background.pending_offences.payloads import (
    PendingOffencesPayload,
)
from packages.valory.skills.abstract_round_abci.background.pending_offences.round import (
    PendingOffencesRound,
)
from packages.valory.skills.abstract_round_abci.base import (
    PendingOffense,
    RoundSequence,
)
from packages.valory.skills.abstract_round_abci.behaviour_utils import BaseBehaviour
from packages.valory.skills.abstract_round_abci.models import SharedState


class PendingOffencesBehaviour(BaseBehaviour):
    """A behaviour responsible for checking whether there are any pending offences."""

    matching_round = PendingOffencesRound

    @property
    def round_sequence(self) -> RoundSequence:
        """Get the round sequence from the shared state."""
        return cast(SharedState, self.context.state).round_sequence

    @property
    def pending_offences(self) -> Set[PendingOffense]:
        """Get the pending offences from the round sequence."""
        return self.round_sequence.pending_offences

    def has_pending_offences(self) -> bool:
        """Check if there are any pending offences."""
        return bool(len(self.pending_offences))

    def async_act(self) -> Generator:
        """
        Checks the pending offences.

        This behaviour simply checks if the set of pending offences is not empty.
        When it’s not empty, it pops the offence from the set, and sends it to the rest of the agents via a payload

        :return: None
        :yield: None
        """
        yield from self.wait_for_condition(self.has_pending_offences)
        offence = self.pending_offences.pop()
        offence_detected_log = (
            f"An offence of type {offence.offense_type.name} has been detected "
            f"for agent with address {offence.accused_agent_address} during round {offence.round_count}. "
        )
        offence_expiration = offence.last_transition_timestamp + offence.time_to_live
        last_timestamp = self.round_sequence.last_round_transition_timestamp

        if offence_expiration < last_timestamp.timestamp():
            ignored_log = "Offence will be ignored as it has expired."
            self.context.logger.info(offence_detected_log + ignored_log)
            return

        sharing_log = "Sharing offence with the other agents."
        self.context.logger.info(offence_detected_log + sharing_log)

        payload = PendingOffencesPayload(
            self.context.agent_address, *asdict(offence).values()
        )
        yield from self.send_a2a_transaction(payload)
        yield from self.wait_until_round_end()
        self.set_done()
