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
import time
from typing import Dict, List, Optional

import requests
from aea.exceptions import enforce
from docker import DockerClient
from docker.models.containers import Container

from tests.helpers.docker.base import DockerImage


DEFAULT_ACN_CONFIG = dict(
    AEA_P2P_ID="d9e43d3f0266d14b3af8627a626fa734450b1c0fcdec6f88f79bcf5543b4668c",
    AEA_P2P_URI_PUBLIC="0.0.0.0:5000",
    AEA_P2P_URI="0.0.0.0:5000",
    AEA_P2P_DELEGATE_URI="0.0.0.0:11000",
    AEA_P2P_URI_MONITORING="0.0.0.0:8080",
    ACN_LOG_FILE="/acn_data/libp2p_node.log",
)


class ACNNodeDockerImage(DockerImage):
    """Wrapper to Ganache Docker image."""
    uris: List = [
        "AEA_P2P_URI_PUBLIC",
        "AEA_P2P_URI",
        "AEA_P2P_DELEGATE_URI",
        "AEA_P2P_URI_MONITORING"
    ]

    def __init__(
            self,
            client: DockerClient,
            config: Optional[Dict] = None,
    ):
        """
        Initialize the Ganache Docker image.

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

        return {f"{port}/tcp": ("0.0.0.0", port)
                for port in [self._config[uri].split(":")[1] for uri in self.uris]
                }  # nosec

    def create(self) -> Container:
        """Create the container."""
        container = self._client.containers.run(
            self.tag, detach=True, ports=self._make_ports(), environment=self._config
        )
        return container

    def wait(self, max_attempts: int = 15, sleep_rate: float = 1.0) -> bool:
        """Wait until the image is up."""
        uris = set([self._config[uri] for uri in self.uris])
        ready_uris = []
        for uri in uris:
            if uri in ready_uris:
                continue
            if set(ready_uris) == uris:
                return True
            for i in range(max_attempts):
                try:
                    response = requests.get(uri)
                    enforce(response.status_code == 200, "")
                    ready_uris.append(uri)
                except Exception:
                    logging.error(
                        "Attempt %s failed. Retrying in %s seconds...", i, sleep_rate
                    )
                    time.sleep(sleep_rate)
        return False


