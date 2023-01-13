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
"""A connection responsible for uploading and downloading files from IPFS."""
import asyncio
import os
import tempfile
from asyncio import Task
from concurrent.futures import Executor
from pathlib import Path
from shutil import rmtree
from typing import Any, Callable, Dict, Optional, cast

import requests
from aea.configurations.base import PublicId
from aea.connections.base import Connection, ConnectionStates
from aea.mail.base import Envelope
from aea.protocols.base import Address, Message
from aea.protocols.dialogue.base import Dialogue as BaseDialogue
from aea_cli_ipfs.exceptions import DownloadError
from aea_cli_ipfs.ipfs_utils import IPFSTool
from ipfshttpclient.exceptions import ErrorResponse

from packages.valory.protocols.ipfs import IpfsMessage
from packages.valory.protocols.ipfs.dialogues import IpfsDialogue
from packages.valory.protocols.ipfs.dialogues import IpfsDialogues as BaseIpfsDialogues


PUBLIC_ID = PublicId.from_str("valory/ipfs:0.1.0")


class IpfsDialogues(BaseIpfsDialogues):
    """A class to keep track of IPFS dialogues."""

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize dialogues.

        :param kwargs: keyword arguments
        """

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> BaseDialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            return IpfsDialogue.Role.CONNECTION

        BaseIpfsDialogues.__init__(
            self,
            self_address=str(kwargs.pop("connection_id")),
            role_from_first_message=role_from_first_message,
            **kwargs,
        )


class IpfsConnection(Connection):
    """An async connection for sending and receiving files to IPFS."""

    connection_id = PUBLIC_ID

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize the connection.

        :param kwargs: keyword arguments passed to component base.
        """
        super().__init__(**kwargs)  # pragma: no cover
        ipfs_domain = self.configuration.config.get("ipfs_domain")
        self.ipfs_tool: IPFSTool = IPFSTool(ipfs_domain)
        self.task_to_request: Dict[asyncio.Future, Envelope] = {}
        self.loop_executor: Optional[Executor] = None
        self.dialogues = IpfsDialogues(connection_id=PUBLIC_ID)
        self._response_envelopes: Optional[asyncio.Queue] = None

    @property
    def response_envelopes(self) -> asyncio.Queue:
        """Returns the response envelopes queue."""
        if self._response_envelopes is None:
            raise ValueError(
                "`IPFSConnection.response_envelopes` is not yet initialized. Is the connection setup?"
            )
        return self._response_envelopes

    async def connect(self) -> None:
        """Set up the connection."""
        self.ipfs_tool.check_ipfs_node_running()
        self._response_envelopes = asyncio.Queue()
        self.state = ConnectionStates.connected

    async def disconnect(self) -> None:
        """Tear down the connection."""
        if self.is_disconnected:  # pragma: nocover
            return

        self.state = ConnectionStates.disconnecting

        for task in self.task_to_request.keys():
            if not task.cancelled():  # pragma: nocover
                task.cancel()
        self._response_envelopes = None

        self.state = ConnectionStates.disconnected

    async def send(self, envelope: Envelope) -> None:
        """Send an envelope."""
        task = self._handle_envelope(envelope)
        task.add_done_callback(self._handle_done_task)
        self.task_to_request[task] = envelope

    async def receive(self, *args: Any, **kwargs: Any) -> Optional[Envelope]:
        """Receive an envelope."""
        return await self.response_envelopes.get()

    def run_async(
        self, func: Callable, *args: Any, timeout: Optional[float] = None
    ) -> Task:
        """Run a function asynchronously by using threads."""
        ipfs_operation = self.loop.run_in_executor(
            self.loop_executor,
            func,
            *args,
        )
        timely_operation = asyncio.wait_for(ipfs_operation, timeout=timeout)
        task = self.loop.create_task(timely_operation)
        return task

    def _handle_envelope(self, envelope: Envelope) -> Task:
        """Handle incoming envelopes by dispatching background tasks."""
        message = cast(IpfsMessage, envelope.message)
        performative = message.performative
        handler = getattr(self, f"_handle_{performative.value}", None)
        if handler is None:
            err = f"Performative `{performative.value}` is not supported."
            self.logger.error(err)
            task = self.run_async(self._handle_error, err)
            return task
        dialogue = self.dialogues.update(message)
        task = self.run_async(handler, message, dialogue)
        return task

    def _handle_store_files(
        self, message: IpfsMessage, dialogue: BaseDialogue
    ) -> IpfsMessage:
        """
        Handle a STORE_FILES performative.

        Uploads the provided files to ipfs.

        :param message: The ipfs request.
        :returns: the hash of the uploaded files.
        """
        files = message.files
        if len(files) == 0:
            err = "No files were present."
            self.logger.error(err)
            return self._handle_error(err, dialogue)
        if len(files) == 1:
            # a single file needs to be stored,
            # we don't need to create a dir
            path, data = files.popitem()
            self.__create_file(path, data)
        else:
            # multiple files are present, which means that it's a directory
            # we begin by checking that they belong to the same directory
            dirs = {os.path.dirname(path) for path in files.keys()}
            if len(dirs) > 1:
                err = f"Received files from different dirs {dirs}. "
                self.logger.error(err)
                self.logger.info(
                    "If you want to send multiple files as a single dir, "
                    "make sure the their path matches to one directory only."
                )
                return self._handle_error(err, dialogue)

            # "path" is the directory, it's the same for all the files
            path = dirs.pop()
            os.makedirs(path, exist_ok=True)
            for file_path, data in files.items():
                self.__create_file(file_path, data)
        try:
            # note that path will be a dir if multiple files
            # are being uploaded.
            _, hash_, _ = self.ipfs_tool.add(path)
            self.logger.debug(f"Successfully stored files with hash: {hash_}.")
        except (
            ValueError,
            requests.exceptions.ChunkedEncodingError,
        ) as e:  # pragma: no cover
            err = str(e)
            self.logger.error(err)
            return self._handle_error(err, dialogue)
        finally:
            self.__remove_filepath(path)
        response_message = cast(
            IpfsMessage,
            dialogue.reply(
                performative=IpfsMessage.Performative.IPFS_HASH,
                target_message=message,
                ipfs_hash=hash_,
            ),
        )
        return response_message

    def _handle_get_files(
        self, message: IpfsMessage, dialogue: BaseDialogue
    ) -> IpfsMessage:
        """
        Handle GET_FILES performative.

        Downloads and returns the files resulting from the ipfs hash.

        :param message: The ipfs request.
        :returns: the downloaded files.
        """
        response_body: Dict[str, str] = {}
        ipfs_hash = message.ipfs_hash
        with tempfile.TemporaryDirectory() as tmp_dir:
            try:
                self.ipfs_tool.download(ipfs_hash, tmp_dir)
            except (
                DownloadError,
                PermissionError,
                ErrorResponse,
            ) as e:
                err = str(e)
                self.logger.error(err)
                return self._handle_error(err, dialogue)

            files = os.listdir(tmp_dir)
            if len(files) > 1:
                self.logger.warning(
                    f"Multiple files or dirs found in {tmp_dir}. "
                    f"The first will be used. "
                )
            downloaded_file = files.pop()
            files_to_be_read = [downloaded_file]
            base_dir = Path(tmp_dir)
            if os.path.isdir(base_dir / downloaded_file):
                base_dir = base_dir / downloaded_file
                files_to_be_read = os.listdir(base_dir)

            for file_path in files_to_be_read:
                with open(base_dir / file_path, encoding="utf-8", mode="r") as file:
                    response_body[file_path] = file.read()

            response_message = cast(
                IpfsMessage,
                dialogue.reply(
                    performative=IpfsMessage.Performative.FILES,
                    files=response_body,
                    target_message=message,
                ),
            )
            return response_message

    def _handle_error(  # pylint: disable=no-self-use
        self, reason: str, dialogue: BaseDialogue
    ) -> IpfsMessage:
        """Handler for error messages."""
        message = cast(
            IpfsMessage,
            dialogue.reply(
                performative=IpfsMessage.Performative.ERROR,
                reason=reason,
            ),
        )
        return message

    def _handle_done_task(self, task: asyncio.Future) -> None:
        """
        Process a done receiving task.

        :param task: the done task.
        """
        request = self.task_to_request.pop(task)
        response_message: Optional[Message] = task.result()

        response_envelope = None
        if response_message is not None:
            response_envelope = Envelope(
                to=request.sender,
                sender=request.to,
                message=response_message,
                context=request.context,
            )

        # not handling `asyncio.QueueFull` exception, because the maxsize we defined for the Queue is infinite
        self.response_envelopes.put_nowait(response_envelope)

    @staticmethod
    def __create_file(path: str, data: str) -> None:
        """Creates a file in the specified path."""
        with open(path, "w", encoding="utf-8") as f:
            f.write(data)

    def __remove_filepath(self, filepath: str) -> None:
        """Remove a file or a folder. If filepath is not a file or a folder, an `IPFSInteractionError` is raised."""
        if os.path.isfile(filepath):
            os.remove(filepath)
        elif os.path.isdir(filepath):
            rmtree(filepath)
        else:  # pragma: no cover
            self.logger.error(f"`{filepath}` is not an existing filepath!")
