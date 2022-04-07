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

"""Tendermint manager."""
import logging
import os
import signal
import subprocess  # nosec:
from logging import Logger
from typing import List, Optional


DEFAULT_LOG_FILE = "tendermint.log"


class TendermintParams:  # pylint: disable=too-few-public-methods
    """Tendermint node parameters."""

    def __init__(  # pylint: disable=too-many-arguments
        self,
        proxy_app: str,
        # p2p_seeds: List[str],
        consensus_create_empty_blocks: bool,
        p2p_laddr: str = "tcp://0.0.0.0:26656",
        rpc_laddr: str = "tcp://0.0.0.0:26657",
        home: Optional[str] = None,
    ):
        """
        Initialize the parameters to the Tendermint node.

        :param proxy_app: ABCI address.
        :param rpc_laddr: RPC address.
        :param p2p_laddr: P2P address.
        :param consensus_create_empty_blocks: if true, Tendermint node creates empty blocks.
        :param home: Tendermint's home directory.
        """
        self.proxy_app = proxy_app
        self.p2p_laddr = p2p_laddr
        self.rpc_laddr = rpc_laddr
        # self.p2p_seeds = p2p_seeds # :noqa E800
        self.consensus_create_empty_blocks = consensus_create_empty_blocks
        self.home = home


class TendermintNode:
    """A class to manage a Tendermint node."""

    def __init__(self, params: TendermintParams, logger: Optional[Logger] = None):
        """
        Initialize a Tendermint node.

        :param params: the parameters.
        :param logger: the logger.
        """
        self.params = params
        self.logger = logger or logging.getLogger()

        self._process: Optional[subprocess.Popen] = None

    def _build_init_command(self) -> List[str]:
        """Build the 'init' command."""
        cmd = [
            "tendermint",
            "init",
        ]
        if self.params.home is not None:  # pragma: nocover
            cmd += ["--home", self.params.home]
        return cmd

    def _build_node_command(self) -> List[str]:
        """Build the 'node' command."""
        cmd = [
            "tendermint",
            "node",
            f"--proxy_app={self.params.proxy_app}",
            f"--rpc.laddr={self.params.rpc_laddr}",
            f"--p2p.laddr={self.params.p2p_laddr}",
            # f"--p2p.seeds={','.join(self.params.p2p_seeds)}", # noqa: E800
            f"--consensus.create_empty_blocks={str(self.params.consensus_create_empty_blocks).lower()}",
        ]
        if self.params.home is not None:  # pragma: nocover
            cmd += ["--home", self.params.home]
        return cmd

    def init(self) -> None:
        """Initialize Tendermint node."""
        cmd = self._build_init_command()
        subprocess.call(cmd)  # nosec

    def start(self) -> None:
        """Start a Tendermint node process."""
        if self._process is not None:  # pragma: nocover
            return
        cmd = self._build_node_command()
        log_file = os.environ.get("LOG_FILE", DEFAULT_LOG_FILE)

        with open(log_file, "a") as file:
            self._process = (
                subprocess.Popen(  # nosec # pylint: disable=consider-using-with,W1509
                    cmd, preexec_fn=os.setsid, stdout=file
                )
            )

    def stop(self) -> None:
        """Stop a Tendermint node process."""
        if self._process is None:
            return
        os.killpg(os.getpgid(self._process.pid), signal.SIGTERM)
        self._process = None

    def prune_blocks(self) -> None:
        """Prune blocks from the Tendermint state"""
        subprocess.call(  # nosec:
            ["tendermint", "--home", str(self.params.home), "unsafe-reset-all"]
        )
