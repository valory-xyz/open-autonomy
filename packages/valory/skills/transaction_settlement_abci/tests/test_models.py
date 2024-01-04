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
# pylint: disable=unused-import

"""Test the models.py module of the skill."""
from typing import Any, Dict
from unittest.mock import MagicMock

import pytest
import yaml
from aea.exceptions import AEAEnforceError

from packages.valory.skills.abstract_round_abci.test_tools.base import DummyContext
from packages.valory.skills.transaction_settlement_abci.models import (
    TransactionParams,
    _MINIMUM_VALIDATE_TIMEOUT,
)
from packages.valory.skills.transaction_settlement_abci.tests import PACKAGE_DIR


class TestTransactionParams:  # pylint: disable=too-few-public-methods
    """Test TransactionParams class."""

    default_config: Dict

    def setup_class(self) -> None:
        """Read the default config only once."""
        skill_yaml = PACKAGE_DIR / "skill.yaml"
        with open(skill_yaml, "r", encoding="utf-8") as skill_file:
            skill = yaml.safe_load(skill_file)
        self.default_config = skill["models"]["params"]["args"]

    def test_ensure_validate_timeout(  # pylint: disable=no-self-use
        self,
    ) -> None:
        """Test that `_ensure_validate_timeout` raises when `validate_timeout` is lower than the allowed minimum."""
        dummy_value = 0
        mock_args, mock_kwargs = (
            MagicMock(),
            {
                **self.default_config,
                "validate_timeout": dummy_value,
                "skill_context": DummyContext(),
            },
        )
        with pytest.raises(
            expected_exception=AEAEnforceError,
            match=f"`validate_timeout` must be greater than or equal to {_MINIMUM_VALIDATE_TIMEOUT}",
        ):
            TransactionParams(mock_args, **mock_kwargs)

    @pytest.mark.parametrize(
        "gas_params",
        [
            {},
            {"gas_price": 1},
            {"max_fee_per_gas": 1},
            {"max_priority_fee_per_gas": 1},
            {
                "gas_price": 1,
                "max_fee_per_gas": 1,
                "max_priority_fee_per_gas": 1,
            },
        ],
    )
    def test_gas_params(self, gas_params: Dict[str, Any]) -> None:
        """Test that gas params are being handled properly."""
        mock_args, mock_kwargs = (
            MagicMock(),
            {
                **self.default_config,
                "gas_params": gas_params,
                "skill_context": DummyContext(),
            },
        )
        params = TransactionParams(mock_args, **mock_kwargs)
        # verify that the gas params are being set properly
        for key, value in gas_params.items():
            assert getattr(params.gas_params, key) == value
