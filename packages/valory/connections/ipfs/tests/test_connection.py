# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023 Valory AG
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

"""Tests for ipfs connection."""
import logging
from typing import Iterator
from unittest import mock
from unittest.mock import MagicMock

import pytest
from _pytest.logging import LogCaptureFixture
from aea.configurations.base import ConnectionConfig
from aea.connections.base import ConnectionStates
from aea.mail.base import Envelope
from aea_cli_ipfs.ipfs_utils import IPFSDaemon

from packages.valory.connections.ipfs.connection import IpfsConnection, CONNECTION_ID
from packages.valory.protocols.ipfs import IpfsMessage


@pytest.fixture(scope="module")
def ipfs_daemon() -> Iterator[bool]:
    """Starts an IPFS daemon for the tests."""
    print("Starting IPFS daemon...")
    daemon = IPFSDaemon()
    daemon.start()
    yield daemon.is_started()
    print("Tearing down IPFS daemon...")
    daemon.stop()

use_ipfs_daemon = pytest.mark.usefixtures("ipfs_daemon")
LOCAL_IPFS = "/dns/localhost/tcp/5001/http"
ANY_SKILL = "skill/any:0.1.0"
@use_ipfs_daemon
class TestIpfsConnection:
    """Tests for IpfsConnection"""
    def setup(self) -> None:
        """Set up the tests."""
        configuration = ConnectionConfig(
            ipfs_domain=LOCAL_IPFS,
            connection_id=IpfsConnection.connection_id,
        )
        self.connection = IpfsConnection(
            configuration=configuration,
            data_dir=MagicMock(),
        )
    @pytest.mark.asyncio
    async def test_connect(self) -> None:
        """Test connect"""
        await self.connection.connect()
        assert self.connection.response_envelopes is not None
        assert self.connection.state == ConnectionStates.connected

    @pytest.mark.asyncio
    async def test_disconnect(self) -> None:
        """Test disconnect"""
        await self.connection.connect()
        await self.connection.disconnect()
        assert self.connection.state == ConnectionStates.disconnected
        with pytest.raises(ValueError):
            self.connection.response_envelopes
    @pytest.mark.parametrize(
        ("performative", "expected_error"),
        [
            (IpfsMessage.Performative.GET_FILES, False),
            (IpfsMessage.Performative.STORE_FILES, False),
            (IpfsMessage.Performative.IPFS_HASH, True),
            (IpfsMessage.Performative.FILES, True),
        ],
    )
    def test_handle_envelope(
        self,
        performative: IpfsMessage.Performative,
        expected_error: bool,
        caplog: LogCaptureFixture,
    ) -> None:
        """Tests for _handle_envelope."""
        dummy_msg = IpfsMessage(
            performative=performative
        )
        envelope = Envelope(to=str(CONNECTION_ID), sender=ANY_SKILL, message=dummy_msg)
        with mock.patch.object(
            IpfsConnection,
            "run_async",
            return_value=MagicMock()
        ):
            self.connection._handle_envelope(envelope)
            if expected_error:
                with caplog.at_level(logging.ERROR):
                    err = f"Performative `{performative.value}` is not supported."
                    assert err in caplog.text
