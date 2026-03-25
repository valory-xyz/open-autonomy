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
import os
import platform
import tempfile
from typing import Dict, List, Optional
from unittest import mock
from unittest.mock import MagicMock

import pytest
from aea.configurations.base import ConnectionConfig
from aea.connections.base import ConnectionStates
from aea.mail.base import Envelope
from aea_cli_ipfs.exceptions import DownloadError
from aea_cli_ipfs.ipfs_utils import IPFSTool
from aea_test_autonomy.fixture_helpers import (  # noqa: F401; pylint: disable=unused-import
    LOCAL_IPFS,
    ipfs_daemon,
    use_ipfs_daemon,
)

from packages.valory.connections.ipfs.connection import (
    IpfsConnection,
    IpfsDialogues,
    PUBLIC_ID,
)
from packages.valory.protocols.ipfs import IpfsMessage

ANY_SKILL = "skill/any:0.1.0"


@use_ipfs_daemon
class TestIpfsConnection:
    """Tests for IpfsConnection"""

    def setup_method(self) -> None:
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
            to=str(PUBLIC_ID), sender=ANY_SKILL, message=self.dummy_msg
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
    ) -> None:
        """Tests for _handle_envelope."""
        dummy_msg = IpfsMessage(performative=performative)
        envelope = Envelope(to=str(PUBLIC_ID), sender=ANY_SKILL, message=dummy_msg)
        with mock.patch.object(
            IpfsConnection,
            "run_async",
            return_value=MagicMock(),
        ), mock.patch.object(
            self.connection.logger,
            "error",
        ) as mock_logger:
            self.connection._handle_envelope(envelope)
            if expected_error:
                mock_logger.assert_called_with(
                    f"Performative `{performative.value}` is not supported."
                )

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
        dummy_request = MagicMock(to=ANY_SKILL, sender=str(PUBLIC_ID), context=None)
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
    async def test_run_async(self) -> None:
        """Test run async."""
        dummy_log = "dummy operation is being performed"

        def dummy_operation() -> None:
            """A dummy handler."""
            self.connection.logger.info(dummy_log)

        await self.connection.connect()
        with mock.patch.object(
            self.connection.logger,
            "info",
        ) as mock_logger:
            task = self.connection.run_async(dummy_operation)
            assert task is not None

            # give some time for the task to be scheduled and run
            await asyncio.sleep(1)
            mock_logger.assert_called_with(dummy_log)

    @pytest.mark.parametrize(
        ("files", "expected_log", "log_level"),
        [
            ({}, "No files were present.", "error"),
            (
                {"dummy_filename": "dummy_content"},
                "Successfully stored files with hash: QmYn1qHyFMDdVxYcwseLBdooLAyc3orNBH8vvj4iPTXd4R.",
                "debug",
            ),
            (
                {
                    "dummy_dir/dummy_filename1": "dummy_content",
                    "dummy_dir/dummy_filename2": "dummy_content",
                },
                "Successfully stored files with hash: QmRP7wK1NZKwno9CFxQUeFaJip5eaaLBo1v8WFtyECgLCz.",
                "debug",
            ),
            (
                {
                    "dummy_dir/dummy_dir_nested/dummy_filename1": "dummy_content",
                    "dummy_dir/dummy_dir_nested/dummy_filename2": "dummy_content",
                },
                "Successfully stored files with hash: QmcYhNziJDuwmRVg8TYY5S5fUycuBguM6zxukgMDnVQt8H.",
                "debug",
            ),
            (
                {
                    "dummy_dir1/dummy_filename1": "dummy_content",
                    "dummy_dir2/dummy_filename2": "dummy_content",
                },
                "If you want to send multiple files as a single dir, "
                "make sure the their path matches to one directory only.",
                "info",
            ),
        ],
    )
    def test_handle_store_files(
        self, files: Dict[str, str], expected_log: str, log_level: str
    ) -> None:
        """Test _handle_store_files."""
        with mock.patch.object(
            self.connection.logger,
            log_level,
        ) as mock_logger:
            message = IpfsMessage(
                performative=IpfsMessage.Performative.STORE_FILES, files=files  # type: ignore
            )
            dialogue = MagicMock()
            message = self.connection._handle_store_files(message, dialogue)
            assert message is not None
            mock_logger.assert_called_with(expected_log)

    @pytest.mark.skipif(
        platform.system() == "Windows",
        reason="PermissionError: [Errno 13] Permission denied",
    )
    @pytest.mark.parametrize(
        ("extra_files", "download_side_effect"),
        [
            ([], None),
            (["dummy_unexpected_extra_file"], None),
            ([], DownloadError),
        ],
    )
    def test_handle_get_files(
        self,
        extra_files: List[str],
        download_side_effect: Optional[Exception],
    ) -> None:
        """Test _handle_get_files"""
        with tempfile.NamedTemporaryFile() as tmp_file, mock.patch.object(
            os,
            "listdir",
        ) as mock_listdir, mock.patch.object(
            IPFSTool, "download", side_effect=download_side_effect
        ):
            mock_listdir.side_effect = [extra_files + [tmp_file.name]]

            tmp_file.write(b"dummy_data")
            tmp_file.flush()

            _, ipfs_hash, _ = self.connection.ipfs_tool.add(tmp_file.name)
            message = IpfsMessage(
                performative=IpfsMessage.Performative.GET_FILES, ipfs_hash=ipfs_hash  # type: ignore
            )
            dialogue = MagicMock()
            message = self.connection._handle_get_files(message, dialogue)
            assert message is not None

    @pytest.mark.skipif(
        platform.system() == "Windows",
        reason="PermissionError: [Errno 13] Permission denied",
    )
    def test_handle_get_files_with_subdirectory(self) -> None:
        """Test _handle_get_files reads files recursively from subdirectories."""
        with tempfile.TemporaryDirectory() as pkg_dir:
            # Create a package with a subdirectory
            os.makedirs(os.path.join(pkg_dir, "tests"))
            with open(
                os.path.join(pkg_dir, "component.yaml"), "w", encoding="utf-8"
            ) as f:
                f.write("name: test_tool")
            with open(os.path.join(pkg_dir, "tool.py"), "w", encoding="utf-8") as f:
                f.write("def run(): pass")
            with open(
                os.path.join(pkg_dir, "tests", "__init__.py"),
                "w",
                encoding="utf-8",
            ) as f:
                f.write("")
            with open(
                os.path.join(pkg_dir, "tests", "test_tool.py"),
                "w",
                encoding="utf-8",
            ) as f:
                f.write("def test_run(): pass")

            _, ipfs_hash, _ = self.connection.ipfs_tool.add(
                pkg_dir, wrap_with_directory=False
            )

            message = IpfsMessage(
                performative=IpfsMessage.Performative.GET_FILES,
                ipfs_hash=ipfs_hash,  # type: ignore
            )
            dialogue = MagicMock()
            result = self.connection._handle_get_files(message, dialogue)
            assert result is not None

            # Verify the reply was called with files containing subdirectory paths
            call_kwargs = dialogue.reply.call_args[1]
            files = call_kwargs["files"]
            assert "component.yaml" in files
            assert "tool.py" in files
            assert os.path.join("tests", "__init__.py") in files
            assert os.path.join("tests", "test_tool.py") in files

    @pytest.mark.skipif(
        platform.system() == "Windows",
        reason="PermissionError: [Errno 13] Permission denied",
    )
    def test_handle_get_files_with_binary_file(self) -> None:
        """Test _handle_get_files skips binary files with a warning."""
        with tempfile.TemporaryDirectory() as pkg_dir:
            with open(
                os.path.join(pkg_dir, "component.yaml"), "w", encoding="utf-8"
            ) as f:
                f.write("name: test_tool")
            # Write a binary file that will cause UnicodeDecodeError
            with open(os.path.join(pkg_dir, "data.bin"), "wb") as f:
                f.write(bytes(range(256)))

            _, ipfs_hash, _ = self.connection.ipfs_tool.add(
                pkg_dir, wrap_with_directory=False
            )

            message = IpfsMessage(
                performative=IpfsMessage.Performative.GET_FILES,
                ipfs_hash=ipfs_hash,  # type: ignore
            )
            dialogue = MagicMock()
            with mock.patch.object(self.connection.logger, "warning") as mock_warning:
                result = self.connection._handle_get_files(message, dialogue)

            assert result is not None
            call_kwargs = dialogue.reply.call_args[1]
            files = call_kwargs["files"]
            assert "component.yaml" in files
            assert "data.bin" not in files
            mock_warning.assert_any_call("Skipping non-UTF-8 file: data.bin")

    @pytest.mark.skipif(
        platform.system() == "Windows",
        reason="PermissionError: [Errno 13] Permission denied",
    )
    def test_handle_get_files_with_nested_subdirectories(self) -> None:
        """Test _handle_get_files handles deeply nested directories."""
        with tempfile.TemporaryDirectory() as pkg_dir:
            nested = os.path.join(pkg_dir, "a", "b", "c")
            os.makedirs(nested)
            with open(os.path.join(pkg_dir, "root.py"), "w", encoding="utf-8") as f:
                f.write("root")
            with open(os.path.join(nested, "deep.py"), "w", encoding="utf-8") as f:
                f.write("deep")

            _, ipfs_hash, _ = self.connection.ipfs_tool.add(
                pkg_dir, wrap_with_directory=False
            )

            message = IpfsMessage(
                performative=IpfsMessage.Performative.GET_FILES,
                ipfs_hash=ipfs_hash,  # type: ignore
            )
            dialogue = MagicMock()
            result = self.connection._handle_get_files(message, dialogue)
            assert result is not None

            call_kwargs = dialogue.reply.call_args[1]
            files = call_kwargs["files"]
            assert "root.py" in files
            assert os.path.join("a", "b", "c", "deep.py") in files

    @pytest.mark.skipif(
        platform.system() == "Windows",
        reason="PermissionError: [Errno 13] Permission denied",
    )
    def test_handle_get_files_flat_package_unchanged(self) -> None:
        """Test _handle_get_files backwards compatibility with flat packages."""
        with tempfile.TemporaryDirectory() as pkg_dir:
            with open(
                os.path.join(pkg_dir, "component.yaml"), "w", encoding="utf-8"
            ) as f:
                f.write("name: test_tool")
            with open(os.path.join(pkg_dir, "tool.py"), "w", encoding="utf-8") as f:
                f.write("def run(): pass")

            _, ipfs_hash, _ = self.connection.ipfs_tool.add(
                pkg_dir, wrap_with_directory=False
            )

            message = IpfsMessage(
                performative=IpfsMessage.Performative.GET_FILES,
                ipfs_hash=ipfs_hash,  # type: ignore
            )
            dialogue = MagicMock()
            result = self.connection._handle_get_files(message, dialogue)
            assert result is not None

            call_kwargs = dialogue.reply.call_args[1]
            files = call_kwargs["files"]
            assert "component.yaml" in files
            assert files["component.yaml"] == "name: test_tool"
            assert "tool.py" in files
            assert files["tool.py"] == "def run(): pass"

    def test_ipfs_dialogue(self) -> None:
        """Test 'IpfsDialogues' creation."""
        dialogues = IpfsDialogues(connection_id=str(PUBLIC_ID))
        dialogues.create(
            counterparty=ANY_SKILL,
            performative=IpfsMessage.Performative.GET_FILES,
        )
