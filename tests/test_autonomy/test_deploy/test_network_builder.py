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

"""Tests for network builder."""

import ipaddress
from typing import Any, cast
from unittest import mock

from aea_test_autonomy.docker.base import skip_docker_tests
from docker.client import NetworkCollection

from autonomy.deploy.generators.docker_compose.base import Network


BASE_SUBNET = cast(
    ipaddress.IPv4Network,
    ipaddress.ip_network("192.168.21.0/24"),
)


@skip_docker_tests
class TestNetworkBuilder:
    """Test `NetworkBuilder`"""

    @staticmethod
    def patch_docker() -> Any:
        """Patch docker"""
        return

    def test_base(self) -> None:
        """Test initialization."""
        network = Network(
            name="test_network",
            base=BASE_SUBNET,
        )

        assert network.build() == BASE_SUBNET
        assert network.next_address == str(BASE_SUBNET.network_address + 2)

    def test_next_subnet(self) -> None:
        """Test next available subnet."""

        with mock.patch.object(
            NetworkCollection,
            "list",
            return_value=[
                mock.MagicMock(
                    attrs={
                        "Name": "test_network_1",
                        "IPAM": {"Config": [{"Subnet": str(BASE_SUBNET)}]},
                    }
                ),
            ],
        ):
            network = Network(
                name="test_network",
                base=BASE_SUBNET,
            )
            assert network.subnet == Network.next_subnet(subnet=BASE_SUBNET)

    def test_subnet_exists(self) -> None:
        """Test next available subnet."""
        network = Network(
            name="test_network",
            base=BASE_SUBNET,
        )
        with mock.patch.object(
            NetworkCollection,
            "list",
            return_value=[
                mock.MagicMock(
                    attrs={
                        "Name": "abci_build_test_network",
                        "IPAM": {
                            "Config": [
                                {"Subnet": str(Network.next_subnet(subnet=BASE_SUBNET))}
                            ]
                        },
                    }
                ),
            ],
        ):
            assert network.build() == Network.next_subnet(subnet=BASE_SUBNET)
