# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023-2026 Valory AG
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

import json
import os
from typing import List, Optional, TypedDict, cast

from aea.configurations.data_types import PackageId, PackageType
from aea.helpers.http_requests import post

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

    def __init__(self, url: Optional[str] = None) -> None:
        """Initialize object"""
        self._url = url or SUBGRAPH_URL

    def _query(self, query: str) -> UnitContainer:
        """Perform a query"""
        # Cloudflare fronts the default subgraph and 403s requests without
        # a User-Agent; urllib (used by aea.helpers.http_requests) sends
        # none by default, so set one explicitly.
        resp = post(
            self._url,
            data=json.dumps({"query": query}).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "User-Agent": "open-autonomy",
            },
        )
        if resp.status_code >= 400:
            raise RuntimeError(
                f"Subgraph HTTP {resp.status_code} from {self._url}: "
                f"{resp.text[:200]}"
            )
        payload = resp.json()
        if "errors" in payload:
            raise RuntimeError(f"Subgraph query failed: {payload['errors']}")
        return cast(UnitContainer, payload["data"])

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
