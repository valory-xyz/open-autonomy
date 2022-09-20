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

# needed because many test base classes do not have public methods
# pylint: disable=too-few-public-methods

# needed because many fixture auto-loaders of test classes do not use fixtures
# pylint: disable=unused-argument

import logging
from typing import Any, Dict, Generator, List, Tuple, cast

import docker
import pytest
from aea_test_autonomy.configurations import GANACHE_CONFIGURATION, KEY_PAIRS, LOCALHOST
from aea_test_autonomy.docker.acn_node import ACNNodeDockerImage, DEFAULT_ACN_CONFIG
from aea_test_autonomy.docker.amm_net import AMMNetDockerImage
from aea_test_autonomy.docker.base import (
    DockerBaseTest,
    DockerImage,
    launch_image,
    launch_many_containers,
)
from aea_test_autonomy.docker.ganache import (
    DEFAULT_GANACHE_ADDR,
    DEFAULT_GANACHE_PORT,
    GanacheDockerImage,
)
from aea_test_autonomy.docker.gnosis_safe_net import (
    DEFAULT_HARDHAT_ADDR,
    DEFAULT_HARDHAT_PORT,
    GnosisSafeNetDockerImage,
)
from aea_test_autonomy.docker.registries import RegistriesDockerImage
from aea_test_autonomy.docker.tendermint import (
    DEFAULT_ABCI_HOST,
    DEFAULT_ABCI_PORT,
    DEFAULT_TENDERMINT_PORT,
    FlaskTendermintDockerImage,
    TendermintDockerImage,
)
from eth_account import Account


logger = logging.getLogger(__name__)


###
# Vanilla Tendermint
###


@pytest.fixture(scope="session")
def tendermint_port() -> int:
    """Get the Tendermint port"""
    return DEFAULT_TENDERMINT_PORT


@pytest.fixture(scope="session")
def abci_host() -> str:
    """Get the ABCI host"""
    return DEFAULT_ABCI_HOST


@pytest.fixture(scope="session")
def abci_port() -> int:
    """Get the ABCI port"""
    return DEFAULT_ABCI_PORT


@pytest.fixture(scope="class")
def tendermint(
    tendermint_port: int,  # pylint: disable=redefined-outer-name
    abci_host: str,  # pylint: disable=redefined-outer-name
    abci_port: int,  # pylint: disable=redefined-outer-name
    timeout: float = 2.0,
    max_attempts: int = 10,
) -> Generator:
    """Launch the Ganache image."""
    client = docker.from_env()
    logging.info(f"Launching Tendermint at port {tendermint_port}")
    image = TendermintDockerImage(client, abci_host, abci_port, tendermint_port)
    yield from launch_image(image, timeout=timeout, max_attempts=max_attempts)


@pytest.mark.integration
class UseTendermint:
    """Inherit from this class to use Tendermint."""

    _tendermint_image: TendermintDockerImage
    tendermint_port: int

    @pytest.fixture(autouse=True, scope="class")
    def _start_tendermint(
        self,
        tendermint: TendermintDockerImage,  # pylint: disable=redefined-outer-name
        tendermint_port: int,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Start a Tendermint image."""
        cls = type(self)
        cls._tendermint_image = tendermint  # pylint: disable=protected-access
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


###
# Tendermint managed by Flask server
###


@pytest.fixture
def nb_nodes(request: Any) -> int:
    """Get a parametrized number of nodes."""
    return request.param


@pytest.fixture
def flask_tendermint(
    tendermint_port: int,  # pylint: disable=redefined-outer-name
    nb_nodes: int,  # pylint: disable=redefined-outer-name
    abci_host: str,  # pylint: disable=redefined-outer-name
    abci_port: int,  # pylint: disable=redefined-outer-name
    timeout: float = 2.0,
    max_attempts: int = 10,
) -> Generator[FlaskTendermintDockerImage, None, None]:
    """Launch the Flask server with Tendermint container."""
    client = docker.from_env()
    logging.info(
        f"Launching Tendermint nodes managed by Flask server at ports {[tendermint_port + i * 10 for i in range(nb_nodes)]}"
    )
    image = FlaskTendermintDockerImage(client, abci_host, abci_port, tendermint_port)
    yield from cast(
        Generator[FlaskTendermintDockerImage, None, None],
        launch_many_containers(image, nb_nodes, timeout, max_attempts),
    )


@pytest.mark.integration
class UseFlaskTendermintNode:
    """Inherit from this class to use flask server with Tendermint."""

    @pytest.fixture(autouse=True)
    def _start_tendermint(
        self,
        flask_tendermint: FlaskTendermintDockerImage,  # pylint: disable=redefined-outer-name
        tendermint_port: int,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Start a Tendermint image."""
        self._tendermint_image = (  # pylint: disable=attribute-defined-outside-init
            flask_tendermint
        )
        self.tendermint_port = (  # pylint: disable=attribute-defined-outside-init
            tendermint_port
        )

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


###
# Vanilla Ganache
###


@pytest.fixture(scope="session")
def ganache_addr() -> str:
    """HTTP address to the Ganache node."""
    return DEFAULT_GANACHE_ADDR


@pytest.fixture(scope="session")
def ganache_port() -> int:
    """Port of the connection to the Ganache Node to use during the tests."""
    return DEFAULT_GANACHE_PORT


@pytest.fixture(scope="session")
def ganache_configuration() -> Dict:
    """Get the Ganache configuration for testing purposes."""
    return GANACHE_CONFIGURATION


# TODO: remove as not used
@pytest.fixture(scope="function")
def ganache_scope_function(
    ganache_configuration: Dict,  # pylint: disable=redefined-outer-name
    ganache_addr: str,  # pylint: disable=redefined-outer-name
    ganache_port: int,  # pylint: disable=redefined-outer-name
    timeout: float = 2.0,
    max_attempts: int = 10,
) -> Generator:
    """Launch the Ganache image. This fixture is scoped to a function which means it will destroyed at the end of the test."""
    client = docker.from_env()
    image = GanacheDockerImage(
        client, ganache_addr, ganache_port, config=ganache_configuration
    )
    yield from launch_image(image, timeout=timeout, max_attempts=max_attempts)


@pytest.fixture(scope="class")
def ganache_scope_class(
    ganache_configuration: Dict,  # pylint: disable=redefined-outer-name
    ganache_addr: str,  # pylint: disable=redefined-outer-name
    ganache_port: int,  # pylint: disable=redefined-outer-name
    timeout: float = 2.0,
    max_attempts: int = 10,
) -> Generator:
    """Launch the Ganache image. This fixture is scoped to a class which means it will destroyed after running every test in a class."""
    client = docker.from_env()
    image = GanacheDockerImage(
        client, ganache_addr, ganache_port, config=ganache_configuration
    )
    yield from launch_image(image, timeout=timeout, max_attempts=max_attempts)


@pytest.mark.integration
class UseGanache:
    """Inherit from this class to use Ganache."""

    key_pairs: List[Tuple[str, str]] = []

    @classmethod
    @pytest.fixture(autouse=True, scope="class")
    def _start_ganache(
        cls,
        ganache_scope_class: GanacheDockerImage,  # pylint: disable=redefined-outer-name
        ganache_configuration: Dict,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Start Ganache instance."""
        cls.key_pairs = cast(
            List[Tuple[str, str]],
            [
                key
                if type(key) == tuple  # pylint: disable=unidiomatic-typecheck
                else (
                    Account.from_key(  # pylint: disable=no-value-for-parameter
                        key
                    ).address,
                    key,
                )
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
        key_pairs_ = cast(
            List[Tuple[str, str]],
            [
                key
                if type(key) == tuple  # pylint: disable=unidiomatic-typecheck
                else (
                    Account.from_key(  # pylint: disable=no-value-for-parameter
                        key
                    ).address,
                    key,
                )
                for key, _ in cls.configuration.get("accounts_balances", [])
            ],
        )
        return key_pairs_

    @classmethod
    def url(cls) -> str:
        """Get the url under which the image is reachable."""
        return f"{cls.addr}:{cls.port}"


###
# Vanilla ACN
###


@pytest.fixture(scope="session")
def acn_config() -> Dict:
    """ACN node configuration."""
    return DEFAULT_ACN_CONFIG


@pytest.fixture(scope="function")
def acn_node(
    acn_config: Dict,  # pylint: disable=redefined-outer-name
    timeout: float = 2.0,
    max_attempts: int = 10,
) -> Generator:
    """Launch the Ganache image."""
    client = docker.from_env()
    logging.info(f"Launching ACNNode with the following config: {acn_config}")
    image = ACNNodeDockerImage(client, acn_config)
    yield from launch_image(image, timeout=timeout, max_attempts=max_attempts)


@pytest.mark.integration
class UseACNNode:
    """Inherit from this class to use an ACNNode for a client connection"""

    _acn_node_image: ACNNodeDockerImage

    @classmethod
    @pytest.fixture(autouse=True)
    def _start_acn(
        cls,
        acn_node: ACNNodeDockerImage,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Start an ACN instance."""
        cls._acn_node_image = acn_node


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


###
# Vanilla HardHat
###


@pytest.fixture(scope="session")
def hardhat_addr() -> str:
    """Get the hardhat addr"""
    return DEFAULT_HARDHAT_ADDR


@pytest.fixture(scope="session")
def hardhat_port() -> int:
    """Get the hardhat port"""
    return DEFAULT_HARDHAT_PORT


@pytest.fixture(scope="session")
def key_pairs() -> List[Tuple[str, str]]:
    """Get the default key paris for hardhat."""
    return KEY_PAIRS


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


###
# Custom HardHat: HardHat + Autonolas Registry
###


@pytest.fixture(scope="class")
def registries_scope_class(
    timeout: float = 2.0,
    max_attempts: int = 20,
) -> Generator:
    """Launch the Registry contracts image. This fixture is scoped to a class which means it will destroyed after running every test in a class."""
    client = docker.from_env()
    image = RegistriesDockerImage(client)
    yield from launch_image(image, timeout=timeout, max_attempts=max_attempts)


@pytest.mark.integration
class UseRegistries:
    """Inherit from this class to use a local Ethereum network with deployed registry contracts"""

    key_pairs: List[Tuple[str, str]] = KEY_PAIRS

    @classmethod
    @pytest.fixture(autouse=True)
    def _start_gnosis_and_registries(
        cls,
        registries_scope_class: Any,  # pylint: disable=redefined-outer-name
        hardhat_port: int,  # pylint: disable=redefined-outer-name
        key_pairs: List[Tuple[str, str]],  # pylint: disable=redefined-outer-name
    ) -> None:
        """Start a Hardhat instance, with registries contracts deployed."""
        cls.key_pairs = key_pairs


###
# Custom HardHat: HardHat + Gnosis Safe contracts
###


@pytest.fixture(scope="function")
def gnosis_safe_hardhat_scope_function(
    hardhat_addr: str,  # pylint: disable=redefined-outer-name
    hardhat_port: int,  # pylint: disable=redefined-outer-name
    timeout: float = 3.0,
    max_attempts: int = 40,
) -> Generator:
    """Launch the HardHat node with Gnosis Safe contracts deployed. This fixture is scoped to a function which means it will destroyed at the end of the test."""
    client = docker.from_env()
    logging.info(f"Launching Hardhat at port {hardhat_port}")
    image = GnosisSafeNetDockerImage(client, hardhat_addr, hardhat_port)
    yield from launch_image(image, timeout=timeout, max_attempts=max_attempts)


@pytest.fixture(scope="class")
def gnosis_safe_hardhat_scope_class(
    hardhat_addr: str,  # pylint: disable=redefined-outer-name
    hardhat_port: int,  # pylint: disable=redefined-outer-name
    timeout: float = 3.0,
    max_attempts: int = 40,
) -> Generator:
    """Launch the HardHat node with Gnosis Safe contracts deployed.This fixture is scoped to a class which means it will destroyed after running every test in a class."""
    client = docker.from_env()
    logging.info(f"Launching Hardhat at port {hardhat_port}")
    image = GnosisSafeNetDockerImage(client, hardhat_addr, hardhat_port)
    yield from launch_image(image, timeout=timeout, max_attempts=max_attempts)


@pytest.mark.integration
class UseGnosisSafeHardHatNet:
    """Inherit from this class to use HardHat local net with Gnosis-Safe deployed."""

    key_pairs: List[Tuple[str, str]] = KEY_PAIRS

    @classmethod
    @pytest.fixture(autouse=True)
    def _start_hardhat(
        cls,
        gnosis_safe_hardhat_scope_function: Any,  # pylint: disable=redefined-outer-name
        hardhat_port: int,  # pylint: disable=redefined-outer-name
        key_pairs: List[Tuple[str, str]],  # pylint: disable=redefined-outer-name
    ) -> None:
        """Start an HardHat instance."""
        cls.key_pairs = key_pairs


class HardHatGnosisBaseTest(HardHatBaseTest):
    """Base pytest class for HardHat with Gnosis deployed."""

    @classmethod
    def _build_image(cls) -> DockerImage:
        """Build the image."""
        client = docker.from_env()
        return GnosisSafeNetDockerImage(client, cls.addr, cls.port)


###
# Custom HardHat: HardHat + AMM contracts
###


class HardHatAMMBaseTest(HardHatBaseTest):
    """Base pytest class for HardHat with Gnosis and Uniswap deployed."""

    @classmethod
    def _build_image(cls) -> DockerImage:
        """Build the image."""
        client = docker.from_env()
        return AMMNetDockerImage(client, cls.addr, cls.port)
