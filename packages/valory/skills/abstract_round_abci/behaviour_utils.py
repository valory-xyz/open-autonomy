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

"""This module contains helper classes for behaviours."""
import datetime
import inspect
import json
import pprint
from abc import ABC, abstractmethod
from enum import Enum
from functools import partial
from typing import (
    Any,
    Callable,
    Dict,
    Generator,
    List,
    Optional,
    OrderedDict,
    Tuple,
    Type,
    cast,
)

from aea.exceptions import enforce
from aea.protocols.base import Message
from aea.protocols.dialogue.base import Dialogue
from aea.skills.behaviours import SimpleBehaviour

from packages.open_aea.protocols.signing import SigningMessage
from packages.open_aea.protocols.signing.custom_types import (
    RawMessage,
    RawTransaction,
    Terms,
)
from packages.valory.connections.http_client.connection import (
    PUBLIC_ID as HTTP_CLIENT_PUBLIC_ID,
)
from packages.valory.protocols.contract_api import ContractApiMessage
from packages.valory.protocols.http import HttpMessage
from packages.valory.protocols.ledger_api import LedgerApiMessage
from packages.valory.skills.abstract_round_abci.base import (
    AbstractRound,
    BasePeriodState,
    BaseTxPayload,
    LEDGER_API_ADDRESS,
    OK_CODE,
    Transaction,
)
from packages.valory.skills.abstract_round_abci.dialogues import (
    ContractApiDialogue,
    ContractApiDialogues,
    HttpDialogue,
    HttpDialogues,
    LedgerApiDialogue,
    LedgerApiDialogues,
    SigningDialogues,
)
from packages.valory.skills.abstract_round_abci.models import (
    BaseParams,
    Requests,
    SharedState,
)


_DEFAULT_REQUEST_RETRY_DELAY = 1.0
_DEFAULT_REQUEST_TIMEOUT = 10.0
_DEFAULT_TX_TIMEOUT = 10.0


class SendException(Exception):
    """This exception is raised if the 'try_send' to an AsyncBehaviour failed."""


class TimeoutException(Exception):
    """This exception is raised if the 'try_send' to an AsyncBehaviour failed."""


class AsyncBehaviour(ABC):
    """
    MixIn behaviour class that support limited asynchronous programming.

    An AsyncBehaviour can be in three states:
    - READY: no suspended 'async_act' execution;
    - RUNNING: 'act' called, and waiting for a message
    - WAITING_TICK: 'act' called, and waiting for the next 'act' call
    """

    class AsyncState(Enum):
        """Enumeration of AsyncBehaviour states."""

        READY = "ready"
        RUNNING = "running"
        WAITING_MESSAGE = "waiting_message"

    def __init__(self) -> None:
        """Initialize the async behaviour."""
        self.__state = self.AsyncState.READY
        self.__generator_act: Optional[Generator] = None

        # temporary variables for the waiting message state
        self.__stopped: bool = True
        self.__notified: bool = False
        self.__message: Any = None
        self.__setup_called: bool = False

    @abstractmethod
    def async_act(self) -> Generator:
        """Do the act, supporting asynchronous execution."""

    @abstractmethod
    def async_act_wrapper(self) -> Generator:
        """Do the act, supporting asynchronous execution."""

    @property
    def state(self) -> AsyncState:
        """Get the 'async state'."""
        return self.__state

    @property
    def is_stopped(self) -> bool:
        """Check whether the behaviour has stopped."""
        return self.__stopped

    def __get_generator_act(self) -> Generator:
        """Get the _generator_act."""
        if self.__generator_act is None:
            raise ValueError("generator act not set!")  # pragma: nocover
        return self.__generator_act

    def try_send(self, message: Any) -> None:
        """
        Try to send a message to a waiting behaviour.

        It will be send only if the behaviour is actually
        waiting for a message and it was not already notified.

        :param message: a Python object.
        :raises: SendException if the behaviour was not waiting for a message,
            or if it was already notified.
        """
        in_waiting_message_state = self.__state == self.AsyncState.WAITING_MESSAGE
        already_notified = self.__notified
        enforce(
            in_waiting_message_state and not already_notified,
            "cannot send message",
            exception_class=SendException,
        )
        self.__notified = True
        self.__message = message

    @classmethod
    def wait_for_condition(
        cls, condition: Callable[[], bool], timeout: Optional[float] = None
    ) -> Generator[None, None, None]:
        """Wait for a condition to happen."""
        if timeout is not None:
            deadline = datetime.datetime.now() + datetime.timedelta(0, timeout)
        else:
            deadline = datetime.datetime.max

        while not condition():
            if timeout is not None and datetime.datetime.now() > deadline:
                raise TimeoutException()
            yield

    def sleep(self, seconds: float) -> Any:
        """
        Delay execution for a given number of seconds.

        The argument may be a floating point number for subsecond precision.

        :param seconds: the seconds
        :yield: None
        """
        deadline = datetime.datetime.now() + datetime.timedelta(0, seconds)

        def _wait_until() -> bool:
            return datetime.datetime.now() > deadline

        yield from self.wait_for_condition(_wait_until)

    def wait_for_message(
        self,
        condition: Callable = lambda message: True,
        timeout: Optional[float] = None,
    ) -> Any:
        """
        Wait for message.

        Care must be taken. This method does not handle concurrent requests.
        Use directly after a request is being sent.

        :param condition: a callable
        :param timeout: max time to wait (in seconds)
        :return: a message
        :yield: None
        """
        if timeout is not None:
            deadline = datetime.datetime.now() + datetime.timedelta(0, timeout)
        else:
            deadline = datetime.datetime.max

        self.__state = self.AsyncState.WAITING_MESSAGE
        try:
            message = None
            while message is None or not condition(message):
                message = yield
                if timeout is not None and datetime.datetime.now() > deadline:
                    raise TimeoutException()
            message = cast(Message, message)
            return message
        finally:
            self.__state = self.AsyncState.RUNNING

    def setup(self) -> None:
        """Setup behaviour."""

    def act(self) -> None:
        """Do the act."""
        # call setup only the first time act is called
        if not self.__setup_called:
            self.setup()
            self.__setup_called = True

        if self.__state == self.AsyncState.READY:
            self.__call_act_first_time()
            return
        if self.__state == self.AsyncState.WAITING_MESSAGE:
            self.__handle_waiting_for_message()
            return
        enforce(self.__state == self.AsyncState.RUNNING, "not in 'RUNNING' state")
        self.__handle_tick()

    def stop(self) -> None:
        """Stop the execution of the behaviour."""
        if self.__stopped or self.__state == self.AsyncState.READY:
            return
        self.__get_generator_act().close()
        self.__state = self.AsyncState.READY
        self.__stopped = True

    def __call_act_first_time(self) -> None:
        """Call the 'async_act' method for the first time."""
        self.__stopped = False
        self.__state = self.AsyncState.RUNNING
        try:
            self.__generator_act = self.async_act_wrapper()
            # if the method 'async_act' was not a generator function
            # (i.e. no 'yield' or 'yield from' statement)
            # just return
            if not inspect.isgenerator(self.__generator_act):
                self.__state = self.AsyncState.READY
                return
            # trigger first execution, up to next 'yield' statement
            self.__get_generator_act().send(None)
        except StopIteration:
            # this may happen if the generator is empty
            self.__state = self.AsyncState.READY

    def __handle_waiting_for_message(self) -> None:
        """Handle an 'act' tick, when waiting for a message."""
        # if there is no message coming, skip.
        if self.__notified:
            try:
                self.__get_generator_act().send(self.__message)
            except StopIteration:
                self.__handle_stop_iteration()
            finally:
                # wait for the next message
                self.__notified = False
                self.__message = None

    def __handle_tick(self) -> None:
        """Handle an 'act' tick."""
        try:
            self.__get_generator_act().send(None)
        except StopIteration:
            self.__handle_stop_iteration()

    def __handle_stop_iteration(self) -> None:
        """
        Handle 'StopIteration' exception.

        The exception means that the 'async_act'
        generator function terminated the execution,
        and therefore the state needs to be reset.
        """
        self.__state = self.AsyncState.READY


class BaseState(AsyncBehaviour, SimpleBehaviour, ABC):
    """Base class for FSM states."""

    is_programmatically_defined = True
    state_id = ""
    matching_round: Optional[Type[AbstractRound]] = None

    def __init__(self, **kwargs: Any):  # pylint: disable=super-init-not-called
        """Initialize a base state behaviour."""
        AsyncBehaviour.__init__(self)
        SimpleBehaviour.__init__(self, **kwargs)
        self._is_done: bool = False
        self._is_started: bool = False
        enforce(self.state_id != "", "State id not set.")

    @property
    def params(self) -> BaseParams:
        """Return the params."""
        return cast(BaseParams, self.context.params)

    @property
    def period_state(self) -> BasePeriodState:
        """Return the period state."""
        return cast(BasePeriodState, cast(SharedState, self.context.state).period_state)

    def check_in_round(self, round_id: str) -> bool:
        """Check that we entered in a specific round."""
        return cast(SharedState, self.context.state).period.current_round_id == round_id

    def check_in_last_round(self, round_id: str) -> bool:
        """Check that we entered in a specific round."""
        return cast(SharedState, self.context.state).period.last_round_id == round_id

    def check_not_in_round(self, round_id: str) -> bool:
        """Check that we are not in a specific round."""
        return not self.check_in_round(round_id)

    def check_not_in_last_round(self, round_id: str) -> bool:
        """Check that we are not in a specific round."""
        return not self.check_in_last_round(round_id)

    def check_round_has_finished(self, round_id: str) -> bool:
        """Check that the round has finished."""
        return self.check_in_last_round(round_id)

    def check_round_height_has_changed(self, round_height: int) -> bool:
        """Check that the round height has changed."""
        return (
            cast(SharedState, self.context.state).period.current_round_height
            != round_height
        )

    def is_round_ended(self, round_id: str) -> Callable[[], bool]:
        """Get a callable to check whether the current round has ended."""
        return partial(self.check_not_in_round, round_id)

    def wait_until_round_end(
        self, timeout: Optional[float] = None
    ) -> Generator[None, None, None]:
        """
        Wait until the ABCI application exits from a round.

        :param timeout: the timeout for the wait
        :yield: None
        """
        if self.matching_round is None:
            raise ValueError("No matching_round set!")
        round_id = self.matching_round.round_id
        round_height = cast(SharedState, self.context.state).period.current_round_height
        if self.check_not_in_round(round_id) and self.check_not_in_last_round(round_id):
            raise ValueError(
                f"Should be in matching round ({round_id}) or last round ({self.context.state.period.last_round_id}), actual round {self.context.state.period.current_round_id}!"
            )
        yield from self.wait_for_condition(
            partial(self.check_round_height_has_changed, round_height), timeout=timeout
        )

    def wait_from_last_timestamp(self, seconds: float) -> Any:
        """
        Delay execution for a given number of seconds from the last timestamp.

        The argument may be a floating point number for subsecond precision.

        :param seconds: the seconds
        :yield: None
        """
        deadline = cast(
            SharedState, self.context.state
        ).period.abci_app.last_timestamp + datetime.timedelta(0, seconds)

        def _wait_until() -> bool:
            return datetime.datetime.now() > deadline

        yield from self.wait_for_condition(_wait_until)

    def is_done(self) -> bool:
        """Check whether the state is done."""
        return self._is_done

    def set_done(self) -> None:
        """Set the behaviour to done."""
        self._is_done = True

    def send_a2a_transaction(self, payload: BaseTxPayload) -> Generator:
        """
        Send transaction and wait for the response, and repeat until not successful.

        Calls `_send_transaction` and uses the default stop condition (based on round id).

        :param: payload: the payload to send
        :yield: the responses
        """
        if self.matching_round is None:
            raise ValueError("No matching_round set!")
        stop_condition = self.is_round_ended(self.matching_round.round_id)
        yield from self._send_transaction(payload, stop_condition=stop_condition)

    def async_act_wrapper(self) -> Generator:
        """Do the act, supporting asynchronous execution."""
        if not self._is_started:
            self._log_start()
            self._is_started = True
        try:
            yield from self.async_act()
        except (GeneratorExit, StopIteration):
            self.clean_up()
            self.set_done()
            self._log_end()
            return
        if self._is_done:
            self._log_end()

    def _log_start(self) -> None:
        """Log the entering in the behaviour state."""
        self.context.logger.info(f"Entered in the '{self.name}' behaviour state")

    def _log_end(self) -> None:
        """Log the exiting from the behaviour state."""
        self.context.logger.info(f"'{self.name}' behaviour state is done")

    @classmethod
    def _get_request_nonce_from_dialogue(cls, dialogue: Dialogue) -> str:
        """Get the request nonce for the request, from the protocol's dialogue."""
        return dialogue.dialogue_label.dialogue_reference[0]

    def _send_transaction(
        self,
        payload: BaseTxPayload,
        stop_condition: Callable[[], bool] = lambda: False,
        request_timeout: float = _DEFAULT_REQUEST_TIMEOUT,
        request_retry_delay: float = _DEFAULT_REQUEST_RETRY_DELAY,
        tx_timeout: float = _DEFAULT_TX_TIMEOUT,
    ) -> Generator:
        """
        Send transaction and wait for the response, and repeat until not successful.

        Steps:
        - Request the signature of the payload to the Decision Maker
        - Send the transaction to the 'price-estimation' app via the Tendermint node,
          and wait/repeat until the transaction is not mined.

        :param: payload: the payload to send
        :param: stop_condition: the condition to be checked to interrupt the waiting loop.
        :param: request_timeout: the timeout for the requests
        :param: request_retry_delay: the delay to wait after failed requests
        :param: tx_timeout: the timeout to wait for tx delivery
        :yield: the responses
        """
        while not stop_condition():
            signature_bytes = yield from self.get_signature(payload.encode())
            transaction = Transaction(payload, signature_bytes)
            try:
                response = yield from self._submit_tx(
                    transaction.encode(), timeout=request_timeout
                )
            except TimeoutException:
                self.context.logger.info(
                    f"Timeout expired for submit tx. Retrying in {request_retry_delay} seconds..."
                )
                yield from self.sleep(request_retry_delay)
                continue
            response = cast(HttpMessage, response)
            if not self._check_http_return_code_200(response):
                self.context.logger.info(
                    f"Received return code != 200. Retrying in {request_retry_delay} seconds..."
                )
                yield from self.sleep(request_retry_delay)
                continue
            try:
                json_body = json.loads(response.body)
            except json.JSONDecodeError as e:  # pragma: nocover
                raise ValueError(
                    f"Unable to decode response: {response} with body {str(response.body)}"
                ) from e
            self.context.logger.debug(f"JSON response: {pprint.pformat(json_body)}")
            tx_hash = json_body["result"]["hash"]

            try:
                is_delivered = yield from self._wait_until_transaction_delivered(
                    tx_hash, timeout=tx_timeout
                )
            except TimeoutException:
                self.context.logger.info(
                    f"Timeout expired for wait until transaction delivered. Retrying in {request_retry_delay} seconds..."
                )
                yield from self.sleep(request_retry_delay)
                continue

            if is_delivered:
                self.context.logger.info("A2A transaction delivered!")
                break
            # otherwise, repeat until done, or until stop condition is true

    def _send_signing_request(
        self, raw_message: bytes, is_deprecated_mode: bool = False
    ) -> None:
        """Send a signing request."""
        signing_dialogues = cast(SigningDialogues, self.context.signing_dialogues)
        signing_msg, signing_dialogue = signing_dialogues.create(
            counterparty=self.context.decision_maker_address,
            performative=SigningMessage.Performative.SIGN_MESSAGE,
            raw_message=RawMessage(
                self.context.default_ledger_id,
                raw_message,
                is_deprecated_mode=is_deprecated_mode,
            ),
            terms=Terms(
                ledger_id=self.context.default_ledger_id,
                sender_address="",
                counterparty_address="",
                amount_by_currency_id={},
                quantities_by_good_id={},
                nonce="",
            ),
        )
        request_nonce = self._get_request_nonce_from_dialogue(signing_dialogue)
        cast(Requests, self.context.requests).request_id_to_callback[
            request_nonce
        ] = self.default_callback_request
        self.context.decision_maker_message_queue.put_nowait(signing_msg)

    def _send_transaction_signing_request(
        self, raw_transaction: RawTransaction, terms: Terms
    ) -> None:
        """Send a transaction signing request."""
        signing_dialogues = cast(SigningDialogues, self.context.signing_dialogues)
        signing_msg, signing_dialogue = signing_dialogues.create(
            counterparty=self.context.decision_maker_address,
            performative=SigningMessage.Performative.SIGN_TRANSACTION,
            raw_transaction=raw_transaction,
            terms=terms,
        )
        request_nonce = self._get_request_nonce_from_dialogue(signing_dialogue)
        cast(Requests, self.context.requests).request_id_to_callback[
            request_nonce
        ] = self.default_callback_request
        self.context.decision_maker_message_queue.put_nowait(signing_msg)

    def _send_transaction_request(self, signing_msg: SigningMessage) -> None:
        ledger_api_dialogues = cast(
            LedgerApiDialogues, self.context.ledger_api_dialogues
        )
        ledger_api_msg, ledger_api_dialogue = ledger_api_dialogues.create(
            counterparty=LEDGER_API_ADDRESS,
            performative=LedgerApiMessage.Performative.SEND_SIGNED_TRANSACTION,
            signed_transaction=signing_msg.signed_transaction,
        )
        ledger_api_dialogue = cast(LedgerApiDialogue, ledger_api_dialogue)
        request_nonce = self._get_request_nonce_from_dialogue(ledger_api_dialogue)
        cast(Requests, self.context.requests).request_id_to_callback[
            request_nonce
        ] = self.default_callback_request
        self.context.outbox.put_message(message=ledger_api_msg)
        self.context.logger.info("sending transaction to ledger.")

    def _send_transaction_receipt_request(
        self,
        tx_digest: str,
        retry_timeout: Optional[int] = None,
        retry_attempts: Optional[int] = None,
    ) -> None:
        ledger_api_dialogues = cast(
            LedgerApiDialogues, self.context.ledger_api_dialogues
        )
        ledger_api_msg, ledger_api_dialogue = ledger_api_dialogues.create(
            counterparty=LEDGER_API_ADDRESS,
            performative=LedgerApiMessage.Performative.GET_TRANSACTION_RECEIPT,
            transaction_digest=LedgerApiMessage.TransactionDigest(
                ledger_id=self.context.default_ledger_id, body=tx_digest
            ),
            retry_timeout=retry_timeout,
            retry_attempts=retry_attempts,
        )
        ledger_api_dialogue = cast(LedgerApiDialogue, ledger_api_dialogue)
        request_nonce = self._get_request_nonce_from_dialogue(ledger_api_dialogue)
        cast(Requests, self.context.requests).request_id_to_callback[
            request_nonce
        ] = self.default_callback_request
        self.context.outbox.put_message(message=ledger_api_msg)
        self.context.logger.info(
            f"sending transaction receipt request for tx_digest='{tx_digest}'."
        )

    def _handle_signing_failure(self) -> None:
        """Handle signing failure."""
        self.context.logger.error("the transaction could not be signed.")

    def _submit_tx(
        self, tx_bytes: bytes, timeout: Optional[float] = None
    ) -> Generator[None, None, HttpMessage]:
        """Send a broadcast_tx_sync request."""
        request_message, http_dialogue = self._build_http_request_message(
            "GET",
            self.context.params.tendermint_url
            + f"/broadcast_tx_sync?tx=0x{tx_bytes.hex()}",
        )
        result = yield from self._do_request(
            request_message, http_dialogue, timeout=timeout
        )
        return result

    def _get_tx_info(
        self, tx_hash: str, timeout: Optional[float] = None
    ) -> Generator[None, None, HttpMessage]:
        """Get transaction info from tx hash."""
        request_message, http_dialogue = self._build_http_request_message(
            "GET",
            self.context.params.tendermint_url + f"/tx?hash=0x{tx_hash}",
        )
        result = yield from self._do_request(
            request_message, http_dialogue, timeout=timeout
        )
        return result

    def _get_health(self) -> Generator[None, None, HttpMessage]:
        """Get Tendermint node's health."""
        request_message, http_dialogue = self._build_http_request_message(
            "GET",
            self.context.params.tendermint_url + "/health",
        )
        result = yield from self._do_request(request_message, http_dialogue)
        return result

    def _get_status(self) -> Generator[None, None, HttpMessage]:
        """Get Tendermint node's status."""
        request_message, http_dialogue = self._build_http_request_message(
            "GET",
            self.context.params.tendermint_url + "/status",
        )
        result = yield from self._do_request(request_message, http_dialogue)
        return result

    def default_callback_request(self, message: Message) -> None:
        """Implement default callback request."""
        if self.is_stopped:
            self.context.logger.debug(
                "dropping message as behaviour has stopped: %s", message
            )
        elif self.state == AsyncBehaviour.AsyncState.WAITING_MESSAGE:
            self.try_send(message)
        else:
            self.context.logger.warning(
                "could not send message to FSMBehaviour: %s", message
            )

    def get_http_response(
        self,
        method: str,
        url: str,
        content: Optional[bytes] = None,
        headers: Optional[List[OrderedDict[str, str]]] = None,
        parameters: Optional[List[Tuple[str, str]]] = None,
    ) -> Generator[None, None, HttpMessage]:
        """
        Send an http request message from the skill context.

        This method is skill-specific, and therefore
        should not be used elsewhere.

        :param method: the http request method (i.e. 'GET' or 'POST').
        :param url: the url to send the message to.
        :param content: the payload.
        :param headers: headers to be included.
        :param parameters: url query parameters.
        :yield: wait the response message
        :return: the http message and the http dialogue
        """
        http_message, http_dialogue = self._build_http_request_message(
            method=method,
            url=url,
            content=content,
            headers=headers,
            parameters=parameters,
        )
        response = yield from self._do_request(http_message, http_dialogue)
        return response

    def _do_request(
        self,
        request_message: HttpMessage,
        http_dialogue: HttpDialogue,
        timeout: Optional[float] = None,
    ) -> Generator[None, None, HttpMessage]:
        """
        Do a request and wait the response, asynchronously.

        :param request_message: The request message
        :param http_dialogue: the HTTP dialogue associated to the request
        :param timeout: seconds to wait for the reply.
        :yield: wait the response message
        :return: the response message
        """
        self.context.outbox.put_message(message=request_message)
        request_nonce = self._get_request_nonce_from_dialogue(http_dialogue)
        cast(Requests, self.context.requests).request_id_to_callback[
            request_nonce
        ] = self.default_callback_request
        try:
            response = yield from self.wait_for_message(timeout=timeout)
            return response
        finally:
            # remove request id in case already timed out,
            # but notify caller by propagating exception.
            cast(Requests, self.context.requests).request_id_to_callback.pop(
                request_nonce, None
            )

    def _build_http_request_message(
        self,
        method: str,
        url: str,
        content: Optional[bytes] = None,
        headers: Optional[List[OrderedDict[str, str]]] = None,
        parameters: Optional[List[Tuple[str, str]]] = None,
    ) -> Tuple[HttpMessage, HttpDialogue]:
        """
        Send an http request message from the skill context.

        This method is skill-specific, and therefore
        should not be used elsewhere.

        :param method: the http request method (i.e. 'GET' or 'POST').
        :param url: the url to send the message to.
        :param content: the payload.
        :param headers: headers to be included.
        :param parameters: url query parameters.
        :return: the http message and the http dialogue
        """
        if parameters:
            url = url + "?"
            for key, val in parameters:
                url += f"{key}={val}&"
            url = url[:-1]

        header_string = ""
        if headers:
            for header in headers:
                for key, val in header.items():
                    header_string += f"{key}: {val}\r\n"

        # context
        http_dialogues = cast(HttpDialogues, self.context.http_dialogues)

        # http request message
        request_http_message, http_dialogue = http_dialogues.create(
            counterparty=str(HTTP_CLIENT_PUBLIC_ID),
            performative=HttpMessage.Performative.REQUEST,
            method=method,
            url=url,
            headers=header_string,
            version="",
            body=b"" if content is None else content,
        )
        request_http_message = cast(HttpMessage, request_http_message)
        http_dialogue = cast(HttpDialogue, http_dialogue)
        return request_http_message, http_dialogue

    def _wait_until_transaction_delivered(
        self,
        tx_hash: str,
        timeout: Optional[float] = None,
        request_retry_delay: float = _DEFAULT_REQUEST_RETRY_DELAY,
    ) -> Generator[None, None, bool]:
        """
        Wait until transaction is delivered.

        :param tx_hash: the transaction hash to check.
        :param timeout: timeout
        :param: request_retry_delay: the delay to wait after failed requests
        :yield: None
        :return: True if it is delivered successfully, False otherwise
        """
        if timeout is not None:
            deadline = datetime.datetime.now() + datetime.timedelta(0, timeout)
        else:
            deadline = datetime.datetime.max

        while True:
            request_timeout = (
                (deadline - datetime.datetime.now()).total_seconds()
                if timeout is not None
                else None
            )
            if request_timeout is not None and request_timeout < 0:
                raise TimeoutException()

            response = yield from self._get_tx_info(tx_hash, timeout=request_timeout)
            if response.status_code != 200:
                yield from self.sleep(request_retry_delay)
                continue
            try:
                json_body = json.loads(response.body)
            except json.JSONDecodeError as e:  # pragma: nocover
                raise ValueError(
                    f"Unable to decode response: {response} with body {str(response.body)}"
                ) from e
            tx_result = json_body["result"]["tx_result"]
            return tx_result["code"] == OK_CODE

    @classmethod
    def _check_http_return_code_200(cls, response: HttpMessage) -> bool:
        """Check the HTTP response has return code 200."""
        return response.status_code == 200

    def _get_default_terms(self) -> Terms:
        """
        Get default transaction terms.

        :return: terms
        """
        terms = Terms(
            ledger_id=self.context.default_ledger_id,
            sender_address=self.context.agent_address,
            counterparty_address=self.context.agent_address,
            amount_by_currency_id={},
            quantities_by_good_id={},
            nonce="",
        )
        return terms

    def get_signature(
        self, message: bytes, is_deprecated_mode: bool = False
    ) -> Generator[None, None, str]:
        """Get signature for message."""
        self._send_signing_request(message, is_deprecated_mode)
        signature_response = yield from self.wait_for_message()
        signature_response = cast(SigningMessage, signature_response)
        if signature_response.performative == SigningMessage.Performative.ERROR:
            self._handle_signing_failure()
            raise RuntimeError("Internal error: failure during signing.")
        signature_bytes = signature_response.signed_message.body
        return signature_bytes

    def send_raw_transaction(
        self, transaction: RawTransaction
    ) -> Generator[None, None, Optional[str]]:
        """Send raw transactions to the ledger for mining."""
        terms = Terms(
            self.context.default_ledger_id,
            self.context.agent_address,
            counterparty_address="",
            amount_by_currency_id={},
            quantities_by_good_id={},
            nonce="",
        )
        self._send_transaction_signing_request(transaction, terms)
        signature_response = yield from self.wait_for_message()
        signature_response = cast(SigningMessage, signature_response)
        if (
            signature_response.performative
            != SigningMessage.Performative.SIGNED_TRANSACTION
        ):  # pragma: nocover
            self.context.logger.error("Error when requesting transaction signature.")
            return None
        self._send_transaction_request(signature_response)
        transaction_digest_msg = yield from self.wait_for_message()
        if (
            transaction_digest_msg.performative
            != LedgerApiMessage.Performative.TRANSACTION_DIGEST
        ):  # pragma: nocover
            self.context.logger.error(
                f"Error when requesting transaction digest: {transaction_digest_msg.message}"
            )
            return None
        tx_hash = transaction_digest_msg.transaction_digest.body
        return tx_hash

    def get_transaction_receipt(
        self,
        tx_digest: str,
        retry_timeout: Optional[int] = None,
        retry_attempts: Optional[int] = None,
    ) -> Generator[None, None, Optional[Dict]]:
        """Get transaction receipt."""
        self._send_transaction_receipt_request(tx_digest, retry_timeout, retry_attempts)
        transaction_receipt_msg = yield from self.wait_for_message()
        if (
            transaction_receipt_msg.performative == LedgerApiMessage.Performative.ERROR
        ):  # pragma: nocover
            self.context.logger.error(
                f"Error when requesting transaction receipt: {transaction_receipt_msg.message}"
            )
            return None
        tx_receipt = transaction_receipt_msg.transaction_receipt.receipt
        return tx_receipt

    def get_ledger_api_response(
        self,
        performative: LedgerApiMessage.Performative,
        ledger_callable: str,
        **kwargs: Any,
    ) -> Generator[None, None, LedgerApiMessage]:
        """
        Request contract safe transaction hash

        :param performative: the message performative
        :param ledger_callable: the collable to call on the contract
        :param kwargs: keyword argument for the contract api request
        :return: the contract api response
        :yields: the contract api response
        """
        ledger_api_dialogues = cast(
            LedgerApiDialogues, self.context.ledger_api_dialogues
        )
        kwargs = {
            "performative": performative,
            "counterparty": LEDGER_API_ADDRESS,
            "ledger_id": self.context.default_ledger_id,
            "callable": ledger_callable,
            "kwargs": LedgerApiMessage.Kwargs(kwargs),
            "args": tuple(),
        }
        ledger_api_msg, ledger_api_dialogue = ledger_api_dialogues.create(**kwargs)
        ledger_api_dialogue = cast(
            LedgerApiDialogue,
            ledger_api_dialogue,
        )
        ledger_api_dialogue.terms = self._get_default_terms()
        request_nonce = self._get_request_nonce_from_dialogue(ledger_api_dialogue)
        cast(Requests, self.context.requests).request_id_to_callback[
            request_nonce
        ] = self.default_callback_request
        self.context.outbox.put_message(message=ledger_api_msg)
        response = yield from self.wait_for_message()
        return response

    def get_contract_api_response(
        self,
        performative: ContractApiMessage.Performative,
        contract_address: Optional[str],
        contract_id: str,
        contract_callable: str,
        **kwargs: Any,
    ) -> Generator[None, None, ContractApiMessage]:
        """
        Request contract safe transaction hash

        :param performative: the message performative
        :param contract_address: the contract address
        :param contract_id: the contract id
        :param contract_callable: the collable to call on the contract
        :param kwargs: keyword argument for the contract api request
        :return: the contract api response
        :yields: the contract api response
        """
        contract_api_dialogues = cast(
            ContractApiDialogues, self.context.contract_api_dialogues
        )
        kwargs = {
            "performative": performative,
            "counterparty": LEDGER_API_ADDRESS,
            "ledger_id": self.context.default_ledger_id,
            "contract_id": contract_id,
            "callable": contract_callable,
            "kwargs": ContractApiMessage.Kwargs(kwargs),
        }
        if contract_address is not None:
            kwargs["contract_address"] = contract_address
        contract_api_msg, contract_api_dialogue = contract_api_dialogues.create(
            **kwargs
        )
        contract_api_dialogue = cast(
            ContractApiDialogue,
            contract_api_dialogue,
        )
        contract_api_dialogue.terms = self._get_default_terms()
        request_nonce = self._get_request_nonce_from_dialogue(contract_api_dialogue)
        cast(Requests, self.context.requests).request_id_to_callback[
            request_nonce
        ] = self.default_callback_request
        self.context.outbox.put_message(message=contract_api_msg)
        response = yield from self.wait_for_message()
        return response

    def clean_up(self) -> None:
        """
        Clean up the resources due to a 'stop' event.

        It can be optionally implemented by the concrete classes.
        """
