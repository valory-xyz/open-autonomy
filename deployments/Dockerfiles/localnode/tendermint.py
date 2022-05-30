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
import json
import logging
import os
import signal
import subprocess  # nosec:
from logging import Logger
from pathlib import Path
from threading import Event, Thread
from typing import Any, List, Optional


DEFAULT_LOG_FILE = "tendermint.log"
DEFAULT_P2P_LADDR = "tcp://0.0.0.0:26656"
DEFAULT_RPC_LADDR = "tcp://0.0.0.0:26657"


class StoppableThread(Thread):
    """Thread class with a stop() method."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialise the thread."""
        super(StoppableThread, self).__init__(*args, **kwargs)
        self._stop_event = Event()

    def stop(self) -> None:
        """Set the stop event."""
        self._stop_event.set()

    def stopped(self) -> bool:
        """Check if the thread is stopped."""
        return self._stop_event.is_set()


class TendermintParams:  # pylint: disable=too-few-public-methods
    """Tendermint node parameters."""

    def __init__(  # pylint: disable=too-many-arguments
        self,
        proxy_app: str,
        consensus_create_empty_blocks: bool,
        p2p_laddr: str = DEFAULT_P2P_LADDR,
        rpc_laddr: str = DEFAULT_RPC_LADDR,
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
        self._monitoring: Optional[StoppableThread] = None

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
            f"--consensus.create_empty_blocks={str(self.params.consensus_create_empty_blocks).lower()}",
        ]
        if self.params.home is not None:  # pragma: nocover
            cmd += ["--home", self.params.home]
        return cmd

    def init(self) -> None:
        """Initialize Tendermint node."""
        cmd = self._build_init_command()
        subprocess.call(cmd)  # nosec

    def _start_tm_process(self) -> None:
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
        self.write_line("Tendermint process started\n")

    def _start_monitoring_thread(self) -> None:
        """Start a monitoring thread."""
        self._monitoring = StoppableThread(target=self.check_server_status)
        self._monitoring.start()

    def start(self) -> None:
        """Start a Tendermint node process."""
        self._start_tm_process()
        self._start_monitoring_thread()

    def _stop_tm_process(self) -> None:
        """Stop a Tendermint node process."""
        if self._process is None:
            return
        os.killpg(os.getpgid(self._process.pid), signal.SIGTERM)
        self._process = None
        self.write_line("Tendermint process stopped\n")

    def _stop_monitoring_thread(self) -> None:
        """Stop a monitoring process."""
        if self._monitoring is not None:
            self._monitoring.stop()  # set stop event
            self._monitoring.join()

    def stop(self) -> None:
        """Stop a Tendermint node process."""
        self._stop_monitoring_thread()
        self._stop_tm_process()

    def prune_blocks(self) -> None:
        """Prune blocks from the Tendermint state"""
        subprocess.call(  # nosec:
            ["tendermint", "--home", str(self.params.home), "unsafe-reset-all"]
        )

    def write_line(self, line: str) -> None:
        """Open and write a line to the log file."""
        with open(self.log_file, "a") as file:
            file.write(line)

    def check_server_status(
        self,
    ) -> None:
        """Check server status."""
        self.write_line("Monitoring thread started\n")
        while True:
            try:
                if self._monitoring.stopped():  # type: ignore
                    break  # break from the loop immediately.
                line = self._process.stdout.readline()  # type: ignore
                self.write_line(line)
                for trigger in [
                    "RPC HTTP server stopped",  # this occurs when we lose connection from the tm side
                    "Stopping abci.socketClient for error: read message: EOF module=abci-client connection=",  # this occurs when we lose connection from the AEA side.
                ]:
                    if line.find(trigger) >= 0:
                        self._stop_tm_process()
                        self._start_tm_process()
                        self.write_line(
                            f"Restarted the HTTP RPC server, as a connection was dropped with message:\n\t\t {line}\n"
                        )
            except Exception as e:
                self.write_line(f"Error!: {str(e)}")
        self.write_line("Monitoring thread terminated\n")

    def reset_genesis_file(self, genesis_time: str) -> None:
        """Reset genesis file."""

        genesis_file = Path(str(self.params.home), "config", "genesis.json")
        genesis_config = json.loads(genesis_file.read_text())
        genesis_config["genesis_time"] = genesis_time
        genesis_file.write_text(json.dumps(genesis_config, indent=2))
