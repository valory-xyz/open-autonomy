# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023-2024 Valory AG
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
from typing import List, Optional, cast

from aea.configurations.data_types import PackageId, PackageType
from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport
from typing_extensions import TypedDict

from autonomy.chain.subgraph.queries import (
    FIND_BY_PACKAGE_HASH,
    FIND_BY_PUBLIC_ID,
    FIND_BY_TOKEN_ID,
)


SUBGRAPH_URL = os.environ.get(
    "OPEN_AUTONOMY_SUBGRAPH_URL",
    "https://subgraph.autonolas.tech/subgraphs/name/autonolas",
)


class Unit(TypedDict):
    """Unit container."""

    tokenId: str
    packageHash: str
    publicId: str


class UnitContainer(TypedDict):
    """Unit container"""

    units: List[Unit]


class SubgraphClient:
    """Subgraph helper class."""

    client: Client

    def __init__(self, url: Optional[str] = None) -> None:
        """Initialize object"""

        self._url = url or SUBGRAPH_URL
        self._transport = RequestsHTTPTransport(
            url=self._url,
        )
        self.client = Client(
            transport=self._transport,
            fetch_schema_from_transport=True,
        )

    def _query(self, query: str) -> UnitContainer:
        """Perform a query"""
        return cast(UnitContainer, self.client.execute(gql(request_string=query)))

    def get_component_by_token(
        self, token_id: int, package_type: PackageType
    ) -> UnitContainer:
        """Get component by package hash"""
        return self._query(
            FIND_BY_TOKEN_ID.format(
                token_id=token_id,
                package_type=package_type.value,
            )
        )

    def get_record_by_package_hash(self, package_hash: str) -> UnitContainer:
        """Get component by package hash"""
        return self._query(
            FIND_BY_PACKAGE_HASH.format(
                package_hash=package_hash,
            )
        )

    def get_record_by_package_id(self, package_id: PackageId) -> UnitContainer:
        """Get component by package hash"""
        public_id = f"{package_id.author}/{package_id.name}"
        return self._query(
            FIND_BY_PUBLIC_ID.format(
                public_id=public_id,
                package_type=package_id.package_type.value,
            )
        )
