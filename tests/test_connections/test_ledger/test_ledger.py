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

"""This module contains the tests of the ledger connection module."""

import asyncio
import logging
from asyncio import Task
from pathlib import Path
from threading import Thread
from typing import Any, Callable, cast
from unittest import mock

import pytest
from aea.configurations.base import ConnectionConfig
from aea.mail.base import Envelope
from aea.multiplexer import Multiplexer
from aea.test_tools.test_skill import BaseSkillTestCase

from packages.valory.connections.abci.dialogues import AbciDialogues
from packages.valory.connections.ledger.connection import LedgerConnection
from packages.valory.protocols.abci import AbciMessage
from packages.valory.skills.abstract_abci.handlers import ABCIHandler

from tests.conftest import ROOT_DIR, make_ledger_api_connection


def dummy_task_wrapper(waiting_time: float, result_message: AbciMessage) -> Task:
    """Create a dummy task that simply waits for a given `waiting_time` and returns a given `result_message`."""

    async def dummy_task(*_: Any) -> AbciMessage:
        """Wait for the given `waiting_time` and return the given `result_message`."""
        await asyncio.sleep(waiting_time)
        return result_message

    task = asyncio.create_task(dummy_task())
    return task


class TestLedgerConnection:
    """Test `LedgerConnection` class."""

    @pytest.mark.asyncio
    async def test_not_hanging(self) -> None:
        """Test that the connection does not hang and that the tasks cannot get blocked."""
        # create configurations for the test, re bocking and non-blocking tasks' waiting times
        blocking_time = 100
        wait_time_among_tasks = 0.1
        non_blocking_time = 1
        tolerance = 1
        assert (
            non_blocking_time + tolerance + wait_time_among_tasks < blocking_time
        ), "`non_blocking_time + tolerance + wait_time_among_tasks` should be less than the `blocking_time`."

        # setup a dummy ledger connection
        ledger_connection = LedgerConnection(
            configuration=ConnectionConfig("ledger", "valory", "0.1.0"),
            data_dir="test_data_dir",
        )

        # connect() is called by the multiplexer
        await ledger_connection.connect()

        # once a connection is ready, `receive()` is called by the multiplexer
        receive_task = asyncio.ensure_future(ledger_connection.receive())

        # create a blocking task lasting `blocking_time` secs
        blocking_task = dummy_task_wrapper(
            blocking_time,
            AbciMessage(
                AbciMessage.Performative.DUMMY, _body={"data": b"blocking_task"}  # type: ignore
            ),
        )
        blocking_dummy_envelope = Envelope(
            to="test_blocking_to",
            sender="test_blocking_sender",
            message=AbciMessage(AbciMessage.Performative.DUMMY),  # type: ignore
        )
        with mock.patch.object(
            LedgerConnection, "_schedule_request", return_value=blocking_task
        ):
            await ledger_connection.send(blocking_dummy_envelope)

        # create a non-blocking task lasting `non_blocking_time` secs, after `wait_time_among_tasks`
        await asyncio.sleep(wait_time_among_tasks)
        normal_task = dummy_task_wrapper(
            non_blocking_time,
            AbciMessage(AbciMessage.Performative.DUMMY, _body={"data": b"normal_task"}),  # type: ignore
        )
        normal_dummy_envelope = Envelope(
            to="test_normal_to",
            sender="test_normal_sender",
            message=AbciMessage(AbciMessage.Performative.DUMMY),  # type: ignore
        )
        with mock.patch.object(
            LedgerConnection, "_schedule_request", return_value=normal_task
        ):
            await ledger_connection.send(normal_dummy_envelope)

        # sleep for `non_blocking_time + tolerance`
        await asyncio.sleep(non_blocking_time + tolerance)

        # the normal task should be finished
        assert normal_task.done(), "Normal task should be done at this point."

        # the `receive_task` should be done, and not await for the `blocking_task`
        assert receive_task.done(), "Receive task is blocked by blocking task!"

        # the blocking task should not be done
        assert not blocking_task.done(), "Blocking task should be still running."
        # cancel remaining task before ending test
        blocking_task.cancel()


class TestLedgerConnectionWithMultiplexer(BaseSkillTestCase):
    """Test `LedgerConnection` class, using the multiplexer, via the `BaseSkillTestCase`."""

    path_to_skill = Path(ROOT_DIR, "packages", "valory", "skills", "abstract_abci")
    abci_handler: ABCIHandler
    logger: logging.Logger
    abci_dialogues: AbciDialogues
    running_loop: asyncio.AbstractEventLoop
    thread_loop: Thread
    _multiplexer: Multiplexer
    ledger_connection: LedgerConnection
    make_ledger_connection_callable: Callable = make_ledger_api_connection

    @classmethod
    def setup(cls, **kwargs: Any) -> None:
        """Setup the test class."""
        super().setup()
        cls.abci_handler = cast(ABCIHandler, cls._skill.skill_context.handlers.abci)
        cls.logger = cls._skill.skill_context.logger

        cls.abci_dialogues = cast(
            AbciDialogues, cls._skill.skill_context.abci_dialogues
        )

        # set up a multiplexer with the required ledger connection
        cls.running_loop = asyncio.new_event_loop()
        cls.thread_loop = Thread(target=cls.running_loop.run_forever)
        cls.thread_loop.start()
        cls._multiplexer = Multiplexer(
            [cls.make_ledger_connection_callable()], loop=cls.running_loop
        )
        cls._multiplexer.connect()
        # the ledger connection's connect() is called by the multiplexer
        # once a connection is ready, `receive()` is called by the multiplexer
        cls.ledger_connection = cast(LedgerConnection, cls._multiplexer.connections[0])

    @classmethod
    def teardown(cls) -> None:
        """Tear down the multiplexer."""
        if cls._multiplexer.is_connected:
            cls._multiplexer.disconnect()
        cls.running_loop.call_soon_threadsafe(cls.running_loop.stop)
        cls.thread_loop.join()

    @pytest.mark.asyncio
    async def test_not_hanging_with_multiplexer(self) -> None:
        """Test that the connection does not hang and that the tasks cannot get blocked, using the multiplexer."""
        # create configurations for the test, re bocking and non-blocking tasks' waiting times
        blocking_time = 100
        wait_time_among_tasks = 0.1
        non_blocking_time = 1
        tolerance = 1
        assert (
            non_blocking_time + tolerance + wait_time_among_tasks < blocking_time
        ), "`non_blocking_time + tolerance + wait_time_among_tasks` should be less than the `blocking_time`."

        # create a blocking task lasting `blocking_time` secs
        blocking_task = dummy_task_wrapper(
            blocking_time,
            AbciMessage(
                AbciMessage.Performative.DUMMY, _body={"data": b"blocking_task"}  # type: ignore
            ),
        )
        blocking_dummy_envelope = Envelope(
            to="test_blocking_to",
            sender="test_blocking_sender",
            message=AbciMessage(AbciMessage.Performative.DUMMY),  # type: ignore
        )
        with mock.patch.object(
            self.ledger_connection, "_schedule_request", return_value=blocking_task
        ):
            await self.ledger_connection.send(blocking_dummy_envelope)

        # create a non-blocking task lasting `non_blocking_time` secs, after `wait_time_among_tasks`
        await asyncio.sleep(wait_time_among_tasks)
        normal_task = dummy_task_wrapper(
            non_blocking_time,
            AbciMessage(AbciMessage.Performative.DUMMY, _body={"data": b"normal_task"}),  # type: ignore
        )
        normal_dummy_envelope = Envelope(
            to="test_normal_to",
            sender="test_normal_sender",
            message=AbciMessage(AbciMessage.Performative.DUMMY),  # type: ignore
        )
        with mock.patch.object(
            self.ledger_connection, "_schedule_request", return_value=normal_task
        ):
            await self.ledger_connection.send(normal_dummy_envelope)

        # the response envelopes of the ledger connection should be empty
        assert self.ledger_connection.response_envelopes.empty()
        # `receive()` should not be done,
        # and multiplexer's `_receiving_loop` should be still running and have an empty `in_queue`
        assert (
            len(self._multiplexer.in_queue.queue) == 0
        ), "The multiplexer's `in_queue` should not contain anything."

        # sleep for `non_blocking_time + tolerance`
        await asyncio.sleep(non_blocking_time + tolerance)

        # the normal task should be finished
        assert normal_task.done(), "Normal task should be done at this point."

        # the blocking task should not be done
        assert not blocking_task.done(), "Blocking task should be still running."
        # cancel remaining task before ending test
        blocking_task.cancel()
