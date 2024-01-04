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
from typing import Dict
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
    def status(
        self,
    ) -> Dict[str, OffenceStatus]:
        """Get a stub offence status."""
        return {participant: OffenceStatus() for participant in self.participants}

    @property
    def serialized_status(
        self,
    ) -> str:
        """Get a stub offence status, serialized."""
        return json.dumps(self.status, cls=OffenseStatusEncoder, sort_keys=True)

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
        context_mock = MagicMock()
        context_mock.state.round_sequence.offence_status = None
        test_round = OffendRound(self.synchronized_data, context_mock)

        self._complete_run(
            self._test_round(
                test_round=test_round,
                round_payloads=self.participant_to_offend,
                synchronized_data_update_fn=lambda _synchronized_data, _: _synchronized_data,
                synchronized_data_attr_checks=[],
                most_voted_payload=self.serialized_status,
                exit_event=Event.DONE,
            )
        )

        assert context_mock.state.round_sequence.offence_status == self.status

    def test_no_majority_event(self) -> None:
        """Test the no-majority event."""
        test_round = OffendRound(self.synchronized_data, MagicMock())
        self._test_no_majority_event(test_round)
