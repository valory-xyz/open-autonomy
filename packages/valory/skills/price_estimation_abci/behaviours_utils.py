# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021 Valory AG
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

"""This module contains helper functions and classes to implement async behaviours."""
from typing import Any, Callable, Generator, Optional

from aea.skills.behaviours import State


DONE_EVENT = "done"
FAIL_EVENT = "fail"


class AsyncBehaviour:
    """MixIn behaviour that support limited asynchronous programming."""

    async_act: Callable

    def __init__(self) -> None:
        """Initialize the async behaviour."""
        self._called_once: bool = False
        self._notified: bool = False
        self._message: Any = None

        self._condition: Callable = lambda message: True
        self._generator_act: Optional[Generator] = None

    @property
    def generator_act(self) -> Generator:
        """Get the _generator_act."""
        if self._generator_act is None:
            raise ValueError("Generator act not set!")
        return self._generator_act

    def try_send(self, message: Any) -> None:
        """
        Try to send a message to a waiting behaviour.

        It will be send only if:
        - the behaviour is actually waiting, and
        - the condition specified by the behaviour holds for the incoming message

        :param message: a Python object.
        """
        if self._called_once and self._condition(message):
            self._notified = True
            self._message = message

    def wait_for_message(self, condition: Callable = lambda message: True) -> Any:
        """Wait for message."""
        self._condition = condition
        message = yield
        return message

    def act(self) -> None:
        """Do the act."""
        if not self._called_once:
            self._called_once = True
            self._generator_act = self.async_act()
            self.generator_act.send(None)  # trigger first execution
            return
        if self._notified:
            try:
                self.generator_act.send(self._message)
            except StopIteration:
                # end of 'act' function -> reset state
                self._called_once = False
            finally:
                # wait for the next message
                self._notified = False
                self._message = None


class WaitForConditionBehaviour(State):
    """This behaviour waits for a condition to happen."""

    is_programmatically_defined = True

    def __init__(
        self, condition: Callable, event: str = DONE_EVENT, **kwargs: Any
    ) -> None:
        """Initialize the behaviour."""
        super().__init__(**kwargs)
        self.condition = condition
        self.event_to_raise = event
        self._is_done: bool = False

    def is_done(self) -> bool:
        """Check whether the behaviour is done."""
        return self._is_done

    def act(self) -> None:
        """Do the action."""
        if not self.is_done() and self.condition():
            self._is_done = True
            self._event = self.event_to_raise
