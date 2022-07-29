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

"""Test the behaviours_utils.py module of the skill."""
import json
import logging
import math
import sys
import time
from abc import ABC
from collections import OrderedDict
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, Generator, Optional, Tuple, Type, Union
from unittest import mock
from unittest.mock import MagicMock

import pytest
import pytz  # type: ignore  # pylint: disable=import-error


try:
    import atheris  # type: ignore
except (ImportError, ModuleNotFoundError):
    pytestmark = pytest.mark.skip


from packages.open_aea.protocols.signing import SigningMessage
from packages.valory.connections.http_client.connection import HttpDialogues
from packages.valory.protocols.http import HttpMessage
from packages.valory.protocols.ledger_api.message import LedgerApiMessage
from packages.valory.skills.abstract_round_abci.base import (
    AbstractRound,
    BaseSynchronizedData,
    BaseTxPayload,
    Transaction,
)
from packages.valory.skills.abstract_round_abci.behaviour_utils import (
    AsyncBehaviour,
    BaseBehaviour,
    DegenerateBehaviour,
    HEIGHT_OFFSET_MULTIPLIER,
    MIN_HEIGHT_OFFSET,
    NON_200_RETURN_CODE_DURING_RESET_THRESHOLD,
    RESET_HASH,
    ROOT_HASH,
    SendException,
    TimeoutException,
    make_degenerate_behaviour,
)
from packages.valory.skills.abstract_round_abci.models import (
    _DEFAULT_REQUEST_RETRY_DELAY,
    _DEFAULT_REQUEST_TIMEOUT,
    _DEFAULT_TX_MAX_ATTEMPTS,
    _DEFAULT_TX_TIMEOUT,
)

from tests.helpers.base import try_send


def yield_and_return_bool_wrapper(
    flag_value: bool,
) -> Callable[[], Generator[None, None, Optional[bool]]]:
    """Wrapper for a Dummy generator that returns a `bool`."""

    def yield_and_return_bool(
        **_: bool,
    ) -> Generator[None, None, Optional[bool]]:
        """Dummy generator that returns a `bool`."""
        yield
        return flag_value

    return yield_and_return_bool


class AsyncBehaviourTest(AsyncBehaviour, ABC):
    """Concrete AsyncBehaviour class for testing purposes."""

    def async_act_wrapper(self) -> Generator:
        """Do async act wrapper. Forwards to 'async_act'."""
        yield from self.async_act()

    def async_act(self) -> Generator:
        """Do 'async_act'."""


def async_behaviour_initial_state_is_ready() -> None:
    """Check that the initial async state is "READY"."""
    behaviour = AsyncBehaviourTest()
    assert behaviour.state == AsyncBehaviour.AsyncState.READY


def test_async_behaviour_ticks() -> None:
    """Test "AsyncBehaviour", only ticks."""

    class MyAsyncBehaviour(AsyncBehaviourTest):
        counter = 0

        def async_act(self) -> Generator:
            self.counter += 1
            yield
            self.counter += 1
            yield
            self.counter += 1

    behaviour = MyAsyncBehaviour()
    assert behaviour.counter == 0
    behaviour.act()
    assert behaviour.counter == 1
    assert behaviour.state == AsyncBehaviour.AsyncState.RUNNING
    behaviour.act()
    assert behaviour.counter == 2
    assert behaviour.state == AsyncBehaviour.AsyncState.RUNNING
    behaviour.act()
    assert behaviour.counter == 3
    assert behaviour.state == AsyncBehaviour.AsyncState.READY


def test_async_behaviour_wait_for_message() -> None:
    """Test 'wait_for_message'."""

    expected_message = "message"

    class MyAsyncBehaviour(AsyncBehaviourTest):
        counter = 0
        message = None

        def async_act(self) -> Generator:
            self.counter += 1
            self.message = yield from self.wait_for_message(
                lambda message: message == expected_message
            )
            self.counter += 1

    behaviour = MyAsyncBehaviour()
    assert behaviour.counter == 0
    behaviour.act()
    assert behaviour.counter == 1
    assert behaviour.state == AsyncBehaviour.AsyncState.WAITING_MESSAGE

    # another call to act doesn't change the state (still waiting for message)
    behaviour.act()
    assert behaviour.counter == 1
    assert behaviour.state == AsyncBehaviour.AsyncState.WAITING_MESSAGE

    # sending a message that does not satisfy the condition won't change state
    behaviour.try_send("wrong_message")
    behaviour.act()
    assert behaviour.counter == 1
    assert behaviour.state == AsyncBehaviour.AsyncState.WAITING_MESSAGE

    # sending a message before it is processed raises an exception
    behaviour.try_send("wrong_message")
    with pytest.raises(SendException, match="cannot send message"):
        behaviour.try_send("wrong_message")
    behaviour.act()

    # sending the right message will transition to the next state,
    # but only when calling act()
    behaviour.try_send(expected_message)
    assert behaviour.counter == 1
    assert behaviour.state == AsyncBehaviour.AsyncState.WAITING_MESSAGE
    behaviour.act()
    assert behaviour.counter == 2
    assert behaviour.message == expected_message
    assert behaviour.state == AsyncBehaviour.AsyncState.READY


def test_async_behaviour_wait_for_message_raises_timeout_exception() -> None:
    """Test 'wait_for_message' when it raises TimeoutException."""

    with pytest.raises(TimeoutException):
        behaviour = AsyncBehaviourTest()
        gen = behaviour.wait_for_message(lambda _: False, timeout=0.01)
        # trigger function
        try_send(gen)
        # sleep so to run out the timeout
        time.sleep(0.02)
        # trigger function and make the exception to raise
        try_send(gen)


def test_async_behaviour_wait_for_condition() -> None:
    """Test 'wait_for_condition' method."""

    condition = False

    class MyAsyncBehaviour(AsyncBehaviourTest):
        counter = 0

        def async_act(self) -> Generator:
            self.counter += 1
            yield from self.wait_for_condition(lambda: condition)
            self.counter += 1

    behaviour = MyAsyncBehaviour()
    assert behaviour.counter == 0
    behaviour.act()
    assert behaviour.counter == 1
    assert behaviour.state == AsyncBehaviour.AsyncState.RUNNING

    # if condition is false, execution remains at the same point
    behaviour.act()
    assert behaviour.counter == 1
    assert behaviour.state == AsyncBehaviour.AsyncState.RUNNING

    # if condition is true, execution continues
    condition = True
    behaviour.act()
    assert behaviour.counter == 2
    assert behaviour.state == AsyncBehaviour.AsyncState.READY


def test_async_behaviour_wait_for_condition_with_timeout() -> None:
    """Test 'wait_for_condition' method with timeout expired."""

    class MyAsyncBehaviour(AsyncBehaviourTest):
        counter = 0

        def async_act(self) -> Generator:
            self.counter += 1
            yield from self.wait_for_condition(lambda: False, timeout=0.05)
            self.counter += 1

    behaviour = MyAsyncBehaviour()
    assert behaviour.counter == 0
    behaviour.act()
    assert behaviour.counter == 1
    assert behaviour.state == AsyncBehaviour.AsyncState.RUNNING

    # sleep so the timeout expires
    time.sleep(0.1)

    # the next call to act raises TimeoutException
    with pytest.raises(TimeoutException):
        behaviour.act()


def test_async_behaviour_sleep() -> None:
    """Test 'sleep' method."""

    timedelta = 0.5

    class MyAsyncBehaviour(AsyncBehaviourTest):
        counter = 0
        first_datetime = None
        last_datetime = None

        def async_act_wrapper(self) -> Generator:
            yield from self.async_act()

        def async_act(self) -> Generator:
            self.first_datetime = datetime.now()
            self.counter += 1
            yield from self.sleep(timedelta)
            self.counter += 1
            self.last_datetime = datetime.now()

    behaviour = MyAsyncBehaviour()
    assert behaviour.counter == 0

    behaviour.act()
    assert behaviour.counter == 1
    assert behaviour.state == AsyncBehaviour.AsyncState.RUNNING

    # calling 'act()' before the sleep interval will keep the behaviour in the same state
    behaviour.act()
    assert behaviour.counter == 1
    assert behaviour.state == AsyncBehaviour.AsyncState.RUNNING

    # wait the sleep timeout
    time.sleep(timedelta)

    assert behaviour.counter == 1
    assert behaviour.state == AsyncBehaviour.AsyncState.RUNNING
    behaviour.act()
    assert behaviour.counter == 2
    assert behaviour.state == AsyncBehaviour.AsyncState.READY
    assert behaviour.last_datetime is not None and behaviour.first_datetime is not None
    assert (
        behaviour.last_datetime - behaviour.first_datetime
    ).total_seconds() > timedelta


def test_async_behaviour_without_yield() -> None:
    """Test AsyncBehaviour, async_act without yield/yield from."""

    class MyAsyncBehaviour(AsyncBehaviourTest):
        def async_act_wrapper(self) -> Generator:
            pass

        def async_act(self) -> Generator:
            pass

    behaviour = MyAsyncBehaviour()
    behaviour.act()
    assert behaviour.state == AsyncBehaviour.AsyncState.READY


def test_async_behaviour_raise_stopiteration() -> None:
    """Test AsyncBehaviour, async_act raising 'StopIteration'."""

    class MyAsyncBehaviour(AsyncBehaviourTest):
        def async_act_wrapper(self) -> Generator:
            raise StopIteration

        def async_act(self) -> Generator:
            pass

    behaviour = MyAsyncBehaviour()
    behaviour.act()
    assert behaviour.state == AsyncBehaviour.AsyncState.READY


def test_async_behaviour_stop() -> None:
    """Test AsyncBehaviour.stop method."""

    class MyAsyncBehaviour(AsyncBehaviourTest):
        def async_act(self) -> Generator:
            yield

    behaviour = MyAsyncBehaviour()
    assert behaviour.is_stopped
    behaviour.act()
    assert not behaviour.is_stopped
    behaviour.stop()
    assert behaviour.is_stopped
    behaviour.stop()
    assert behaviour.is_stopped


class RoundA(AbstractRound):
    """Concrete ABCI round."""

    round_id = "round_a"

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Enum]]:
        """Handle end block."""
        return None

    def check_payload(self, payload: BaseTxPayload) -> None:
        """Check payload."""

    def process_payload(self, payload: BaseTxPayload) -> None:
        """Process payload."""


class BehaviourATest(BaseBehaviour):
    """Concrete BaseBehaviour class."""

    behaviour_id = "behaviour_a"
    matching_round: Type[RoundA] = RoundA

    def async_act(self) -> Generator:
        """Do the 'async_act'."""
        yield


def _get_status_patch_wrapper(
    latest_block_height: int,
    expected_round_count: Optional[int],
    expected_reset_index: Optional[int],
) -> Callable[[Any, Any], Generator[None, None, MagicMock]]:
    """Wrapper for `_get_status` method patch."""

    if any(
        app_hash_param is None
        for app_hash_param in (expected_round_count, expected_reset_index)
    ):
        app_hash = ""
    else:
        app_hash = (
            f"{ROOT_HASH}{expected_round_count}{RESET_HASH}{expected_reset_index}"
        )

    def _get_status_patch(*_: Any, **__: Any) -> Generator[None, None, MagicMock]:
        """Patch `_get_status` method"""
        yield
        return MagicMock(
            body=json.dumps(
                {
                    "result": {
                        "sync_info": {
                            "latest_block_height": latest_block_height,
                            "latest_app_hash": app_hash,
                        }
                    }
                }
            ).encode()
        )

    return _get_status_patch


def _get_status_wrong_patch(
    *args: Any, **kwargs: Any
) -> Generator[None, None, MagicMock]:
    """Patch `_get_status` method"""
    return MagicMock(
        body=json.dumps({"result": {"sync_info": {"latest_block_height": -1}}}).encode()
    )
    yield


def _wait_until_transaction_delivered_patch(
    *args: Any, **kwargs: Any
) -> Generator[None, None, Tuple]:
    """Patch `_wait_until_transaction_delivered` method"""
    return False, HttpMessage(
        performative=HttpMessage.Performative.RESPONSE,  # type: ignore
        body=json.dumps({"tx_result": {"info": "TransactionNotValidError"}}),
    )
    yield


class TestBaseBehaviour:
    """Tests for the 'BaseBehaviour' class."""

    def setup(self) -> None:
        """Set up the tests."""
        self.context_mock = MagicMock()
        self.context_params_mock = MagicMock(
            ipfs_domain_name=None,
            request_timeout=_DEFAULT_REQUEST_TIMEOUT,
            request_retry_delay=_DEFAULT_REQUEST_RETRY_DELAY,
            tx_timeout=_DEFAULT_TX_TIMEOUT,
            max_attempts=_DEFAULT_TX_MAX_ATTEMPTS,
        )
        self.context_state_synchronized_data_mock = MagicMock()
        self.context_mock.params = self.context_params_mock
        self.context_mock.state.synchronized_data = (
            self.context_state_synchronized_data_mock
        )
        self.context_mock.state.round_sequence.current_round_id = "round_a"
        self.context_mock.state.round_sequence.syncing_up = False
        self.context_mock.state.round_sequence.block_stall_deadline_expired = False
        self.context_mock.http_dialogues = HttpDialogues()
        self.context_mock.handlers.__dict__ = {"http": MagicMock()}
        self.behaviour = BehaviourATest(name="", skill_context=self.context_mock)

    def test_params_property(self) -> None:
        """Test the 'params' property."""
        assert self.behaviour.params == self.context_params_mock

    def test_synchronized_data_property(self) -> None:
        """Test the 'synchronized_data' property."""
        assert (
            self.behaviour.synchronized_data
            == self.context_state_synchronized_data_mock
        )

    def test_check_in_round(self) -> None:
        """Test 'BaseBehaviour' initialization."""
        expected_round_id = "round"
        self.context_mock.state.round_sequence.current_round_id = expected_round_id
        assert self.behaviour.check_in_round(expected_round_id)
        assert not self.behaviour.check_in_round("wrong round")

        assert not self.behaviour.check_not_in_round(expected_round_id)
        assert self.behaviour.check_not_in_round("wrong round")

        func = self.behaviour.is_round_ended(expected_round_id)
        assert not func()

    def test_check_in_last_round(self) -> None:
        """Test 'BaseBehaviour' initialization."""
        expected_round_id = "round"
        self.context_mock.state.round_sequence.last_round_id = expected_round_id
        assert self.behaviour.check_in_last_round(expected_round_id)
        assert not self.behaviour.check_in_last_round("wrong round")

        assert not self.behaviour.check_not_in_last_round(expected_round_id)
        assert self.behaviour.check_not_in_last_round("wrong round")

        assert self.behaviour.check_round_has_finished(expected_round_id)

    def test_check_round_height_has_changed(self) -> None:
        """Test 'check_round_height_has_changed'."""
        current_height = 0
        self.context_mock.state.round_sequence.current_round_height = current_height
        assert not self.behaviour.check_round_height_has_changed(current_height)
        new_height = current_height + 1
        self.context_mock.state.round_sequence.current_round_height = new_height
        assert self.behaviour.check_round_height_has_changed(current_height)
        assert not self.behaviour.check_round_height_has_changed(new_height)

    def test_wait_until_round_end_negative_last_round_or_matching_round(self) -> None:
        """Test 'wait_until_round_end' method, negative case (not in matching nor last round)."""
        self.behaviour.context.state.round_sequence.current_round_id = (
            "current_round_id"
        )
        self.behaviour.context.state.round_sequence.last_round_id = "last_round_id"
        self.behaviour.matching_round.round_id = "matching_round"
        generator = self.behaviour.wait_until_round_end()
        with pytest.raises(
            ValueError,
            match=r"Should be in matching round \(matching_round\) or last round \(last_round_id\), actual round current_round_id!",
        ):
            generator.send(None)

    @mock.patch.object(BaseBehaviour, "wait_for_condition")
    @mock.patch.object(BaseBehaviour, "check_not_in_round", return_value=False)
    @mock.patch.object(BaseBehaviour, "check_not_in_last_round", return_value=False)
    def test_wait_until_round_end_positive(self, *_: Any) -> None:
        """Test 'wait_until_round_end' method, positive case."""
        gen = self.behaviour.wait_until_round_end()
        try_send(gen)

    def test_wait_from_last_timestamp(self) -> None:
        """Test 'wait_from_last_timestamp'."""
        timeout = 1.0
        last_timestamp = datetime.now()
        self.behaviour.context.state.round_sequence.abci_app.last_timestamp = (
            last_timestamp
        )
        gen = self.behaviour.wait_from_last_timestamp(timeout)
        # trigger first execution
        try_send(gen)
        # at the time this line is executed, the generator is not empty
        # as the timeout has not run out yet
        try_send(gen)
        # sleep enough time to make the timeout to run out
        time.sleep(timeout)
        # the next iteration of the generator raises StopIteration
        # because its execution terminates
        with pytest.raises(StopIteration):
            gen.send(MagicMock())

    def test_wait_from_last_timestamp_negative(self) -> None:
        """Test 'wait_from_last_timestamp'."""
        timeout = -1.0
        last_timestamp = datetime.now()
        self.behaviour.context.state.round_sequence.abci_app.last_timestamp = (
            last_timestamp
        )
        with pytest.raises(ValueError):
            gen = self.behaviour.wait_from_last_timestamp(timeout)
            # trigger first execution
            try_send(gen)

    def test_set_done(self) -> None:
        """Test 'set_done' method."""
        assert not self.behaviour.is_done()
        self.behaviour.set_done()
        assert self.behaviour.is_done()

    @mock.patch.object(BaseBehaviour, "_send_transaction")
    def test_send_a2a_transaction_positive(self, *_: Any) -> None:
        """Test 'send_a2a_transaction' method, positive case."""
        gen = self.behaviour.send_a2a_transaction(MagicMock())
        try_send(gen)

    @mock.patch.object(
        BaseBehaviour,
        "tm_communication_unhealthy",
        new_callable=mock.PropertyMock,
        return_value=True,
    )
    @pytest.mark.parametrize("tm_reset_success", (True, False))
    def test__check_tm_communication(
        self, _: mock._patch, tm_reset_success: bool
    ) -> None:
        """Test `__check_tm_communication`."""
        gen = self.behaviour._BaseBehaviour__check_tm_communication()

        with mock.patch.object(
            self.behaviour,
            "reset_tendermint_with_wait",
            side_effect=yield_and_return_bool_wrapper(tm_reset_success),
        ):
            try_send(gen)
            try_send(gen)

    @pytest.mark.parametrize("communication_is_healthy", (True, False))
    def test_async_act_wrapper_communication(
        self, communication_is_healthy: bool
    ) -> None:
        """Test 'async_act_wrapper' when tm communication is unhealthy."""
        gen = self.behaviour.async_act_wrapper()

        with mock.patch.object(
            self.behaviour,
            "_BaseBehaviour__check_tm_communication",
            side_effect=yield_and_return_bool_wrapper(communication_is_healthy),
        ):
            try_send(gen)
            try_send(gen)

        self.behaviour.set_done()
        with mock.patch.object(BaseBehaviour, "_log_end") as _log_end_mock:
            try_send(gen)
            if communication_is_healthy:
                _log_end_mock.assert_called_once()
            else:
                _log_end_mock.assert_not_called()

    def test_sync_state(self) -> None:
        """Test `_sync_state`."""
        app_hash = ""
        self.behaviour._sync_state(app_hash)
        assert self.behaviour.context.state.round_sequence.abci_app.reset_index == 0

        app_hash = "726F6F743A356072657365743A370"
        self.behaviour._sync_state(app_hash)
        assert self.behaviour.context.state.round_sequence.abci_app.reset_index == 70

        app_hash = "incorrect"
        with pytest.raises(
            ValueError,
            match=(
                "Expected an app hash of the form: `726F6F743A3{ROUND_COUNT}72657365743A3{RESET_INDEX}`,"
                "which is derived from `root:{ROUND_COUNT}reset:{RESET_INDEX}`. "
                "For example, `root:90reset:4` would be `726F6F743A39072657365743A34`. "
                f"However, the app hash received is: `{app_hash}`."
            ),
        ):
            self.behaviour._sync_state(app_hash)

    @pytest.mark.parametrize(
        "expected_round_count, expected_reset_index",
        ((None, None), (0, 0), (123, 4), (235235, 754)),
    )
    @mock.patch.object(
        BehaviourATest,
        "_BaseBehaviour__check_tm_communication",
        side_effect=yield_and_return_bool_wrapper(True),
    )
    def test_async_act_wrapper_agent_sync_mode(
        self,
        _: mock._patch,
        expected_round_count: Optional[int],
        expected_reset_index: Optional[int],
    ) -> None:
        """Test 'async_act_wrapper' in sync mode."""
        self.behaviour.context.state.round_sequence.syncing_up = True
        self.behaviour.context.state.round_sequence.height = 0
        self.behaviour.matching_round = MagicMock()
        self.behaviour.context.logger.info = lambda msg: logging.info(msg)  # type: ignore

        with mock.patch.object(logging, "info") as log_mock, mock.patch.object(
            BaseBehaviour,
            "_get_status",
            _get_status_patch_wrapper(0, expected_round_count, expected_reset_index),
        ):
            gen = self.behaviour.async_act_wrapper()
            for __ in range(3):
                try_send(gen)
            log_mock.assert_called_with("local height == remote == 0; Sync complete...")

        if any(
            app_hash_param is None
            for app_hash_param in (expected_round_count, expected_reset_index)
        ):
            expected_reset_index = 0

        assert (
            self.behaviour.context.state.round_sequence.abci_app.reset_index
            == expected_reset_index
        )

    @mock.patch.object(BaseBehaviour, "_get_status", _get_status_wrong_patch)
    def test_async_act_wrapper_agent_sync_mode_where_height_dont_match(self) -> None:
        """Test 'async_act_wrapper' in sync mode."""
        self.behaviour.context.state.round_sequence.syncing_up = True
        self.behaviour.context.state.round_sequence.height = 0
        self.behaviour.context.params.tendermint_check_sleep_delay = 3
        self.behaviour.matching_round = MagicMock()
        self.behaviour.context.logger.info = lambda msg: logging.info(msg)  # type: ignore

        gen = self.behaviour.async_act_wrapper()
        try_send(gen)

    @mock.patch.object(
        BehaviourATest,
        "_BaseBehaviour__check_tm_communication",
        side_effect=yield_and_return_bool_wrapper(True),
    )
    @pytest.mark.parametrize("exception_cls", [StopIteration])
    def test_async_act_wrapper_exception(
        self, _: mock._patch, exception_cls: Exception
    ) -> None:
        """Test 'async_act_wrapper'."""
        with mock.patch.object(self.behaviour, "async_act", side_effect=exception_cls):
            with mock.patch.object(self.behaviour, "clean_up") as clean_up_mock:
                gen = self.behaviour.async_act_wrapper()
                try_send(gen)
                try_send(gen)
                clean_up_mock.assert_called()

    def test_get_request_nonce_from_dialogue(self) -> None:
        """Test '_get_request_nonce_from_dialogue' helper method."""
        dialogue_mock = MagicMock()
        expected_value = "dialogue_reference"
        dialogue_mock.dialogue_label.dialogue_reference = (expected_value, None)
        result = BaseBehaviour._get_request_nonce_from_dialogue(dialogue_mock)
        assert result == expected_value

    @mock.patch.object(BaseBehaviour, "_send_signing_request")
    @mock.patch.object(Transaction, "encode", return_value=MagicMock())
    @mock.patch.object(
        BaseBehaviour,
        "_build_http_request_message",
        return_value=(MagicMock(), MagicMock()),
    )
    @mock.patch.object(BaseBehaviour, "_check_http_return_code_200", return_value=False)
    def test_send_transaction_stop_condition(self, *_: Any) -> None:
        """Test '_send_transaction' method's `stop_condition` as provided by `send_a2a_transaction`."""
        request_retry_delay = 0.01
        # set the current round's id so that it does not meet the requirements for a `stop_condition`
        self.behaviour.context.state.round_sequence.current_round_id = (
            self.behaviour.matching_round.round_id
        ) = "round_a"
        # assert that everything is pre-set correctly
        assert (
            self.behaviour.context.state.round_sequence.current_round_id
            == self.behaviour.matching_round.round_id
            == "round_a"
        )

        # create the exact same stop condition that we create in the `send_a2a_transaction` method
        stop_condition = self.behaviour.is_round_ended(
            self.behaviour.matching_round.round_id
        )
        gen = self.behaviour._send_transaction(
            MagicMock(),
            request_retry_delay=request_retry_delay,
            stop_condition=stop_condition,
        )
        # assert that the stop condition does not apply yet
        assert not stop_condition()
        # trigger the generator function so that we enter the `stop_condition` loop
        try_send(gen)

        # set the current round's id so that it meets the requirements for a `stop_condition`
        self.behaviour.context.state.round_sequence.current_round_id = "test"

        # assert that everything was set as expected
        assert (
            self.behaviour.context.state.round_sequence.current_round_id
            != self.behaviour.matching_round.round_id
            and self.behaviour.context.state.round_sequence.current_round_id == "test"
        )
        # assert that the stop condition now applies
        assert stop_condition()

        # test with a non-200 response in order to cause the execution to re-enter the while `stop_condition`
        # we expect that the second time we will not enter, since we have caused the `stop_condition` to be `True`
        with mock.patch.object(self.behaviour.context.logger, "info") as mock_info:
            # send message to 'wait_for_message'
            try_send(gen, obj=MagicMock(status_code=200))
            # send message to '_submit_tx'
            response = MagicMock(body='{"result": {"hash": "", "code": 0}}')
            try_send(gen, obj=response)
            mock_info.assert_called_with(
                f"Received return code != 200 with response {response} with body {str(response.body)}. "
                f"Retrying in {request_retry_delay} seconds..."
            )
            time.sleep(request_retry_delay)
            try_send(gen)
            # assert that the stop condition is now `True` and we reach at the end of the method
            mock_info.assert_called_with(
                "Stop condition is true, no more attempts to send the transaction."
            )

    def test_send_transaction_positive_false_condition(self) -> None:
        """Test '_send_transaction', positive case (false condition)"""
        with mock.patch.object(self.behaviour.context.logger, "info") as mock_info:
            try_send(
                self.behaviour._send_transaction(
                    MagicMock(), stop_condition=lambda: True
                )
            )
            mock_info.assert_called_with(
                "Stop condition is true, no more attempts to send the transaction."
            )

    @mock.patch.object(BaseBehaviour, "_send_signing_request")
    @mock.patch.object(Transaction, "encode", return_value=MagicMock())
    @mock.patch.object(
        BaseBehaviour,
        "_build_http_request_message",
        return_value=(MagicMock(), MagicMock()),
    )
    @mock.patch.object(BaseBehaviour, "_check_http_return_code_200", return_value=True)
    def test_send_transaction_positive(self, *_: Any) -> None:
        """Test '_send_transaction', positive case."""
        m = MagicMock(status_code=200)
        gen = self.behaviour._send_transaction(m)
        # trigger generator function
        try_send(gen, obj=None)
        # send message to 'wait_for_message'
        try_send(gen, obj=m)
        # send message to '_submit_tx'
        try_send(gen, obj=MagicMock(body='{"result": {"hash": "", "code": 0}}'))
        # send message to '_wait_until_transaction_delivered'
        success_response = MagicMock(
            status_code=200, body='{"result": {"tx_result": {"code": 0}}}'
        )
        try_send(gen, obj=success_response)

    @mock.patch.object(BaseBehaviour, "_send_signing_request")
    @mock.patch.object(Transaction, "encode", return_value=MagicMock())
    @mock.patch.object(
        BaseBehaviour,
        "_build_http_request_message",
        return_value=(MagicMock(), MagicMock()),
    )
    @mock.patch.object(BaseBehaviour, "_check_http_return_code_200", return_value=True)
    @mock.patch.object(
        BaseBehaviour,
        "_wait_until_transaction_delivered",
        new=_wait_until_transaction_delivered_patch,
    )
    def test_send_transaction_invalid_transaction(self, *_: Any) -> None:
        """Test '_send_transaction', positive case."""
        m = MagicMock(status_code=200)
        gen = self.behaviour._send_transaction(m)
        try_send(gen, obj=None)
        try_send(gen, obj=m)
        try_send(gen, obj=MagicMock(body='{"result": {"hash": "", "code": 0}}'))
        success_response = MagicMock(
            status_code=200, body='{"result": {"tx_result": {"code": 0}}}'
        )
        try_send(gen, obj=success_response)

    @mock.patch.object(BaseBehaviour, "_send_signing_request")
    @mock.patch.object(BaseBehaviour, "_is_invalid_transaction", return_value=False)
    @mock.patch.object(BaseBehaviour, "_tx_not_found", return_value=True)
    @mock.patch.object(Transaction, "encode", return_value=MagicMock())
    @mock.patch.object(
        BaseBehaviour,
        "_build_http_request_message",
        return_value=(MagicMock(), MagicMock()),
    )
    @mock.patch.object(BaseBehaviour, "_check_http_return_code_200", return_value=True)
    @mock.patch.object(
        BaseBehaviour,
        "_wait_until_transaction_delivered",
        new=_wait_until_transaction_delivered_patch,
    )
    def test_send_transaction_valid_transaction(self, *_: Any) -> None:
        """Test '_send_transaction', positive case."""
        m = MagicMock(status_code=200)
        gen = self.behaviour._send_transaction(m)
        try_send(gen, obj=None)
        try_send(gen, obj=m)
        try_send(gen, obj=MagicMock(body='{"result": {"hash": "", "code": 0}}'))
        success_response = MagicMock(
            status_code=200, body='{"result": {"tx_result": {"code": 0}}}'
        )
        try_send(gen, obj=success_response)

    def test_tx_not_found(self, *_: Any) -> None:
        """Test _tx_not_found"""
        res = MagicMock(
            body='{"error": {"code": "dummy_code", "message": "dummy_message", "data": "dummy_data"}}'
        )
        self.behaviour._tx_not_found(tx_hash="tx_hash", res=res)

    @mock.patch.object(BaseBehaviour, "_send_signing_request")
    def test_send_transaction_signing_error(self, *_: Any) -> None:
        """Test '_send_transaction', signing error."""
        m = MagicMock(performative=SigningMessage.Performative.ERROR)
        gen = self.behaviour._send_transaction(m)
        # trigger generator function
        try_send(gen, obj=None)
        with pytest.raises(RuntimeError):
            try_send(gen, obj=m)

    @mock.patch.object(BaseBehaviour, "_send_signing_request")
    @mock.patch.object(Transaction, "encode", return_value=MagicMock())
    @mock.patch.object(
        BaseBehaviour,
        "_build_http_request_message",
        return_value=(MagicMock(), MagicMock()),
    )
    def test_send_transaction_timeout_exception_submit_tx(self, *_: Any) -> None:
        """Test '_send_transaction', timeout exception."""
        timeout = 0.05
        delay = 0.1
        m = MagicMock()
        with mock.patch.object(self.behaviour.context.logger, "info") as mock_info:
            gen = self.behaviour._send_transaction(
                m, request_timeout=timeout, request_retry_delay=delay
            )
            # trigger generator function
            try_send(gen, obj=None)
            try_send(gen, obj=m)
            time.sleep(timeout)
            try_send(gen, obj=m)
            time.sleep(delay)
            mock_info.assert_called_with(
                f"Timeout expired for submit tx. Retrying in {delay} seconds..."
            )
            try_send(gen, obj=None)

    @mock.patch.object(BaseBehaviour, "_send_signing_request")
    @mock.patch.object(Transaction, "encode", return_value=MagicMock())
    @mock.patch.object(
        BaseBehaviour,
        "_build_http_request_message",
        return_value=(MagicMock(), MagicMock()),
    )
    @mock.patch.object(BaseBehaviour, "_check_http_return_code_200", return_value=True)
    def test_send_transaction_timeout_exception_wait_until_transaction_delivered(
        self, *_: Any
    ) -> None:
        """Test '_send_transaction', timeout exception."""
        timeout = 0.05
        delay = 0.1
        m = MagicMock()
        with mock.patch.object(self.behaviour.context.logger, "info") as mock_info:
            gen = self.behaviour._send_transaction(
                m, request_retry_delay=delay, tx_timeout=timeout
            )
            # trigger generator function
            try_send(gen, obj=None)
            # send message to 'wait_for_message'
            try_send(gen, obj=m)
            # send message to '_submit_tx'
            try_send(gen, obj=MagicMock(body='{"result": {"hash": "", "code": 0}}'))
            # send message to '_wait_until_transaction_delivered'
            time.sleep(timeout)
            try_send(gen, obj=m)

            mock_info.assert_called_with(
                f"Timeout expired for wait until transaction delivered. Retrying in {delay} seconds..."
            )

    @mock.patch.object(BaseBehaviour, "_send_signing_request")
    @mock.patch.object(Transaction, "encode", return_value=MagicMock())
    @mock.patch.object(
        BaseBehaviour,
        "_build_http_request_message",
        return_value=(MagicMock(), MagicMock()),
    )
    @mock.patch.object(BaseBehaviour, "_check_http_return_code_200", return_value=True)
    def test_send_transaction_transaction_not_delivered(self, *_: Any) -> None:
        """Test '_send_transaction', timeout exception."""
        timeout = 0.05
        delay = 0.1
        m = MagicMock()
        with mock.patch.object(self.behaviour.context.logger, "info") as mock_info:
            gen = self.behaviour._send_transaction(
                m, request_retry_delay=delay, tx_timeout=timeout, max_attempts=0
            )
            # trigger generator function
            try_send(gen, obj=None)
            # send message to 'wait_for_message'
            try_send(gen, obj=m)
            # send message to '_submit_tx'
            try_send(gen, obj=MagicMock(body='{"result": {"hash": "", "code": 0}}'))
            # send message to '_wait_until_transaction_delivered'
            time.sleep(timeout)
            try_send(gen, obj=m)

            mock_info.assert_called_with("Tx sent but not delivered. Response = None")

    @mock.patch.object(BaseBehaviour, "_send_signing_request")
    @mock.patch.object(Transaction, "encode", return_value=MagicMock())
    @mock.patch.object(
        BaseBehaviour,
        "_build_http_request_message",
        return_value=(MagicMock(), MagicMock()),
    )
    @mock.patch.object(BaseBehaviour, "_check_http_return_code_200", return_value=True)
    def test_send_transaction_wrong_ok_code(self, *_: Any) -> None:
        """Test '_send_transaction', positive case."""
        m = MagicMock(status_code=200)
        gen = self.behaviour._send_transaction(m)

        with mock.patch.object(self.behaviour.context.logger, "info") as mock_info:
            # trigger generator function
            try_send(gen, obj=None)
            # send message to 'wait_for_message'
            try_send(gen, obj=m)
            # send message to '_submit_tx'
            try_send(gen, obj=MagicMock(body='{"result": {"hash": "", "code": -1}}'))
            # send message to '_wait_until_transaction_delivered'
            success_response = MagicMock(
                status_code=200, body='{"result": {"tx_result": {"code": 0}}}'
            )
            try_send(gen, obj=success_response)

            mock_info.assert_called_with(
                "Received tendermint code != 0. Retrying in 1.0 seconds..."
            )

    @pytest.mark.skip
    @mock.patch.object(BaseBehaviour, "_send_signing_request")
    @mock.patch.object(Transaction, "encode", return_value=MagicMock())
    @mock.patch.object(
        BaseBehaviour,
        "_build_http_request_message",
        return_value=(MagicMock(), MagicMock()),
    )
    @mock.patch.object(
        BaseBehaviour,
        "_check_http_return_code_200",
        return_value=True,
    )
    @mock.patch("json.loads")
    def test_send_transaction_wait_delivery_timeout_exception(self, *_: Any) -> None:
        """Test '_send_transaction', timeout exception on tx delivery."""
        timeout = 0.05
        delay = 0.1
        m = MagicMock()
        with mock.patch.object(self.behaviour.context.logger, "info") as mock_info:
            gen = self.behaviour._send_transaction(
                m,
                request_timeout=timeout,
                request_retry_delay=delay,
                tx_timeout=timeout,
            )
            # trigger generator function
            try_send(gen, obj=None)
            try_send(gen, obj=m)
            try_send(gen, obj=m)
            time.sleep(timeout)
            try_send(gen, obj=m)
            mock_info.assert_called_with(
                f"Timeout expired for wait until transaction delivered. Retrying in {delay} seconds..."
            )
            time.sleep(delay)
            try_send(gen, obj=m)

    @pytest.mark.parametrize("resetting", (True, False))
    @pytest.mark.parametrize(
        "non_200_count",
        (
            0,
            NON_200_RETURN_CODE_DURING_RESET_THRESHOLD,
            NON_200_RETURN_CODE_DURING_RESET_THRESHOLD + 1,
        ),
    )
    @mock.patch.object(BaseBehaviour, "_send_signing_request")
    @mock.patch.object(Transaction, "encode", return_value=MagicMock())
    @mock.patch.object(
        BaseBehaviour,
        "_build_http_request_message",
        return_value=(MagicMock(), MagicMock()),
    )
    @mock.patch("json.loads")
    def test_send_transaction_error_status_code(
        self, _: Any, __: Any, ___: Any, ____: Any, resetting: bool, non_200_count: int
    ) -> None:
        """Test '_send_transaction', error status code."""
        delay = 0.1
        self.behaviour._non_200_return_code_count = non_200_count
        m = MagicMock()
        with mock.patch.object(self.behaviour.context.logger, "info") as mock_info:
            gen = self.behaviour._send_transaction(
                m, resetting, request_retry_delay=delay
            )
            # trigger generator function
            try_send(gen, obj=None)
            try_send(gen, obj=m)
            # send message to '_submit_tx'
            res = MagicMock(body="{'test': 'test'}")
            try_send(gen, obj=res)
            if (
                resetting
                and non_200_count <= NON_200_RETURN_CODE_DURING_RESET_THRESHOLD
            ):
                mock_info.assert_not_called()
            else:
                mock_info.assert_called_with(
                    f"Received return code != 200 with response {res} with body {str(res.body)}. "
                    f"Retrying in {delay} seconds..."
                )
            time.sleep(delay)
            try_send(gen, obj=None)

    @mock.patch.object(BaseBehaviour, "_get_request_nonce_from_dialogue")
    @mock.patch("packages.valory.skills.abstract_round_abci.behaviour_utils.RawMessage")
    @mock.patch("packages.valory.skills.abstract_round_abci.behaviour_utils.Terms")
    def test_send_signing_request(self, *_: Any) -> None:
        """Test '_send_signing_request'."""
        with mock.patch.object(
            self.behaviour.context.signing_dialogues,
            "create",
            return_value=(MagicMock(), MagicMock()),
        ):
            self.behaviour._send_signing_request(b"")

    @pytest.mark.skip
    def test_fuzz_send_signing_request(self) -> None:
        """Test '_send_signing_request'.

        Do not run this test through pytest. Add the following lines at the bottom
        of the file and run it as a script:
        t = TestBaseBehaviour()
        t.setup()
        t.test_fuzz_send_signing_request()
        """

        @atheris.instrument_func
        def fuzz_send_signing_request(input_bytes: bytes) -> None:
            """Fuzz '_send_signing_request'.

            Mock context manager decorators don't work here.

            :param input_bytes: fuzz input
            """
            with mock.patch.object(
                self.behaviour.context.signing_dialogues,
                "create",
                return_value=(MagicMock(), MagicMock()),
            ):
                with mock.patch(
                    "packages.valory.skills.abstract_round_abci.behaviour_utils.RawMessage"
                ):
                    with mock.patch(
                        "packages.valory.skills.abstract_round_abci.behaviour_utils.Terms"
                    ):
                        self.behaviour._send_signing_request(input_bytes)

        atheris.instrument_all()
        atheris.Setup(sys.argv, fuzz_send_signing_request)
        atheris.Fuzz()

    @mock.patch.object(BaseBehaviour, "_get_request_nonce_from_dialogue")
    @mock.patch("packages.valory.skills.abstract_round_abci.behaviour_utils.RawMessage")
    @mock.patch("packages.valory.skills.abstract_round_abci.behaviour_utils.Terms")
    def test_send_transaction_signing_request(self, *_: Any) -> None:
        """Test '_send_signing_request'."""
        with mock.patch.object(
            self.behaviour.context.signing_dialogues,
            "create",
            return_value=(MagicMock(), MagicMock()),
        ):
            self.behaviour._send_transaction_signing_request(MagicMock(), MagicMock())

    def test_send_transaction_request(self) -> None:
        """Test '_send_transaction_request'."""
        with mock.patch.object(
            self.behaviour.context.ledger_api_dialogues,
            "create",
            return_value=(MagicMock(), MagicMock()),
        ):
            self.behaviour._send_transaction_request(MagicMock())

    def test_send_transaction_receipt_request(self) -> None:
        """Test '_send_transaction_receipt_request'."""
        with mock.patch.object(
            self.behaviour.context.ledger_api_dialogues,
            "create",
            return_value=(MagicMock(), MagicMock()),
        ):
            self.behaviour.context.default_ledger_id = "default_ledger_id"  # type: ignore
            self.behaviour._send_transaction_receipt_request("digest")

    def test_build_http_request_message(self, *_: Any) -> None:
        """Test '_build_http_request_message'."""
        with mock.patch.object(
            self.behaviour.context.http_dialogues,
            "create",
            return_value=(MagicMock(), MagicMock()),
        ):
            self.behaviour._build_http_request_message(
                "",
                "",
                parameters=[("foo", "bar")],
                headers=[OrderedDict({"foo": "foo_val", "bar": "bar_val"})],
            )

    @mock.patch.object(Transaction, "encode", return_value=MagicMock())
    @mock.patch.object(
        BaseBehaviour,
        "_build_http_request_message",
        return_value=(MagicMock(), MagicMock()),
    )
    @mock.patch.object(BaseBehaviour, "_check_http_return_code_200", return_value=True)
    @mock.patch.object(BaseBehaviour, "sleep")
    @mock.patch("json.loads")
    def test_wait_until_transaction_delivered(self, *_: Any) -> None:
        """Test '_wait_until_transaction_delivered' method."""
        gen = self.behaviour._wait_until_transaction_delivered(MagicMock())
        # trigger generator function
        try_send(gen, obj=None)

        # first check attempt fails
        failure_response = MagicMock(status_code=500)
        try_send(gen, failure_response)

        # second check attempt succeeds
        success_response = MagicMock(
            status_code=200, body='{"result": {"tx_result": {"code": 0}}}'
        )
        try_send(gen, success_response)

    @mock.patch.object(Transaction, "encode", return_value=MagicMock())
    @mock.patch.object(
        BaseBehaviour,
        "_build_http_request_message",
        return_value=(MagicMock(), MagicMock()),
    )
    @mock.patch.object(BaseBehaviour, "_check_http_return_code_200", return_value=True)
    @mock.patch.object(BaseBehaviour, "sleep")
    @mock.patch("json.loads")
    def test_wait_until_transaction_delivered_failed(self, *_: Any) -> None:
        """Test '_wait_until_transaction_delivered' method."""
        gen = self.behaviour._wait_until_transaction_delivered(
            MagicMock(), max_attempts=0
        )
        # trigger generator function
        try_send(gen, obj=None)

        # first check attempt fails
        failure_response = MagicMock(status_code=500)
        try_send(gen, failure_response)

        # second check attempt succeeds
        success_response = MagicMock(
            status_code=200, body='{"result": {"tx_result": {"code": -1}}}'
        )
        try_send(gen, success_response)

    def test_wait_until_transaction_delivered_raises_timeout(self, *_: Any) -> None:
        """Test '_wait_until_transaction_delivered' method."""
        gen = self.behaviour._wait_until_transaction_delivered(MagicMock(), timeout=0.0)
        with pytest.raises(TimeoutException):
            # trigger generator function
            try_send(gen, obj=None)

    @mock.patch("packages.valory.skills.abstract_round_abci.behaviour_utils.Terms")
    def test_get_default_terms(self, *_: Any) -> None:
        """Test '_get_default_terms'."""
        self.behaviour._get_default_terms()

    @mock.patch.object(BaseBehaviour, "_send_transaction_signing_request")
    @mock.patch.object(BaseBehaviour, "_send_transaction_request")
    @mock.patch.object(BaseBehaviour, "_send_transaction_receipt_request")
    @mock.patch("packages.valory.skills.abstract_round_abci.behaviour_utils.Terms")
    def test_send_raw_transaction(self, *_: Any) -> None:
        """Test 'send_raw_transaction'."""
        m = MagicMock()
        gen = self.behaviour.send_raw_transaction(m)
        # trigger generator function
        try_send(gen, obj=None)
        try_send(
            gen,
            obj=MagicMock(performative=SigningMessage.Performative.SIGNED_TRANSACTION),
        )
        try_send(
            gen,
            obj=MagicMock(
                performative=LedgerApiMessage.Performative.TRANSACTION_DIGEST
            ),
        )
        try_send(gen, obj=m)

    @mock.patch.object(BaseBehaviour, "_send_transaction_signing_request")
    @mock.patch.object(BaseBehaviour, "_send_transaction_request")
    @mock.patch.object(BaseBehaviour, "_send_transaction_receipt_request")
    @mock.patch("packages.valory.skills.abstract_round_abci.behaviour_utils.Terms")
    def test_send_raw_transaction_with_wrong_signing_performative(
        self, *_: Any
    ) -> None:
        """Test 'send_raw_transaction'."""
        m = MagicMock()
        gen = self.behaviour.send_raw_transaction(m)
        # trigger generator function
        try_send(gen, obj=None)
        try_send(
            gen,
            obj=MagicMock(performative=SigningMessage.Performative.ERROR),
        )
        try_send(gen, obj=m)
        try_send(gen, obj=m)

    @mock.patch.object(BaseBehaviour, "_send_transaction_signing_request")
    @mock.patch.object(BaseBehaviour, "_send_transaction_request")
    @mock.patch.object(BaseBehaviour, "_send_transaction_receipt_request")
    @mock.patch("packages.valory.skills.abstract_round_abci.behaviour_utils.Terms")
    def test_send_raw_transaction_transaction_digest_error(self, *_: Any) -> None:
        """Test 'send_raw_transaction'."""
        m = MagicMock()
        gen = self.behaviour.send_raw_transaction(m)
        # trigger generator function
        try_send(gen, obj=None)
        try_send(
            gen,
            obj=MagicMock(performative=SigningMessage.Performative.SIGNED_TRANSACTION),
        )
        try_send(
            gen,
            obj=MagicMock(performative=LedgerApiMessage.Performative.ERROR),
        )
        try_send(gen, obj=m)

    @pytest.mark.parametrize(
        "message",
        ("replacement transaction underpriced", "nonce too low", "insufficient funds"),
    )
    @mock.patch.object(BaseBehaviour, "_send_transaction_signing_request")
    @mock.patch.object(BaseBehaviour, "_send_transaction_request")
    @mock.patch.object(BaseBehaviour, "_send_transaction_receipt_request")
    @mock.patch("packages.valory.skills.abstract_round_abci.behaviour_utils.Terms")
    def test_send_raw_transaction_errors(
        self, _: Any, __: Any, ___: Any, ____: Any, message: str
    ) -> None:
        """Test 'send_raw_transaction'."""
        m = MagicMock()
        gen = self.behaviour.send_raw_transaction(m)
        # trigger generator function
        try_send(gen, obj=None)
        try_send(
            gen,
            obj=MagicMock(performative=SigningMessage.Performative.SIGNED_TRANSACTION),
        )
        try_send(
            gen,
            obj=MagicMock(
                performative=LedgerApiMessage.Performative.ERROR,
                message=message,
            ),
        )
        try_send(gen, obj=m)

    @pytest.mark.parametrize("contract_address", [None, "contract_address"])
    def test_get_contract_api_response(self, contract_address: Optional[str]) -> None:
        """Test 'get_contract_api_response'."""
        with mock.patch.object(
            self.behaviour.context.contract_api_dialogues,
            "create",
            return_value=(MagicMock(), MagicMock()),
        ), mock.patch(
            "packages.valory.skills.abstract_round_abci.behaviour_utils.Terms"
        ), mock.patch.object(
            BaseBehaviour, "_send_transaction_signing_request"
        ), mock.patch.object(
            BaseBehaviour, "_send_transaction_request"
        ):
            gen = self.behaviour.get_contract_api_response(
                MagicMock(), contract_address, "contract_id", "contract_callable"
            )
            # first trigger
            try_send(gen, obj=None)
            # wait for message
            try_send(gen, obj=MagicMock())

    @mock.patch.object(
        BaseBehaviour, "_build_http_request_message", return_value=(None, None)
    )
    def test_get_status(self, _: mock.Mock) -> None:
        """Test '_get_status'."""
        expected_result = json.dumps("Test result.").encode()

        def dummy_do_request(*_: Any) -> Generator[None, None, MagicMock]:
            """Dummy `_do_request` method."""
            yield
            return mock.MagicMock(body=expected_result)

        with mock.patch.object(
            BaseBehaviour, "_do_request", side_effect=dummy_do_request
        ):
            get_status_generator = self.behaviour._get_status()
            next(get_status_generator)
            with pytest.raises(StopIteration) as e:
                next(get_status_generator)
            res = e.value.args[0]
            assert isinstance(res, MagicMock)
            assert res.body == expected_result

    def test_default_callback_request_stopped(self) -> None:
        """Test 'default_callback_request' when stopped."""
        message = MagicMock()
        current_behaviour = self.behaviour
        with mock.patch.object(self.behaviour.context.logger, "debug") as info_mock:
            self.behaviour.get_callback_request()(message, current_behaviour)
            info_mock.assert_called_with(
                "dropping message as behaviour has stopped: %s", message
            )

    def test_default_callback_late_arriving_message(self, *_: Any) -> None:
        """Test 'default_callback_request' when a message arrives late."""
        self.behaviour._AsyncBehaviour__stopped = False  # type: ignore
        message = MagicMock()
        current_behaviour = MagicMock()
        with mock.patch.object(self.behaviour.context.logger, "warning") as info_mock:
            self.behaviour.get_callback_request()(message, current_behaviour)
            info_mock.assert_called_with(
                "No callback defined for request with nonce: "
                f"{message.dialogue_reference.__getitem__()}, "
                f"arriving for behaviour: behaviour_a"
            )

    def test_default_callback_request_waiting_message(self, *_: Any) -> None:
        """Test 'default_callback_request' when waiting message."""
        self.behaviour._AsyncBehaviour__stopped = False  # type: ignore
        self.behaviour._AsyncBehaviour__state = (  # type: ignore
            AsyncBehaviour.AsyncState.WAITING_MESSAGE
        )
        message = MagicMock()
        current_behaviour = self.behaviour
        self.behaviour.get_callback_request()(message, current_behaviour)

    def test_default_callback_request_else(self, *_: Any) -> None:
        """Test 'default_callback_request' else branch."""
        self.behaviour._AsyncBehaviour__stopped = False  # type: ignore
        message = MagicMock()
        current_behaviour = self.behaviour
        with mock.patch.object(self.behaviour.context.logger, "warning") as info_mock:
            self.behaviour.get_callback_request()(message, current_behaviour)
            info_mock.assert_called_with(
                "could not send message to FSMBehaviour: %s", message
            )

    def test_stop(self) -> None:
        """Test the stop method."""
        self.behaviour.stop()

    @staticmethod
    def dummy_sleep(*_: Any) -> Generator[None, None, None]:
        """Dummy `sleep` method."""
        yield

    def test_start_reset(self) -> None:
        """Test the `_start_reset` method."""
        with mock.patch.object(
            BaseBehaviour,
            "wait_from_last_timestamp",
            new_callable=lambda *_: self.dummy_sleep,
        ):
            res = self.behaviour._start_reset()
            for _ in range(2):
                next(res)
            assert self.behaviour._check_started is not None
            assert self.behaviour._check_started <= datetime.now()
            assert self.behaviour._timeout == self.behaviour.params.max_healthcheck
            assert not self.behaviour._is_healthy

    def test_end_reset(self) -> None:
        """Test the `_end_reset` method."""
        self.behaviour._end_reset()
        assert self.behaviour._check_started is None
        assert self.behaviour._timeout == -1.0
        assert self.behaviour._is_healthy

    @pytest.mark.parametrize(
        "check_started, is_healthy, timeout, expiration_expected",
        (
            (None, True, 0, False),
            (None, False, 0, False),
            (datetime(1, 1, 1), True, 0, False),
            (datetime.now(), False, 3000, False),
            (datetime(1, 1, 1), False, 0, True),
        ),
    )
    def test_is_timeout_expired(
        self,
        check_started: Optional[datetime],
        is_healthy: bool,
        timeout: float,
        expiration_expected: bool,
    ) -> None:
        """Test the `_is_timeout_expired` method."""
        self.behaviour._check_started = check_started
        self.behaviour._is_healthy = is_healthy
        self.behaviour._timeout = timeout
        assert self.behaviour._is_timeout_expired() == expiration_expected

    @mock.patch.object(BaseBehaviour, "_start_reset")
    @mock.patch.object(BaseBehaviour, "_is_timeout_expired")
    def test_reset_tendermint_with_wait_timeout_expired(self, *_: mock.Mock) -> None:
        """Test tendermint reset."""
        with pytest.raises(RuntimeError, match="Error resetting tendermint node."):
            next(self.behaviour.reset_tendermint_with_wait())

    @mock.patch.object(BaseBehaviour, "_start_reset")
    @mock.patch.object(
        BaseBehaviour, "_build_http_request_message", return_value=(None, None)
    )
    @pytest.mark.parametrize(
        "reset_response, status_response, local_height, n_iter, expecting_success",
        (
            (
                {"message": "Tendermint reset was successful.", "status": True},
                {"result": {"sync_info": {"latest_block_height": 1}}},
                1,
                3,
                True,
            ),
            (
                {"message": "Tendermint reset was successful.", "status": True},
                {"result": {"sync_info": {"latest_block_height": 1}}},
                3,
                3,
                False,
            ),
            (
                {"message": "Error resetting tendermint.", "status": False},
                {},
                0,
                2,
                False,
            ),
            ("wrong_response", {}, 0, 2, False),
            (
                {"message": "Reset Successful.", "status": True},
                "not_accepting_txs_yet",
                0,
                3,
                False,
            ),
        ),
    )
    def test_reset_tendermint_with_wait(
        self,
        build_http_request_message_mock: mock.Mock,
        _start_reset: mock.Mock,
        reset_response: Union[Dict[str, Union[bool, str]], str],
        status_response: Union[Dict[str, Union[int, str]], str],
        local_height: int,
        n_iter: int,
        expecting_success: bool,
    ) -> None:
        """Test tendermint reset."""

        def dummy_do_request(*_: Any) -> Generator[None, None, MagicMock]:
            """Dummy `_do_request` method."""
            yield
            if reset_response == "wrong_response":
                return mock.MagicMock(body=b"")
            return mock.MagicMock(body=json.dumps(reset_response).encode())

        def dummy_get_status(*_: Any) -> Generator[None, None, MagicMock]:
            """Dummy `_get_status` method."""
            yield
            if status_response == "not_accepting_txs_yet":
                return mock.MagicMock(body=b"")
            return mock.MagicMock(body=json.dumps(status_response).encode())

        self.behaviour.params.observation_interval = 1
        with mock.patch.object(
            BaseBehaviour, "_is_timeout_expired", return_value=False
        ), mock.patch.object(
            BaseBehaviour,
            "wait_from_last_timestamp",
            new_callable=lambda *_: self.dummy_sleep,
        ), mock.patch.object(
            BaseBehaviour, "_do_request", new_callable=lambda *_: dummy_do_request
        ), mock.patch.object(
            BaseBehaviour, "_get_status", new_callable=lambda *_: dummy_get_status
        ), mock.patch.object(
            BaseBehaviour, "sleep", new_callable=lambda *_: self.dummy_sleep
        ):
            self.behaviour.context.state.round_sequence.height = local_height
            reset = self.behaviour.reset_tendermint_with_wait()
            for _ in range(n_iter):
                next(reset)
            offset = math.ceil(
                self.behaviour.params.observation_interval * HEIGHT_OFFSET_MULTIPLIER
            )
            offset = max(MIN_HEIGHT_OFFSET, offset)
            assert offset == 10
            initial_height = str(
                self.behaviour.context.state.round_sequence.last_round_transition_tm_height
                + offset
            )
            genesis_time = self.behaviour.context.state.round_sequence.last_round_transition_timestamp.astimezone(
                pytz.UTC
            ).strftime(
                "%Y-%m-%dT%H:%M:%S.%fZ"
            )

            expected_parameters = [
                ("genesis_time", genesis_time),
                ("initial_height", initial_height),
            ]
            build_http_request_message_mock.assert_called_with(
                "GET",
                self.behaviour.context.params.tendermint_com_url + "/hard_reset",
                parameters=expected_parameters,
            )
            # perform the last iteration which also returns the result
            try:
                next(reset)
            except StopIteration as e:
                assert e.value == expecting_success
            else:
                pytest.fail("`reset_tendermint_with_wait` did not finish!")

    @pytest.mark.skip
    def test_fuzz_submit_tx(self) -> None:
        """Test '_submit_tx'.

        Do not run this test through pytest. Add the following lines at the bottom
        of the file and run it as a script:
        t = TestBaseBehaviour()
        t.setup()
        t.test_fuzz_submit_tx()
        """

        @atheris.instrument_func
        def fuzz_submit_tx(input_bytes: bytes) -> None:
            """Fuzz '_submit_tx'.

            Mock context manager decorators don't work here.

            :param input_bytes: fuzz input
            """
            self.behaviour._submit_tx(input_bytes)

        atheris.instrument_all()
        atheris.Setup(sys.argv, fuzz_submit_tx)
        atheris.Fuzz()


@mock.patch.object(
    DegenerateBehaviour,
    "_BaseBehaviour__check_tm_communication",
    side_effect=yield_and_return_bool_wrapper(True),
)
def test_degenerate_behaviour_async_act(_: mock._patch) -> None:
    """Test DegenerateBehaviour.async_act."""

    class ConcreteDegenerateBehaviour(DegenerateBehaviour):
        """Concrete DegenerateBehaviour class."""

        behaviour_id = "concrete_degenerate_behaviour"
        matching_round = MagicMock()

    context = MagicMock()
    context.params.ipfs_domain_name = None
    # this is needed to trigger execution of async_act
    context.state.round_sequence.syncing_up = False
    context.state.round_sequence.block_stall_deadline_expired = False

    behaviour = ConcreteDegenerateBehaviour(
        name=ConcreteDegenerateBehaviour.behaviour_id, skill_context=context
    )
    behaviour.act()
    with pytest.raises(
        RuntimeError,
        match="The execution reached a degenerate behaviour. "
        "This means a degenerate round has been reached during the execution of the ABCI application. "
        "Please check the functioning of the ABCI app.",
    ):
        behaviour.act()


def test_make_degenerate_behaviour() -> None:
    """Test 'make_degenerate_behaviour'."""
    round_id = "round_id"
    new_cls = make_degenerate_behaviour(round_id)

    assert isinstance(new_cls, type)
    assert issubclass(new_cls, DegenerateBehaviour)

    assert new_cls.behaviour_id == f"degenerate_{round_id}"
