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
import os
import subprocess
import time
from typing import List

import docker
from docker.models.containers import Container

from tests.helpers.docker.base import DockerImage

DEFAULT_TENDERMINT_PORT = 26657
DEFAULT_ABCI_PORT = 26658
# we need this because we want to connect from the Tendermint
# Docker container to the ABCI server that lives in the host
DEFAULT_ABCI_HOST = "host.docker.internal"

_SLEEP_TIME = 1


class TendermintDockerImage(DockerImage):
    """Tendermint Docker image."""

    def __init__(
        self,
        client: docker.DockerClient,
        n_agents: int,
        abci_host: str = DEFAULT_ABCI_HOST,
        abci_port: int = DEFAULT_ABCI_PORT,
        port: int = DEFAULT_TENDERMINT_PORT,
    ):
        """Initialize."""
        super().__init__(client)
        self.n_agents = n_agents
        self.abci_host = abci_host
        self.abci_port = abci_port
        self.port = port
        self.proxy_app = f"tcp://{self.abci_host}:{self.abci_port}"
        self.__create_image()

    def __create_image(self) -> None:
        """Create and tag an image from our Flask with Tendermint Dockerfile."""
        cmd = [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{os.getcwd()}/deployments/build/build:/tendermint:Z",
            f"--entrypoint=/usr/bin/tendermint",
            f"{self.tag}",
            "testnet",
            "--config",
            "/etc/tendermint/config-template.toml",
            f"--v",
            f"{self.n_agents}",
            "--o",
            ".",
        ]
        for i in range(self.n_agents):
            cmd.append(f"--hostname=node{i}")
        subprocess.Popen(cmd)

    @property
    def tag(self) -> str:
        """Get the tag."""
        return "valory/consensus-algorithms-tendermint:0.1.0"

    def _build_command(self) -> List[str]:
        """Build command."""
        cmd = ["node", f"--proxy_app={self.proxy_app}"]
        return cmd

    def create(self) -> Container:
        """Create the container."""
        cmd = self._build_command()
        ports = {
            f"{DEFAULT_TENDERMINT_PORT}/tcp": ("0.0.0.0", self.port),  # nosec
        }
        if self.abci_host == DEFAULT_ABCI_HOST:
            extra_hosts_config = {self.abci_host: "host-gateway"}
        else:
            extra_hosts_config = {}
        container = self._client.containers.run(
            self.tag,
            command=cmd,
            detach=True,
            ports=ports,
            extra_hosts=extra_hosts_config,
        )
        return container

    def wait(self, max_attempts: int = 15, sleep_rate: float = 1.0) -> bool:
        """
        Wait until the image is running.

        :param max_attempts: max number of attempts.
        :param sleep_rate: the amount of time to sleep between different requests.
        :return: True if the wait was successful, False otherwise.
        """
        time.sleep(_SLEEP_TIME)
        return True
