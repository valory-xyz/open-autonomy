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
import time
from abc import ABC
from collections import OrderedDict
from datetime import datetime
from enum import Enum
from typing import Any, Generator, Optional, Tuple, Type
from unittest import mock
from unittest.mock import MagicMock

import pytest

from packages.open_aea.protocols.signing import SigningMessage
from packages.valory.skills.abstract_round_abci.base import (
    AbstractRound,
    BasePeriodState,
    Period,
    Transaction,
)
from packages.valory.skills.abstract_round_abci.behaviour_utils import (
    AsyncBehaviour,
    BaseState,
    SendException,
    TimeoutException,
    _DEFAULT_REQUEST_RETRY_DELAY,
)

from tests.helpers.base import try_send


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

    def end_block(self) -> Optional[Tuple[BasePeriodState, Enum]]:
        """Handle end block."""
        return None

    round_id = "round_a"


class StateATest(BaseState):
    """Concrete BaseState class."""

    state_id = "state_a"
    matching_round: Optional[Type[RoundA]] = RoundA

    def async_act(self) -> Generator:
        """Do the 'async_act'."""
        yield


def _get_status_patch(*args: Any, **kwargs: Any) -> Generator[None, None, MagicMock]:
    """Patch `_get_status` method"""
    return MagicMock(
        body=json.dumps({"result": {"sync_info": {"latest_block_height": 0}}}).encode()
    )
    yield


def _wait_until_round_ends_patch(*args: Any, **kwargs: Any) -> Generator:
    """Patch `wait_until_round_ends` method"""
    yield


class TestBaseState:
    """Tests for the 'BaseState' class."""

    def setup(self) -> None:
        """Set up the tests."""
        self.context_mock = MagicMock()
        self.context_params_mock = MagicMock()
        self.context_state_period_state_mock = MagicMock()
        self.context_mock.params = self.context_params_mock
        self.context_mock.state.period_state = self.context_state_period_state_mock
        self.context_mock.state.period.current_round_id = "round_a"
        self.context_mock.state.period.syncing_up = False
        self.behaviour = StateATest(name="", skill_context=self.context_mock)

    def test_params_property(self) -> None:
        """Test the 'params' property."""
        assert self.behaviour.params == self.context_params_mock

    def test_period_state_property(self) -> None:
        """Test the 'period_state' property."""
        assert self.behaviour.period_state == self.context_state_period_state_mock

    def test_check_in_round(self) -> None:
        """Test 'BaseState' initialization."""
        expected_round_id = "round"
        self.context_mock.state.period.current_round_id = expected_round_id
        assert self.behaviour.check_in_round(expected_round_id)
        assert not self.behaviour.check_in_round("wrong round")

        assert not self.behaviour.check_not_in_round(expected_round_id)
        assert self.behaviour.check_not_in_round("wrong round")

        func = self.behaviour.is_round_ended(expected_round_id)
        assert not func()

    def test_check_in_last_round(self) -> None:
        """Test 'BaseState' initialization."""
        expected_round_id = "round"
        self.context_mock.state.period.last_round_id = expected_round_id
        assert self.behaviour.check_in_last_round(expected_round_id)
        assert not self.behaviour.check_in_last_round("wrong round")

        assert not self.behaviour.check_not_in_last_round(expected_round_id)
        assert self.behaviour.check_not_in_last_round("wrong round")

        assert self.behaviour.check_round_has_finished(expected_round_id)

    def test_check_round_height_has_changed(self) -> None:
        """Test 'check_round_height_has_changed'."""
        current_height = 0
        self.context_mock.state.period.current_round_height = current_height
        assert not self.behaviour.check_round_height_has_changed(current_height)
        new_height = current_height + 1
        self.context_mock.state.period.current_round_height = new_height
        assert self.behaviour.check_round_height_has_changed(current_height)
        assert not self.behaviour.check_round_height_has_changed(new_height)

    def test_wait_until_round_end_negative_no_matching_round(self) -> None:
        """Test 'wait_until_round_end' method, negative case (no matching round)."""
        self.behaviour.matching_round = None
        generator = self.behaviour.wait_until_round_end()
        with pytest.raises(ValueError, match="No matching_round set!"):
            generator.send(None)

    def test_wait_until_round_end_negative_last_round_or_matching_round(self) -> None:
        """Test 'wait_until_round_end' method, negative case (not in matching nor last round)."""
        self.behaviour.context.state.period.current_round_id = "current_round_id"
        self.behaviour.context.state.period.last_round_id = "last_round_id"
        assert self.behaviour.matching_round is not None
        self.behaviour.matching_round.round_id = "matching_round"
        generator = self.behaviour.wait_until_round_end()
        with pytest.raises(
            ValueError,
            match=r"Should be in matching round \(matching_round\) or last round \(last_round_id\), actual round current_round_id!",
        ):
            generator.send(None)

    @mock.patch.object(BaseState, "wait_for_condition")
    @mock.patch.object(BaseState, "check_not_in_round", return_value=False)
    @mock.patch.object(BaseState, "check_not_in_last_round", return_value=False)
    def test_wait_until_round_end_positive(self, *_: Any) -> None:
        """Test 'wait_until_round_end' method, positive case."""
        gen = self.behaviour.wait_until_round_end()
        try_send(gen)

    def test_wait_from_last_timestamp(self) -> None:
        """Test 'wait_from_last_timestamp'."""
        timeout = 1.0
        last_timestamp = datetime.now()
        self.behaviour.context.state.period.abci_app.last_timestamp = last_timestamp
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

    def test_set_done(self) -> None:
        """Test 'set_done' method."""
        assert not self.behaviour.is_done()
        self.behaviour.set_done()
        assert self.behaviour.is_done()

    def test_send_a2a_transaction_negative_no_matching_round(self) -> None:
        """Test 'send_a2a_transaction' method, negative case (no matching round)."""
        self.behaviour.matching_round = None
        generator = self.behaviour.send_a2a_transaction(MagicMock())
        with pytest.raises(ValueError, match="No matching_round set!"):
            try_send(generator)

    @mock.patch.object(BaseState, "_send_transaction")
    def test_send_a2a_transaction_positive(self, *_: Any) -> None:
        """Test 'send_a2a_transaction' method, positive case."""
        gen = self.behaviour.send_a2a_transaction(MagicMock())
        try_send(gen)

    def test_async_act_wrapper(self) -> None:
        """Test 'async_act_wrapper'."""
        gen = self.behaviour.async_act_wrapper()
        try_send(gen)
        self.behaviour.set_done()
        try_send(gen)

    @pytest.mark.parametrize("exception_cls", [StopIteration])
    def test_async_act_wrapper_exception(self, exception_cls: Exception) -> None:
        """Test 'async_act_wrapper'."""
        with mock.patch.object(self.behaviour, "async_act", side_effect=exception_cls):
            with mock.patch.object(self.behaviour, "clean_up") as clean_up_mock:
                gen = self.behaviour.async_act_wrapper()
                try_send(gen)
                clean_up_mock.assert_called()

    @mock.patch.object(BaseState, "_get_status", _get_status_patch)
    @mock.patch.object(BaseState, "wait_until_round_end", _wait_until_round_ends_patch)
    def test_async_act_wrapper_agent_sync_mode(self) -> None:
        """Test 'async_act_wrapper' in sync mode."""
        self.behaviour.context.state.period = Period(MagicMock())  # type: ignore
        self.behaviour.context.state.period.start_sync()
        self.behaviour.context.logger.info = lambda msg: logging.info(msg)  # type: ignore
        gen = self.behaviour.async_act_wrapper()
        gen.send(None)

    @mock.patch.object(BaseState, "_get_status", _get_status_patch)
    def test_async_act_wrapper_agent_sync_mode_with_round_none(self) -> None:
        """Test 'async_act_wrapper' in sync mode."""
        self.behaviour.context.state.period.syncing_up = True
        self.behaviour.context.state.period.height = 0
        self.behaviour.matching_round = None
        matching_round = self.behaviour.matching_round
        self.behaviour.context.logger.info = lambda msg: logging.info(msg)  # type: ignore

        with mock.patch.object(logging, "info") as log_mock:
            gen = self.behaviour.async_act_wrapper()
            gen.send(None)
            log_mock.assert_called()

        self.behaviour.matching_round = matching_round

    def test_get_request_nonce_from_dialogue(self) -> None:
        """Test '_get_request_nonce_from_dialogue' helper method."""
        dialogue_mock = MagicMock()
        expected_value = "dialogue_reference"
        dialogue_mock.dialogue_label.dialogue_reference = (expected_value, None)
        result = BaseState._get_request_nonce_from_dialogue(dialogue_mock)
        assert result == expected_value

    def test_send_transaction_positive_false_condition(self) -> None:
        """Test '_send_transaction', positive case (false condition)"""
        try_send(
            self.behaviour._send_transaction(MagicMock(), stop_condition=lambda: True)
        )

    @mock.patch.object(BaseState, "_send_signing_request")
    @mock.patch.object(Transaction, "encode", return_value=MagicMock())
    @mock.patch.object(
        BaseState,
        "_build_http_request_message",
        return_value=(MagicMock(), MagicMock()),
    )
    @mock.patch.object(BaseState, "_check_http_return_code_200", return_value=True)
    def test_send_transaction_positive(self, *_: Any) -> None:
        """Test '_send_transaction', positive case."""
        m = MagicMock(status_code=200)
        gen = self.behaviour._send_transaction(m)
        # trigger generator function
        try_send(gen, obj=None)
        # send message to 'wait_for_message'
        try_send(gen, obj=m)
        # send message to '_submit_tx'
        try_send(gen, obj=MagicMock(body='{"result": {"hash": ""}}'))
        # send message to '_wait_until_transaction_delivered'
        success_response = MagicMock(
            status_code=200, body='{"result": {"tx_result": {"code": 0}}}'
        )
        try_send(gen, obj=success_response)

    @mock.patch.object(BaseState, "_send_signing_request")
    def test_send_transaction_signing_error(self, *_: Any) -> None:
        """Test '_send_transaction', signing error."""
        m = MagicMock(performative=SigningMessage.Performative.ERROR)
        gen = self.behaviour._send_transaction(m)
        # trigger generator function
        try_send(gen, obj=None)
        with pytest.raises(RuntimeError):
            try_send(gen, obj=m)

    @mock.patch.object(BaseState, "_send_signing_request")
    @mock.patch.object(Transaction, "encode", return_value=MagicMock())
    @mock.patch.object(
        BaseState,
        "_build_http_request_message",
        return_value=(MagicMock(), MagicMock()),
    )
    def test_send_transaction_timeout_exception(self, *_: Any) -> None:
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

    @mock.patch.object(BaseState, "_send_signing_request")
    @mock.patch.object(Transaction, "encode", return_value=MagicMock())
    @mock.patch.object(
        BaseState,
        "_build_http_request_message",
        return_value=(MagicMock(), MagicMock()),
    )
    @mock.patch.object(
        BaseState,
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

    @mock.patch.object(BaseState, "_send_signing_request")
    @mock.patch.object(Transaction, "encode", return_value=MagicMock())
    @mock.patch.object(
        BaseState,
        "_build_http_request_message",
        return_value=(MagicMock(), MagicMock()),
    )
    @mock.patch("json.loads")
    def test_send_transaction_error_status_code(self, *_: Any) -> None:
        """Test '_send_transaction', erorr status code."""
        m = MagicMock()
        gen = self.behaviour._send_transaction(m)
        # trigger generator function
        try_send(gen, obj=None)
        try_send(gen, obj=m)
        try_send(gen, obj=m)
        time.sleep(_DEFAULT_REQUEST_RETRY_DELAY)
        try_send(gen, obj=None)

    @mock.patch.object(BaseState, "_get_request_nonce_from_dialogue")
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

    @mock.patch.object(BaseState, "_get_request_nonce_from_dialogue")
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
        BaseState,
        "_build_http_request_message",
        return_value=(MagicMock(), MagicMock()),
    )
    @mock.patch.object(BaseState, "_check_http_return_code_200", return_value=True)
    @mock.patch.object(BaseState, "sleep")
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
        BaseState,
        "_build_http_request_message",
        return_value=(MagicMock(), MagicMock()),
    )
    @mock.patch.object(BaseState, "_check_http_return_code_200", return_value=True)
    @mock.patch.object(BaseState, "sleep")
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

    @mock.patch.object(BaseState, "_send_transaction_signing_request")
    @mock.patch.object(BaseState, "_send_transaction_request")
    @mock.patch.object(BaseState, "_send_transaction_receipt_request")
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
        try_send(gen, obj=m)
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
            BaseState, "_send_transaction_signing_request"
        ), mock.patch.object(
            BaseState, "_send_transaction_request"
        ):
            gen = self.behaviour.get_contract_api_response(
                MagicMock(), contract_address, "contract_id", "contract_callable"
            )
            # first trigger
            try_send(gen, obj=None)
            # wait for message
            try_send(gen, obj=MagicMock())

    def test_default_callback_request_stopped(self) -> None:
        """Test 'default_callback_request' when stopped."""
        message = MagicMock()
        with mock.patch.object(self.behaviour.context.logger, "debug") as info_mock:
            self.behaviour.default_callback_request(message)
            info_mock.assert_called_with(
                "dropping message as behaviour has stopped: %s", message
            )

    def test_default_callback_request_waiting_message(self, *_: Any) -> None:
        """Test 'default_callback_request' when waiting message."""
        self.behaviour._AsyncBehaviour__stopped = False  # type: ignore
        self.behaviour._AsyncBehaviour__state = (  # type: ignore
            AsyncBehaviour.AsyncState.WAITING_MESSAGE
        )
        message = MagicMock()
        self.behaviour.default_callback_request(message)

    def test_default_callback_request_else(self, *_: Any) -> None:
        """Test 'default_callback_request' else branch."""
        self.behaviour._AsyncBehaviour__stopped = False  # type: ignore
        message = MagicMock()
        self.behaviour.default_callback_request(message)

    def test_stop(self) -> None:
        """Test the stop method."""
        self.behaviour.stop()
