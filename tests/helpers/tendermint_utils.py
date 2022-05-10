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

"""Helpers for Tendermint."""
import subprocess  # nosec
from pathlib import Path
from typing import List

from tests.fixture_helpers import UseTendermint
from tests.helpers.constants import LOCALHOST

_TCP = "tcp://"
_HTTP = "http://"
_LOCAL_ADDRESS = "0.0.0.0"  # nosec
_STARTING_ABCI_PORT = 26658
_STARTING_RPC_PORT = 26657
_STARTING_P2P_PORT = 26656


class TendermintNodeInfo:
    """Data class to store Tendermint node info."""

    def __init__(
        self, node_id: str, abci_port: int, rpc_port: int, p2p_port: int, home: Path
    ):
        """Initialize Tendermint node info."""
        self.node_id = node_id
        self.abci_port = abci_port
        self.rpc_port = rpc_port
        self.p2p_port = p2p_port
        self.home = home

    @property
    def rpc_laddr(self) -> str:
        """Get ith rpc_laddr."""
        return f"{_TCP}{_LOCAL_ADDRESS}:{self.rpc_port}"

    def get_http_addr(self, host: str) -> str:
        """Get ith HTTP RCP address, given the host."""
        return f"{_HTTP}{host}:{self.rpc_port}"

    @property
    def p2p_laddr(self) -> str:
        """Get ith p2p_laddr."""
        return f"{_TCP}{_LOCAL_ADDRESS}:{self.p2p_port}"


class TendermintLocalNetworkBuilder(UseTendermint):
    """Build a local Tendermint network."""

    def __init__(
        self,
        nb_nodes: int,
        directory: Path,
        consensus_create_empty_blocks: bool = True,
    ) -> None:
        """Initialize the builder."""
        self.nb_nodes = nb_nodes
        self.directory = Path(directory).resolve().absolute()
        self.consensus_create_empty_blocks = consensus_create_empty_blocks

        self._create()

    def _create(self) -> None:
        """Create a Tendermint local network."""
        self.nodes = [
            TendermintNodeInfo(
                self._get_node_id(i),
                _STARTING_ABCI_PORT + i * 10,
                _STARTING_RPC_PORT + i * 10,
                _STARTING_P2P_PORT + i * 10,
                self.directory / f"node{i}",
            )
            for i in range(self.nb_nodes)
        ]

    @staticmethod
    def _get_node_id(i: int) -> str:
        """Get the node id."""
        node_name = f"node{i}"
        process = subprocess.Popen(  # nosec
            ["tendermint", "--home", node_name, "show-node-id"], stdout=subprocess.PIPE
        )
        output, _ = process.communicate()
        node_id = output.decode().strip()
        return node_id

    def get_p2p_seeds(self) -> List[str]:
        """Get p2p seeds."""
        return [f"{_TCP}{n.node_id}@{_LOCAL_ADDRESS}:{n.p2p_port}" for n in self.nodes]

    @property
    def http_rpc_laddrs(self) -> List[str]:
        """Get HTTP RPC listening addresses."""
        return [node.get_http_addr(LOCALHOST) for node in self.nodes]
