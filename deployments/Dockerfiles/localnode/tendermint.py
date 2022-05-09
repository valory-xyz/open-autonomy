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
import time
from logging import Logger
from threading import Thread
from typing import List, Optional


DEFAULT_LOG_FILE = "tendermint.log"


class TendermintParams:  # pylint: disable=too-few-public-methods
    """Tendermint node parameters."""

    def __init__(  # pylint: disable=too-many-arguments
        self,
        proxy_app: str,
        consensus_create_empty_blocks: bool,
        p2p_laddr: str = "tcp://0.0.0.0:26656",
        rpc_laddr: str = "tcp://0.0.0.0:26657",
        # p2p_seeds: Optional[List[str]] = None,
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
        self.log_file = os.environ.get("LOG_FILE", DEFAULT_LOG_FILE)
        self.params = params
        self.logger = logger or logging.getLogger()

        self._process: Optional[subprocess.Popen] = None
        self._monitoring: Optional[Thread] = None

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

        self._process = (
            subprocess.Popen(  # nosec # pylint: disable=consider-using-with,W1509
                cmd,
                preexec_fn=os.setsid,  # stdout=file
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1,
                universal_newlines=True,
            )
        )
        if self._monitoring is not None:  # pragma: nocover
            return
        self._monitoring = Thread(target=self.check_server_status)
        self._monitoring.start()

    def check_server_status(
        self,
    ) -> None:
        """Check server status."""
        while True:
            try:
                if self._monitoring is None:
                    break  # break from the loop immediately.
                if self._process is None:
                    time.sleep(0.05)
                    continue
                line = self._process.stdout.readline()  # type: ignore
                if line.find("RPC HTTP server stopped") > 0:
                    self.stop()
                    self.start()
                    self.write_line(
                        "Restarted the HTTP RCP server, as a connection was dropped!\n"
                    )
                self.write_line(line)
            except Exception as e:
                print("Error!", str(e))
        self.write_line(
            "Monitoring thread terminated\n"
        )

    def write_line(self, line: str) -> None:
        """Open and write a line to the log file."""
        with open(self.log_file, "a") as file:
            file.write(line)

    def stop(self) -> None:
        """Stop a Tendermint node process."""
        if self._process is None:
            return
        self._monitoring = None
        os.killpg(os.getpgid(self._process.pid), signal.SIGTERM)
        self._process = None

    def prune_blocks(self) -> None:
        """Prune blocks from the Tendermint state"""
        subprocess.call(  # nosec:
            ["tendermint", "--home", str(self.params.home), "unsafe-reset-all"]
        )
