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

"""This module contains helper classes/functions for fixtures."""
import logging
from typing import Any, Dict, List, Tuple, cast

import docker
import pytest
from eth_account import Account

from tests.conftest import GANACHE_CONFIGURATION
from tests.helpers.constants import KEY_PAIRS, LOCALHOST
from tests.helpers.docker.base import DockerBaseTest, DockerImage
from tests.helpers.docker.ganache import (
    DEFAULT_GANACHE_ADDR,
    DEFAULT_GANACHE_PORT,
    GanacheDockerImage,
)
from tests.helpers.docker.gnosis_safe_net import (
    DEFAULT_HARDHAT_ADDR,
    DEFAULT_HARDHAT_PORT,
    GnosisSafeNetDockerImage,
)


logger = logging.getLogger(__name__)


@pytest.mark.integration
class UseTendermint:
    """Inherit from this class to use Tendermint."""

    @pytest.fixture(autouse=True)
    def _start_tendermint(self, tendermint: Any, tendermint_port: Any) -> None:
        """Start a Tendermint image."""
        self.tendermint_port = tendermint_port

    @property
    def node_address(self) -> str:
        """Get the node address."""
        return f"http://{LOCALHOST}:{self.tendermint_port}"


@pytest.mark.integration
class UseGnosisSafeHardHatNet:
    """Inherit from this class to use HardHat local net with Gnosis-Safe deployed."""

    key_pairs: List[Tuple[str, str]] = []

    @classmethod
    @pytest.fixture(autouse=True)
    def _start_hardhat(
        cls, gnosis_safe_hardhat: Any, hardhat_port: Any, key_pairs: Any
    ) -> None:
        """Start an HardHat instance."""
        cls.key_pairs = key_pairs


@pytest.mark.integration
class UseGanache:
    """Inherit from this class to use Ganache."""

    key_pairs: List[Tuple[str, str]] = []

    @classmethod
    @pytest.fixture(autouse=True)
    def _start_ganache(cls, ganache: Any, ganache_configuration: Any) -> None:
        """Start Ganache instance."""
        cls.key_pairs = cast(
            List[Tuple[str, str]],
            [
                key if type(key) == tuple else (Account.from_key(key).address, key)
                for key, _ in ganache_configuration.get("accounts_balances", [])
            ],
        )


class GanacheBaseTest(DockerBaseTest):
    """Base pytest class for Ganache."""

    addr: str = DEFAULT_GANACHE_ADDR
    port: int = DEFAULT_GANACHE_PORT
    configuration: Dict = GANACHE_CONFIGURATION

    @classmethod
    def setup_class_kwargs(cls) -> Dict[str, Any]:
        """Get kwargs for _setup_class call."""
        setup_class_kwargs = {
            "key_pairs": cls.key_pairs(),
            "url": cls.url(),
        }
        return setup_class_kwargs

    @classmethod
    def _build_image(cls) -> DockerImage:
        """Build the image."""
        client = docker.from_env()
        return GanacheDockerImage(client, cls.addr, cls.port, config=cls.configuration)

    @classmethod
    def key_pairs(cls) -> List[Tuple[str, str]]:
        """Get the key pairs which are funded."""
        key_pairs = cast(
            List[Tuple[str, str]],
            [
                key if type(key) == tuple else (Account.from_key(key).address, key)
                for key, _ in cls.configuration.get("accounts_balances", [])
            ],
        )
        return key_pairs

    @classmethod
    def url(cls) -> str:
        """Get the url under which the image is reachable."""
        return f"{cls.addr}:{cls.port}"


class HardHatBaseTest(DockerBaseTest):
    """Base pytest class for HardHat."""

    addr: str = DEFAULT_HARDHAT_ADDR
    port: int = DEFAULT_HARDHAT_PORT

    @classmethod
    def setup_class_kwargs(cls) -> Dict[str, Any]:
        """Get kwargs for _setup_class call."""
        setup_class_kwargs = {
            "key_pairs": cls.key_pairs(),
            "url": cls.url(),
        }
        return setup_class_kwargs

    @classmethod
    def _build_image(cls) -> DockerImage:
        """Build the image."""
        client = docker.from_env()
        return GnosisSafeNetDockerImage(client, cls.addr, cls.port)

    @classmethod
    def key_pairs(cls) -> List[Tuple[str, str]]:
        """Get the key pairs which are funded."""
        return KEY_PAIRS

    @classmethod
    def url(cls) -> str:
        """Get the url under which the image is reachable."""
        return f"{cls.addr}:{cls.port}"
