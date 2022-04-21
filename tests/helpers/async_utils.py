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

"""Helpers for Pytest tests with asynchronous programming."""
import asyncio
import logging
import time
from asyncio import AbstractEventLoop
from threading import Thread
from typing import Any, Awaitable, Callable, Optional


def wait_for_condition(
    condition_checker: Callable,
    timeout: int = 2,
    error_msg: str = "Timeout",
    period: float = 0.001,
) -> None:
    """Wait for condition occures in selected timeout."""
    start_time = time.time()

    while not condition_checker():
        time.sleep(period)
        if time.time() > start_time + timeout:
            raise TimeoutError(error_msg)


class AnotherThreadTask:
    """
    Schedule a task to run on the loop in another thread.

    Provides better cancel behaviour: on cancel it will wait till cancelled completely.
    """

    def __init__(self, coro: Awaitable, loop: AbstractEventLoop) -> None:
        """
        Init the task.

        :param coro: coroutine to schedule
        :param loop: an event loop to schedule on.
        """
        self._loop = loop
        self._coro = coro
        self._task: Optional[asyncio.Task] = None
        self._future = asyncio.run_coroutine_threadsafe(self._get_task_result(), loop)

    async def _get_task_result(self) -> Any:
        """
        Get task result, should be run in target loop.

        :return: task result value or raise an exception if task failed
        """
        self._task = self._loop.create_task(self._coro)
        return await self._task

    def result(self, timeout: Optional[float] = None) -> Any:
        """
        Wait for coroutine execution result.

        :param timeout: optional timeout to wait in seconds.
        :return: result
        """
        return self._future.result(timeout)

    def cancel(self) -> None:
        """Cancel coroutine task execution in a target loop."""
        if self._task is None:
            self._loop.call_soon_threadsafe(self._future.cancel)
        else:
            self._loop.call_soon_threadsafe(self._task.cancel)

    def done(self) -> bool:
        """Check task is done."""
        return self._future.done()


class ThreadedAsyncRunner(Thread):
    """Util to run thread with event loop and execute coroutines inside."""

    def __init__(self, loop: Optional[AbstractEventLoop] = None) -> None:
        """
        Init threaded runner.

        :param loop: optional event loop. is it's running loop, threaded runner will use it.
        """
        self._loop = loop or asyncio.new_event_loop()
        if self._loop.is_closed():
            raise ValueError("Event loop closed.")  # pragma: nocover
        super().__init__(daemon=True)

    def start(self) -> None:
        """Start event loop in dedicated thread."""
        if self.is_alive() or self._loop.is_running():  # pragma: nocover
            return
        super().start()
        self.call(asyncio.sleep(0.001)).result(1)

    def run(self) -> None:
        """Run code inside thread."""
        logging.debug("Starting threaded asyncio loop...")
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()
        logging.debug("Asyncio loop has been stopped.")

    def call(self, coro: Awaitable) -> Any:
        """
        Run a coroutine inside the event loop.

        :param coro: a coroutine to run.
        :return: task
        """
        return AnotherThreadTask(coro, self._loop)

    def stop(self) -> None:
        """Stop event loop in thread."""
        logging.debug("Stopping...")

        if not self.is_alive():  # pragma: nocover
            return

        if self._loop.is_running():
            logging.debug("Stopping loop...")
            self._loop.call_soon_threadsafe(self._loop.stop)

        logging.debug("Wait thread to join...")
        self.join(10)
        logging.debug("Stopped.")


class BaseThreadedAsyncLoop:
    """Test class with a threaded event loop running."""

    DEFAULT_ASYNC_TIMEOUT = 5.0
    loop: ThreadedAsyncRunner
    thread: Thread

    def setup(self) -> None:
        """Set up the class."""
        self.loop = ThreadedAsyncRunner()
        self.loop.start()

    def execute(self, coro: Awaitable, timeout: float = DEFAULT_ASYNC_TIMEOUT) -> Any:
        """Execute a coroutine and wait its completion."""
        task: AnotherThreadTask = self.loop.call(coro)
        return task.result(timeout=timeout)

    def teardown(self) -> None:
        """Teardown the class."""
        self.loop.start()
        self.loop.join(5.0)
