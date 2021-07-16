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
"""Connection to interact with an ABCI server."""
from typing import Any, Optional, cast

from aea.configurations.base import PublicId
from aea.connections.base import Connection
from aea.mail.base import Envelope


CONNECTION_ID = PublicId.from_str("valory/abci:0.1.0")


class ABCIConnection(Connection):
    """AEA Connection to interact with an ABCI server."""

    connection_id = CONNECTION_ID

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize the connection.

        :param kwargs: keyword arguments passed to component base
        """
        super().__init__(**kwargs)  # pragma: no cover
        host = cast(str, self.configuration.config.get("host"))
        port = cast(int, self.configuration.config.get("port"))
        if host is None or port is None:  # pragma: nocover
            raise ValueError("host and port must be set!")

    async def connect(self) -> None:
        """
        Set up the connection.

        In the implementation, remember to update 'connection_status' accordingly.
        """
        raise NotImplementedError  # pragma: no cover

    async def disconnect(self) -> None:
        """
        Tear down the connection.

        In the implementation, remember to update 'connection_status' accordingly.
        """
        raise NotImplementedError  # pragma: no cover

    async def send(self, envelope: Envelope) -> None:
        """
        Send an envelope.

        :param envelope: the envelope to send.
        """
        raise NotImplementedError  # pragma: no cover

    async def receive(self, *args: Any, **kwargs: Any) -> Optional[Envelope]:
        """
        Receive an envelope. Blocking.

        :param args: arguments to receive
        :param kwargs: keyword arguments to receive
        :return: the envelope received, if present.  # noqa: DAR202
        """
        raise NotImplementedError  # pragma: no cover
