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

"""Tendermint Docker image."""
import time
from typing import List

import docker
from docker.models.containers import Container

from tests.helpers.docker.base import DockerImage


DEFAULT_TENDERMINT_PORT = 26657
DEFAULT_ABCI_PORT = 26658
DEFAULT_PROXY_APP = f"tcp://host.docker.internal:{DEFAULT_ABCI_PORT}"

_SLEEP_TIME = 1


class TendermintDockerImage(DockerImage):
    """Tendermint Docker image."""

    def __init__(
        self,
        client: docker.DockerClient,
        port: int = DEFAULT_TENDERMINT_PORT,
        proxy_app: str = DEFAULT_PROXY_APP,
    ):
        """Initialize."""
        super().__init__(client)
        self.port = port
        self.proxy_app = proxy_app

    @property
    def tag(self) -> str:
        """Get the tag."""
        return "tendermint/tendermint:v0.34.11"

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
        container = self._client.containers.run(
            self.tag,
            command=cmd,
            detach=True,
            ports=ports,
            extra_hosts={"host.docker.internal": "host-gateway"},
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
