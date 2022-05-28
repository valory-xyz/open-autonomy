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
import logging
import subprocess  # nosec
from pathlib import Path
from typing import Any, List

import pytest

from tests.helpers.base import tendermint_health_check
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


class TendermintLocalNetworkBuilder:
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
        self._create_testnet()
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

    def _create_testnet(self) -> None:
        """Create a testnet calling 'tendermint testnet'."""
        subprocess.call(  # nosec
            [
                "tendermint",
                "testnet",
                "--v",
                str(self.nb_nodes),
                "--o",
                str(self.directory),
            ]
        )

    def _get_node_id(self, i: int) -> str:
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

    def get_command(self, i: int) -> List[str]:
        """Get command-line command for the ith process."""
        n = self.nodes[i]
        return [
            "tendermint",
            "node",
            "--home",
            str(n.home),
            f"--rpc.laddr={n.rpc_laddr}",
            f"--p2p.laddr={n.p2p_laddr}",
            f"--p2p.seeds={','.join(self.get_p2p_seeds())}",
            f"--consensus.create_empty_blocks={self.consensus_create_empty_blocks}",
        ]

    @property
    def http_rpc_laddrs(self) -> List[str]:
        """Get HTTP RPC listening addresses."""
        return [node.get_http_addr(LOCALHOST) for node in self.nodes]


class BaseTendermintTestClass:
    """MixIn class for Pytest classes."""

    @staticmethod
    def health_check(
        tendermint_net: TendermintLocalNetworkBuilder, **kwargs: Any
    ) -> None:
        """Do a health-check of the Tendermint network."""
        logging.info("Waiting for Tendermint nodes to be up")
        for rpc_addr in tendermint_net.http_rpc_laddrs:
            if not tendermint_health_check(rpc_addr, **kwargs):
                pytest.fail(f"Tendermint node {rpc_addr} did not pass health-check")
