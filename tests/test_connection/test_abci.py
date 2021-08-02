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
import logging
from typing import Callable, cast

import pytest
from aea.configurations.base import ConnectionConfig
from aea.identity.base import Identity
from aea.mail.base import Envelope

from packages.valory.connections.abci.connection import (
    ABCIServerConnection,
    DEFAULT_ABCI_PORT,
    DEFAULT_LISTEN_ADDRESS,
)
from packages.valory.protocols.abci import AbciMessage
from packages.valory.protocols.abci.custom_types import Events, ValidatorUpdates


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
            data=b"data",
            retain_height=0,
        )

    def no_match(self, request: AbciMessage):
        """No match."""
        raise Exception(
            f"Received request with performative {request.performative.value}, but no handler available"
        )


@pytest.mark.asyncio
async def test_run(tendermint):
    """Test execution of ABCI connection."""
    agent_identity = Identity("name", address="some string")
    configuration = ConnectionConfig(
        host=DEFAULT_LISTEN_ADDRESS,
        port=DEFAULT_ABCI_PORT,
        connection_id=ABCIServerConnection.connection_id,
    )
    connection = ABCIServerConnection(
        identity=agent_identity, configuration=configuration, data_dir=""
    )
    app = ABCIAppTest()

    await connection.connect()

    # process N messages
    nb_messages = 100
    for _ in range(nb_messages):
        request_envelope = await connection.receive()
        request_type = request_envelope.message.performative.value
        response = app.process(cast(AbciMessage, request_envelope.message))
        if response is not None:
            response_envelope = Envelope(
                to=request_envelope.sender, sender=request_envelope.to, message=response
            )
            await connection.send(response_envelope)
        else:
            logging.warning(f"Response to {request_type} was None.")

    await connection.disconnect()
