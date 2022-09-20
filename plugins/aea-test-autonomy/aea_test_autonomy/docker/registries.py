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

"""Tendermint Docker image."""
import logging
import time
from typing import Dict, List, Optional

import docker
import requests
from aea.exceptions import enforce
from aea_test_autonomy.docker.base import DockerImage
from docker.models.containers import Container


DEFAULT_HARDHAT_ADDR = "http://127.0.0.1"
DEFAULT_HARDHAT_PORT = 8545
REGISTRIES_CONTRACTS_DIR = "autonolas-registries"

DEFAULT_ACCOUNT = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"
COMPONENT_REGISTRY = "0x5FbDB2315678afecb367f032d93F642f64180aa3"
AGENT_REGISTRY = "0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512"
REGISTRIES_MANAGER = "0x9fE46736679d2D9a65F0992F2272dE9f3c7fa6e0"
GNOSIS_SAFE_MULTISIG = "0xA51c1fc2f0D1a1b8494Ed1FE312d7C3a78Ed91C0"
SERVICE_REGISTRY = "0x998abeb3E57409262aE5b751f60747921B33613E"
SERVICE_MANAGER = "0x70e0bA845a1A0F2DA3359C97E0285013525FFC49"
GNOSIS_SAFE_MASTER_COPY = "0x4826533B4897376654Bb4d4AD88B7faFD0C98528"
GNOSIS_SAFE_PROXY_FACTORY = "0x99bbA657f2BbC93c02D617f8bA121cB8Fc104Acf"
GNOSIS_SAFE_MULTISIG = "0x0E801D84Fa97b50751Dbf25036d067dCf18858bF"
GNOSIS_SAFE_MULTISIG_WITH_SAME_ADDRESS = "0x8f86403A4DE0BB5791fa46B8e795C547942fE4Cf"
GNOSIS_SAFE_MULTISEND = "0x9d4454B023096f34B160D6B654540c56A1F81688"
SERVICE_MULTISIG_1 = "0xD8dE647170163a981bb3Fdb2063583eAcF7D55AC"
SERVICE_MULTISIG_2 = "0x070fC9F640b0cC01ab0159d23f09f8936077C9e9"
DEFAULT_SERVICE_CONFIG_HASH = (
    "0xd913b5bf68193dfacb941538d5900466c449c9ec8121153f152de2e026fa7f3a"
)


class RegistriesDockerImage(DockerImage):
    """Spawn a local Ethereum network with deployed registry contracts, using HardHat."""

    _CONTAINER_PORT = DEFAULT_HARDHAT_PORT
    _SERVICE_CONFIG_HASH_ENV_VAR = "SERVICE_CONFIG_HASH"
    _env_vars = {
        _SERVICE_CONFIG_HASH_ENV_VAR: DEFAULT_SERVICE_CONFIG_HASH,
    }

    def __init__(
        self,
        client: docker.DockerClient,
        addr: str = DEFAULT_HARDHAT_ADDR,
        port: int = DEFAULT_HARDHAT_PORT,
        env_vars: Optional[Dict] = None,
    ):
        """Initialize."""
        super().__init__(client)
        self.addr = addr
        self.port = port
        if env_vars is not None:
            self._env_vars = {**self._env_vars, **env_vars}

    @property
    def tag(self) -> str:
        """Get the tag."""
        return "valory/autonolas-registries:latest"

    def create(self) -> Container:
        """Create the container."""
        ports = {f"{self._CONTAINER_PORT}/tcp": ("0.0.0.0", self.port)}  # nosec
        container = self._client.containers.run(
            self.tag,
            detach=True,
            ports=ports,
            extra_hosts={"host.docker.internal": "host-gateway"},
            environment=self._env_vars,
        )
        return container

    def create_many(self, nb_containers: int) -> List[Container]:
        """Instantiate the image in many containers, parametrized."""
        raise NotImplementedError()

    def wait(self, max_attempts: int = 15, sleep_rate: float = 1.0) -> bool:
        """
        Wait until the image is running.

        :param max_attempts: max number of attempts.
        :param sleep_rate: the amount of time to sleep between different requests.
        :return: True if the wait was successful, False otherwise.
        """
        for i in range(max_attempts):
            try:
                response = requests.get(f"{self.addr}:{self.port}")
                enforce(response.status_code == 200, "")
                return True
            except Exception as e:  # pylint: disable=broad-except
                logging.error("Exception: %s: %s", type(e).__name__, str(e))
                logging.info(
                    "Attempt %s failed. Retrying in %s seconds...", i, sleep_rate
                )
                time.sleep(sleep_rate)
        return False
