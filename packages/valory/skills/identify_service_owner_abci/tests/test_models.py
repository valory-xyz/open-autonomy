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

"""Tests for the identify_service_owner_abci models."""

# pylint: disable=too-few-public-methods

from packages.valory.skills.abstract_round_abci.models import (
    BaseParams,
)
from packages.valory.skills.abstract_round_abci.models import (
    BenchmarkTool as BaseBenchmarkTool,
)
from packages.valory.skills.abstract_round_abci.models import Requests as BaseRequests
from packages.valory.skills.identify_service_owner_abci.models import (
    BenchmarkTool,
    IdentifyServiceOwnerParams,
    Requests,
    SharedState,
)
from packages.valory.skills.identify_service_owner_abci.rounds import (
    IdentifyServiceOwnerAbciApp,
)


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
        assert SharedState.abci_app_cls is IdentifyServiceOwnerAbciApp


class TestIdentifyServiceOwnerParams:
    """Test IdentifyServiceOwnerParams inherits from BaseParams."""

    def test_is_subclass(self) -> None:
        """Test it is a subclass of BaseParams."""
        assert issubclass(IdentifyServiceOwnerParams, BaseParams)
