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
import re
import signal
import subprocess  # nosec
import time
from pathlib import Path
from typing import Any, Dict, IO, List, cast

import docker
import pytest
from docker.errors import ImageNotFound
from docker.models.containers import Container

from aea_swarm.deploy.constants import TENDERMINT_VERSION

from tests.helpers.base import tendermint_health_check
from tests.helpers.docker.base import DockerImage


_TCP = "tcp://"
_HTTP = "http://"
_LOCAL_ADDRESS = "0.0.0.0"  # nosec

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
        p2p_port: int = DEFAULT_P2P_PORT,
        com_port: int = DEFAULT_TENDERMINT_COM_PORT,
    ):
        """Initialize."""
        super().__init__(client)
        self.abci_host = abci_host
        self.abci_port = abci_port
        self.port = port
        self.p2p_port = p2p_port
        self.com_port = com_port
        self.proxy_app = f"{_TCP}{self.abci_host}:{self.abci_port}"

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
            f"{DEFAULT_TENDERMINT_PORT}/tcp": (_LOCAL_ADDRESS, self.port),  # nosec
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

    _extra_hosts: Dict[str, str]

    def __init__(
        self,
        client: docker.DockerClient,
        abci_host: str = DEFAULT_ABCI_HOST,
        abci_port: int = DEFAULT_ABCI_PORT,
        port: int = DEFAULT_TENDERMINT_PORT,
        p2p_port: int = DEFAULT_P2P_PORT,
        com_port: int = DEFAULT_TENDERMINT_COM_PORT,
    ):
        """Initialize."""
        super().__init__(client, abci_host, abci_port, port, p2p_port, com_port)
        self.__create_flask_tendermint_image()

    def __create_flask_tendermint_image(self) -> None:
        """Create an image of the Flask server with Tendermint."""
        try:
            self._client.images.get(self.tag)
        except ImageNotFound:
            cwd = os.getcwd()
            current_file_folder = os.path.dirname(os.path.realpath(__file__))
            root = current_file_folder.split(os.path.sep)[:-3]
            root_path = Path(os.path.join(os.path.sep, *root))
            cmd = [
                "skaffold",
                "build",
                "-p",
                "dependencies",
                "--push",
                "false",
            ]
            env = {"VERSION": TENDERMINT_VERSION}
            try:
                process = subprocess.Popen(  # nosec # pylint: disable=consider-using-with,W1509
                    cmd,
                    preexec_fn=os.setsid,
                    env=env,
                    stdout=subprocess.PIPE,
                    cwd=str(root_path),
                )

                for line in iter(cast(IO[bytes], process.stdout).readline, ""):
                    if line == b"":
                        break
                    print(f"[Skaffold] {line.decode().strip()}")

            except KeyboardInterrupt:
                cast(IO[bytes], process.stdout).close()
                process.send_signal(signal.SIGTERM)
            process.wait(timeout=30)
            poll = process.poll()
            if poll is None:
                process.terminate()
                process.wait(2)

            if process.returncode != 0:
                print("Image build failed.")

    @property
    def tag(self) -> str:
        """Get the tag."""
        return f"valory/consensus-algorithms-tendermint:{TENDERMINT_VERSION}"

    @staticmethod
    def get_node_name(i: int) -> str:
        """Get the ith node's name."""
        return f"node{i}"

    def _get_node_id(self, i: int) -> str:
        """Get the node id."""
        cmd = [
            "docker",
            "exec",
            self.get_node_name(i),
            "tendermint",
            "--home",
            self.get_node_name(i),
            "show-node-id",
        ]
        process = subprocess.Popen(  # nosec
            cmd,
            stdout=subprocess.PIPE,
        )
        output, _ = process.communicate()
        node_id = output.decode().strip()
        return node_id

    @staticmethod
    def __increment_port(port: int, i: int) -> int:
        """Increment a port"""
        return port + i * 10

    def get_port(self, i: int) -> int:
        """Get the ith port."""
        return self.__increment_port(self.port, i)

    def get_com_port(self, i: int) -> int:
        """Get the ith com port."""
        return self.__increment_port(self.com_port, i)

    def get_p2p_port(self, i: int) -> int:
        """Get the ith p2p port."""
        return self.__increment_port(self.p2p_port, i)

    def get_abci_port(self, i: int) -> int:
        """Get the ith abci port."""
        return self.__increment_port(self.abci_port, i)

    def get_addr(self, prefix: str, i: int, p2p: bool = False) -> str:
        """Get a node's address."""
        valid_prefixes = {_TCP, _HTTP}
        if prefix not in valid_prefixes:
            raise ValueError(f"Invalid prefix! Should be one of: {valid_prefixes}")

        if p2p:
            prefix += self._get_node_id(i) + "@"
            port = self.get_p2p_port(i)
        else:
            port = self.get_port(i)

        return f"{prefix}{_LOCAL_ADDRESS}:{port}"

    @property
    def p2p_seeds(self) -> List[str]:
        """Get p2p seeds."""
        if self.nb_nodes is None:
            raise ValueError("Trying to get p2p seeds before initializing containers!")

        return [self.get_addr(_TCP, i) for i in range(self.nb_nodes)]

    def _build_command(self) -> List[str]:
        """Build command."""
        return ["run", "--no-reload", f"--host={_LOCAL_ADDRESS}", "--port=8080"]

    def _create_one(self, i: int) -> Container:
        """Create a node container."""
        name = self.get_node_name(i)
        extra_hosts = (
            {self.abci_host: "host-gateway"}
            if self.abci_host == DEFAULT_ABCI_HOST
            else {}
        )
        extra_hosts.update(self._extra_hosts)

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
                "PROXY_APP": f"{_TCP}{self.abci_host}:{self.get_abci_port(i)}",
                "TMHOME": f"/tendermint/{name}",
                "CREATE_EMPTY_BLOCKS": "true",
                "DEV_MODE": "1",
                "LOG_FILE": f"/logs/{name}.txt",
            },
            working_dir="/tendermint",
            volumes=[
                f"{os.getcwd()}/nodes:/tendermint:Z",
                f"{os.getcwd()}/logs:/logs:Z",
                f"{os.getcwd()}/tm_state:/tm_state:Z",
            ],
            ports={
                f"{DEFAULT_TENDERMINT_PORT}/tcp": (
                    _LOCAL_ADDRESS,  # nosec,
                    self.get_port(i),
                ),
                f"{DEFAULT_TENDERMINT_COM_PORT}/tcp": (
                    _LOCAL_ADDRESS,  # nosec,
                    self.get_com_port(i),
                ),
                f"{DEFAULT_P2P_PORT}/tcp": (
                    _LOCAL_ADDRESS,  # nosec,
                    self.get_p2p_port(i),
                ),
            },
            extra_hosts=extra_hosts,
        )
        container = self._client.containers.run(**run_kwargs)
        return container

    def _create_config(self, nb_nodes: int) -> None:
        """Create necessary configuration."""
        self.nb_nodes = nb_nodes
        cmd = [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{os.getcwd()}/nodes:/tendermint:Z",
            "--entrypoint=/usr/bin/tendermint",
            self.tag,
            "testnet",
            "--config",
            "/etc/tendermint/config-template.toml",
            "--v",
            f"{nb_nodes}",
            "--o",
            "/tendermint/",
        ]
        for i in range(nb_nodes):
            cmd.append(f"--hostname=node{i}")

        subprocess.run(cmd)  # nosec
        for config_file in Path().cwd().glob("nodes/**/*.toml"):
            config_text = config_file.read_text(encoding="utf-8")
            peers = re.findall(r"[a-z0-9]+@node\d:\d+", config_text)

            updated_peers = []
            for peer in peers:
                peer_id, address = peer.split("@")
                peer_name, port_string = address.split(":")
                *_, peer_number_string = peer_name

                port = int(port_string)
                peer_number = int(peer_number_string)
                new_port = port + (peer_number * 10)
                updated_peers.append(f"{peer_id}@{peer_name}:{new_port}")

            persistent_peers_string = (
                'persistent_peers = "' + ",".join(updated_peers) + '"\n'
            )
            updated_config = re.sub(
                'persistent_peers = ".*\n', persistent_peers_string, config_text
            )

            config_file.write_text(updated_config, encoding="utf-8")

        self._extra_hosts = {
            self.get_node_name(i): "host-gateway" for i in range(nb_nodes)
        }

    def create_many(self, nb_containers: int) -> List[Container]:
        """Create a list of node containers."""
        self._create_config(nb_containers)
        containers = [self._create_one(i) for i in range(nb_containers)]
        return containers

    def health_check(self, **kwargs: Any) -> None:
        """Do a health-check of the Tendermint network."""
        http_rpc_laddresses = [self.get_addr(_HTTP, i) for i in range(self.nb_nodes)]
        for http_rpc_laddr in http_rpc_laddresses:
            if not tendermint_health_check(http_rpc_laddr, **kwargs):
                pytest.fail(
                    f"Tendermint node {http_rpc_laddr} did not pass health-check"
                )
