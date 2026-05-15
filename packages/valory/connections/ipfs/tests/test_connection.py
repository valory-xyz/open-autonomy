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
# pylint: disable=protected-access,attribute-defined-outside-init,consider-using-with

"""Tests for ipfs connection."""

import asyncio
import os
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

    @pytest.mark.asyncio
    async def test_handle_done_task_recovers_dialogue_on_task_failure(self) -> None:
        """Failed task is converted to an error response via dialogue recovery.

        When ``task.result()`` raises, ``_handle_done_task`` must rebuild the
        dialogue and emit an error response, not blow up. Without the
        ``try/except`` added in the audit, the broken task would crash the
        connection's done-callback and silently drop the response.
        """
        await self.connection.connect()
        assert self.connection.response_envelopes.qsize() == 0
        boom_task = MagicMock(result=MagicMock(side_effect=RuntimeError("boom")))
        request_message = IpfsMessage(performative=IpfsMessage.Performative.GET_FILES)  # type: ignore
        request_envelope = MagicMock(
            to=ANY_SKILL,
            sender=str(PUBLIC_ID),
            context=None,
            message=request_message,
        )
        self.connection.task_to_request[boom_task] = request_envelope
        recovered_dialogue = MagicMock()
        with mock.patch.object(
            self.connection.dialogues, "update", return_value=recovered_dialogue
        ), mock.patch.object(
            self.connection, "_handle_error", return_value=self.dummy_msg
        ) as mock_handle_error:
            self.connection._handle_done_task(boom_task)
        # Error message put on the response queue, NOT None.
        assert self.connection.response_envelopes.qsize() == 1
        envelope = self.connection.response_envelopes.get_nowait()
        assert envelope is not None
        mock_handle_error.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_done_task_drops_response_when_dialogue_cannot_be_rebuilt(
        self,
    ) -> None:
        """Unrecoverable dialogue surfaces a logged ``None`` response.

        If the failed task's dialogue also can't be recovered,
        ``response_message`` falls through to ``None`` and a ``None`` envelope
        is put on the queue. The recovery-failure branch must log so the
        silent drop is debuggable.
        """
        await self.connection.connect()
        assert self.connection.response_envelopes.qsize() == 0
        boom_task = MagicMock(result=MagicMock(side_effect=RuntimeError("boom")))
        request_message = IpfsMessage(performative=IpfsMessage.Performative.GET_FILES)  # type: ignore
        request_envelope = MagicMock(
            to=ANY_SKILL,
            sender=str(PUBLIC_ID),
            context=None,
            message=request_message,
        )
        self.connection.task_to_request[boom_task] = request_envelope
        with mock.patch.object(
            self.connection.dialogues, "update", return_value=None
        ), mock.patch.object(self.connection.logger, "error") as mock_log_error:
            self.connection._handle_done_task(boom_task)
        # None propagated to the queue; the recovery-failure path is logged.
        assert self.connection.response_envelopes.qsize() == 1
        envelope = self.connection.response_envelopes.get_nowait()
        assert envelope is None
        mock_log_error.assert_any_call(
            "Could not recover dialogue for failed IPFS task; dropping "
            "response. The requesting skill will time out."
        )

    @pytest.mark.asyncio
    async def test_handle_envelope_dispatches_executable_error_task_when_dialogue_update_is_none(
        self,
    ) -> None:
        """Request-path None-guard dispatches an actually-runnable error task.

        If ``dialogues.update(message)`` returns ``None``, the per-performative
        handler must not be called (it would crash on ``dialogue.reply(...)``).
        The fix routes through ``_handle_error`` with ``dialogue=None``; the
        task body must complete cleanly (returning ``None``) rather than
        ``TypeError``-ing on a missing positional argument. The previous test
        mocked ``run_async`` and so never executed the task body — this one
        awaits the task end-to-end.
        """
        await self.connection.connect()
        envelope = Envelope(to=str(PUBLIC_ID), sender=ANY_SKILL, message=self.dummy_msg)
        with mock.patch.object(
            self.connection.dialogues, "update", return_value=None
        ), mock.patch.object(self.connection.logger, "error") as mock_log_error:
            task = self.connection._handle_envelope(envelope)
            # The task is real; awaiting it actually runs ``_handle_error``
            # in the executor. Pre-fix this raised
            # ``TypeError: _handle_error() missing 1 required positional
            # argument: 'dialogue'``.
            result = await task
        assert result is None
        # Both the scheduling log and ``_handle_error``'s own "dropping
        # error response" log fire — the latter proves the task body ran.
        log_messages = [call.args[0] for call in mock_log_error.call_args_list]
        assert any(
            "Could not update dialogue for message" in msg for msg in log_messages
        )
        assert any(
            "Dropping error response, no dialogue available." in msg
            for msg in log_messages
        )

    def test_handle_error_returns_none_when_dialogue_is_none(self) -> None:
        """_handle_error tolerates dialogue=None and logs the dropped reply.

        Direct unit test for the widened signature: passing ``dialogue=None``
        must return ``None`` and log at error level rather than dereferencing
        a ``NoneType`` to build the reply.
        """
        with mock.patch.object(self.connection.logger, "error") as mock_log_error:
            result = self.connection._handle_error(reason="dropped", dialogue=None)
        assert result is None
        mock_log_error.assert_called_once()
        log_msg = mock_log_error.call_args.args[0]
        assert "Dropping error response, no dialogue available." in log_msg

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
        tmp_file = tempfile.NamedTemporaryFile(delete=False)
        try:
            tmp_file.write(b"dummy_data")
            tmp_file.close()  # close before IPFS reads to avoid Windows file lock

            with mock.patch.object(
                os,
                "listdir",
            ) as mock_listdir, mock.patch.object(
                IPFSTool, "download", side_effect=download_side_effect
            ):
                mock_listdir.side_effect = [extra_files + [tmp_file.name]]
                _, ipfs_hash, _ = self.connection.ipfs_tool.add(tmp_file.name)
                message = IpfsMessage(
                    performative=IpfsMessage.Performative.GET_FILES, ipfs_hash=ipfs_hash  # type: ignore
                )
                dialogue = MagicMock()
                message = self.connection._handle_get_files(message, dialogue)
                assert message is not None
        finally:
            os.unlink(tmp_file.name)

    def test_handle_get_files_returns_error_on_empty_download_dir(self) -> None:
        """Empty download dir routes to ``_handle_error`` instead of IndexError.

        An IPFS download that produces no files (empty ``os.listdir``) must
        route through ``_handle_error`` with an explicit message, NOT index
        into the empty list and raise ``IndexError``. Drives the empty-listdir
        guard added by the audit.
        """
        with mock.patch.object(IPFSTool, "download"), mock.patch.object(
            os, "listdir", return_value=[]
        ), mock.patch.object(
            self.connection, "_handle_error"
        ) as mock_handle_error, mock.patch.object(
            self.connection.logger, "error"
        ):
            message = IpfsMessage(
                performative=IpfsMessage.Performative.GET_FILES,  # type: ignore
                ipfs_hash="bafyemptydir",
            )
            self.connection._handle_get_files(message, MagicMock())
        mock_handle_error.assert_called_once()
        err_arg = mock_handle_error.call_args.args[0]
        assert "produced no files" in err_arg
        assert "bafyemptydir" in err_arg

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
                performative=IpfsMessage.Performative.GET_FILES,  # type: ignore
                ipfs_hash=ipfs_hash,
            )
            dialogue = MagicMock()
            message = self.connection._handle_get_files(message, dialogue)
            assert message is not None

            # Verify the reply was called with files containing subdirectory paths
            call_kwargs = dialogue.reply.call_args[1]
            files = call_kwargs["files"]
            assert "component.yaml" in files
            assert "tool.py" in files
            assert os.path.join("tests", "__init__.py") in files
            assert os.path.join("tests", "test_tool.py") in files

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
                performative=IpfsMessage.Performative.GET_FILES,  # type: ignore
                ipfs_hash=ipfs_hash,
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
                performative=IpfsMessage.Performative.GET_FILES,  # type: ignore
                ipfs_hash=ipfs_hash,
            )
            dialogue = MagicMock()
            message = self.connection._handle_get_files(message, dialogue)
            assert message is not None

            call_kwargs = dialogue.reply.call_args[1]
            files = call_kwargs["files"]
            assert "root.py" in files
            assert os.path.join("a", "b", "c", "deep.py") in files

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
                performative=IpfsMessage.Performative.GET_FILES,  # type: ignore
                ipfs_hash=ipfs_hash,
            )
            dialogue = MagicMock()
            message = self.connection._handle_get_files(message, dialogue)
            assert message is not None

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
