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
from asyncio import Task
from typing import Any
from unittest import mock

import pytest
from aea.configurations.base import ConnectionConfig

from packages.valory.connections.ledger.connection import LedgerConnection


def dummy_task_wrapper(waiting_time: float, result: Any) -> Task:
    """Create a dummy task that simply waits for a given `waiting_time` and returns a given `result`."""

    async def dummy_task(*_: Any) -> None:
        """Wait for the given `waiting_time` and return the given `result`."""
        await asyncio.sleep(waiting_time, result)

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
        blocking_task = dummy_task_wrapper(blocking_time, "blocking_task")
        dummy_envelope = mock.MagicMock()
        with mock.patch.object(
            LedgerConnection, "_schedule_request", return_value=blocking_task
        ):
            await ledger_connection.send(dummy_envelope)

        # create a non-blocking task lasting `non_blocking_time` secs, after `wait_time_among_tasks`
        await asyncio.sleep(wait_time_among_tasks)
        normal_task = dummy_task_wrapper(non_blocking_time, "normal_task")
        dummy_envelope = mock.MagicMock()
        with mock.patch.object(
            LedgerConnection, "_schedule_request", return_value=normal_task
        ):
            await ledger_connection.send(dummy_envelope)

        # sleep for `non_blocking_time + tolerance`
        await asyncio.sleep(non_blocking_time + tolerance)

        # the normal task should be finished
        assert normal_task.done(), "Normal task should be done at this point."

        # the blocking task should not be done
        assert not blocking_task.done(), "Blocking task should be still running."

        # the `receive_task` should be done, and not await for the `blocking_task`
        assert receive_task.done(), "Receive task is blocked by blocking task!"
