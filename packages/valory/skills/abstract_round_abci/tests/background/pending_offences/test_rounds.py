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

"""Test the pending offences background round."""

from calendar import timegm
from copy import deepcopy
from datetime import datetime
from unittest.mock import MagicMock

from hypothesis import given, settings
from hypothesis import strategies as st

from packages.valory.skills.abstract_round_abci.background.pending_offences.payloads import (
    PendingOffencesPayload,
)
from packages.valory.skills.abstract_round_abci.background.pending_offences.round import (
    PendingOffencesRound,
)
from packages.valory.skills.abstract_round_abci.base import (
    BaseSynchronizedData,
    OffenceStatus,
    OffenseType,
)
from packages.valory.skills.abstract_round_abci.test_tools.rounds import (
    BaseRoundTestClass,
    get_participants,
)
from packages.valory.skills.abstract_round_abci.tests.conftest import profile_name


settings.load_profile(profile_name)


class TestPendingOffencesRound(BaseRoundTestClass):
    """Tests for `PendingOffencesRound`."""

    _synchronized_data_class = BaseSynchronizedData

    @given(
        accused_agent_address=st.sampled_from(list(get_participants())),
        offense_round=st.integers(min_value=0),
        offense_type_value=st.sampled_from(
            [value.value for value in OffenseType.__members__.values()]
        ),
        last_transition_timestamp=st.floats(
            min_value=timegm(datetime(1971, 1, 1).utctimetuple()),
            max_value=timegm(datetime(8000, 1, 1).utctimetuple()) - 2000,
        ),
        time_to_live=st.floats(min_value=1, max_value=2000),
    )
    def test_run(
        self,
        accused_agent_address: str,
        offense_round: int,
        offense_type_value: int,
        last_transition_timestamp: float,
        time_to_live: float,
    ) -> None:
        """Run tests."""

        test_round = PendingOffencesRound(
            synchronized_data=self.synchronized_data,
            context=MagicMock(),
        )
        # initialize the offence status
        status_initialization = dict.fromkeys(self.participants, OffenceStatus())
        test_round.context.state.round_sequence.offence_status = status_initialization

        # create the actual and expected value
        actual = test_round.context.state.round_sequence.offence_status
        expected_invalid = offense_type_value == OffenseType.INVALID_PAYLOAD.value
        expected = deepcopy(status_initialization)

        first_payload, *payloads = [
            PendingOffencesPayload(
                sender,
                accused_agent_address,
                offense_round,
                offense_type_value,
                last_transition_timestamp,
                time_to_live,
            )
            for sender in self.participants
        ]

        test_round.process_payload(first_payload)
        assert test_round.collection == {first_payload.sender: first_payload}
        test_round.end_block()
        assert actual == expected

        for payload in payloads:
            test_round.process_payload(payload)
            test_round.end_block()

        expected[accused_agent_address].invalid_payload.add(expected_invalid)
        assert actual == expected
