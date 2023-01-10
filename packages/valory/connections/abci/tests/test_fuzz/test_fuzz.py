# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2023 Valory AG
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

"""Fuzzy tests for valory/abci connection"""
import os
import platform

import pytest
from hypothesis import settings

from packages.valory.connections.abci import CI
from packages.valory.connections.abci.tests.test_fuzz.base import BaseFuzzyTests
from packages.valory.connections.abci.tests.test_fuzz.mock_node.channels.grpc_channel import (
    GrpcChannel,
)
from packages.valory.connections.abci.tests.test_fuzz.mock_node.channels.tcp_channel import (
    TcpChannel,
)


running_on_ci = os.getenv(CI)
if running_on_ci:
    settings.load_profile(CI)


@pytest.mark.skipif(
    platform.system() == "Windows",
    reason="<IocpProactor overlapped#=1175 result#=0> is running after closing for ... seconds (windows_events.py:871)",
)
class TestFuzzyGrpc(BaseFuzzyTests):
    """Test the connection when gRPC is used"""

    CHANNEL_TYPE = GrpcChannel
    USE_GRPC = True
    AGENT_TIMEOUT_SECONDS = 30


@pytest.mark.skipif(
    platform.system() == "Windows",
    reason="<IocpProactor overlapped#=1175 result#=0> is running after closing for ... seconds (windows_events.py:871)",
)
class TestFuzzyTcp(BaseFuzzyTests):
    """Test the connection when TCP is used"""

    CHANNEL_TYPE = TcpChannel
    USE_GRPC = False
    AGENT_TIMEOUT_SECONDS = 30
