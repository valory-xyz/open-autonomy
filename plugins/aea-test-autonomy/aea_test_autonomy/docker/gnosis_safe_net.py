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
from typing import List

import docker
import requests
from aea.exceptions import enforce
from aea_test_autonomy.docker.base import DockerImage
from docker.models.containers import Container


DEFAULT_HARDHAT_ADDR = "http://127.0.0.1"
DEFAULT_HARDHAT_PORT = 8545
GNOSIS_SAFE_CONTRACTS_DIR = "safe-contracts"
CONFIG_FILE = "hardhat.config.ts"

_SLEEP_TIME = 1

# Note: addresses of deployment of master contracts are deterministic
SAFE_CONTRACT = "0xd9Db270c1B5E3Bd161E8c8503c55cEABeE709552"
DEFAULT_CALLBACK_HANDLER = "0xf48f2B2d2a534e402487b3ee7C18c33Aec0Fe5e4"
PROXY_FACTORY_CONTRACT = "0xa6B71E26C5e0845f74c812102Ca7114b6a896AB2"
MULTISEND_CONTRACT = "0xA238CBeb142c10Ef7Ad8442C6D1f9E89e07e7761"
MULTISEND_CALL_ONLY_CONTRACT = "0x40A2aCCbd92BCA938b02010E17A5b8929b49130D"


class GnosisSafeNetDockerImage(DockerImage):
    """Spawn a local Ethereum network with deployed Gnosis Safe contracts, using HardHat."""

    _CONTAINER_PORT = DEFAULT_HARDHAT_PORT

    def __init__(
        self,
        client: docker.DockerClient,
        addr: str = DEFAULT_HARDHAT_ADDR,
        port: int = DEFAULT_HARDHAT_PORT,
    ):
        """Initialize."""
        super().__init__(client)
        self.addr = addr
        self.port = port

    @property
    def tag(self) -> str:
        """Get the tag."""
        return "valory/safe-contract-net:latest"

    def create(self) -> Container:
        """Create the container."""
        ports = {f"{self._CONTAINER_PORT}/tcp": ("0.0.0.0", self.port)}  # nosec
        container = self._client.containers.run(
            self.tag,
            detach=True,
            ports=ports,
            extra_hosts={"host.docker.internal": "host-gateway"},
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
