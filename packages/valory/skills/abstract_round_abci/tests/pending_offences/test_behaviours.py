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

"""Tests the behaviours of the pending offences."""

from datetime import datetime
from pathlib import Path
from unittest import mock
from unittest.mock import MagicMock

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from packages.valory.skills.abstract_round_abci.background.pending_offences.behaviour import (
    PendingOffencesBehaviour,
)
from packages.valory.skills.abstract_round_abci.base import OffenseType, PendingOffense
from packages.valory.skills.abstract_round_abci.tests.conftest import profile_name


PACKAGE_DIR = Path(__file__).parents[3]
settings.load_profile(profile_name)


class TestPendingOffencesBehaviour:
    """Tests for `PendingOffencesBehaviour`."""

    behaviour: PendingOffencesBehaviour

    @classmethod
    def setup_class(cls) -> None:
        """Setup the test class."""
        cls.behaviour = PendingOffencesBehaviour(
            name="test",
            skill_context=MagicMock(),
        )

    @given(
        offence=st.builds(
            PendingOffense,
            accused_agent_address=st.text(),
            round_count=st.integers(min_value=0),
            offense_type=st.sampled_from(OffenseType),
            last_transition_timestamp=st.floats(
                min_value=datetime(2, 1, 1).timestamp(),
                max_value=datetime(8000, 1, 1).timestamp() - 2000,
            ),
            time_to_live=st.floats(min_value=1, max_value=2000),
        ),
        wait_ticks=st.integers(min_value=0, max_value=1000),
        expired=st.booleans(),
    )
    def test_pending_offences_act(
        self,
        offence: PendingOffense,
        wait_ticks: int,
        expired: bool,
    ) -> None:
        """Test `PendingOffencesBehaviour`."""
        offence_expiration = offence.last_transition_timestamp + offence.time_to_live
        offence_expiration += 1 if expired else -1
        self.behaviour.round_sequence.last_round_transition_timestamp = datetime.fromtimestamp(  # type: ignore
            offence_expiration
        )

        gen = self.behaviour.async_act()

        with mock.patch.object(
            self.behaviour,
            "send_a2a_transaction",
        ) as mock_send_a2a_transaction, mock.patch.object(
            self.behaviour,
            "wait_until_round_end",
        ) as mock_wait_until_round_end, mock.patch.object(
            self.behaviour,
            "set_done",
        ) as mock_set_done:

            # while pending offences are empty, the behaviour simply waits
            for _ in range(wait_ticks):
                next(gen)

            self.behaviour.round_sequence.pending_offences = {offence}

            with pytest.raises(StopIteration):
                next(gen)

            check = "assert_not_called" if expired else "assert_called_once"

            for mocked in (
                mock_send_a2a_transaction,
                mock_wait_until_round_end,
                mock_set_done,
            ):
                getattr(mocked, check)()
