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

"""Test the models.py module of the skill."""
from typing import Dict, Union

import pytest

from packages.valory.skills.apy_estimation_abci.models import (
    APYParams,
    MARGIN,
    SharedState,
)
from packages.valory.skills.apy_estimation_abci.rounds import (
    APYEstimationAbciApp,
    Event,
)


class TestSharedState:
    """Test SharedState(Model) class."""

    def test_setup(
        self,
        shared_state: SharedState,
    ) -> None:
        """Test setup."""
        shared_state.setup()
        assert (
            APYEstimationAbciApp.event_to_timeout[Event.ROUND_TIMEOUT]
            == shared_state.context.params.round_timeout_seconds
        )
        assert (
            APYEstimationAbciApp.event_to_timeout[Event.RESET_TIMEOUT]
            == shared_state.context.params.observation_interval + MARGIN
        )


class TestAPYParams:
    """Test `APYParams`"""

    @pytest.mark.parametrize("param_value", ("None", "not_an_int", 0))
    def test__validate_params(self, param_value: Union[str, int]) -> None:
        """Test `__validate_params`."""
        args = "test", "test"

        kwargs: Dict[str, Union[str, Dict[str, Union[str, int]]]] = {
            "tendermint_url": "test",
            "tendermint_com_url": "test",
            "reset_tendermint_after": "test",
            "ipfs_domain_name": "test",
            "consensus": {"max_participants": 0},
            "max_healthcheck": "test",
            "round_timeout_seconds": "test",
            "sleep_time": "test",
            "retry_attempts": "test",
            "retry_timeout": "test",
            "observation_interval": "test",
            "drand_public_key": "test",
            "history_duration": "test",
            "optimizer": {"timeout": param_value, "window_size": param_value},
            "testing": "test",
            "estimation": "test",
            "pair_ids": "test",
        }

        if param_value == "None":
            apy_params = APYParams(*args, **kwargs)
            assert apy_params.optimizer_params["timeout"] is None
            assert apy_params.optimizer_params["window_size"] is None
            return

        if not isinstance(param_value, int):
            with pytest.raises(ValueError):
                APYParams(*args, **kwargs)

            kwargs["optimizer"]["timeout"] = "None"  # type: ignore

            with pytest.raises(ValueError):
                APYParams(*args, **kwargs)

            return

        apy_params = APYParams(*args, **kwargs)
        assert apy_params.optimizer_params["timeout"] == param_value
        assert apy_params.optimizer_params["window_size"] == param_value
