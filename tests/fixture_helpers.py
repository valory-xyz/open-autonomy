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
import secrets
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, cast

import docker
import pytest
from docker.models.containers import Container
from eth_account import Account
from web3 import Web3

from tests.conftest import (
    DEFAULT_AMOUNT,
    ETHEREUM_KEY_DEPLOYER,
    ETHEREUM_KEY_PATH_1,
    ETHEREUM_KEY_PATH_2,
    ETHEREUM_KEY_PATH_3,
    ETHEREUM_KEY_PATH_4,
    get_key,
)
from tests.helpers.constants import KEY_PAIRS
from tests.helpers.docker.base import DockerImage
from tests.helpers.docker.ganache import (
    DEFAULT_GANACHE_ADDR,
    DEFAULT_GANACHE_PORT,
    GanacheDockerImage,
)


logger = logging.getLogger(__name__)


@pytest.mark.integration
class UseTendermint:
    """Inherit from this class to use Tendermint."""

    @pytest.fixture(autouse=True)
    def _start_tendermint(self, tendermint, tendermint_port):
        """Start a Tendermint image."""
        self.tendermint_port = tendermint_port


@pytest.mark.integration
class UseGnosisSafeHardHatNet:
    """Inherit from this class to use HardHat local net with Gnosis-Safe deployed."""

    NB_OWNERS: int = 4
    THRESHOLD: int = 1
    SALT_NONCE: Optional[int] = None

    hardhat_port: int
    hardhat_key_pairs: List[Tuple[str, str]]
    proxy_contract_address: str

    @classmethod
    @pytest.fixture(autouse=True)
    def _start_hardhat(cls, gnosis_safe_hardhat, hardhat_port, key_pairs) -> None:
        """Start an HardHat instance."""
        cls.hardhat_port = hardhat_port
        cls.hardhat_key_pairs = key_pairs

    @property
    def owner_key_pairs(self) -> List[Tuple[str, str]]:
        """Get the owners."""
        return self.hardhat_key_pairs[: self.NB_OWNERS]

    @property
    def owners(self) -> List[str]:
        """Get the owners."""
        return [Web3.toChecksumAddress(t[0]) for t in self.owner_key_pairs]

    @property
    def deployer(self) -> Tuple[str, str]:
        """Get the key pair of the deployer."""
        # for simplicity, get the first owner
        return self.owner_key_pairs[0]

    @property
    def threshold(
        self,
    ) -> int:
        """Returns the amount of threshold."""
        return self.THRESHOLD

    @property
    def get_nonce(self) -> int:
        """Get the nonce."""
        if self.SALT_NONCE is not None:
            return self.SALT_NONCE
        return secrets.SystemRandom().randint(0, 2 ** 256 - 1)


@pytest.mark.integration
class UseGanache:
    """Inherit from this class to use Ganache."""

    NB_OWNERS: int = 4
    THRESHOLD: int = 1
    SALT_NONCE: Optional[int] = None

    ganache_port: int = DEFAULT_GANACHE_PORT
    key_pairs: List[Tuple[str, str]] = KEY_PAIRS

    @classmethod
    @pytest.fixture(autouse=True)
    def _start_ganache(cls, ganache, ganache_configuration) -> None:
        """Start Ganache instance."""
        cls.key_pairs = cast(
            List[Tuple[str, str]],
            [
                key if type(key) == tuple else (Account.from_key(key).address, key)
                for key, _ in ganache_configuration.get("accounts_balances", [])
            ],
        )

    @property
    def owner_key_pairs(self) -> List[Tuple[str, str]]:
        """Get the owners."""
        return self.key_pairs[: self.NB_OWNERS]

    @property
    def owners(self) -> List[str]:
        """Get the owners."""
        return [Web3.toChecksumAddress(t[0]) for t in self.owner_key_pairs]

    @property
    def deployer(self) -> Tuple[str, str]:
        """Get the key pair of the deployer."""
        # for simplicity, get the first owner
        return self.owner_key_pairs[0]

    @property
    def threshold(
        self,
    ) -> int:
        """Returns the amount of threshold."""
        return self.THRESHOLD

    @property
    def get_nonce(self) -> int:
        """Get the nonce."""
        if self.SALT_NONCE is not None:
            return self.SALT_NONCE
        return secrets.SystemRandom().randint(0, 2 ** 256 - 1)


class DockerBaseTest(ABC):
    """Base pytest class for setting up Docker images."""

    timeout: float = 2.0
    max_attempts: int = 10

    _image: DockerImage
    _container: Container

    @classmethod
    def setup_class(cls):
        """Setup up the test class."""
        cls._image = cls._build_image()
        cls._image.check_skip()
        cls._image.stop_if_already_running()
        cls._container = cls._image.create()
        cls._container.start()
        logger.info(f"Setting up image {cls._image.tag}...")
        success = cls._image.wait(cls.max_attempts, cls.timeout)
        if not success:
            cls._container.stop()
            logger.info(
                "Error logs from container:\n%s", cls._container.logs().decode()
            )
            cls._container.remove()
            pytest.fail(f"{cls._image.tag} doesn't work. Exiting...")
        else:
            logger.info("Done!")
            time.sleep(cls.timeout)

    @classmethod
    def teardown_class(cls):
        """Tear down the test."""
        logger.info(f"Stopping the image {cls._image.tag}...")
        cls._container.stop()
        logger.info("Logs from container:\n%s", cls._container.logs().decode())
        cls._container.remove()

    @classmethod
    @abstractmethod
    def _build_image(cls) -> DockerImage:
        """Instantiate the Docker image."""


class GanacheBaseTest(DockerBaseTest):
    """Base pytest class for Ganache."""

    ganache_addr: str = DEFAULT_GANACHE_ADDR
    ganache_port: int = DEFAULT_GANACHE_PORT
    ganache_configuration: Dict = dict(
        accounts_balances=[
            (get_key(ETHEREUM_KEY_DEPLOYER), DEFAULT_AMOUNT),
            (get_key(ETHEREUM_KEY_PATH_1), DEFAULT_AMOUNT),
            (get_key(ETHEREUM_KEY_PATH_2), DEFAULT_AMOUNT),
            (get_key(ETHEREUM_KEY_PATH_3), DEFAULT_AMOUNT),
            (get_key(ETHEREUM_KEY_PATH_4), DEFAULT_AMOUNT),
        ]
    )

    @classmethod
    def _build_image(cls) -> DockerImage:
        """Build the image."""
        client = docker.from_env()
        return GanacheDockerImage(
            client, cls.ganache_addr, cls.ganache_port, config=cls.ganache_configuration
        )
