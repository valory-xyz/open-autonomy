# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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
from tests.helpers.docker.acn_node import ACNNodeDockerImage, DEFAULT_ACN_CONFIG
from tests.helpers.docker.amm_net import AMMNetDockerImage
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
from tests.helpers.docker.tendermint import (
    FlaskTendermintDockerImage,
    TendermintDockerImage,
)


logger = logging.getLogger(__name__)


@pytest.mark.integration
class UseTendermint:
    """Inherit from this class to use Tendermint."""

    _tendermint_image: TendermintDockerImage
    tendermint_port: int

    @pytest.fixture(autouse=True, scope="class")
    def _start_tendermint(
        self, tendermint: TendermintDockerImage, tendermint_port: Any
    ) -> None:
        """Start a Tendermint image."""
        cls = type(self)
        cls._tendermint_image = tendermint
        cls.tendermint_port = tendermint_port

    @property
    def abci_host(self) -> str:
        """Get the abci host address."""
        return self._tendermint_image.abci_host

    @property
    def abci_port(self) -> int:
        """Get the abci port."""
        return self._tendermint_image.abci_port

    @property
    def node_address(self) -> str:
        """Get the node address."""
        return f"http://{LOCALHOST}:{self.tendermint_port}"


@pytest.mark.integration
class UseFlaskTendermintNode:
    """Inherit from this class to use flask server with Tendermint."""

    @pytest.fixture(autouse=True)
    def _start_tendermint(
        self, flask_tendermint: FlaskTendermintDockerImage, tendermint_port: Any
    ) -> None:
        """Start a Tendermint image."""
        self._tendermint_image = flask_tendermint
        self.tendermint_port = tendermint_port

    @property
    def p2p_seeds(self) -> List[str]:
        """Get the p2p seeds."""
        return self._tendermint_image.p2p_seeds

    def get_node_name(self, i: int) -> str:
        """Get the node's name."""
        return self._tendermint_image.get_node_name(i)

    def get_abci_port(self, i: int) -> int:
        """Get the ith rpc port."""
        return self._tendermint_image.get_abci_port(i)

    def get_port(self, i: int) -> int:
        """Get the ith port."""
        return self._tendermint_image.get_port(i)

    def get_com_port(self, i: int) -> int:
        """Get the ith com port."""
        return self._tendermint_image.get_com_port(i)

    def get_laddr(self, i: int, p2p: bool = False) -> str:
        """Get the ith rpc port."""
        return self._tendermint_image.get_addr("tcp://", i, p2p)

    def health_check(self, **kwargs: Any) -> None:
        """Perform a health check."""
        self._tendermint_image.health_check(**kwargs)


@pytest.mark.integration
class UseGnosisSafeHardHatNet:
    """Inherit from this class to use HardHat local net with Gnosis-Safe deployed."""

    key_pairs: List[Tuple[str, str]] = KEY_PAIRS

    @classmethod
    @pytest.fixture(autouse=True)
    def _start_hardhat(
        cls, gnosis_safe_hardhat_scope_function: Any, hardhat_port: Any, key_pairs: Any
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


@pytest.mark.integration
class UseACNNode:
    """Inherit from this class to use an ACNNode for a client connection"""

    configuration: Dict = DEFAULT_ACN_CONFIG
    _acn_node_image: ACNNodeDockerImage

    @classmethod
    @pytest.fixture(autouse=True)
    def _start_acn(cls, acn_node: Any, acn_config: Any = None) -> None:
        """Start an ACN instance."""
        cls._acn_node_image = acn_node
        cls.configuration = acn_config or cls.configuration


class ACNNodeBaseTest(DockerBaseTest):
    """Base pytest class for Ganache."""

    configuration: Dict = DEFAULT_ACN_CONFIG

    @classmethod
    def setup_class_kwargs(cls) -> Dict[str, Any]:
        """Get kwargs for _setup_class call."""
        setup_class_kwargs = {
            "config": cls.configuration,
        }
        return setup_class_kwargs

    @classmethod
    def _build_image(cls) -> DockerImage:
        """Build the image."""
        client = docker.from_env()
        return ACNNodeDockerImage(client, config=cls.configuration)

    @classmethod
    def url(cls) -> str:
        """Get the url under which the image is reachable."""
        return str(cls.configuration.get("AEA_P2P_URI_PUBLIC"))


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
    def key_pairs(cls) -> List[Tuple[str, str]]:
        """Get the key pairs which are funded."""
        return KEY_PAIRS

    @classmethod
    def url(cls) -> str:
        """Get the url under which the image is reachable."""
        return f"{cls.addr}:{cls.port}"


class HardHatGnosisBaseTest(HardHatBaseTest):
    """Base pytest class for HardHat with Gnosis deployed."""

    @classmethod
    def _build_image(cls) -> DockerImage:
        """Build the image."""
        client = docker.from_env()
        return GnosisSafeNetDockerImage(client, cls.addr, cls.port)


class HardHatAMMBaseTest(HardHatBaseTest):
    """Base pytest class for HardHat with Gnosis and Uniswap deployed."""

    @classmethod
    def _build_image(cls) -> DockerImage:
        """Build the image."""
        client = docker.from_env()
        return AMMNetDockerImage(client, cls.addr, cls.port)
