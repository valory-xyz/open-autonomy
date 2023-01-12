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
# pylint: disable=protected-access,attribute-defined-outside-init

"""Tests for ipfs connection."""
import asyncio
import logging
import os
import tempfile
from typing import Dict, Iterator, List, Optional
from unittest import mock
from unittest.mock import MagicMock

import pytest
from _pytest.logging import LogCaptureFixture
from aea.configurations.base import ConnectionConfig
from aea.connections.base import ConnectionStates
from aea.mail.base import Envelope
from aea_cli_ipfs.exceptions import DownloadError
from aea_cli_ipfs.ipfs_utils import IPFSDaemon, IPFSTool

from packages.valory.connections.ipfs.connection import (
    CONNECTION_ID,
    IpfsConnection,
    IpfsDialogues,
)
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
        self.dummy_msg = IpfsMessage(performative=IpfsMessage.Performative.GET_FILES)  # type: ignore
        self.dummy_envelope = Envelope(
            to=str(CONNECTION_ID), sender=ANY_SKILL, message=self.dummy_msg
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
            self.connection.response_envelopes  # pylint: disable=pointless-statement

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
        dummy_msg = IpfsMessage(performative=performative)
        envelope = Envelope(to=str(CONNECTION_ID), sender=ANY_SKILL, message=dummy_msg)
        with mock.patch.object(IpfsConnection, "run_async", return_value=MagicMock()):
            self.connection._handle_envelope(envelope)
            if expected_error:
                with caplog.at_level(logging.ERROR):
                    err = f"Performative `{performative.value}` is not supported."
                    assert err in caplog.text

    @pytest.mark.asyncio
    async def test_send(self) -> None:
        """Test send."""
        await self.connection.connect()
        with mock.patch.object(
            IpfsConnection,
            "_handle_envelope",
            return_value=MagicMock(add_done_callback=lambda *_: _),
        ):
            assert len(self.connection.task_to_request) == 0
            await self.connection.send(self.dummy_envelope)
            assert len(self.connection.task_to_request) == 1

    @pytest.mark.asyncio
    async def test_receive(self) -> None:
        """Tests receive."""
        await self.connection.connect()
        expected_envelope = self.dummy_envelope
        self.connection.response_envelopes.put_nowait(expected_envelope)
        actual_envelope = await self.connection.receive()

        assert expected_envelope == actual_envelope

    @pytest.mark.asyncio
    async def test_handle_done_task(self) -> None:
        """Test _handle_done_tasks."""
        await self.connection.connect()
        assert self.connection.response_envelopes.qsize() == 0
        dummy_task = MagicMock(result=lambda: self.dummy_msg)
        dummy_request = MagicMock(to=ANY_SKILL, sender=str(CONNECTION_ID), context=None)
        self.connection.task_to_request[dummy_task] = dummy_request
        self.connection._handle_done_task(dummy_task)
        assert self.connection.response_envelopes.qsize() == 1

    def test_handle_error(self) -> None:
        """Test handle_error."""
        message = self.connection._handle_error(
            reason="dummy reason",
            dialogue=MagicMock(),
        )
        assert message is not None

    @pytest.mark.asyncio
    async def test_run_async(self, caplog: LogCaptureFixture) -> None:
        """Test run async."""
        dummy_log = "dummy operation is being performed"

        def dummy_operation() -> None:
            """A dummy handler."""
            self.connection.logger.info(dummy_log)

        await self.connection.connect()
        task = self.connection.run_async(dummy_operation)
        assert task is not None

        # give some time for the task to be scheduled and run
        await asyncio.sleep(1)
        assert dummy_log in caplog.text

    @pytest.mark.parametrize(
        ("files", "expected_log"),
        [
            ({}, "No files were present."),
            (
                {"dummy_filename": "dummy_content"},
                "Successfully stored files with hash: ",
            ),
            (
                {
                    "dummy_dir/dummy_filename1": "dummy_content",
                    "dummy_dir/dummy_filename2": "dummy_content",
                },
                "Successfully stored files with hash: ",
            ),
            (
                {
                    "dummy_dir1/dummy_filename1": "dummy_content",
                    "dummy_dir2/dummy_filename2": "dummy_content",
                },
                "If you want to send multiple files as a single dir, "
                "make sure the their path matches to one directory only.",
            ),
        ],
    )
    def test_handle_store_files(
        self, files: Dict[str, str], expected_log: str, caplog: LogCaptureFixture
    ) -> None:
        """Test _handle_store_files."""
        message = IpfsMessage(
            performative=IpfsMessage.Performative.STORE_FILES, files=files  # type: ignore
        )
        dialogue = MagicMock()
        message = self.connection._handle_store_files(message, dialogue)
        assert message is not None
        assert expected_log in caplog.text

    @pytest.mark.parametrize(
        ("extra_files", "download_side_effect", "is_dir"),
        [
            ([], None, False),
            (["dummy_unexpected_extra_file"], None, False),
            ([], DownloadError, False),
            ([], None, True),
        ],
    )
    def test_handle_get_files(
        self,
        extra_files: List[str],
        download_side_effect: Optional[Exception],
        is_dir: bool,
    ) -> None:
        """Test _handle_get_files"""
        with tempfile.NamedTemporaryFile() as tmp_file, mock.patch.object(
            os,
            "listdir",
        ) as mock_listdir, mock.patch.object(
            IPFSTool, "download", side_effect=download_side_effect
        ):
            listdir_value = [extra_files + [tmp_file.name]]
            if is_dir:
                listdir_value = [["/tmp"]] + listdir_value
            mock_listdir.side_effect = listdir_value

            tmp_file.write(b"dummy_data")
            tmp_file.flush()

            _, ipfs_hash, _ = self.connection.ipfs_tool.add(tmp_file.name)
            message = IpfsMessage(
                performative=IpfsMessage.Performative.GET_FILES, ipfs_hash=ipfs_hash  # type: ignore
            )
            dialogue = MagicMock()
            message = self.connection._handle_get_files(message, dialogue)
            assert message is not None

    def test_ipfs_dialogue(self) -> None:  # pylint: disable=no-self-use
        """Test 'IpfsDialogues' creation."""
        dialogues = IpfsDialogues(connection_id=str(CONNECTION_ID))
        dialogues.create(
            counterparty=ANY_SKILL,
            performative=IpfsMessage.Performative.GET_FILES,
        )
