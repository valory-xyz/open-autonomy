# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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

"""ACN Docker Image."""
import logging
import socket
import time
from typing import Dict, List, Optional

from aea.exceptions import enforce
from docker import DockerClient
from docker.models.containers import Container

from tests.helpers.docker.base import DockerImage


_LOCAL_ADDRESS = "0.0.0.0"  # nosec

DEFAULT_ACN_CONFIG: Dict[str, str] = dict(
    AEA_P2P_ID="d9e43d3f0266d14b3af8627a626fa734450b1c0fcdec6f88f79bcf5543b4668c",
    AEA_P2P_URI_PUBLIC=f"{_LOCAL_ADDRESS}:5000",
    AEA_P2P_URI=f"{_LOCAL_ADDRESS}:5000",
    AEA_P2P_DELEGATE_URI=f"{_LOCAL_ADDRESS}:11000",
    AEA_P2P_URI_MONITORING=f"{_LOCAL_ADDRESS}:8081",
    ACN_LOG_FILE="/acn/libp2p_node.log",
)


class ACNNodeDockerImage(DockerImage):
    """Wrapper to ACNNode Docker image."""

    uris: List = [
        "AEA_P2P_URI_PUBLIC",
        "AEA_P2P_URI",
        "AEA_P2P_DELEGATE_URI",
        "AEA_P2P_URI_MONITORING",
    ]

    def __init__(
        self,
        client: DockerClient,
        config: Optional[Dict] = None,
    ):
        """
        Initialize the ACNNode Docker image.

        :param client: the Docker client.
        :param config: optional configuration to command line.
        """
        super().__init__(client)
        self._config = config or {}

    @property
    def tag(self) -> str:
        """Get the image tag."""
        return "valory/acn-node:0.1.0"

    def _make_ports(self) -> Dict:
        """Make ports dictionary for Docker."""

        return {
            f"{port}/tcp": (_LOCAL_ADDRESS, port)
            for port in [self._config[uri].split(":")[1] for uri in self.uris]
        }

    def create(self) -> Container:
        """Create the container."""
        container = self._client.containers.run(
            self.tag,
            "--config-from-env",
            detach=True,
            ports=self._make_ports(),
            environment=self._config,
        )
        return container

    def create_many(self, nb_containers: int) -> List[Container]:
        """Instantiate the image in many containers, parametrized."""
        raise NotImplementedError()

    def wait(self, max_attempts: int = 15, sleep_rate: float = 1.0) -> bool:
        """Wait until the image is up."""

        i, to_be_connected = 0, {self._config[uri] for uri in self.uris}
        while i < max_attempts and to_be_connected:
            i += 1
            for uri in to_be_connected:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    host, port = uri.split(":")
                    result = sock.connect_ex((host, int(port)))
                    sock.close()
                    enforce(result == 0, "")
                    to_be_connected.remove(uri)
                    logging.info(f"URI ready: {uri}")
                    break
                except Exception:
                    logging.error(
                        f"Attempt {i} failed on {uri}. Retrying in {sleep_rate} seconds..."
                    )
                    time.sleep(sleep_rate)

        return not to_be_connected
