# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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

"""Tests for valory/reset_pause_abci skill's behaviours."""
from pathlib import Path
from typing import Callable, Generator, Optional
from unittest import mock
from unittest.mock import MagicMock

import pytest

from packages.valory.skills.abstract_round_abci.base import AbciAppDB
from packages.valory.skills.abstract_round_abci.behaviour_utils import (
    make_degenerate_state,
)
from packages.valory.skills.reset_pause_abci.behaviours import ResetAndPauseBehaviour
from packages.valory.skills.reset_pause_abci.rounds import Event as ResetEvent
from packages.valory.skills.reset_pause_abci.rounds import FinishedResetAndPauseRound
from packages.valory.skills.reset_pause_abci.rounds import (
    SynchronizedData as ResetSynchronizedData,
)

from tests.conftest import ROOT_DIR
from tests.test_skills.base import FSMBehaviourBaseCase


class ResetPauseAbciFSMBehaviourBaseCase(FSMBehaviourBaseCase):
    """Base case for testing PauseReset FSMBehaviour."""

    path_to_skill = Path(ROOT_DIR, "packages", "valory", "skills", "reset_pause_abci")


def dummy_reset_tendermint_with_wait_wrapper(
    reset_successfully: Optional[bool],
) -> Callable[[], Generator[None, None, Optional[bool]]]:
    """Wrapper for a Dummy `reset_tendermint_with_wait` method."""

    def dummy_reset_tendermint_with_wait() -> Generator[None, None, Optional[bool]]:
        """Dummy `reset_tendermint_with_wait` method."""
        yield
        return reset_successfully

    return dummy_reset_tendermint_with_wait


class TestResetAndPauseBehaviour(ResetPauseAbciFSMBehaviourBaseCase):
    """Test ResetBehaviour."""

    behaviour_class = ResetAndPauseBehaviour
    next_behaviour_class = make_degenerate_state(FinishedResetAndPauseRound.round_id)

    @pytest.mark.parametrize("tendermint_reset_status", (None, True, False))
    def test_reset_behaviour(
        self,
        tendermint_reset_status: Optional[bool],
    ) -> None:
        """Test reset behaviour."""
        if tendermint_reset_status is None:
            initial_round = 0
        else:
            initial_round = 1

        self.fast_forward_to_state(
            behaviour=self.behaviour,
            state_id=self.behaviour_class.state_id,
            synchronized_data=ResetSynchronizedData(
                AbciAppDB(
                    initial_data=dict(
                        period_count=initial_round,
                        most_voted_estimate=0.1,
                        tx_hashes_history=["68656c6c6f776f726c64"],
                    ),
                )
            ),
        )
        assert self.behaviour.current_state is not None
        assert self.behaviour.current_state.state_id == self.behaviour_class.state_id

        with mock.patch.object(
            self.behaviour.current_state,
            "send_a2a_transaction",
            side_effect=self.behaviour.current_state.send_a2a_transaction,
        ), mock.patch.object(
            self.behaviour.current_state,
            "reset_tendermint_with_wait",
            side_effect=dummy_reset_tendermint_with_wait_wrapper(
                tendermint_reset_status
            ),
        ) as mock_reset_tendermint_with_wait, mock.patch.object(
            self.behaviour.current_state,
            "wait_from_last_timestamp",
            side_effect=lambda _: (yield),
        ):
            self.behaviour.act_wrapper()
            self.behaviour.act_wrapper()

            # now if the first reset attempt has been simulated to fail, let's simulate the second attempt to succeed.
            if tendermint_reset_status is not None and not tendermint_reset_status:
                mock_reset_tendermint_with_wait.side_effect = (
                    dummy_reset_tendermint_with_wait_wrapper(True)
                )
                self.behaviour.act_wrapper()
                # make sure that the behaviour does not send any txs to other agents when Tendermint reset fails
                assert isinstance(
                    self.behaviour.current_state.send_a2a_transaction, MagicMock
                )
                self.behaviour.current_state.send_a2a_transaction.assert_not_called()
                self.behaviour.act_wrapper()

        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round(ResetEvent.DONE)
        assert (
            self.behaviour.current_state.state_id == self.next_behaviour_class.state_id
        )
