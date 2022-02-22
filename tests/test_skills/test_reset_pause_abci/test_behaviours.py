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
import datetime
import json
import logging
import time
from pathlib import Path
from typing import Generator, cast
from unittest import mock

import pytest
from aea.exceptions import AEAActException

from packages.valory.skills.abstract_round_abci.base import (
    BasePeriodState as ResetPeriodState,
)
from packages.valory.skills.abstract_round_abci.base import StateDB
from packages.valory.skills.abstract_round_abci.behaviour_utils import (
    BaseState,
    make_degenerate_state,
)
from packages.valory.skills.reset_pause_abci.behaviours import (
    ResetAndPauseBehaviour,
    ResetBehaviour,
)
from packages.valory.skills.reset_pause_abci.rounds import Event as ResetEvent
from packages.valory.skills.reset_pause_abci.rounds import (
    FinishedResetAndPauseRound,
    FinishedResetRound,
)

from tests.conftest import ROOT_DIR
from tests.test_skills.base import FSMBehaviourBaseCase


class ResetPauseAbciFSMBehaviourBaseCase(FSMBehaviourBaseCase):
    """Base case for testing PauseReset FSMBehaviour."""

    path_to_skill = Path(ROOT_DIR, "packages", "valory", "skills", "reset_pause_abci")


class TestResetAndPauseBehaviour(ResetPauseAbciFSMBehaviourBaseCase):
    """Test ResetBehaviour."""

    behaviour_class = ResetAndPauseBehaviour
    next_behaviour_class = make_degenerate_state(FinishedResetAndPauseRound.round_id)

    def test_reset_behaviour(
        self,
    ) -> None:
        """Test reset behaviour."""
        self.fast_forward_to_state(
            behaviour=self.behaviour,
            state_id=self.behaviour_class.state_id,
            period_state=ResetPeriodState(
                StateDB(
                    initial_period=0,
                    initial_data=dict(
                        most_voted_estimate=0.1,
                        tx_hashes_history=["68656c6c6f776f726c64"],
                    ),
                )
            ),
        )
        assert (
            cast(
                BaseState,
                cast(BaseState, self.behaviour.current_state),
            ).state_id
            == self.behaviour_class.state_id
        )
        with mock.patch(
            "packages.valory.skills.abstract_round_abci.base.AbciApp.last_timestamp",
            new_callable=mock.PropertyMock,
        ) as pmock:
            pmock.return_value = datetime.datetime.now()
            self.behaviour.context.params.observation_interval = 0.1
            self.behaviour.act_wrapper()
            time.sleep(0.3)
            self.behaviour.act_wrapper()
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round(ResetEvent.DONE)
        state = cast(BaseState, self.behaviour.current_state)
        assert state.state_id == self.next_behaviour_class.state_id

    def _tendermint_reset(
        self, reset_response: bytes, status_response: bytes
    ) -> Generator:
        """Test reset behaviour."""
        self.fast_forward_to_state(
            behaviour=self.behaviour,
            state_id=self.behaviour_class.state_id,
            period_state=ResetPeriodState(
                StateDB(
                    initial_period=2,
                    initial_data=dict(
                        most_voted_estimate=0.1,
                        tx_hashes_history=["68656c6c6f776f726c64"],
                    ),
                )
            ),
        )
        assert (
            cast(
                BaseState,
                cast(BaseState, self.behaviour.current_state),
            ).state_id
            == self.behaviour_class.state_id
        )
        with mock.patch(
            "packages.valory.skills.abstract_round_abci.base.AbciApp.last_timestamp",
            new_callable=mock.PropertyMock,
        ) as pmock:
            pmock.return_value = datetime.datetime.now()
            self.behaviour.context.params.observation_interval = 0.1
            self.behaviour.act_wrapper()
            time.sleep(0.3)
            self.behaviour.act_wrapper()
            self.behaviour.act_wrapper()
            self.mock_http_request(
                request_kwargs=dict(
                    method="GET",
                    url=self.skill.skill_context.params.tendermint_com_url
                    + "/hard_reset",
                    headers="",
                    version="",
                    body=b"",
                ),
                response_kwargs=dict(
                    version="",
                    status_code=500,
                    status_text="",
                    headers="",
                    body=reset_response,
                ),
            )
            yield

            self.mock_http_request(
                request_kwargs=dict(
                    method="GET",
                    url=self.skill.skill_context.params.tendermint_url + "/status",
                    headers="",
                    version="",
                    body=b"",
                ),
                response_kwargs=dict(
                    version="",
                    status_code=200,
                    status_text="",
                    headers="",
                    body=status_response,
                ),
            )
            yield

            time.sleep(0.3)
            self.behaviour.act_wrapper()
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round(ResetEvent.DONE)
        state = cast(BaseState, self.behaviour.current_state)
        assert state.state_id == self.next_behaviour_class.state_id
        yield

    def test_reset_behaviour_with_tendermint_reset(
        self,
    ) -> None:
        """Test reset behaviour."""
        with mock.patch.object(self.behaviour.context.logger, "log") as mock_logger:
            test_runner = self._tendermint_reset(
                json.dumps(
                    {"message": "Tendermint reset was successful.", "status": True}
                ).encode(),
                json.dumps(
                    {
                        "result": {
                            "sync_info": {
                                "latest_block_height": self.behaviour.context.state.period.height
                            }
                        }
                    }
                ).encode(),
            )
            for _ in range(3):
                next(test_runner)
            mock_logger.assert_any_call(
                logging.INFO,
                "Tendermint reset was successful.",
            )

    def test_reset_behaviour_with_tendermint_reset_error_message(
        self,
    ) -> None:
        """Test reset behaviour with error message."""
        with mock.patch.object(self.behaviour.context.logger, "log") as mock_logger:
            test_runner = self._tendermint_reset(
                json.dumps(
                    {"message": "Error resetting tendermint.", "status": False}
                ).encode(),
                json.dumps(
                    {
                        "result": {
                            "sync_info": {
                                "latest_block_height": self.behaviour.context.state.period.height
                            }
                        }
                    }
                ).encode(),
            )
            for _ in range(1):
                next(test_runner)
            mock_logger.assert_any_call(
                logging.ERROR,
                "Error resetting: Error resetting tendermint.",
            )

    def test_reset_behaviour_with_tendermint_reset_wrong_response(
        self,
    ) -> None:
        """Test reset behaviour with wrong response."""
        with mock.patch.object(self.behaviour.context.logger, "log") as mock_logger:
            test_runner = self._tendermint_reset(
                b"",
                b"",
            )
            for _ in range(1):
                next(test_runner)
            mock_logger.assert_any_call(
                logging.ERROR,
                "Error communicating with tendermint com server.",
            )

    def test_timeout_expired(
        self,
    ) -> None:
        """Test reset behaviour with wrong response."""
        self.fast_forward_to_state(
            behaviour=self.behaviour,
            state_id=self.behaviour_class.state_id,
            period_state=ResetPeriodState(
                StateDB(
                    initial_period=2,
                    initial_data=dict(
                        most_voted_estimate=0.1,
                        tx_hashes_history=["68656c6c6f776f726c64"],
                    ),
                )
            ),
        )
        assert (
            cast(
                BaseState,
                cast(BaseState, self.behaviour.current_state),
            ).state_id
            == self.behaviour_class.state_id
        )
        with mock.patch.object(
            self.behaviour.current_state,
            "_is_timeout_expired",
            return_value=True,
        ):
            with pytest.raises(AEAActException):
                self.behaviour.act_wrapper()

    def test_reset_behaviour_with_tendermint_transaction_error(
        self,
    ) -> None:
        """Test reset behaviour with error message."""
        with mock.patch.object(self.behaviour.context.logger, "log") as mock_logger:
            test_runner = self._tendermint_reset(
                json.dumps({"message": "Reset Successful.", "status": True}).encode(),
                b"",
            )
            for _ in range(2):
                next(test_runner)
            mock_logger.assert_any_call(
                logging.ERROR,
                "Tendermint not accepting transactions yet, trying again!",
            )

    def test_reset_behaviour_with_block_height_dont_match(
        self,
    ) -> None:
        """Test reset behaviour with error message."""
        with mock.patch.object(self.behaviour.context.logger, "log") as mock_logger:
            test_runner = self._tendermint_reset(
                json.dumps({"message": "Reset Successful.", "status": True}).encode(),
                json.dumps(
                    {"result": {"sync_info": {"latest_block_height": -1}}}
                ).encode(),
            )
            for _ in range(2):
                next(test_runner)
            mock_logger.assert_any_call(
                logging.INFO,
                "local height != remote height; retrying...",
            )


class TestResetBehaviour(ResetPauseAbciFSMBehaviourBaseCase):
    """Test the reset behaviour."""

    behaviour_class = ResetBehaviour
    next_behaviour_class = make_degenerate_state(FinishedResetRound.round_id)

    def test_reset_behaviour(
        self,
    ) -> None:
        """Test reset behaviour."""
        self.fast_forward_to_state(
            behaviour=self.behaviour,
            state_id=self.behaviour_class.state_id,
            period_state=ResetPeriodState(
                StateDB(initial_period=0, initial_data=dict(estimate=1.0)),
            ),
        )
        assert (
            cast(
                BaseState,
                cast(BaseState, self.behaviour.current_state),
            ).state_id
            == self.behaviour_class.state_id
        )
        self.behaviour.context.params.observation_interval = 0.1
        self.behaviour.act_wrapper()
        time.sleep(0.3)
        self.behaviour.act_wrapper()
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round(ResetEvent.DONE)
        state = cast(BaseState, self.behaviour.current_state)
        assert state.state_id == self.next_behaviour_class.state_id
