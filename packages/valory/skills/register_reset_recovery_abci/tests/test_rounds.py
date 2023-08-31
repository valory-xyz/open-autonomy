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

"""Test the rounds of the skill."""

from copy import deepcopy
from unittest.mock import MagicMock

from packages.valory.skills.abstract_round_abci.base import BaseSynchronizedData
from packages.valory.skills.abstract_round_abci.test_tools.rounds import (
    BaseRoundTestClass as ExternalBaseRoundTestClass,
)
from packages.valory.skills.register_reset_recovery_abci.payloads import (
    RoundCountPayload,
)
from packages.valory.skills.register_reset_recovery_abci.rounds import (
    Event,
    RoundCountRound,
)


class BaseRoundTestClass(
    ExternalBaseRoundTestClass
):  # pylint: disable=too-few-public-methods
    """Base test class for Rounds."""

    _synchronized_data_class = BaseSynchronizedData
    _event_class = Event


class TestTerminationRound(BaseRoundTestClass):
    """Tests for TerminationRound."""

    def test_run(
        self,
    ) -> None:
        """Run tests."""

        test_round = RoundCountRound(
            synchronized_data=deepcopy(self.synchronized_data),
            context=MagicMock(),
        )
        payload_data = 1
        first_payload, *payloads = [
            RoundCountPayload(sender=participant, current_round_count=payload_data)
            for participant in self.participants
        ]

        test_round.process_payload(first_payload)
        assert test_round.collection == {first_payload.sender: first_payload}
        assert test_round.end_block() is None

        for payload in payloads:
            test_round.process_payload(payload)

        res = test_round.end_block()
        assert res is not None
        _, event = res

        assert event == Event.DONE
