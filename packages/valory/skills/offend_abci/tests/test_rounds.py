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

"""Test the rounds of the skill."""

import json
from typing import Any, Dict
from unittest.mock import MagicMock

from packages.valory.skills.abstract_round_abci.base import (
    BaseSynchronizedData,
    OffenceStatus,
    OffenseStatusEncoder,
)
from packages.valory.skills.abstract_round_abci.test_tools.rounds import (
    BaseCollectSameUntilThresholdRoundTest,
)
from packages.valory.skills.offend_abci.payloads import OffencesPayload
from packages.valory.skills.offend_abci.rounds import Event, OffendRound


class TestOffendRound(BaseCollectSameUntilThresholdRoundTest):
    """Tests for OffendRound."""

    _synchronized_data_class = BaseSynchronizedData
    _event_class = Event

    @property
    def serialized_status(
        self,
    ) -> str:
        """Get a stub offence status, serialized."""
        status = {participant: OffenceStatus() for participant in self.participants}
        return json.dumps(status, cls=OffenseStatusEncoder, sort_keys=True)

    @property
    def participant_to_offend(
        self,
    ) -> Dict[str, OffencesPayload]:
        """Get participant to offend payload mapping."""
        return {
            participant: OffencesPayload(participant, self.serialized_status)
            for participant in self.participants
        }

    def test_run(self) -> None:
        """Runs test."""
        test_round = OffendRound(self.synchronized_data, MagicMock())

        def expected_update(
            synchronized_data: BaseSynchronizedData, _: Any
        ) -> BaseSynchronizedData:
            """Update the synchronized data as expected."""
            synchronized_data.slashing_config = self.serialized_status
            return synchronized_data

        self._complete_run(
            self._test_round(
                test_round=test_round,
                round_payloads=self.participant_to_offend,
                synchronized_data_update_fn=expected_update,
                synchronized_data_attr_checks=[
                    lambda _synchronized_data: _synchronized_data.slashing_config
                ],
                most_voted_payload=self.serialized_status,
                exit_event=Event.DONE,
            )
        )

    def test_no_majority_event(self) -> None:
        """Test the no-majority event."""
        test_round = OffendRound(self.synchronized_data, MagicMock())
        self._test_no_majority_event(test_round)
