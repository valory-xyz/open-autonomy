# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023 Valory AG
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

"""Subgraph client."""

from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport

from autonomy.chain.subgraph.queries import FIND_BY_PACKAGE_HASH, FIND_BY_PUBLIC_ID


SUBGRAPH_LOCAL = "http://localhost:8000"
SUBGRAPH_NAME = "autonolas"


class ComponentTypes:
    """Component types."""

    COMPONENT = "COMPONENT"
    AGENT = "AGENT"
    SERVICE = "SERVICE"


class SubgraphClient:
    """Subgraph helper class."""

    def __init__(
        self,
        name: str = SUBGRAPH_NAME,
        url: str = SUBGRAPH_LOCAL,
    ) -> None:
        """Initialize object"""

        self._url = f"{url}/subgraphs/name/{name}"
        self._transport = AIOHTTPTransport(
            url=self._url,
        )
        self.client = Client(
            transport=self._transport,
            fetch_schema_from_transport=True,
        )

    def getRecordByPackageHash(self, package_hash: str) -> None:
        """Get component by package hash"""
        query_str = FIND_BY_PACKAGE_HASH.format(
            package_hash=package_hash,
        )
        query = gql(query_str)
        return self.client.execute(query)

    def getRecordByPublicId(self, public_id: str) -> None:
        """Get component by package hash"""
        query_str = FIND_BY_PUBLIC_ID.format(
            public_id=public_id,
        )
        query = gql(query_str)
        return self.client.execute(query)
