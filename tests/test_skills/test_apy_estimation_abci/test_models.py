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

"""Test the models.py module of the skill."""
from typing import Dict, Union
from unittest.mock import MagicMock

import pytest

from packages.valory.skills.apy_estimation_abci.models import APYParams, SharedState
from packages.valory.skills.apy_estimation_abci.rounds import APYEstimationAbciApp


class TestSharedState:
    """Test SharedState(Model) class."""

    def test_setup(
        self,
        shared_state: SharedState,
    ) -> None:
        """Test setup."""
        shared_state.context.params.setup_params = {"test": []}
        shared_state.context.params.consensus_params = MagicMock()
        shared_state.setup()
        assert shared_state.abci_app_cls == APYEstimationAbciApp


class TestAPYParams:
    """Test `APYParams`"""

    @pytest.mark.parametrize("param_value", (None, "not_an_int", 0))
    def test__validate_params(self, param_value: Union[str, int]) -> None:
        """Test `__validate_params`."""
        args = "test", "test"

        kwargs: Dict[str, Union[str, int, float, Dict[str, Union[str, int]]]] = {
            "tendermint_url": "test",
            "tendermint_com_url": "test",
            "tendermint_check_sleep_delay": "test",
            "tendermint_max_retries": "test",
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
            "history_interval_in_unix": 86400,
            "history_start": 1652544875,
            "optimizer": {"timeout": param_value, "window_size": param_value},
            "testing": "test",
            "estimation": "test",
            "pair_ids": "test",
            "service_id": "apy_estimation",
            "service_registry_address": "0xa51c1fc2f0d1a1b8494ed1fe312d7c3a78ed91c0",
            "keeper_timeout": 30.0,
            "cleanup_history_depth": 0,
        }

        if param_value == None:  # noqa: E711
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
