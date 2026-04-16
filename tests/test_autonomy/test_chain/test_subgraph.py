# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2024 Valory AG
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

"""Tests for the subgraph client."""

from unittest import mock

from aea.configurations.data_types import PackageId, PackageType

from autonomy.chain.subgraph.client import SubgraphClient


class TestClient:
    """Test subgraph client"""

    client = SubgraphClient()

    def test_get_component_by_token(self) -> None:
        """Test get component by token query."""
        with mock.patch.object(SubgraphClient, "_query") as query:
            self.client.get_component_by_token(
                token_id=1,
                package_type=PackageType.PROTOCOL,
            )
            query.assert_called_once_with(
                '\nquery getUnit {\n  units(where:{tokenId: "1",'
                "packageType:protocol}){\n    tokenId\n    packageHash\n"
                "    publicId\n  }\n}\n"
            )

    def test_get_record_by_package_hash(self) -> None:
        """Test get record by package hash query."""
        with mock.patch.object(SubgraphClient, "_query") as query:
            self.client.get_record_by_package_hash(package_hash="bayfei")
            query.assert_called_once_with(
                '\nquery getUnit {\n  units(where:{packageHash:"bayfei"})'
                "{\n    tokenId\n    packageHash\n    publicId\n  }\n}\n"
            )

    def test_get_record_by_package_id(self) -> None:
        """Test get record by package hash query."""
        with mock.patch.object(SubgraphClient, "_query") as query:
            self.client.get_record_by_package_id(
                package_id=PackageId.from_uri_path("skill/valory/abci/0.1.0")
            )
            query.assert_called_once_with(
                '\nquery getUnit {\n  units(where:{publicId: "valory/abci"'
                ",packageType:skill}){\n    tokenId\n    packageHash\n    "
                "publicId\n  }\n}\n"
            )
