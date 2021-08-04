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

"""Tests for valory/abci connection."""
import asyncio
import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Callable, List, cast

import pytest
import requests
from aea.configurations.base import ConnectionConfig
from aea.identity.base import Identity
from aea.mail.base import Envelope
from aea.protocols.base import Address, Message
from aea.protocols.dialogue.base import Dialogue as BaseDialogue

from packages.valory.connections.abci.connection import (
    ABCIServerConnection,
    DEFAULT_ABCI_PORT,
    DEFAULT_LISTEN_ADDRESS,
)
from packages.valory.protocols.abci import AbciMessage
from packages.valory.protocols.abci.custom_types import (
    Events,
    ProofOps,
    ValidatorUpdate,
    ValidatorUpdates,
)
from packages.valory.protocols.abci.dialogues import AbciDialogue
from packages.valory.protocols.abci.dialogues import AbciDialogues as BaseAbciDialogues

from tests.conftest import HTTP_LOCALHOST, UseTendermint
from tests.helpers.async_utils import (
    AnotherThreadTask,
    BaseThreadedAsyncLoop,
    wait_for_condition,
)


class ABCIAppTest:
    """A dummy ABCI application for testing purposes."""

    class AbciDialogues(BaseAbciDialogues):
        """The dialogues class keeps track of all ABCI dialogues."""

        def __init__(self, address) -> None:
            """Initialize dialogues."""
            self.address = address

            def role_from_first_message(  # pylint: disable=unused-argument
                message: Message, receiver_address: Address
            ) -> BaseDialogue.Role:
                """Infer the role of the agent from an incoming/outgoing first message

                :param message: an incoming/outgoing first message
                :param receiver_address: the address of the receiving agent
                :return: The role of the agent
                """
                return AbciDialogue.Role.SERVER

            BaseAbciDialogues.__init__(
                self,
                self_address=self.address,
                role_from_first_message=role_from_first_message,
                dialogue_class=AbciDialogue,
            )

    def __init__(self, address: str):
        """Initialize."""
        self._dialogues = ABCIAppTest.AbciDialogues(address)

    def handle(self, request: AbciMessage) -> AbciMessage:
        """Process a request."""
        # check that it is not a response
        assert "request" in request.performative.value, "performative is not a Request"
        # performative of requests is of the form "request_{request_name}"
        request_type = request.performative.value.replace("request_", "")
        handler: Callable[[AbciMessage], AbciMessage] = getattr(
            self, request_type, self.no_match
        )
        return handler(request)

    def _update_dialogues(self, request: AbciMessage) -> AbciDialogue:
        """Update dialogues."""
        abci_dialogue = self._dialogues.update(request)
        assert abci_dialogue is not None, "cannot update dialogue"
        return cast(AbciDialogue, abci_dialogue)

    def info(self, request: AbciMessage) -> AbciMessage:
        """Process an info request."""
        abci_dialogue = self._update_dialogues(request)
        assert request.performative == AbciMessage.Performative.REQUEST_INFO
        info_data = ""
        version = request.version
        app_version = 0
        last_block_height = 0
        last_block_app_hash = b""
        response = abci_dialogue.reply(
            performative=AbciMessage.Performative.RESPONSE_INFO,
            info_data=info_data,
            version=version,
            app_version=app_version,
            last_block_height=last_block_height,
            last_block_app_hash=last_block_app_hash,
        )
        return cast(AbciMessage, response)

    def flush(self, request: AbciMessage):
        """Process a flush request."""
        abci_dialogue = self._update_dialogues(request)
        response = abci_dialogue.reply(
            performative=AbciMessage.Performative.RESPONSE_FLUSH
        )
        return cast(AbciMessage, response)

    def init_chain(self, request: AbciMessage):
        """Process an init_chain request."""
        abci_dialogue = self._update_dialogues(request)
        validators: List[ValidatorUpdate] = []
        app_hash = b""
        response = abci_dialogue.reply(
            performative=AbciMessage.Performative.RESPONSE_INIT_CHAIN,
            validators=ValidatorUpdates(validators),
            app_hash=app_hash,
        )
        return cast(AbciMessage, response)

    def query(self, request: AbciMessage) -> AbciMessage:
        """Process a query request."""
        abci_dialogue = self._update_dialogues(request)
        response = abci_dialogue.reply(
            performative=AbciMessage.Performative.RESPONSE_QUERY,
            code=0,
            log="",
            info="",
            index=0,
            key=b"",
            value=b"",
            proof_ops=ProofOps([]),
            height=0,
            codespace="",
        )
        return cast(AbciMessage, response)

    def check_tx(self, request: AbciMessage) -> AbciMessage:
        """Process a check_tx request."""
        abci_dialogue = self._update_dialogues(request)
        response = abci_dialogue.reply(
            performative=AbciMessage.Performative.RESPONSE_CHECK_TX,
            code=0,  # OK
            data=b"",
            log="",
            info="",
            gas_wanted=0,
            gas_used=0,
            events=Events([]),
            codespace="",
        )
        return cast(AbciMessage, response)

    def deliver_tx(self, request: AbciMessage) -> AbciMessage:
        """Process a deliver_tx request."""
        abci_dialogue = self._update_dialogues(request)
        response = abci_dialogue.reply(
            performative=AbciMessage.Performative.RESPONSE_DELIVER_TX,
            code=0,  # OK
            data=b"",
            log="",
            info="",
            gas_wanted=0,
            gas_used=0,
            events=Events([]),
            codespace="",
        )
        return cast(AbciMessage, response)

    def begin_block(self, request: AbciMessage):
        """Process a begin_block request."""
        abci_dialogue = self._update_dialogues(request)
        response = abci_dialogue.reply(
            performative=AbciMessage.Performative.RESPONSE_BEGIN_BLOCK,
            events=Events([]),
        )
        return cast(AbciMessage, response)

    def end_block(self, request: AbciMessage):
        """Process an end_block request."""
        abci_dialogue = self._update_dialogues(request)
        response = abci_dialogue.reply(
            performative=AbciMessage.Performative.RESPONSE_END_BLOCK,
            validator_updates=ValidatorUpdates([]),
            events=Events([]),
        )
        return cast(AbciMessage, response)

    def commit(self, request: AbciMessage):
        """Process a commit request."""
        abci_dialogue = self._update_dialogues(request)
        response = abci_dialogue.reply(
            performative=AbciMessage.Performative.RESPONSE_COMMIT,
            data=b"",
            retain_height=0,
        )
        return cast(AbciMessage, response)

    def no_match(self, request: AbciMessage):
        """No match."""
        raise Exception(
            f"Received request with performative {request.performative.value}, but no handler available"
        )


class BaseABCITest:
    """Base class for ABCI test."""

    def make_app(self) -> ABCIAppTest:
        """Make an ABCI app."""
        return ABCIAppTest(self.TARGET_SKILL_ID)  # type: ignore


@pytest.mark.integration
class BaseTestABCITendermintIntegration(BaseThreadedAsyncLoop, UseTendermint, ABC):
    """
    Integration test between ABCI connection and Tendermint node.

    To use this class:

    - inherit from this class, and write test methods;
    - overwrite the method "make_app". The app must implement a 'handle(message)' method.
    """

    TARGET_SKILL_ID = "dummy_author/dummy:0.1.0"
    ADDRESS = "agent_address"

    def setup(self):
        """Set up the test."""
        super().setup()
        self.agent_identity = Identity("name", address=self.ADDRESS)
        self.configuration = ConnectionConfig(
            connection_id=ABCIServerConnection.connection_id,
            host=DEFAULT_LISTEN_ADDRESS,
            port=DEFAULT_ABCI_PORT,
            target_skill_id=self.TARGET_SKILL_ID,
            use_tendermint=False,
        )
        self.connection = ABCIServerConnection(
            identity=self.agent_identity, configuration=self.configuration, data_dir=""
        )
        self.app = self.make_app()

        self.execute(self.connection.connect())

        self.stopped = False
        self.receiving_task: AnotherThreadTask = self.loop.call(
            self.process_incoming_messages()
        )

        # wait until tendermint node synchronized with abci
        wait_for_condition(self.health_check, period=0.5, timeout=1000000)

    @abstractmethod
    def make_app(self) -> Any:
        """Make an ABCI app."""
        raise NotImplementedError

    def health_check(self):
        """Do a health-check."""
        try:
            result = requests.get(self.tendermint_url() + "/health").status_code == 200
        except requests.exceptions.ConnectionError:
            result = False
        logging.debug(f"Health-check result: {result}")
        return result

    def tendermint_url(self) -> str:
        """Get the current Tendermint URL."""
        return f"{HTTP_LOCALHOST}:{self.tendermint_port}"

    def teardown(self):
        """Tear down the test."""
        self.stopped = True
        self.receiving_task.cancel()
        self.execute(self.connection.disconnect())
        super().teardown()

    async def process_incoming_messages(self):
        """Receive requests and send responses from/to the Tendermint node"""
        while not self.stopped:
            try:
                request_envelope = await self.connection.receive()
            except asyncio.CancelledError:
                break
            request_type = request_envelope.message.performative.value
            logging.debug(f"Received request {request_type}")
            response = self.app.handle(cast(AbciMessage, request_envelope.message))
            if response is not None:
                response_envelope = Envelope(
                    to=request_envelope.sender,
                    sender=request_envelope.to,
                    message=response,
                )
                await self.connection.send(response_envelope)
            else:
                logging.warning(f"Response to {request_type} was None.")


class TestNoop(BaseABCITest, BaseTestABCITendermintIntegration):
    """Test integration between ABCI connection and Tendermint, without txs."""

    SECONDS = 5

    def test_run(self):
        """
        Run the test.

        Sleep for N seconds, check Tendermint is still running, and then stop the test.
        """
        time.sleep(self.SECONDS)
        assert self.health_check()


class TestQuery(BaseABCITest, BaseTestABCITendermintIntegration):
    """Test integration ABCI-Tendermint with a query."""

    def test_run(self):
        """
        Run the test.

        Send a query request to the Tendermint node, which will trigger
        a query request to the ABCI connection.
        """
        logging.debug("Send request")
        response = requests.get(self.tendermint_url() + "/abci_query")
        assert response.status_code == 200


class TestTransaction(BaseABCITest, BaseTestABCITendermintIntegration):
    """Test integration ABCI-Tendermint by sending a transaction."""

    def test_run(self):
        """
        Run the test.

        Send a query request to the Tendermint node, which will trigger
        a query request to the ABCI connection.
        """
        logging.debug("Send request")
        response = requests.get(
            self.tendermint_url() + "/broadcast_tx_commit", params=dict(tx="0x01")
        )
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_connection_standalone_tendermint_setup():
    """Test the setup of the connection configured with Tendermint."""
    agent_identity = Identity("name", address="agent_address")
    configuration = ConnectionConfig(
        connection_id=ABCIServerConnection.connection_id,
        host=DEFAULT_LISTEN_ADDRESS,
        port=DEFAULT_ABCI_PORT,
        target_skill_id="dummy_author/dummy:0.1.0",
        use_tendermint=True,
        rpc_laddr="0.0.0.0:26657",
        p2p_laddr="0.0.0.0:26656",
        p2p_seeds=[],
    )
    connection = ABCIServerConnection(
        identity=agent_identity, configuration=configuration, data_dir=""
    )

    await connection.connect()
    await asyncio.sleep(2.0)
    await connection.disconnect()
