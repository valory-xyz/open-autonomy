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

"""Test the behaviours_utils.py module of the skill."""
import time
from abc import ABC
from datetime import datetime
from typing import Generator, Optional, Tuple
from unittest import mock
from unittest.mock import MagicMock

import pytest

from packages.fetchai.protocols.signing import SigningMessage
from packages.valory.skills.abstract_round_abci.base import (
    AbstractRound,
    BasePeriodState,
    Transaction,
)
from packages.valory.skills.abstract_round_abci.behaviour_utils import (
    AsyncBehaviour,
    BaseState,
    DONE_EVENT,
    FAIL_EVENT,
    SendException,
    _REQUEST_RETRY_DELAY,
)

from tests.helpers.base import try_send


class AsyncBehaviourTest(AsyncBehaviour, ABC):
    """Concrete AsyncBehaviour class for testing purposes."""

    def async_act_wrapper(self) -> Generator:
        """Do async act wrapper. Forwards to 'async_act'."""
        yield from self.async_act()

    def async_act(self) -> Generator:
        """Do 'async_act'."""


def async_behaviour_initial_state_is_ready():
    """Check that the initial async state is "READY"."""
    behaviour = AsyncBehaviourTest()
    assert behaviour.state == AsyncBehaviour.AsyncState.READY


def test_async_behaviour_ticks():
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


def test_async_behaviour_wait_for_message():
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


def test_async_behaviour_wait_for_condition():
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


def test_async_behaviour_sleep():
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
    assert (
        behaviour.last_datetime - behaviour.first_datetime
    ).total_seconds() > timedelta


def test_async_behaviour_without_yield():
    """Test AsyncBehaviour, async_act without yield/yield from."""

    class MyAsyncBehaviour(AsyncBehaviourTest):
        def async_act_wrapper(self) -> Generator:
            pass

        def async_act(self) -> Generator:
            pass

    behaviour = MyAsyncBehaviour()
    behaviour.act()
    assert behaviour.state == AsyncBehaviour.AsyncState.READY


def test_async_behaviour_raise_stopiteration():
    """Test AsyncBehaviour, async_act raising 'StopIteration'."""

    class MyAsyncBehaviour(AsyncBehaviourTest):
        def async_act_wrapper(self) -> Generator:
            raise StopIteration

        def async_act(self) -> Generator:
            pass

    behaviour = MyAsyncBehaviour()
    behaviour.act()
    assert behaviour.state == AsyncBehaviour.AsyncState.READY


class RoundA(AbstractRound):
    """Concrete ABCI round."""

    def end_block(self) -> Optional[Tuple[BasePeriodState, "AbstractRound"]]:
        """Handle end block."""
        return None

    round_id = "round_a"


class StateATest(BaseState):
    """Concrete BaseState class."""

    state_id = "state_a"
    matching_round = RoundA

    def async_act(self) -> Generator:
        """Do the 'async_act'."""
        yield


class TestBaseState:
    """Tests for the 'BaseState' class."""

    def setup(self):
        """Set up the tests."""
        self.context_mock = MagicMock()
        self.behaviour = StateATest(name="", skill_context=self.context_mock)

    def test_check_in_round(self):
        """Test 'BaseState' initialization."""
        expected_round_id = "round"
        self.context_mock.state.period.current_round_id = expected_round_id
        assert self.behaviour.check_in_round(expected_round_id)
        assert not self.behaviour.check_in_round("wrong round")

        assert not self.behaviour.check_not_in_round(expected_round_id)
        assert self.behaviour.check_not_in_round("wrong round")

        func = self.behaviour.is_round_ended(expected_round_id)
        assert not func()

    def test_wait_until_round_end_negative_no_matching_round(self):
        """Test 'wait_until_round_end' method, negative case (no matching round)."""
        self.behaviour.matching_round = None
        generator = self.behaviour.wait_until_round_end()
        with pytest.raises(ValueError):
            generator.send(None)

    @mock.patch.object(BaseState, "wait_for_condition")
    def test_wait_until_round_end_positive(self, *_):
        """Test 'wait_until_round_end' method, positive case."""
        gen = self.behaviour.wait_until_round_end()
        try_send(gen)

    def test_set_done(self):
        """Test 'set_done' method."""
        assert not self.behaviour.is_done()
        self.behaviour.set_done()
        assert self.behaviour.is_done()
        assert self.behaviour._event == DONE_EVENT

    def test_set_fail(self):
        """Test 'set_fail' method."""
        assert not self.behaviour.is_done()
        self.behaviour.set_fail()
        assert self.behaviour.is_done()
        assert self.behaviour._event == FAIL_EVENT

    def test_send_a2a_transaction_negative_no_matching_round(self):
        """Test 'send_a2a_transaction' method, negative case (no matching round)."""
        self.behaviour.matching_round = None
        generator = self.behaviour.send_a2a_transaction(MagicMock())
        with pytest.raises(ValueError, match="No matching_round set!"):
            try_send(generator)

    @mock.patch.object(BaseState, "_send_transaction")
    def test_send_a2a_transaction_positive(self, *_):
        """Test 'send_a2a_transaction' method, positive case."""
        gen = self.behaviour.send_a2a_transaction(MagicMock())
        try_send(gen)

    def test_async_act_wrapper(self):
        """Test 'async_act_wrapper'."""
        gen = self.behaviour.async_act_wrapper()
        try_send(gen)
        self.behaviour.set_done()
        try_send(gen)

    def test_get_request_nonce_from_dialogue(self):
        """Test '_get_request_nonce_from_dialogue' helper method."""
        dialogue_mock = MagicMock()
        expected_value = "dialogue_reference"
        dialogue_mock.dialogue_label.dialogue_reference = (expected_value, None)
        result = BaseState._get_request_nonce_from_dialogue(dialogue_mock)
        assert result == expected_value

    def test_send_transaction_positive_false_condition(self):
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
    @mock.patch.object(BaseState, "_check_transaction_delivered", return_value=True)
    @mock.patch("json.loads")
    def test_send_transaction_positive(self, *_):
        """Test '_send_transaction', positive case."""
        m = MagicMock()
        gen = self.behaviour._send_transaction(m)
        # trigger generator function
        try_send(gen, obj=None)
        # send messages to 'wait_for_message'
        try_send(gen, obj=m)
        try_send(gen, obj=m)

    @mock.patch.object(BaseState, "_send_signing_request")
    def test_send_transaction_signing_error(self, *_):
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
    @mock.patch("json.loads")
    def test_send_transaction_error_status_code(self, *_):
        """Test '_send_transaction', erorr status code."""
        m = MagicMock()
        gen = self.behaviour._send_transaction(m)
        # trigger generator function
        try_send(gen, obj=None)
        try_send(gen, obj=m)
        try_send(gen, obj=m)
        time.sleep(_REQUEST_RETRY_DELAY)
        try_send(gen, obj=None)

    @mock.patch.object(BaseState, "_get_request_nonce_from_dialogue")
    @mock.patch("packages.valory.skills.abstract_round_abci.behaviour_utils.RawMessage")
    @mock.patch("packages.valory.skills.abstract_round_abci.behaviour_utils.Terms")
    def test_send_signing_request(self, *_):
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
    def test_send_transaction_signing_request(self, *_):
        """Test '_send_signing_request'."""
        with mock.patch.object(
            self.behaviour.context.signing_dialogues,
            "create",
            return_value=(MagicMock(), MagicMock()),
        ):
            self.behaviour._send_transaction_signing_request(MagicMock(), MagicMock())

    def test_send_transaction_request(self):
        """Test '_send_transaction_request'."""
        with mock.patch.object(
            self.behaviour.context.ledger_api_dialogues,
            "create",
            return_value=(MagicMock(), MagicMock()),
        ):
            self.behaviour._send_transaction_request(MagicMock())

    @mock.patch.object(BaseState, "try_send")
    def test_default_callback_request(self, *_):
        """Test default callback request."""
        self.behaviour.default_callback_request(MagicMock())

    def test_build_http_request_message(self, *_):
        """Test '_build_http_request_message'."""
        with mock.patch.object(
            self.behaviour.context.http_dialogues,
            "create",
            return_value=(MagicMock(), MagicMock()),
        ):
            self.behaviour._build_http_request_message(
                "", "", parameters=dict(foo="bar"), headers=dict(foo="bar")
            )

    def test_check_transaction_delivered(self):
        """Test '_check_transaction_delivered' method."""
        response = MagicMock(body='{"result": {"deliver_tx": {"code": 0}}}')
        assert self.behaviour._check_transaction_delivered(response)

    @mock.patch("packages.valory.skills.abstract_round_abci.behaviour_utils.Terms")
    def test_get_default_terms(self, *_):
        """Test '_get_default_terms'."""
        self.behaviour.context.default_ledger_id = "ledger_id"
        self.behaviour.context.agent_address = "address"
        self.behaviour._get_default_terms()

    @mock.patch.object(BaseState, "_send_transaction_signing_request")
    @mock.patch.object(BaseState, "_send_transaction_request")
    @mock.patch("packages.valory.skills.abstract_round_abci.behaviour_utils.Terms")
    def test_send_raw_transaction(self, *_):
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

    @pytest.mark.parametrize("contract_address", [None, "contract_address"])
    def test_get_contract_api_response(self, contract_address):
        """Test 'get_contract_api_response'."""
        self.behaviour.context.default_ledger_id = "ledger_id"
        self.behaviour.context.agent_address = "address"
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
                contract_address, "contract_id", "contract_callable"
            )
            # first trigger
            try_send(gen, obj=None)
            # wait for message
            try_send(gen, obj=MagicMock())
