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

"""This module contains helper classes for behaviours."""
import datetime
import inspect
import json
import math
import pprint
import re
from abc import ABC, abstractmethod
from enum import Enum
from functools import partial, wraps
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
    Union,
    cast,
)

import pytz  # type: ignore  # pylint: disable=import-error
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
from packages.valory.contracts.service_registry.contract import (  # noqa: F401  # pylint: disable=unused-import
    ServiceRegistryContract,
)
from packages.valory.protocols.contract_api import ContractApiMessage
from packages.valory.protocols.http import HttpMessage
from packages.valory.protocols.ledger_api import LedgerApiMessage
from packages.valory.skills.abstract_round_abci.base import (
    AbstractRound,
    BaseSynchronizedData,
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
from packages.valory.skills.abstract_round_abci.io_.ipfs import (
    IPFSInteract,
    IPFSInteractionError,
)
from packages.valory.skills.abstract_round_abci.io_.load import CustomLoaderType, Loader
from packages.valory.skills.abstract_round_abci.io_.store import (
    CustomStorerType,
    Storer,
    SupportedFiletype,
    SupportedObjectType,
)
from packages.valory.skills.abstract_round_abci.models import (
    BaseParams,
    Requests,
    SharedState,
)


# TODO: port registration code from registration_abci to here


MIN_HEIGHT_OFFSET = 10
HEIGHT_OFFSET_MULTIPLIER = 1
NON_200_RETURN_CODE_DURING_RESET_THRESHOLD = 3
GENESIS_TIME_FMT = "%Y-%m-%dT%H:%M:%S.%fZ"
ROOT_HASH = "726F6F743A3"
RESET_HASH = "72657365743A3"
APP_HASH_RE = rf"{ROOT_HASH}\d+{RESET_HASH}(\d+)"
INITIAL_APP_HASH = ""


class SendException(Exception):
    """Exception raised if the 'try_send' to an AsyncBehaviour failed."""


class TimeoutException(Exception):
    """Exception raised when a timeout during AsyncBehaviour occurs."""


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

        It will be sent only if the behaviour is actually waiting for a message,
        and it was not already notified.

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
        """Wait for a condition to happen.

        This is a local method that does not depend on the global clock,
        so the usage of datetime.now() is acceptable here.

        :param condition: the condition to wait for
        :param timeout: the maximum amount of time to wait
        :yield: None
        """
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
        This is a local method that does not depend on the global clock, so the
        usage of datetime.now() is acceptable here.

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
        This is a local method that does not depend on the global clock,
        so the usage of datetime.now() is acceptable here.

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


def _check_ipfs_enabled(fn: Callable) -> Callable:
    """Decorator that raises error if IPFS is not enabled."""

    @wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        """The wrap that checks and raises the error."""
        ipfs_enabled = args[0].ipfs_enabled

        if not ipfs_enabled:  # pragma: no cover
            raise ValueError(
                "Trying to perform an IPFS operation, but IPFS has not been enabled! "
                "Please set `ipfs_domain_name` configuration."
            )

        return fn(*args, **kwargs)

    return wrapper


class IPFSBehaviour(SimpleBehaviour, ABC):
    """Behaviour for interactions with IPFS."""

    def __init__(self, **kwargs: Any):
        """Initialize an `IPFSBehaviour`."""
        super().__init__(**kwargs)
        self.ipfs_enabled = False
        # If params are not found `AttributeError` will be raised. This is fine, because something will have gone wrong.
        # If `ipfs_domain_name` is not specified for the skill, then we get a `None` default.
        # Therefore, `IPFSBehaviour` will be disabled.
        domain = getattr(self.params, "ipfs_domain_name", None)  # type: ignore  # pylint: disable=E1101
        loader_cls = kwargs.pop("loader_cls", Loader)
        storer_cls = kwargs.pop("storer_cls", Storer)
        if domain is not None:  # pragma: nocover
            self.ipfs_enabled = True
            self._ipfs_interact = IPFSInteract(domain, loader_cls, storer_cls)

    @_check_ipfs_enabled
    def send_to_ipfs(
        self,
        filepath: str,
        obj: SupportedObjectType,
        multiple: bool = False,
        filetype: Optional[SupportedFiletype] = None,
        custom_storer: Optional[CustomStorerType] = None,
        **kwargs: Any,
    ) -> Optional[str]:
        """Send a file to IPFS."""
        try:
            hash_ = self._ipfs_interact.store_and_send(
                filepath, obj, multiple, filetype, custom_storer, **kwargs
            )
            self.context.logger.info(f"IPFS hash is: {hash_}")
            return hash_
        except IPFSInteractionError as e:  # pragma: no cover
            self.context.logger.error(
                f"An error occurred while trying to send a file to IPFS: {str(e)}"
            )
            return None

    @_check_ipfs_enabled
    def get_from_ipfs(  # pylint: disable=too-many-arguments
        self,
        hash_: str,
        target_dir: str,
        multiple: bool = False,
        filename: Optional[str] = None,
        filetype: Optional[SupportedFiletype] = None,
        custom_loader: CustomLoaderType = None,
    ) -> Optional[SupportedObjectType]:
        """Get a file from IPFS."""
        try:
            return self._ipfs_interact.get_and_read(
                hash_, target_dir, multiple, filename, filetype, custom_loader
            )
        except IPFSInteractionError as e:
            self.context.logger.error(
                f"An error occurred while trying to fetch a file from IPFS: {str(e)}"
            )
            return None


class CleanUpBehaviour(SimpleBehaviour, ABC):
    """Class for clean-up related functionality of behaviours."""

    def __init__(self, **kwargs: Any):  # pylint: disable=super-init-not-called
        """Initialize a base behaviour."""
        SimpleBehaviour.__init__(self, **kwargs)

    def clean_up(self) -> None:
        """
        Clean up the resources due to a 'stop' event.

        It can be optionally implemented by the concrete classes.
        """

    def handle_late_messages(self, behaviour_id: str, message: Message) -> None:
        """
        Handle late arriving messages.

        Runs from another behaviour, even if the behaviour implementing the method has been exited.
        It can be optionally implemented by the concrete classes.

        :param behaviour_id: the id of the behaviour in which the message belongs to.
        :param message: the late arriving message to handle.
        """
        request_nonce = message.dialogue_reference[0]
        self.context.logger.warning(
            f"No callback defined for request with nonce: {request_nonce}, arriving for behaviour: {behaviour_id}"
        )


class RPCResponseStatus(Enum):
    """A custom status of an RPC response."""

    SUCCESS = 1
    INCORRECT_NONCE = 2
    UNDERPRICED = 3
    INSUFFICIENT_FUNDS = 4
    ALREADY_KNOWN = 5
    UNCLASSIFIED_ERROR = 6


class BaseBehaviour(AsyncBehaviour, IPFSBehaviour, CleanUpBehaviour, ABC):
    """Base class for FSM behaviours."""

    is_programmatically_defined = True
    behaviour_id = ""
    matching_round: Type[AbstractRound]
    is_degenerate: bool = False

    def __init__(self, **kwargs: Any):  # pylint: disable=super-init-not-called
        """Initialize a base behaviour."""
        AsyncBehaviour.__init__(self)
        IPFSBehaviour.__init__(self, **kwargs)
        CleanUpBehaviour.__init__(self, **kwargs)
        self._is_done: bool = False
        self._is_started: bool = False
        self._check_started: Optional[datetime.datetime] = None
        self._timeout: float = 0
        self._is_healthy: bool = False
        self._non_200_return_code_count: int = 0
        enforce(self.behaviour_id != "", "State id not set.")

    @property
    def params(self) -> BaseParams:
        """Return the params."""
        return cast(BaseParams, self.context.params)

    @property
    def synchronized_data(self) -> BaseSynchronizedData:
        """Return the synchronized data."""
        return cast(
            BaseSynchronizedData,
            cast(SharedState, self.context.state).synchronized_data,
        )

    @property
    def tm_communication_unhealthy(self) -> bool:
        """Return if the Tendermint communication is not healthy anymore."""
        return cast(
            SharedState, self.context.state
        ).round_sequence.block_stall_deadline_expired

    def check_in_round(self, round_id: str) -> bool:
        """Check that we entered a specific round."""
        return (
            cast(SharedState, self.context.state).round_sequence.current_round_id
            == round_id
        )

    def check_in_last_round(self, round_id: str) -> bool:
        """Check that we entered a specific round."""
        return (
            cast(SharedState, self.context.state).round_sequence.last_round_id
            == round_id
        )

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
            cast(SharedState, self.context.state).round_sequence.current_round_height
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
        round_id = self.matching_round.round_id
        round_height = cast(
            SharedState, self.context.state
        ).round_sequence.current_round_height
        if self.check_not_in_round(round_id) and self.check_not_in_last_round(round_id):
            raise ValueError(
                f"Should be in matching round ({round_id}) or last round ({self.context.state.round_sequence.last_round_id}), actual round {self.context.state.round_sequence.current_round_id}!"
            )
        yield from self.wait_for_condition(
            partial(self.check_round_height_has_changed, round_height), timeout=timeout
        )

    def wait_from_last_timestamp(self, seconds: float) -> Any:
        """
        Delay execution for a given number of seconds from the last timestamp.

        The argument may be a floating point number for subsecond precision.
        This is a local method that does not depend on the global clock,
        so the usage of datetime.now() is acceptable here.

        :param seconds: the seconds
        :yield: None
        """
        if seconds < 0:
            raise ValueError("Can only wait for a positive amount of time")
        deadline = cast(
            SharedState, self.context.state
        ).round_sequence.abci_app.last_timestamp + datetime.timedelta(seconds=seconds)

        def _wait_until() -> bool:
            return datetime.datetime.now() > deadline

        yield from self.wait_for_condition(_wait_until)

    def is_done(self) -> bool:
        """Check whether the behaviour is done."""
        return self._is_done

    def set_done(self) -> None:
        """Set the behaviour to done."""
        self._is_done = True

    def send_a2a_transaction(
        self, payload: BaseTxPayload, resetting: bool = False
    ) -> Generator:
        """
        Send transaction and wait for the response, and repeat until not successful.

        :param: payload: the payload to send
        :param: resetting: flag indicating if we are resetting Tendermint nodes in this round.
        :yield: the responses
        """
        stop_condition = self.is_round_ended(self.matching_round.round_id)
        payload.round_count = cast(
            SharedState, self.context.state
        ).synchronized_data.round_count
        yield from self._send_transaction(
            payload,
            resetting,
            stop_condition=stop_condition,
        )

    def __check_tm_communication(self) -> Generator[None, None, bool]:
        """Check if the Tendermint communication is considered healthy and if not restart the node."""
        if self.tm_communication_unhealthy:
            self.context.logger.warning(
                "The local deadline for the next `begin_block` request from the Tendermint node has expired! "
                "Trying to reset local Tendermint node as there could be something wrong with the communication."
            )
            reset_successfully = yield from self.reset_tendermint_with_wait()
            return reset_successfully
        return True

    def async_act_wrapper(self) -> Generator:
        """Do the act, supporting asynchronous execution."""
        if not self._is_started:
            self._log_start()
            self._is_started = True

        try:
            communication_is_healthy = yield from self.__check_tm_communication()
            if not communication_is_healthy:
                # if we end up looping here forever,
                # then there is probably something serious going on with the communication
                return
            if self.context.state.round_sequence.syncing_up:
                yield from self._check_sync()
            else:
                yield from self.async_act()
        except StopIteration:
            self.clean_up()
            self.set_done()
            self._log_end()
            return

        if self._is_done:
            self._log_end()

    def _sync_state(self, app_hash: str) -> None:
        """
        Sync the app's state using the given `app_hash`.

        This method is intended for use after syncing local with remote.
        The fact that we sync up with the blockchain does not mean that we also have the correct application state.
        The application state is defined by the abci app's developer and also determines the generation of the app hash.
        When we sync with the blockchain, it means that we no longer lag behind the other agents.
        However, the application's state should also be updated, which is what this method takes care for.
        We have chosen a simple application state for the time being,
        which is a combination of the round count and the times we have reset so far.
        The round count will be automatically updated by the framework while replaying the missed rounds,
        however, the reset index needs to be manually updated.

        Tendermint's block sync and state sync are not to be confused with our application's state;
        they are different methods to sync faster with the blockchain.

        :param app_hash: the app hash from which the state will be updated.
        """
        if app_hash == INITIAL_APP_HASH:
            reset_index = 0
        else:
            match = re.match(APP_HASH_RE, app_hash)
            if match is None:
                raise ValueError(
                    "Expected an app hash of the form: `726F6F743A3{ROUND_COUNT}72657365743A3{RESET_INDEX}`,"
                    "which is derived from `root:{ROUND_COUNT}reset:{RESET_INDEX}`. "
                    "For example, `root:90reset:4` would be `726F6F743A39072657365743A34`. "
                    f"However, the app hash received is: `{app_hash}`."
                )
            reset_index = int(match.group(1))

        self.context.state.round_sequence.abci_app.reset_index = reset_index

    def _check_sync(
        self,
    ) -> Generator[None, None, None]:
        """Check if agent has completed sync."""
        self.context.logger.info("Checking sync...")
        for _ in range(self.context.params.tendermint_max_retries):
            self.context.logger.info(
                "Checking status @ " + self.context.params.tendermint_url + "/status",
            )
            status = yield from self._get_status()
            try:
                json_body = json.loads(status.body.decode())
                remote_height = int(
                    json_body["result"]["sync_info"]["latest_block_height"]
                )
                local_height = int(self.context.state.round_sequence.height)
                _is_sync_complete = local_height == remote_height
                if _is_sync_complete:
                    self.context.logger.info(
                        f"local height == remote == {local_height}; Sync complete..."
                    )
                    remote_app_hash = str(
                        json_body["result"]["sync_info"]["latest_app_hash"]
                    )
                    self._sync_state(remote_app_hash)
                    self.context.state.round_sequence.end_sync()
                    return
                yield from self.sleep(self.context.params.tendermint_check_sleep_delay)
            except (json.JSONDecodeError, KeyError):  # pragma: nocover
                self.context.logger.error(
                    "Tendermint not accepting transactions yet, trying again!"
                )
                yield from self.sleep(self.context.params.tendermint_check_sleep_delay)

    def _log_start(self) -> None:
        """Log the entering in the behaviour."""
        self.context.logger.info(f"Entered in the '{self.name}' behaviour")

    def _log_end(self) -> None:
        """Log the exiting from the behaviour."""
        self.context.logger.info(f"'{self.name}' behaviour is done")

    @classmethod
    def _get_request_nonce_from_dialogue(cls, dialogue: Dialogue) -> str:
        """Get the request nonce for the request, from the protocol's dialogue."""
        return dialogue.dialogue_label.dialogue_reference[0]

    def _send_transaction(  # pylint: disable=too-many-arguments,too-many-locals,too-many-statements
        self,
        payload: BaseTxPayload,
        resetting: bool = False,
        stop_condition: Callable[[], bool] = lambda: False,
        request_timeout: Optional[float] = None,
        request_retry_delay: Optional[float] = None,
        tx_timeout: Optional[float] = None,
        max_attempts: Optional[int] = None,
    ) -> Generator:
        """
        Send transaction and wait for the response, repeat until not successful.

        Steps:
        - Request the signature of the payload to the Decision Maker
        - Send the transaction to the 'price-estimation' app via the Tendermint
          node, and wait/repeat until the transaction is not mined.

        Happy-path full flow of the messages.

        get_signature:
            AbstractRoundAbci skill -> (SigningMessage | SIGN_MESSAGE) -> DecisionMaker
            DecisionMaker -> (SigningMessage | SIGNED_MESSAGE) -> AbstractRoundAbci skill

        _submit_tx:
            AbstractRoundAbci skill -> (HttpMessage | REQUEST) -> Http client connection
            Http client connection -> (HttpMessage | RESPONSE) -> AbstractRoundAbci skill

        _wait_until_transaction_delivered:
            AbstractRoundAbci skill -> (HttpMessage | REQUEST) -> Http client connection
            Http client connection -> (HttpMessage | RESPONSE) -> AbstractRoundAbci skill

        :param: payload: the payload to send
        :param: resetting: flag indicating if we are resetting Tendermint nodes in this round.
        :param: stop_condition: the condition to be checked to interrupt the
                waiting loop.
        :param: request_timeout: the timeout for the requests
        :param: request_retry_delay: the delay to wait after failed requests
        :param: tx_timeout: the timeout to wait for tx delivery
        :param: max_attempts: max retry attempts
        :yield: the responses
        """
        request_timeout = (
            self.params.request_timeout if request_timeout is None else request_timeout
        )
        request_retry_delay = (
            self.params.request_retry_delay
            if request_retry_delay is None
            else request_retry_delay
        )
        tx_timeout = self.params.tx_timeout if tx_timeout is None else tx_timeout
        max_attempts = (
            self.params.max_attempts if max_attempts is None else max_attempts
        )
        while not stop_condition():
            self.context.logger.debug(
                f"Trying to send payload: {pprint.pformat(payload.json)}"
            )
            signature_bytes = yield from self.get_signature(payload.encode())
            transaction = Transaction(payload, signature_bytes)
            try:
                response = yield from self._submit_tx(
                    transaction.encode(), timeout=request_timeout
                )
                # There is no guarantee that beyond this line will be executed for a given behaviour execution.
                # The tx could lead to a round transition which exits us from the behaviour execution.
                # It's unlikely to happen anywhere before line 538 but there it is very likely to not
                # yield in time before the behaviour is finished. As a result logs below might not show
                # up on the happy execution path.
            except TimeoutException:
                self.context.logger.info(
                    f"Timeout expired for submit tx. Retrying in {request_retry_delay} seconds..."
                )
                payload = payload.with_new_id()
                yield from self.sleep(request_retry_delay)
                continue
            response = cast(HttpMessage, response)
            non_200_code = not self._check_http_return_code_200(response)
            if non_200_code and (
                self._non_200_return_code_count
                > NON_200_RETURN_CODE_DURING_RESET_THRESHOLD
                or not resetting
            ):
                self.context.logger.info(
                    f"Received return code != 200 with response {response} with body {str(response.body)}. "
                    f"Retrying in {request_retry_delay} seconds..."
                )
            elif non_200_code and resetting:
                self._non_200_return_code_count += 1
            if non_200_code:
                payload = payload.with_new_id()
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
            if json_body["result"]["code"] != OK_CODE:
                self.context.logger.info(
                    f"Received tendermint code != 0. Retrying in {request_retry_delay} seconds..."
                )
                yield from self.sleep(request_retry_delay)
                continue  # pragma: nocover

            try:
                is_delivered, res = yield from self._wait_until_transaction_delivered(
                    tx_hash,
                    timeout=tx_timeout,
                    max_attempts=max_attempts,
                    request_retry_delay=request_retry_delay,
                )
            except TimeoutException:
                self.context.logger.info(
                    f"Timeout expired for wait until transaction delivered. Retrying in {request_retry_delay} seconds..."
                )
                payload = payload.with_new_id()
                yield from self.sleep(request_retry_delay)
                continue  # pragma: nocover

            if is_delivered:
                self.context.logger.info("A2A transaction delivered!")
                break
            if isinstance(res, HttpMessage) and self._is_invalid_transaction(res):
                self.context.logger.info(
                    f"Tx sent but not delivered. Invalid transaction - not trying again! Response = {res}"
                )
                break
            # otherwise, repeat until done, or until stop condition is true
            if isinstance(res, HttpMessage) and self._tx_not_found(tx_hash, res):
                self.context.logger.info(f"Tx {tx_hash} not found! Response = {res}")
            else:
                self.context.logger.info(f"Tx sent but not delivered. Response = {res}")
            payload = payload.with_new_id()
        self.context.logger.info(
            "Stop condition is true, no more attempts to send the transaction."
        )

    @staticmethod
    def _is_invalid_transaction(res: HttpMessage) -> bool:
        """Check if the transaction is invalid."""
        try:
            error_codes = ["TransactionNotValidError"]
            body_ = json.loads(res.body)
            return any(
                [error_code in body_["tx_result"]["info"] for error_code in error_codes]
            )
        except Exception:  # pylint: disable=broad-except  # pragma: nocover
            return False

    @staticmethod
    def _tx_not_found(tx_hash: str, res: HttpMessage) -> bool:
        """Check if the transaction could not be found."""
        try:
            error = json.loads(res.body)["error"]
            not_found_field_to_text = {
                "code": -32603,
                "message": "Internal error",
                "data": f"tx ({tx_hash}) not found",
            }
            return all(
                [
                    text == error[field]
                    for field, text in not_found_field_to_text.items()
                ]
            )
        except Exception:  # pylint: disable=broad-except  # pragma: nocover
            return False

    def _send_signing_request(
        self, raw_message: bytes, is_deprecated_mode: bool = False
    ) -> None:
        """
        Send a signing request.

        Happy-path full flow of the messages.

        AbstractRoundAbci skill -> (SigningMessage | SIGN_MESSAGE) -> DecisionMaker
        DecisionMaker -> (SigningMessage | SIGNED_MESSAGE) -> AbstractRoundAbci skill

        :param raw_message: raw message bytes
        :param is_deprecated_mode: is deprecated flag.
        """
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
        ] = self.get_callback_request()
        self.context.decision_maker_message_queue.put_nowait(signing_msg)

    def _send_transaction_signing_request(
        self, raw_transaction: RawTransaction, terms: Terms
    ) -> None:
        """
        Send a transaction signing request.

        Happy-path full flow of the messages.

        AbstractRoundAbci skill -> (SigningMessage | SIGN_TRANSACTION) -> DecisionMaker
        DecisionMaker -> (SigningMessage | SIGNED_TRANSACTION) -> AbstractRoundAbci skill

        :param raw_transaction: raw transaction data
        :param terms: signing terms
        """
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
        ] = self.get_callback_request()
        self.context.decision_maker_message_queue.put_nowait(signing_msg)

    def _send_transaction_request(self, signing_msg: SigningMessage) -> None:
        """
        Send transaction request.

        Happy-path full flow of the messages.

        AbstractRoundAbci skill -> (LedgerApiMessage | SEND_SIGNED_TRANSACTION) -> Ledger connection
        Ledger connection -> (LedgerApiMessage | TRANSACTION_DIGEST) -> AbstractRoundAbci skill

        :param signing_msg: signing message
        """
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
        ] = self.get_callback_request()
        self.context.outbox.put_message(message=ledger_api_msg)
        self.context.logger.info("sending transaction to ledger.")

    def _send_transaction_receipt_request(
        self,
        tx_digest: str,
        retry_timeout: Optional[int] = None,
        retry_attempts: Optional[int] = None,
    ) -> None:
        """
        Send transaction receipt request.

        Happy-path full flow of the messages.

        AbstractRoundAbci skill -> (LedgerApiMessage | GET_TRANSACTION_RECEIPT) -> Ledger connection
        Ledger connection -> (LedgerApiMessage | TRANSACTION_RECEIPT) -> AbstractRoundAbci skill

        :param tx_digest: transaction digest string
        :param retry_timeout: retry timeout in seconds
        :param retry_attempts: number of retry attempts
        """
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
        ] = self.get_callback_request()
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
        """Send a broadcast_tx_sync request.

        Happy-path full flow of the messages.

        _do_request:
            AbstractRoundAbci skill -> (HttpMessage | REQUEST) -> Http client connection
            Http client connection -> (HttpMessage | RESPONSE) -> AbstractRoundAbci skill

        :param tx_bytes: transaction bytes
        :param timeout: timeout seconds
        :yield: HttpMessage object
        :return: http response
        """
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
        """
        Get transaction info from tx hash.

        Happy-path full flow of the messages.

        _do_request:
            AbstractRoundAbci skill -> (HttpMessage | REQUEST) -> Http client connection
            Http client connection -> (HttpMessage | RESPONSE) -> AbstractRoundAbci skill

        :param tx_hash: transaction hash
        :param timeout: timeout in seconds
        :yield: HttpMessage object
        :return: http response
        """
        request_message, http_dialogue = self._build_http_request_message(
            "GET",
            self.context.params.tendermint_url + f"/tx?hash=0x{tx_hash}",
        )
        result = yield from self._do_request(
            request_message, http_dialogue, timeout=timeout
        )
        return result

    def _get_status(self) -> Generator[None, None, HttpMessage]:
        """
        Get Tendermint node's status.

        Happy-path full flow of the messages.

        _do_request:
            AbstractRoundAbci skill -> (HttpMessage | REQUEST) -> Http client connection
            Http client connection -> (HttpMessage | RESPONSE) -> AbstractRoundAbci skill

        :yield: HttpMessage object
        :return: http response from tendermint
        """
        request_message, http_dialogue = self._build_http_request_message(
            "GET",
            self.context.params.tendermint_url + "/status",
        )
        result = yield from self._do_request(request_message, http_dialogue)
        return result

    def get_callback_request(self) -> Callable[[Message, "BaseBehaviour"], None]:
        """Wrapper for callback request which depends on whether the message has not been handled on time.

        :return: the request callback.
        """

        def callback_request(
            message: Message, current_behaviour: BaseBehaviour
        ) -> None:
            """The callback request."""
            if self.is_stopped:
                self.context.logger.debug(
                    "dropping message as behaviour has stopped: %s", message
                )
            elif self != current_behaviour:
                self.handle_late_messages(self.behaviour_id, message)
            elif self.state == AsyncBehaviour.AsyncState.WAITING_MESSAGE:
                self.try_send(message)
            else:
                self.context.logger.warning(
                    "could not send message to FSMBehaviour: %s", message
                )

        return callback_request

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

        Happy-path full flow of the messages.

        _do_request:
            AbstractRoundAbci skill -> (HttpMessage | REQUEST) -> Http client connection
            Http client connection -> (HttpMessage | RESPONSE) -> AbstractRoundAbci skill

        :param method: the http request method (i.e. 'GET' or 'POST').
        :param url: the url to send the message to.
        :param content: the payload.
        :param headers: headers to be included.
        :param parameters: url query parameters.
        :yield: HttpMessage object
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

        Happy-path full flow of the messages.

        AbstractRoundAbci skill -> (HttpMessage | REQUEST) -> Http client connection
        Http client connection -> (HttpMessage | RESPONSE) -> AbstractRoundAbci skill

        :param request_message: The request message
        :param http_dialogue: the HTTP dialogue associated to the request
        :param timeout: seconds to wait for the reply.
        :yield: HttpMessage object
        :return: the response message
        """
        self.context.outbox.put_message(message=request_message)
        request_nonce = self._get_request_nonce_from_dialogue(http_dialogue)
        cast(Requests, self.context.requests).request_id_to_callback[
            request_nonce
        ] = self.get_callback_request()
        # notify caller by propagating potential timeout exception.
        response = yield from self.wait_for_message(timeout=timeout)
        return response

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
        max_attempts: Optional[int] = None,
        request_retry_delay: Optional[float] = None,
    ) -> Generator[None, None, Tuple[bool, Optional[HttpMessage]]]:
        """
        Wait until transaction is delivered.

        Happy-path full flow of the messages.

        _get_tx_info:
            AbstractRoundAbci skill -> (HttpMessage | REQUEST) -> Http client connection
            Http client connection -> (HttpMessage | RESPONSE) -> AbstractRoundAbci skill

        This is a local method that does not depend on the global clock,
        so the usage of datetime.now() is acceptable here.

        :param tx_hash: the transaction hash to check.
        :param timeout: timeout
        :param: request_retry_delay: the delay to wait after failed requests
        :param: max_attempts: the maximun number of attempts
        :yield: None
        :return: True if it is delivered successfully, False otherwise
        """
        if timeout is not None:
            deadline = datetime.datetime.now() + datetime.timedelta(0, timeout)
        else:
            deadline = datetime.datetime.max
        request_retry_delay = (
            self.params.request_retry_delay
            if request_retry_delay is None
            else request_retry_delay
        )
        max_attempts = (
            self.params.max_attempts if max_attempts is None else max_attempts
        )

        response = None
        for _ in range(max_attempts):
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
            return tx_result["code"] == OK_CODE, response

        return False, response

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
        """
        Get signature for message.

        Happy-path full flow of the messages.

        _send_signing_request:
            AbstractRoundAbci skill -> (SigningMessage | SIGN_MESSAGE) -> DecisionMaker
            DecisionMaker -> (SigningMessage | SIGNED_MESSAGE) -> AbstractRoundAbci skill

        :param message: message bytes
        :param is_deprecated_mode: is deprecated mode flag
        :yield: SigningMessage object
        :return: message signature
        """
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
    ) -> Generator[
        None,
        Union[None, SigningMessage, LedgerApiMessage],
        Tuple[Optional[str], RPCResponseStatus],
    ]:
        """
        Send raw transactions to the ledger for mining.

        Happy-path full flow of the messages.

        _send_transaction_signing_request:
                AbstractRoundAbci skill -> (SigningMessage | SIGN_TRANSACTION) -> DecisionMaker
                DecisionMaker -> (SigningMessage | SIGNED_TRANSACTION) -> AbstractRoundAbci skill

        _send_transaction_request:
            AbstractRoundAbci skill -> (LedgerApiMessage | SEND_SIGNED_TRANSACTION) -> Ledger connection
            Ledger connection -> (LedgerApiMessage | TRANSACTION_DIGEST) -> AbstractRoundAbci skill

        :param transaction: transaction data
        :yield: SigningMessage object
        :return: transaction hash
        """
        terms = Terms(
            self.context.default_ledger_id,
            self.context.agent_address,
            counterparty_address="",
            amount_by_currency_id={},
            quantities_by_good_id={},
            nonce="",
        )
        self.context.logger.info(
            f"Sending signing request for transaction: {transaction}..."
        )
        self._send_transaction_signing_request(transaction, terms)
        signature_response = yield from self.wait_for_message()
        signature_response = cast(SigningMessage, signature_response)
        tx_hash_backup = signature_response.signed_transaction.body.get("hash")
        if (
            signature_response.performative
            != SigningMessage.Performative.SIGNED_TRANSACTION
        ):
            self.context.logger.error("Error when requesting transaction signature.")
            return None, RPCResponseStatus.UNCLASSIFIED_ERROR
        self.context.logger.info(
            f"Received signature response: {signature_response}\n Sending transaction..."
        )
        self._send_transaction_request(signature_response)
        transaction_digest_msg = yield from self.wait_for_message()
        transaction_digest_msg = cast(LedgerApiMessage, transaction_digest_msg)
        if (
            transaction_digest_msg.performative
            != LedgerApiMessage.Performative.TRANSACTION_DIGEST
        ):
            error = f"Error when requesting transaction digest: {transaction_digest_msg.message}"
            self.context.logger.error(error)
            return tx_hash_backup, self.__parse_rpc_error(error)
        self.context.logger.info(
            f"Transaction sent! Received transaction digest: {transaction_digest_msg}"
        )
        tx_hash = transaction_digest_msg.transaction_digest.body

        if tx_hash != tx_hash_backup:
            # this should never happen
            self.context.logger.error(
                f"Unexpected error! The signature response's hash `{tx_hash_backup}` "
                f"does not match the one received from the transaction response `{tx_hash}`!"
            )
            return None, RPCResponseStatus.UNCLASSIFIED_ERROR

        return tx_hash, RPCResponseStatus.SUCCESS

    def get_transaction_receipt(
        self,
        tx_digest: str,
        retry_timeout: Optional[int] = None,
        retry_attempts: Optional[int] = None,
    ) -> Generator[None, None, Optional[Dict]]:
        """
        Get transaction receipt.

        Happy-path full flow of the messages.

        _send_transaction_receipt_request:
            AbstractRoundAbci skill -> (LedgerApiMessage | GET_TRANSACTION_RECEIPT) -> Ledger connection
            Ledger connection -> (LedgerApiMessage | TRANSACTION_RECEIPT) -> AbstractRoundAbci skill

        :param tx_digest: transaction digest received from raw transaction.
        :param retry_timeout: retry timeout.
        :param retry_attempts: number of retry attempts allowed.
        :yield: LedgerApiMessage object
        :return: transaction receipt data
        """
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
        Request data from ledger api

        Happy-path full flow of the messages.

        AbstractRoundAbci skill -> (LedgerApiMessage | LedgerApiMessage.Performative) -> Ledger connection
        Ledger connection -> (LedgerApiMessage | LedgerApiMessage.Performative) -> AbstractRoundAbci skill

        :param performative: the message performative
        :param ledger_callable: the callable to call on the contract
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
        ] = self.get_callback_request()
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

        Happy-path full flow of the messages.

        AbstractRoundAbci skill -> (ContractApiMessage | ContractApiMessage.Performative) -> Ledger connection (contract dispatcher)
        Ledger connection (contract dispatcher) -> (ContractApiMessage | ContractApiMessage.Performative) -> AbstractRoundAbci skill

        :param performative: the message performative
        :param contract_address: the contract address
        :param contract_id: the contract id
        :param contract_callable: the callable to call on the contract
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
        ] = self.get_callback_request()
        self.context.outbox.put_message(message=contract_api_msg)
        response = yield from self.wait_for_message()
        return response

    @staticmethod
    def __parse_rpc_error(error: str) -> RPCResponseStatus:
        """Parse an RPC error and return an `RPCResponseStatus`"""
        if "replacement transaction underpriced" in error:
            return RPCResponseStatus.UNDERPRICED
        if "nonce too low" in error:
            return RPCResponseStatus.INCORRECT_NONCE
        if "insufficient funds" in error:
            return RPCResponseStatus.INSUFFICIENT_FUNDS
        if "already known" in error:
            return RPCResponseStatus.ALREADY_KNOWN
        return RPCResponseStatus.UNCLASSIFIED_ERROR

    def _start_reset(self) -> Generator:
        """Start tendermint reset.

        This is a local method that does not depend on the global clock,
        so the usage of datetime.now() is acceptable here.

        :yield: None
        """
        if self._check_started is None and not self._is_healthy:
            # we do the reset in the middle of the pause as there are no immediate transactions on either side of the reset
            yield from self.wait_from_last_timestamp(
                self.params.observation_interval / 2
            )
            self._check_started = datetime.datetime.now()
            self._timeout = self.params.max_healthcheck
            self._is_healthy = False
        yield

    def _end_reset(
        self,
    ) -> None:
        """End tendermint reset.

        This is a local method that does not depend on the global clock,
        so the usage of datetime.now() is acceptable here.
        """
        self._check_started = None
        self._timeout = -1.0
        self._is_healthy = True

    def _is_timeout_expired(self) -> bool:
        """Check if the timeout expired.

        This is a local method that does not depend on the global clock,
        so the usage of datetime.now() is acceptable here.

        :return: bool
        """
        if self._check_started is None or self._is_healthy:
            return False
        return datetime.datetime.now() > self._check_started + datetime.timedelta(
            0, self._timeout
        )

    def _get_reset_params(self, default: bool) -> Optional[List[Tuple[str, str]]]:
        """Get the parameters for a hard reset request to Tendermint."""
        if default:
            return None

        last_round_transition_timestamp = (
            self.context.state.round_sequence.last_round_transition_timestamp
        )
        genesis_time = last_round_transition_timestamp.astimezone(pytz.UTC).strftime(
            GENESIS_TIME_FMT
        )
        # Initial height needs to account for the asynchrony among agents.
        # For that reason, we are using an offset in the initial block's height.
        # The bigger the observation interval, the larger the lag among the agents might be.
        # Also, if the observation interval is too tiny, we do not want the offset to be too small.
        # Therefore, we choose between a minimum value and the interval multiplied by a constant.
        # The larger the `HEIGHT_OFFSET_MULTIPLIER` constant's value, the larger the margin of error.
        initial_height = str(
            self.context.state.round_sequence.last_round_transition_tm_height
            + max(
                MIN_HEIGHT_OFFSET,
                math.ceil(self.params.observation_interval * HEIGHT_OFFSET_MULTIPLIER),
            )
        )

        return [
            ("genesis_time", genesis_time),
            ("initial_height", initial_height),
        ]

    def reset_tendermint_with_wait(
        self,
        on_startup: bool = False,
    ) -> Generator[None, None, bool]:
        """Resets the tendermint node."""
        yield from self._start_reset()
        if self._is_timeout_expired():
            # if the Tendermint node cannot update the app then the app cannot work
            raise RuntimeError("Error resetting tendermint node.")

        if not self._is_healthy:
            self.context.logger.info(
                f"Resetting tendermint node at end of period={self.synchronized_data.period_count}."
            )

            request_message, http_dialogue = self._build_http_request_message(
                "GET",
                self.params.tendermint_com_url + "/hard_reset",
                parameters=self._get_reset_params(on_startup),
            )
            result = yield from self._do_request(request_message, http_dialogue)
            try:
                response = json.loads(result.body.decode())
                if response.get("status"):
                    self.context.logger.info(response.get("message"))
                    self.context.logger.info(
                        "Resetting tendermint node successful! Resetting local blockchain."
                    )
                    self.context.state.round_sequence.reset_blockchain(
                        response.get("is_replay", False)
                    )
                    self.context.state.round_sequence.abci_app.cleanup(
                        self.params.cleanup_history_depth,
                        self.params.cleanup_history_depth_current,
                    )

                    for handler_name in self.context.handlers.__dict__.keys():
                        dialogues = getattr(self.context, f"{handler_name}_dialogues")
                        dialogues.cleanup()

                    self._end_reset()
                else:
                    msg = response.get("message")
                    self.context.logger.error(f"Error resetting: {msg}")
                    yield from self.sleep(self.params.sleep_time)
                    return False
            except json.JSONDecodeError:
                self.context.logger.error(
                    "Error communicating with tendermint com server."
                )
                yield from self.sleep(self.params.sleep_time)
                return False

        status = yield from self._get_status()
        try:
            json_body = json.loads(status.body.decode())
        except json.JSONDecodeError:
            self.context.logger.error(
                "Tendermint not accepting transactions yet, trying again!"
            )
            yield from self.sleep(self.params.sleep_time)
            return False

        remote_height = int(json_body["result"]["sync_info"]["latest_block_height"])
        local_height = self.context.state.round_sequence.height
        self.context.logger.info(
            "local-height = %s, remote-height=%s", local_height, remote_height
        )
        if local_height != remote_height:
            self.context.logger.info("local height != remote height; retrying...")
            yield from self.sleep(self.params.sleep_time)
            return False

        self.context.logger.info(
            "local height == remote height; continuing execution..."
        )
        yield from self.wait_from_last_timestamp(self.params.observation_interval / 2)
        return True


class DegenerateBehaviour(BaseBehaviour, ABC):
    """An abstract matching behaviour for final and degenerate rounds."""

    matching_round: Type[AbstractRound]
    is_degenerate: bool = True

    def async_act(self) -> Generator:
        """Raise a RuntimeError."""
        raise RuntimeError(
            "The execution reached a degenerate behaviour. "
            "This means a degenerate round has been reached during "
            "the execution of the ABCI application. Please check the "
            "functioning of the ABCI app."
        )


def make_degenerate_behaviour(round_id: str) -> Type[DegenerateBehaviour]:
    """Make a degenerate behaviour class."""

    class NewDegenerateBehaviour(DegenerateBehaviour):
        """A newly defined degenerate behaviour class."""

        behaviour_id = f"degenerate_{round_id}"

    new_behaviour_cls = NewDegenerateBehaviour
    new_behaviour_cls.__name__ = f"DegenerateBehaviour_{round_id}"  # type: ignore # pylint: disable=attribute-defined-outside-init
    return new_behaviour_cls  # type: ignore
