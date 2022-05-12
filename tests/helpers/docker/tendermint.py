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

from deployments.constants import TENDERMINT_VERSION
from tests.helpers.docker.base import DockerImage


_TCP = "tcp://"
_HTTP = "http://"
_LOCAL_ADDRESS = "0.0.0.0"

DEFAULT_TENDERMINT_PORT = 26657
DEFAULT_P2P_PORT = 26656
DEFAULT_TENDERMINT_COM_PORT = 8080
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
        abci_host: str = DEFAULT_ABCI_HOST,
        abci_port: int = DEFAULT_ABCI_PORT,
        port: int = DEFAULT_TENDERMINT_PORT,
    ):
        """Initialize."""
        super().__init__(client)
        self.abci_host = abci_host
        self.abci_port = abci_port
        self.port = port
        self.proxy_app = f"tcp://{self.abci_host}:{self.abci_port}"

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
        time.sleep(_SLEEP_TIME)
        return True


class FlaskTendermintDockerImage(TendermintDockerImage):
    """Flask app with Tendermint Docker image."""

    @property
    def tag(self) -> str:
        """Get the tag."""
        return f"valory/consensus-algorithms-tendermint:{TENDERMINT_VERSION}"

    def _build_command(self) -> List[str]:
        """Build command."""
        return ["run", "--no-reload", "--host=0.0.0.0", "--port=8080"]

    def _create_one(self, i: int) -> Container:
        """Create a node container."""
        name = f"node{i}"
        run_kwargs = dict(
            image=self.tag,
            command=self._build_command(),
            name=name,
            hostname=name,
            detach=True,
            mem_limit="1024m",
            mem_reservation="256M",
            environment={
                "ID": i,
                "PROXY_APP": f"tcp://abci{i}:{self.abci_port}",
                "TMHOME": f"/tendermint/{name}",
                "CREATE_EMPTY_BLOCKS": "true",
                "DEV_MODE": "1",
                "LOG_FILE": f"/logs/{name}.txt",
            },
            working_dir="/tendermint",
            volumes=[
                "./build:/tendermint:Z",
                "../persistent_data/logs:/logs:Z",
                "../persistent_data/tm_state:/tm_state:Z",
            ],
            ports={
                f"{DEFAULT_TENDERMINT_PORT}/tcp": ("0.0.0.0", self.port + i),
            },
            extra_hosts={self.abci_host: "host-gateway"}
            if self.abci_host == DEFAULT_ABCI_HOST
            else {},
        )
        container = self._client.containers.run(**run_kwargs)
        return container

    def _create_config(self, nb_nodes: int) -> None:
        """Create necessary configuration."""
        cmd = [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{os.getcwd()}/deployments/build/build:/tendermint:Z",
            f"--entrypoint=/usr/bin/tendermint",
            self.tag,
            "testnet",
            "--config",
            "/etc/tendermint/config-template.toml",
            f"--v",
            f"{nb_nodes}",
            "--o",
            ".",
        ]
        for i in range(nb_nodes):
            cmd.append(f"--hostname=node{i}")

        subprocess.call(cmd)  # nosec

    def create_many(self, nb_containers: int) -> List[Container]:
        """Create a list of node containers."""
        self._create_config(nb_containers)
        containers = [self._create_one(i) for i in range(nb_containers)]
        return containers
