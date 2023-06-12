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

"""This module contains the pending offences round."""

from typing import Any, Dict, cast

from packages.valory.skills.abstract_round_abci.background.pending_offences.payloads import (
    PendingOffencesPayload,
)
from packages.valory.skills.abstract_round_abci.base import (
    BaseSynchronizedData,
    CollectSameUntilThresholdRound,
    OffenceStatus,
    OffenseType,
    PendingOffense,
)
from packages.valory.skills.abstract_round_abci.models import SharedState


class PendingOffencesRound(CollectSameUntilThresholdRound):
    """Defines the pending offences background round, which runs concurrently with other rounds to sync the offences."""

    payload_class = PendingOffencesPayload
    synchronized_data_class = BaseSynchronizedData

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the `PendingOffencesRound`."""
        super().__init__(*args, **kwargs)
        self._latest_round_processed = -1

    @property
    def offence_status(self) -> Dict[str, OffenceStatus]:
        """Get the offence status from the round sequence."""
        return cast(SharedState, self.context.state).round_sequence.offence_status

    def end_block(self) -> None:
        """
        Process the end of the block for the pending offences background round.

        It is important to note that this is a non-standard type of round, meaning it does not emit any events.
        Instead, it continuously runs in the background.
        The objective of this round is to consistently monitor the received pending offences
        and achieve a consensus among the agents.
        """
        if not self.threshold_reached:
            return

        offence = PendingOffense(*self.most_voted_payload_values)

        # an offence should only be tracked once, not every time a payload is processed after the threshold is reached
        if self._latest_round_processed == offence.round_count:
            return

        # add synchronized offence to the offence status
        # only `INVALID_PAYLOAD` offence types are supported at the moment as pending offences:
        # https://github.com/valory-xyz/open-autonomy/blob/6831d6ebaf10ea8e3e04624b694c7f59a6d05bb4/packages/valory/skills/abstract_round_abci/handlers.py#L215-L222  # noqa
        invalid = offence.offense_type == OffenseType.INVALID_PAYLOAD
        self.offence_status[offence.accused_agent_address].invalid_payload.add(invalid)
        self._latest_round_processed = offence.round_count
