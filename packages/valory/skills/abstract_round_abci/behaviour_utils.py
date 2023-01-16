# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2023 Valory AG
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
import sys
from abc import ABC, ABCMeta, abstractmethod
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
    Union,
    cast,
)

import pytz
from aea.exceptions import enforce
from aea.mail.base import EnvelopeContext
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
from packages.valory.connections.ipfs.connection import PUBLIC_ID as IPFS_CONNECTION_ID
from packages.valory.connections.p2p_libp2p_client.connection import (
    PUBLIC_ID as P2P_LIBP2P_CLIENT_PUBLIC_ID,
)
from packages.valory.contracts.service_registry.contract import (  # noqa: F401  # pylint: disable=unused-import
    ServiceRegistryContract,
)
from packages.valory.protocols.contract_api import ContractApiMessage
from packages.valory.protocols.http import HttpMessage
from packages.valory.protocols.ipfs import IpfsMessage
from packages.valory.protocols.ipfs.dialogues import IpfsDialogue, IpfsDialogues
from packages.valory.protocols.ledger_api import LedgerApiMessage
from packages.valory.protocols.tendermint import TendermintMessage
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
    TendermintDialogues,
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
    TendermintRecoveryParams,
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
TM_REQ_TIMEOUT = 5  # 5 seconds


class SendException(Exception):
    """Exception raised if the 'try_send' to an AsyncBehaviour failed."""


class TimeoutException(Exception):
    """Exception raised when a timeout during AsyncBehaviour occurs."""


class BaseBehaviourInternalError(Exception):
    """Internal error due to a bad implementation of the BaseBehaviour."""

    def __init__(self, message: str, *args: Any) -> None:
        """Initialize the error object."""
        super().__init__("internal error: " + message, *args)


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
    def is_notified(self) -> bool:
        """Returns whether the behaviour has been notified about the arrival of a message."""
        return self.__notified

    @property
    def received_message(self) -> Any:
        """Returns the message the behaviour has received. "__message" should be None if not availble or already consumed."""
        return self.__message

    def _on_sent_message(self) -> None:
        """To be called after the message received is consumed. Removes the already sent notification and message."""
        self.__notified = False
        self.__message = None

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


class IPFSBehaviour(SimpleBehaviour, ABC):
    """Behaviour for interactions with IPFS."""

    def __init__(self, **kwargs: Any):
        """Initialize an `IPFSBehaviour`."""
        super().__init__(**kwargs)
        loader_cls = kwargs.pop("loader_cls", Loader)
        storer_cls = kwargs.pop("storer_cls", Storer)
        self._ipfs_interact = IPFSInteract(loader_cls, storer_cls)

    def _build_ipfs_message(
        self,
        performative: IpfsMessage.Performative,
        timeout: Optional[float] = None,
        **kwargs: Any,
    ) -> Tuple[IpfsMessage, IpfsDialogue]:
        """Builds an IPFS message."""
        ipfs_dialogues = cast(IpfsDialogues, self.context.ipfs_dialogues)
        message, dialogue = ipfs_dialogues.create(
            counterparty=str(IPFS_CONNECTION_ID),
            performative=performative,
            timeout=timeout,
            **kwargs,
        )
        return message, dialogue

    def _build_ipfs_store_file_req(  # pylint: disable=too-many-arguments
        self,
        filename: str,
        obj: SupportedObjectType,
        multiple: bool = False,
        filetype: Optional[SupportedFiletype] = None,
        custom_storer: Optional[CustomStorerType] = None,
        timeout: Optional[float] = None,
        **kwargs: Any,
    ) -> Tuple[IpfsMessage, IpfsDialogue]:
        """
        Builds a STORE_FILES ipfs message.

        :param filename: the file name to store obj in. If "multiple" is True, filename will be the name of the dir.
        :param obj: the object(s) to serialize and store in IPFS as "filename".
        :param multiple: whether obj should be stored as multiple files, i.e. directory.
        :param custom_storer: a custom serializer for "obj".
        :param timeout: timeout for the request.
        :returns: the ipfs message, and its corresponding dialogue.
        """
        serialized_objects = self._ipfs_interact.store(
            filename, obj, multiple, filetype, custom_storer, **kwargs
        )
        message, dialogue = self._build_ipfs_message(
            performative=IpfsMessage.Performative.STORE_FILES,  # type: ignore
            files=serialized_objects,
            timeout=timeout,
        )
        return message, dialogue

    def _build_ipfs_get_file_req(
        self,
        ipfs_hash: str,
        timeout: Optional[float] = None,
    ) -> Tuple[IpfsMessage, IpfsDialogue]:
        """
        Builds a GET_FILES IPFS request.

        :param ipfs_hash: the ipfs hash of the file/dir to download.
        :param timeout: timeout for the request.
        :returns: the ipfs message, and its corresponding dialogue.
        """
        message, dialogue = self._build_ipfs_message(
            performative=IpfsMessage.Performative.GET_FILES,  # type: ignore
            ipfs_hash=ipfs_hash,
            timeout=timeout,
        )
        return message, dialogue

    def _deserialize_ipfs_objects(  # pylint: disable=too-many-arguments
        self,
        serialized_objects: Dict[str, str],
        filetype: Optional[SupportedFiletype] = None,
        custom_loader: CustomLoaderType = None,
    ) -> Optional[SupportedObjectType]:
        """Deserialize objects received from IPFS."""
        deserialized_object = self._ipfs_interact.load(
            serialized_objects, filetype, custom_loader
        )
        return deserialized_object


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


class _MetaBaseBehaviour(ABCMeta):
    """A metaclass that validates BaseBehaviour's attributes."""

    def __new__(mcs, name: str, bases: Tuple, namespace: Dict, **kwargs: Any) -> Type:  # type: ignore
        """Initialize the class."""
        new_cls = super().__new__(mcs, name, bases, namespace, **kwargs)

        if ABC in bases:
            # abstract class, return
            return new_cls
        if not issubclass(new_cls, BaseBehaviour):
            # the check only applies to AbciApp subclasses
            return new_cls

        mcs._check_consistency(cast(Type[BaseBehaviour], new_cls))
        return new_cls

    @classmethod
    def _check_consistency(mcs, base_behaviour_cls: Type["BaseBehaviour"]) -> None:
        """Check consistency of class attributes."""
        mcs._check_required_class_attributes(base_behaviour_cls)

    @classmethod
    def _check_required_class_attributes(
        mcs, base_behaviour_cls: Type["BaseBehaviour"]
    ) -> None:
        """Check that required class attributes are set."""
        if not hasattr(base_behaviour_cls, "matching_round"):
            raise BaseBehaviourInternalError(
                f"'matching_round' not set on {base_behaviour_cls}"
            )


class BaseBehaviour(
    AsyncBehaviour, IPFSBehaviour, CleanUpBehaviour, ABC, metaclass=_MetaBaseBehaviour
):
    """
    This class represents the base class for FSM behaviours

    A behaviour is a state of the FSM App execution. It usually involves
    interactions between participants in the FSM App,
    although this is not enforced at this level of abstraction.

    Concrete classes must set:
    - matching_round: the round class matching the behaviour;

    Optionally, behaviour_id can be defined, although it is recommended to use the autogenerated id.
    """

    __pattern = re.compile(r"(?<!^)(?=[A-Z])")
    is_programmatically_defined = True
    is_degenerate: bool = False

    matching_round: Type[AbstractRound]

    behaviour_id: str

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

    @classmethod
    def auto_behaviour_id(cls) -> str:
        """
        Get behaviour id automatically.

        This method returns the auto generated id from the class name if the
        class variable behaviour_id is not set on the child class.
        Otherwise, it returns the class variable behaviour_id.
        """
        return (
            cls.behaviour_id
            if isinstance(cls.behaviour_id, str)
            else cls.__pattern.sub("_", cls.__name__).lower()
        )

    @property  # type: ignore
    def behaviour_id(self) -> str:
        """Get behaviour id."""
        return self.auto_behaviour_id()

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
        round_id = self.matching_round.auto_round_id()
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
        stop_condition = self.is_round_ended(self.matching_round.auto_round_id())
        round_count = cast(
            SharedState, self.context.state
        ).synchronized_data.round_count
        object.__setattr__(payload, "round_count", round_count)
        yield from self._send_transaction(
            payload,
            resetting,
            stop_condition=stop_condition,
        )

    def async_act_wrapper(self) -> Generator:
        """Do the act, supporting asynchronous execution."""
        if not self._is_started:
            self._log_start()
            self._is_started = True
        try:
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

    def _get_netinfo(
        self, timeout: Optional[float] = None
    ) -> Generator[None, None, HttpMessage]:
        """Makes a GET request to it's tendermint node's /net_info endpoint."""
        request_message, http_dialogue = self._build_http_request_message(
            method="GET", url=f"{self.context.params.tendermint_url}/net_info"
        )
        result = yield from self._do_request(request_message, http_dialogue, timeout)
        return result

    def num_active_peers(
        self, timeout: Optional[float] = None
    ) -> Generator[None, None, Optional[int]]:
        """Returns the number of active peers in the network."""
        try:
            http_response = yield from self._get_netinfo(timeout)
            http_ok = 200
            if http_response.status_code != http_ok:
                # a bad response was received, we cannot retrieve the number of active peers
                self.context.logger.warning(
                    f"/net_info responded with status {http_response.status_code}"
                )
                return None

            res_body = json.loads(http_response.body)
            num_peers_str = res_body.get("result", {}).get("n_peers", None)
            if num_peers_str is None:
                return None
            num_peers = int(num_peers_str)
            # num_peers hold the number of peers the tm node we are
            # making the TX to currently has an active connection
            # we add 1 because the node we are making the request through
            # is not accounted for in this number
            return num_peers + 1
        except TimeoutException:
            self.context.logger.warning(
                f"Couldn't retrieve `/net_info` response in {timeout}s."
            )
            return None

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

    def _acn_request_from_pending(
        self, performative: TendermintMessage.Performative
    ) -> Generator:
        """Perform an ACN request to each one of the agents which have not sent a response yet."""
        not_responded_yet = {
            address
            for address, deliverable in cast(
                SharedState, self.context.state
            ).address_to_acn_deliverable.items()
            if deliverable is None
        }

        if len(not_responded_yet) == 0:
            return

        self.context.logger.debug(f"Need ACN response from {not_responded_yet}.")
        for address in not_responded_yet:
            self.context.logger.debug(f"Sending ACN request to {address}.")
            dialogues = cast(TendermintDialogues, self.context.tendermint_dialogues)
            message, _ = dialogues.create(
                counterparty=address, performative=performative
            )
            message = cast(TendermintMessage, message)
            context = EnvelopeContext(connection_id=P2P_LIBP2P_CLIENT_PUBLIC_ID)
            self.context.outbox.put_message(message=message, context=context)

        # we wait for the `address_to_acn_deliverable` to be populated with the responses (done by the tm handler)
        yield from self.sleep(self.params.sleep_time)

    def _perform_acn_request(
        self, performative: TendermintMessage.Performative
    ) -> Generator[None, None, Any]:
        """Perform an ACN request.

        Waits `sleep_time` to receive a common response from the majority of the agents.
        Retries `max_attempts` times only for the agents which have not responded yet.

        :param performative: the ACN request performative.
        :return: the result that the majority of the agents sent. If majority cannot be reached, returns `None`.
        """
        ourself = {self.context.agent_address}
        # reset the ACN deliverables at the beginning of a new request
        addresses = self.synchronized_data.all_participants - ourself
        cast(
            SharedState, self.context.state
        ).address_to_acn_deliverable = dict.fromkeys(addresses)

        for i in range(self.params.max_attempts):
            self.context.logger.debug(
                f"ACN attempt {i + 1}/{self.params.max_attempts}."
            )
            yield from self._acn_request_from_pending(performative)

            result = cast(SharedState, self.context.state).get_acn_result()
            if result is not None:
                return result

        return None

    def request_recovery_params(self) -> Generator[None, None, bool]:
        """Request the Tendermint recovery parameters from the other agents via the ACN."""

        self.context.logger.info(
            "Requesting the Tendermint recovery parameters from the other agents via the ACN."
        )

        performative = TendermintMessage.Performative.GET_RECOVERY_PARAMS
        acn_result = yield from self._perform_acn_request(performative)  # type: ignore

        if acn_result is None:
            self.context.logger.warning(
                "No majority has been reached for the Tendermint recovery parameters request via the ACN."
            )
            return False

        cast(SharedState, self.context.state).tm_recovery_params = acn_result
        self.context.logger.info(
            f"Updated the Tendermint recovery parameters from the other agents via the ACN: {acn_result}"
        )
        return True

    @property
    def hard_reset_sleep(self) -> float:
        """
        Amount of time to sleep before and after performing a hard reset.

        We sleep for half the observation interval as there are no immediate transactions on either side of the reset.

        :returns: the amount of time to sleep in seconds
        """
        return self.params.observation_interval / 2

    def _start_reset(self, on_startup: bool = False) -> Generator:
        """
        Start tendermint reset.

        This is a local method that does not depend on the global clock,
        so the usage of datetime.now() is acceptable here.

        :param on_startup: Whether we are resetting on the start of the agent.
        :yield: None
        """
        if self._check_started is None and not self._is_healthy:
            if not on_startup:
                # if we are on startup we don't need to wait for the observation interval
                # as the reset is being performed to update the tm config.
                yield from self.wait_from_last_timestamp(self.hard_reset_sleep)
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

    def reset_tendermint_with_wait(  # pylint: disable=too-many-locals, too-many-statements
        self,
        on_startup: bool = False,
        is_recovery: bool = False,
    ) -> Generator[None, None, bool]:
        """
        Performs a hard reset (unsafe-reset-all) on the tendermint node.

        :param on_startup: whether we are resetting on the start of the agent.
        :param is_recovery: whether the reset is being performed to recover the agent <-> tm communication.
        :yields: None
        :returns: whether the reset was successful.
        """
        yield from self._start_reset(on_startup=on_startup)
        if self._is_timeout_expired():
            # if the Tendermint node cannot update the app then the app cannot work
            raise RuntimeError("Error resetting tendermint node.")

        if not self._is_healthy:
            self.context.logger.info(
                f"Resetting tendermint node at end of period={self.synchronized_data.period_count}."
            )

            backup_blockchain = self.context.state.round_sequence.blockchain
            self.context.state.round_sequence.reset_blockchain()
            reset_params = self._get_reset_params(on_startup)
            request_message, http_dialogue = self._build_http_request_message(
                "GET",
                self.params.tendermint_com_url + "/hard_reset",
                parameters=reset_params,
            )
            result = yield from self._do_request(request_message, http_dialogue)
            try:
                response = json.loads(result.body.decode())
                if response.get("status"):
                    self.context.logger.info(response.get("message"))
                    self.context.logger.info("Resetting tendermint node successful!")
                    is_replay = response.get("is_replay", False)
                    if is_replay:
                        # in case of replay, the local blockchain should be set up differently.
                        self.context.state.round_sequence.reset_blockchain(
                            is_replay=is_replay, is_init=True
                        )
                    self.context.state.round_sequence.abci_app.cleanup(
                        self.params.cleanup_history_depth,
                        self.params.cleanup_history_depth_current,
                    )
                    for handler_name in self.context.handlers.__dict__.keys():
                        dialogues = getattr(self.context, f"{handler_name}_dialogues")
                        dialogues.cleanup()
                    if not is_recovery:
                        # in case of successful reset we store the reset params in the shared state,
                        # so that in the future if the communication with tendermint breaks, and we need to
                        # perform a hard reset to restore it, we can use these as the right ones
                        shared_state = cast(SharedState, self.context.state)
                        # we take one from the reset index and round count because they are incremented
                        # when resetting and scheduling rounds respectively
                        reset_index = (
                            shared_state.round_sequence.abci_app.reset_index - 1
                        )
                        round_count = shared_state.synchronized_data.db.round_count - 1
                        # in case we need to reset in order to recover agent <-> tm communication
                        # we store this round as the one to start from
                        restart_from_round = self.matching_round
                        shared_state.tm_recovery_params = TendermintRecoveryParams(
                            reset_params=reset_params,
                            reset_index=reset_index,
                            round_count=round_count,
                            reset_from_round=restart_from_round.auto_round_id(),
                        )
                    self._end_reset()

                else:
                    msg = response.get("message")
                    self.context.state.round_sequence.blockchain = backup_blockchain
                    self.context.logger.error(f"Error resetting: {msg}")
                    yield from self.sleep(self.params.sleep_time)
                    return False
            except json.JSONDecodeError:
                self.context.logger.error(
                    "Error communicating with tendermint com server."
                )
                self.context.state.round_sequence.blockchain = backup_blockchain
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
        if not on_startup:
            # if we are on startup we don't need to wait for the observation interval
            # as the reset is being performed to update the tm config.
            yield from self.wait_from_last_timestamp(self.hard_reset_sleep)
        return True

    def send_to_ipfs(  # pylint: disable=too-many-arguments
        self,
        filename: str,
        obj: SupportedObjectType,
        multiple: bool = False,
        filetype: Optional[SupportedFiletype] = None,
        custom_storer: Optional[CustomStorerType] = None,
        timeout: Optional[float] = None,
        **kwargs: Any,
    ) -> Generator[None, None, Optional[str]]:
        """
        Store an object on IPFS.

        :param filename: the file name to store obj in. If "multiple" is True, filename will be the name of the dir.
        :param obj: the object(s) to serialize and store in IPFS as "filename".
        :param multiple: whether obj should be stored as multiple files, i.e. directory.
        :param filetype: the file type of the object being downloaded.
        :param custom_storer: a custom serializer for "obj".
        :param timeout: timeout for the request.
        :returns: the downloaded object, corresponding to ipfs_hash.
        """
        try:
            message, dialogue = self._build_ipfs_store_file_req(
                filename,
                obj,
                multiple,
                filetype,
                custom_storer,
                timeout,
                **kwargs,
            )
            ipfs_message = yield from self._do_ipfs_request(dialogue, message, timeout)
            if ipfs_message.performative != IpfsMessage.Performative.IPFS_HASH:
                self.context.logger.error(
                    f"Expected performative {IpfsMessage.Performative.IPFS_HASH} but got {ipfs_message.performative}."
                )
                return None
            ipfs_hash = ipfs_message.ipfs_hash
            self.context.logger.info(f"Successfully stored with IPFS hash: {ipfs_hash}")
            return ipfs_hash
        except IPFSInteractionError as e:  # pragma: no cover
            self.context.logger.error(
                f"An error occurred while trying to send a file to IPFS: {str(e)}"
            )
            return None

    def get_from_ipfs(  # pylint: disable=too-many-arguments
        self,
        ipfs_hash: str,
        filetype: Optional[SupportedFiletype] = None,
        custom_loader: CustomLoaderType = None,
        timeout: Optional[float] = None,
    ) -> Generator[None, None, Optional[SupportedObjectType]]:
        """
        Gets an object from IPFS.

        :param ipfs_hash: the ipfs hash of the file/dir to download.
        :param filetype: the file type of the object being downloaded.
        :param custom_loader: a custom deserializer for the object received from IPFS.
        :param timeout: timeout for the request.
        :returns: the downloaded object, corresponding to ipfs_hash.
        """
        try:
            message, dialogue = self._build_ipfs_get_file_req(ipfs_hash, timeout)
            ipfs_message = yield from self._do_ipfs_request(dialogue, message, timeout)
            if ipfs_message.performative != IpfsMessage.Performative.FILES:
                self.context.logger.error(
                    f"Expected performative {IpfsMessage.Performative.FILES} but got {ipfs_message.performative}."
                )
                return None
            serialized_objects = ipfs_message.files
            deserialized_objects = self._deserialize_ipfs_objects(
                serialized_objects, filetype, custom_loader
            )
            self.context.logger.info(
                f"Retrieved {len(ipfs_message.files)} objects from ipfs."
            )
            return deserialized_objects
        except IPFSInteractionError as e:
            self.context.logger.error(
                f"An error occurred while trying to fetch a file from IPFS: {str(e)}"
            )
            return None

    def _do_ipfs_request(
        self,
        dialogue: IpfsDialogue,
        message: IpfsMessage,
        timeout: Optional[float] = None,
    ) -> Generator[None, None, IpfsMessage]:
        """Performs an IPFS request, and asynchronosuly waits for response."""
        self.context.outbox.put_message(message=message)
        request_nonce = self._get_request_nonce_from_dialogue(dialogue)
        cast(Requests, self.context.requests).request_id_to_callback[
            request_nonce
        ] = self.get_callback_request()
        # notify caller by propagating potential timeout exception.
        response = yield from self.wait_for_message(timeout=timeout)
        ipfs_message = cast(IpfsMessage, response)
        return ipfs_message


class TmManager(BaseBehaviour):
    """Util class to be used for managing the tendermint node."""

    _active_generator: Optional[Generator] = None
    _hard_reset_sleep = 20.0  # 20s
    _max_reset_retry = 5

    # TODO: TmManager is not a BaseBehaviour. It should be
    # redesigned!
    matching_round = Type[AbstractRound]

    def async_act(self) -> Generator:
        """The behaviour act."""
        self.context.logger.error(
            f"{type(self).__name__}'s async_act was called. "
            f"This is not allowed as this class is not a behaviour. "
            f"Exiting the agent."
        )
        error_code = 1
        sys.exit(error_code)

    @property
    def is_acting(self) -> bool:
        """This method returns whether there is an active fix being applied."""
        return self._active_generator is not None

    @property
    def hard_reset_sleep(self) -> float:
        """
        Amount of time to sleep before and after performing a hard reset.

        We don't need to wait for half the observation interval, like in normal cases where we perform a hard reset.

        :returns: the amount of time to sleep in seconds
        """
        return self._hard_reset_sleep

    def _kill_if_no_majority_peers(self) -> Generator[None, None, None]:
        """This method checks whether there are enough peers in the network to reach majority. If not, the agent is shut down."""
        # We assign a timeout to the num_active_peers request because we are trying to check whether the unhealthy
        # tm communication, i.e. tm not sending blocks to the abci (agent), is caused by not having enough peers
        # in the network. If that's the case, the node that is being queried has to be healthy, and respond in a
        # timely fashion. If the tm node doesn't respond in the specified timeout, we assume the problem is not
        # the lack of peers in the service.
        num_active_peers = yield from self.num_active_peers(timeout=TM_REQ_TIMEOUT)
        if (
            num_active_peers is not None
            and num_active_peers < self.params.consensus_params.consensus_threshold
        ):
            self.context.logger.error(
                f"There should be at least {self.params.consensus_params.consensus_threshold} peers in the service,"
                f" only {num_active_peers} are currently active. Shutting down the agent."
            )
            not_ok_code = 1
            sys.exit(not_ok_code)

    def _handle_unhealthy_tm(self) -> Generator:
        """This method handles the case when the tendermint node is unhealthy."""
        self.context.logger.warning(
            "The local deadline for the next `begin_block` request from the Tendermint node has expired! "
            "Trying to reset local Tendermint node as there could be something wrong with the communication."
        )

        # we first check whether the reason why we haven't received blocks for more than we allow is because
        # there are not enough peers in the network to reach majority.
        yield from self._kill_if_no_majority_peers()

        # since we have reached this point that means that the cause of blocks not being received
        # cannot be attributed to a lack of peers in the network
        # therefore, we request the recovery parameters via the ACN, and if we succeed, we use them to recover
        acn_communication_success = yield from self.request_recovery_params()
        if not acn_communication_success:
            self.context.logger.error(
                "Failed to get the recovery parameters via the ACN. Cannot reset Tendermint."
            )
            return

        shared_state = cast(SharedState, self.context.state)
        recovery_params = shared_state.tm_recovery_params
        shared_state.round_sequence.reset_state(
            restart_from_round=recovery_params.reset_from_round,
            round_count=recovery_params.round_count,
            reset_index=recovery_params.reset_index,
        )

        for _ in range(self._max_reset_retry):
            reset_successfully = yield from self.reset_tendermint_with_wait(
                is_recovery=True
            )
            if reset_successfully:
                self.context.logger.info(
                    "Tendermint reset was successfully performed. "
                )
                # we sleep to give some time for tendermint to start sending us blocks
                # otherwise we might end-up assuming that tendermint is still not working.
                # Note that the wait_from_last_timestamp() in reset_tendermint_with_wait()
                # doesn't guarantee us this, since the block stall deadline is greater than the
                # hard_reset_sleep, 60s vs 20s. In other words, we haven't received a block for at
                # least 60s, so wait_from_last_timestamp() will return immediately.
                yield from self.sleep(self.hard_reset_sleep)
                return

        self.context.logger.info("Failed to reset tendermint.")

    def _get_reset_params(self, default: bool) -> Optional[List[Tuple[str, str]]]:
        """
        Get the parameters for a hard reset request when trying to recover agent <-> tendermint communication.

        :param default: ignored for this use case.
        :returns: the reset params.
        """
        # we get the params from the latest successful reset, if they are not available,
        # i.e. no successful reset has been performed, we return None.
        # Returning None means default params will be used.
        reset_params = cast(
            SharedState, self.context.state
        ).tm_recovery_params.reset_params
        return reset_params

    def get_callback_request(self) -> Callable[[Message, "BaseBehaviour"], None]:
        """Wrapper for callback_request(), overridden to remove checks not applicable to TmManager."""

        def callback_request(
            message: Message, _current_behaviour: BaseBehaviour
        ) -> None:
            """
            This method gets called when a response for a prior request is received.

            Overridden to remove the check that checks whether the behaviour that made the request is still active.
            The received message gets passed to the behaviour that invoked it, in this case it's always the TmManager.

            :param message: the response.
            :param _current_behaviour: not used, left in to satisfy the interface.
            :return: none
            """
            if self.state == AsyncBehaviour.AsyncState.WAITING_MESSAGE:
                self.try_send(message)
            else:
                self.context.logger.warning(
                    "could not send message to TmManager: %s", message
                )

        return callback_request

    def try_fix(self) -> None:
        """This method tries to fix an unhealthy tendermint node."""
        if self._active_generator is None:
            # There is no active generator set, we need to create one.
            # A generator being active means that a reset operation is
            # being performed.
            self._active_generator = self._handle_unhealthy_tm()
        try:
            # if the behaviour is waiting for a message
            # we check whether one has arrived, and if it has
            # we send it to the generator.
            if self.state == self.AsyncState.WAITING_MESSAGE:
                if self.is_notified:
                    self._active_generator.send(self.received_message)
                    self._on_sent_message()
                # note that if the behaviour is waiting for
                # a message, we deliberately don't send a tick
                # this was done to have consistency between
                # the act here, and acts on normal AsyncBehaviours
                return
            # this will run the active generator until
            # the first yield statement is encountered
            self._active_generator.send(None)

        except StopIteration:
            # the generator is finished
            self.context.logger.info("Applying tendermint fix finished.")
            self._active_generator = None
            # the following is required because the message
            # 'tick' might be the last one the generator needs
            # to complete. In that scenario, we need to call
            # the callback here
            if self.is_notified:
                self._on_sent_message()


class DegenerateBehaviour(BaseBehaviour, ABC):
    """An abstract matching behaviour for final and degenerate rounds."""

    matching_round: Type[AbstractRound]
    is_degenerate: bool = True
    sleep_time_before_exit = 5.0

    def async_act(self) -> Generator:
        """Exit the agent with error when a degenerate round is reached."""
        self.context.logger.error(
            "The execution reached a degenerate behaviour. "
            "This means a degenerate round has been reached during "
            "the execution of the ABCI application. Please check the "
            "functioning of the ABCI app."
        )
        self.context.logger.error(
            f"Sleeping {self.sleep_time_before_exit} seconds before exiting."
        )
        yield from self.sleep(self.sleep_time_before_exit)
        error_code = 1
        sys.exit(error_code)


def make_degenerate_behaviour(
    round_cls: Type[AbstractRound],
) -> Type[DegenerateBehaviour]:
    """Make a degenerate behaviour class."""

    class NewDegenerateBehaviour(DegenerateBehaviour):
        """A newly defined degenerate behaviour class."""

        matching_round = round_cls

    new_behaviour_cls = NewDegenerateBehaviour
    new_behaviour_cls.__name__ = f"DegenerateBehaviour_{round_cls.auto_round_id()}"  # pylint: disable=attribute-defined-outside-init
    return new_behaviour_cls
