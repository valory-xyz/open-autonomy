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

# pylint: skip-file

from pathlib import Path
from typing import Callable, Generator, Optional
from unittest import mock
from unittest.mock import MagicMock

import pytest

from packages.valory.skills.abstract_round_abci.base import AbciAppDB
from packages.valory.skills.abstract_round_abci.base import (
    BaseSynchronizedData as ResetSynchronizedSata,
)
from packages.valory.skills.abstract_round_abci.behaviour_utils import (
    make_degenerate_behaviour,
)
from packages.valory.skills.abstract_round_abci.test_tools.base import (
    FSMBehaviourBaseCase,
)
from packages.valory.skills.reset_pause_abci import PUBLIC_ID
from packages.valory.skills.reset_pause_abci.behaviours import ResetAndPauseBehaviour
from packages.valory.skills.reset_pause_abci.rounds import Event as ResetEvent
from packages.valory.skills.reset_pause_abci.rounds import FinishedResetAndPauseRound


PACKAGE_DIR = Path(__file__).parent.parent


def test_skill_public_id() -> None:
    """Test skill module public ID"""

    assert PUBLIC_ID.name == Path(__file__).parents[1].name
    assert PUBLIC_ID.author == Path(__file__).parents[3].name


class ResetPauseAbciFSMBehaviourBaseCase(FSMBehaviourBaseCase):
    """Base case for testing PauseReset FSMBehaviour."""

    path_to_skill = PACKAGE_DIR


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
    next_behaviour_class = make_degenerate_behaviour(FinishedResetAndPauseRound)

    @pytest.mark.parametrize("tendermint_reset_status", (None, True, False))
    def test_reset_behaviour(
        self,
        tendermint_reset_status: Optional[bool],
    ) -> None:
        """Test reset behaviour."""

        self.fast_forward_to_behaviour(
            behaviour=self.behaviour,
            behaviour_id=self.behaviour_class.auto_behaviour_id(),
            synchronized_data=ResetSynchronizedSata(
                AbciAppDB(
                    setup_data=dict(
                        most_voted_estimate=[0.1],
                        tx_hashes_history=[["68656c6c6f776f726c64"]],
                    ),
                )
            ),
        )

        assert self.behaviour.current_behaviour is not None
        assert (
            self.behaviour.current_behaviour.behaviour_id
            == self.behaviour_class.auto_behaviour_id()
        )

        with mock.patch.object(
            self.behaviour.current_behaviour,
            "send_a2a_transaction",
            side_effect=self.behaviour.current_behaviour.send_a2a_transaction,
        ), mock.patch.object(
            self.behaviour.current_behaviour,
            "reset_tendermint_with_wait",
            side_effect=dummy_reset_tendermint_with_wait_wrapper(
                tendermint_reset_status
            ),
        ) as mock_reset_tendermint_with_wait, mock.patch.object(
            self.behaviour.current_behaviour,
            "wait_from_last_timestamp",
            side_effect=lambda _: (yield),
        ):
            if tendermint_reset_status is not None:
                # Increase the period_count to force the call to reset_tendermint_with_wait()
                self.behaviour.current_behaviour.synchronized_data.create()

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
                    self.behaviour.current_behaviour.send_a2a_transaction, MagicMock
                )
                self.behaviour.current_behaviour.send_a2a_transaction.assert_not_called()
                self.behaviour.act_wrapper()

        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round(ResetEvent.DONE)
        assert (
            self.behaviour.current_behaviour.behaviour_id
            == self.next_behaviour_class.auto_behaviour_id()
        )
