# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2026 Valory AG
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

"""Tests for the funds_forwarder_abci models."""

from packages.valory.skills.abstract_round_abci.models import (
    BenchmarkTool as BaseBenchmarkTool,
)
from packages.valory.skills.abstract_round_abci.models import BaseParams
from packages.valory.skills.abstract_round_abci.models import Requests as BaseRequests
from packages.valory.skills.funds_forwarder_abci.models import (
    ZERO_ADDRESS,
    BenchmarkTool,
    FundsForwarderParams,
    Requests,
    SharedState,
)
from packages.valory.skills.funds_forwarder_abci.rounds import FundsForwarderAbciApp


class TestModelAliases:
    """Test module-level model aliases."""

    def test_requests_alias(self) -> None:
        """Test Requests is aliased correctly."""
        assert Requests is BaseRequests

    def test_benchmark_tool_alias(self) -> None:
        """Test BenchmarkTool is aliased correctly."""
        assert BenchmarkTool is BaseBenchmarkTool


class TestSharedState:
    """Test SharedState."""

    def test_abci_app_cls(self) -> None:
        """Test abci_app_cls is set correctly."""
        assert SharedState.abci_app_cls is FundsForwarderAbciApp


class TestFundsForwarderParams:
    """Test FundsForwarderParams."""

    def test_is_subclass(self) -> None:
        """Test it is a subclass of BaseParams."""
        assert issubclass(FundsForwarderParams, BaseParams)

    def test_init_parses_token_limits(self) -> None:
        """Test that __init__ parses token limits."""
        from unittest.mock import MagicMock, patch

        token_limits = {"0xToken": {"retain_balance": 100, "max_transfer": 50}}
        mock_self = MagicMock(spec=FundsForwarderParams)
        mock_self._ensure = MagicMock(
            side_effect=lambda key, kwargs, type_=None: kwargs.pop(key)
        )
        mock_self._validate_token_limits = (
            FundsForwarderParams._validate_token_limits.__get__(mock_self)
        )
        kwargs = {
            "expected_service_owner_address": "0xOwner",
            "funds_forwarder_token_config": token_limits,
        }
        with patch.object(BaseParams, "__init__", return_value=None):
            FundsForwarderParams.__init__(mock_self, **kwargs)
        assert mock_self.funds_forwarder_token_config == token_limits

    def test_min_transfer_greater_than_max_transfer_raises(self) -> None:
        """Test that min_transfer > max_transfer raises ValueError."""
        import pytest
        from unittest.mock import MagicMock, patch

        bad_limits = {
            "0xToken": {
                "retain_balance": 100,
                "min_transfer": 200,
                "max_transfer": 50,
            }
        }
        mock_self = MagicMock(spec=FundsForwarderParams)
        mock_self._ensure = MagicMock(
            side_effect=lambda key, kwargs, type_=None: kwargs.pop(key)
        )
        mock_self._validate_token_limits = (
            FundsForwarderParams._validate_token_limits.__get__(mock_self)
        )
        kwargs = {
            "expected_service_owner_address": "0xOwner",
            "funds_forwarder_token_config": bad_limits,
        }
        with pytest.raises(ValueError, match="min_transfer.*> max_transfer"):
            with patch.object(BaseParams, "__init__", return_value=None):
                FundsForwarderParams.__init__(mock_self, **kwargs)


class TestZeroAddress:
    """Test ZERO_ADDRESS constant."""

    def test_zero_address(self) -> None:
        """Test zero address is correctly defined."""
        assert ZERO_ADDRESS == "0x0000000000000000000000000000000000000000"
