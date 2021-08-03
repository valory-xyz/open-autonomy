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
from typing import Callable, cast

import requests
from aea.configurations.base import ConnectionConfig
from aea.identity.base import Identity
from aea.mail.base import Envelope

from packages.valory.connections.abci.connection import (
    ABCIServerConnection,
    DEFAULT_ABCI_PORT,
    DEFAULT_LISTEN_ADDRESS,
)
from packages.valory.protocols.abci import AbciMessage
from packages.valory.protocols.abci.custom_types import (
    Events,
    ProofOps,
    ValidatorUpdates,
)

from tests.conftest import HTTP_LOCALHOST, UseTendermint
from tests.helpers.async_utils import (
    AnotherThreadTask,
    BaseThreadedAsyncLoop,
    wait_for_condition,
)


class ABCIAppTest:
    """A dummy ABCI application for testing purposes."""

    def process(self, request: AbciMessage) -> AbciMessage:
        """Process a request."""
        # check that it is not a response
        assert "request" in request.performative.value, "performative is not a Request"
        # performative of requests is of the form "request_{request_name}"
        request_type = request.performative.value.replace("request_", "")
        handler: Callable[[AbciMessage], AbciMessage] = getattr(
            self, request_type, self.no_match
        )
        return handler(request)

    def info(self, request: AbciMessage) -> AbciMessage:
        """Process an info request."""
        assert request.performative == AbciMessage.Performative.REQUEST_INFO
        info_data = ""
        version = request.version
        app_version = 0
        last_block_height = 0
        last_block_app_hash = b""
        return AbciMessage(
            performative=AbciMessage.Performative.RESPONSE_INFO,
            info_data=info_data,
            version=version,
            app_version=app_version,
            last_block_height=last_block_height,
            last_block_app_hash=last_block_app_hash,
        )

    def flush(self, _request: AbciMessage):
        """Process a flush request."""
        return AbciMessage(performative=AbciMessage.Performative.RESPONSE_FLUSH)

    def init_chain(self, _request: AbciMessage):
        """Process an init_chain request."""
        validators = []
        app_hash = b""
        return AbciMessage(
            performative=AbciMessage.Performative.RESPONSE_INIT_CHAIN,
            validators=ValidatorUpdates(validators),
            app_hash=app_hash,
        )

    def query(self, _request: AbciMessage) -> AbciMessage:
        """Process a query request."""
        return AbciMessage(
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

    def check_tx(self, request: AbciMessage) -> AbciMessage:
        """Process a check_tx request."""
        return AbciMessage(
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

    def deliver_tx(self, request: AbciMessage) -> AbciMessage:
        """Process a deliver_tx request."""
        return AbciMessage(
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

    def begin_block(self, _request: AbciMessage):
        """Process a begin_block request."""
        return AbciMessage(
            performative=AbciMessage.Performative.RESPONSE_BEGIN_BLOCK,
            events=Events([]),
        )

    def end_block(self, _request: AbciMessage):
        """Process an end_block request."""
        return AbciMessage(
            performative=AbciMessage.Performative.RESPONSE_END_BLOCK,
            validator_updates=ValidatorUpdates([]),
            events=Events([]),
        )

    def commit(self, _request: AbciMessage):
        """Process a commit request."""
        return AbciMessage(
            performative=AbciMessage.Performative.RESPONSE_COMMIT,
            data=b"",
            retain_height=0,
        )

    def no_match(self, request: AbciMessage):
        """No match."""
        raise Exception(
            f"Received request with performative {request.performative.value}, but no handler available"
        )


class BaseTestABCIConnectionTendermintIntegration(BaseThreadedAsyncLoop, UseTendermint):
    """Integration test between ABCI connection and Tendermint node."""

    def setup(self):
        """Set up the test."""
        super().setup()
        self.agent_identity = Identity("name", address="some string")
        self.configuration = ConnectionConfig(
            host=DEFAULT_LISTEN_ADDRESS,
            port=DEFAULT_ABCI_PORT,
            connection_id=ABCIServerConnection.connection_id,
        )
        self.connection = ABCIServerConnection(
            identity=self.agent_identity, configuration=self.configuration, data_dir=""
        )
        self.app = ABCIAppTest()

        self.execute(self.connection.connect())

        self.stopped = False
        self.receiving_task: AnotherThreadTask = self.loop.call(
            self.process_incoming_messages()
        )

        # wait until tendermint node synchronized with abci
        wait_for_condition(self.health_check, period=0.5)

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
            response = self.app.process(cast(AbciMessage, request_envelope.message))
            if response is not None:
                response_envelope = Envelope(
                    to=request_envelope.sender,
                    sender=request_envelope.to,
                    message=response,
                )
                await self.connection.send(response_envelope)
            else:
                logging.warning(f"Response to {request_type} was None.")


class TestNoop(BaseTestABCIConnectionTendermintIntegration):
    """Test integration between ABCI connection and Tendermint, without txs."""

    SECONDS = 5

    def test_run(self):
        """
        Run the test.

        Sleep for N seconds, check Tendermint is still running, and then stop the test.
        """
        time.sleep(self.SECONDS)
        assert self.health_check()


class TestQuery(BaseTestABCIConnectionTendermintIntegration):
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


class TestTransaction(BaseTestABCIConnectionTendermintIntegration):
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
