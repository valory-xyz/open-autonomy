#!/usr/bin/env python3
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
"""Fuzzy tests for valory/abci connection"""
from unittest import TestCase

import pytest

from tests.test_connections.test_fuzz.base import BaseFuzzyTests
from tests.test_connections.test_fuzz.mock_node.channels.tcp_channel import TcpChannel


@pytest.mark.skip(reason="takes too long time to complete on CI")
class TcpFuzzyTests(BaseFuzzyTests, TestCase):
    """Test the connection when TCP is used"""

    CHANNEL_TYPE = TcpChannel
    AGENT_TIMEOUT = 30  # 3 seconds
