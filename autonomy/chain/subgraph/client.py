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

import os
from typing import Dict, List, Union, cast

from aea.configurations.data_types import PackageId
from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport

from autonomy.chain.subgraph.queries import FIND_BY_PACKAGE_HASH, FIND_BY_PUBLIC_ID


SUBGRAPH_URL = os.environ.get("OPEN_AUTONOMY_SUBGRAPH_URL", "http://localhost:8000")
SUBGRAPH_NAME = os.environ.get("OPEN_AUTONOMY_SUBGRAPH_NAME", "autonolas")

Unit = Dict[str, Union[int, str]]
UnitContainer = Dict[str, List[Unit]]


class SubgraphClient:
    """Subgraph helper class."""

    client: Client

    def __init__(
        self,
        name: str = SUBGRAPH_NAME,
        url: str = SUBGRAPH_URL,
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

    def getRecordByPackageHash(self, package_hash: str) -> UnitContainer:
        """Get component by package hash"""
        query_str = FIND_BY_PACKAGE_HASH.format(package_hash=package_hash)
        query = gql(query_str)
        return cast(UnitContainer, self.client.execute(query))

    def getRecordByPackageId(self, package_id: PackageId) -> UnitContainer:
        """Get component by package hash"""
        public_id = f"{package_id.author}/{package_id.name}"
        query_str = FIND_BY_PUBLIC_ID.format(
            public_id=public_id,
            package_type=package_id.package_type.value.upper(),
        )
        query = gql(query_str)
        return cast(UnitContainer, self.client.execute(query))
