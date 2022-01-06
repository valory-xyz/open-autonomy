# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021 Valory AG
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

"""Tests for valory/registration_abci skill's behaviours."""

import datetime
import json
import logging
import time
from pathlib import Path
from typing import cast
from unittest.mock import patch

import pytest
from aea.exceptions import AEAActException

from packages.valory.skills.abstract_round_abci.base import StateDB
from packages.valory.skills.abstract_round_abci.behaviour_utils import BaseState
from packages.valory.skills.price_estimation_abci.behaviours import ObserveBehaviour
from packages.valory.skills.registration_abci.behaviours import (
    RegistrationBaseBehaviour,
    RegistrationBehaviour,
    RegistrationStartupBehaviour,
    TendermintHealthCheckBehaviour,
)
from packages.valory.skills.registration_abci.rounds import (
    BasePeriodState as RegistrationPeriodState,
)
from packages.valory.skills.registration_abci.rounds import Event
from packages.valory.skills.safe_deployment_abci.behaviours import (
    RandomnessSafeBehaviour,
)

from tests.conftest import ROOT_DIR
from tests.test_skills.base import FSMBehaviourBaseCase


class RegistrationAbciBaseCase(FSMBehaviourBaseCase):
    """Base case for testing RegistrationAbci FSMBehaviour."""

    path_to_skill = Path(
        ROOT_DIR, "packages", "valory", "skills", "price_estimation_abci"
    )  # TOFIX


class TestTendermintHealthcheckBehaviour(RegistrationAbciBaseCase):
    """Test case to test TendermintHealthcheckBehaviour."""

    def test_tendermint_healthcheck_not_live(self) -> None:
        """Test the tendermint health check does not finish if not healthy."""
        assert (
            cast(
                BaseState,
                cast(BaseState, self.behaviour.current_state),
            ).state_id
            == TendermintHealthCheckBehaviour.state_id
        )
        self.behaviour.act_wrapper()

        with patch.object(self.behaviour.context.logger, "log") as mock_logger:
            self.mock_http_request(
                request_kwargs=dict(
                    method="GET",
                    url=self.skill.skill_context.params.tendermint_url + "/health",
                    headers="",
                    version="",
                    body=b"",
                ),
                response_kwargs=dict(
                    version="",
                    status_code=500,
                    status_text="",
                    headers="",
                    body=b"",
                ),
            )
        mock_logger.assert_any_call(
            logging.ERROR,
            "Tendermint not running yet, trying again!",
        )
        time.sleep(1)
        self.behaviour.act_wrapper()

    def test_tendermint_healthcheck_not_live_raises(self) -> None:
        """Test the tendermint health check raises if not healthy for too long."""
        assert (
            cast(
                BaseState,
                cast(BaseState, self.behaviour.current_state),
            ).state_id
            == TendermintHealthCheckBehaviour.state_id
        )
        with patch.object(
            self.behaviour.current_state,
            "_is_timeout_expired",
            return_value=True,
        ):
            with pytest.raises(
                AEAActException, match="Tendermint node did not come live!"
            ):
                self.behaviour.act_wrapper()

    def test_tendermint_healthcheck_live_and_no_status(self) -> None:
        """Test the tendermint health check does finish if healthy."""
        assert (
            cast(
                BaseState,
                cast(BaseState, self.behaviour.current_state),
            ).state_id
            == TendermintHealthCheckBehaviour.state_id
        )
        self.behaviour.act_wrapper()
        self.mock_http_request(
            request_kwargs=dict(
                method="GET",
                url=self.skill.skill_context.params.tendermint_url + "/health",
                headers="",
                version="",
                body=b"",
            ),
            response_kwargs=dict(
                version="",
                status_code=200,
                status_text="",
                headers="",
                body=json.dumps({"status": 1}).encode("utf-8"),
            ),
        )
        with patch.object(self.behaviour.context.logger, "log") as mock_logger:
            self.mock_http_request(
                request_kwargs=dict(
                    method="GET",
                    url=self.skill.skill_context.params.tendermint_url + "/status",
                    headers="",
                    version="",
                    body=b"",
                ),
                response_kwargs=dict(
                    version="", status_code=500, status_text="", headers="", body=b""
                ),
            )
        mock_logger.assert_any_call(
            logging.ERROR, "Tendermint not accepting transactions yet, trying again!"
        )
        state = cast(BaseState, self.behaviour.current_state)
        assert state.state_id == TendermintHealthCheckBehaviour.state_id
        time.sleep(1)
        self.behaviour.act_wrapper()

    def test_tendermint_healthcheck_live_and_status(self) -> None:
        """Test the tendermint health check does finish if healthy."""
        assert (
            cast(
                BaseState,
                cast(BaseState, self.behaviour.current_state),
            ).state_id
            == TendermintHealthCheckBehaviour.state_id
        )
        self.behaviour.act_wrapper()
        self.mock_http_request(
            request_kwargs=dict(
                method="GET",
                url=self.skill.skill_context.params.tendermint_url + "/health",
                headers="",
                version="",
                body=b"",
            ),
            response_kwargs=dict(
                version="",
                status_code=200,
                status_text="",
                headers="",
                body=json.dumps({"status": 1}).encode("utf-8"),
            ),
        )
        with patch.object(self.behaviour.context.logger, "log") as mock_logger:
            current_height = self.behaviour.context.state.period.height
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
                    body=json.dumps(
                        {
                            "result": {
                                "sync_info": {"latest_block_height": current_height}
                            }
                        }
                    ).encode("utf-8"),
                ),
            )
        mock_logger.assert_any_call(logging.INFO, "local height == remote height; done")
        state = cast(BaseState, self.behaviour.current_state)
        assert state.state_id == RegistrationStartupBehaviour.state_id

    def test_tendermint_healthcheck_height_differs(self) -> None:
        """Test the tendermint health check does finish if local-height != remote-height."""
        assert (
            cast(
                BaseState,
                cast(BaseState, self.behaviour.current_state),
            ).state_id
            == TendermintHealthCheckBehaviour.state_id
        )
        cast(
            TendermintHealthCheckBehaviour,
            self.behaviour.current_state,
        )._check_started = datetime.datetime.now()
        cast(
            TendermintHealthCheckBehaviour,
            self.behaviour.current_state,
        )._is_healthy = True
        self.behaviour.act_wrapper()
        with patch.object(self.behaviour.context.logger, "log") as mock_logger:
            current_height = self.behaviour.context.state.period.height
            new_different_height = current_height + 1
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
                    body=json.dumps(
                        {
                            "result": {
                                "sync_info": {
                                    "latest_block_height": new_different_height
                                }
                            }
                        }
                    ).encode("utf-8"),
                ),
            )
        mock_logger.assert_any_call(
            logging.INFO, "local height != remote height; retrying..."
        )
        state = cast(BaseState, self.behaviour.current_state)
        assert state.state_id == TendermintHealthCheckBehaviour.state_id
        time.sleep(1)
        self.behaviour.act_wrapper()


class BaseRegistrationTestBehaviour(RegistrationAbciBaseCase):
    """Base test case to test RegistrationBehaviour."""

    behaviour_class = RegistrationBaseBehaviour
    next_behaviour_class = BaseState

    def test_registration(self) -> None:
        """Test registration."""
        self.fast_forward_to_state(
            self.behaviour,
            self.behaviour_class.state_id,
            RegistrationPeriodState(StateDB(initial_period=0, initial_data={})),
        )
        assert (
            cast(
                BaseState,
                cast(BaseState, self.behaviour.current_state),
            ).state_id
            == self.behaviour_class.state_id
        )
        self.behaviour.act_wrapper()
        self.mock_a2a_transaction()
        self._test_done_flag_set()

        self.end_round(Event.DONE)
        state = cast(BaseState, self.behaviour.current_state)
        assert state.state_id == self.next_behaviour_class.state_id


class TestRegistrationStartupBehaviour(BaseRegistrationTestBehaviour):
    """Test case to test RegistrationStartupBehaviour."""

    behaviour_class = RegistrationStartupBehaviour
    next_behaviour_class = RandomnessSafeBehaviour  # TOFIX


class TestRegistrationBehaviour(BaseRegistrationTestBehaviour):
    """Test case to test RegistrationBehaviour."""

    behaviour_class = RegistrationBehaviour
    next_behaviour_class = ObserveBehaviour  # TOFIX
