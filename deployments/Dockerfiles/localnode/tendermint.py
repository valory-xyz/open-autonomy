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
import platform
import signal
import subprocess  # nosec:
from logging import Logger
from pathlib import Path
from threading import Event, Thread
from typing import Any, List, Optional


ENCODING = "utf-8"
DEFAULT_P2P_LISTEN_ADDRESS = "tcp://0.0.0.0:26656"
DEFAULT_RPC_LISTEN_ADDRESS = "tcp://0.0.0.0:26657"
DEFAULT_TENDERMINT_LOG_FILE = "tendermint.log"


class StoppableThread(Thread):
    """Thread class with a stop() method."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialise the thread."""
        super().__init__(*args, **kwargs)
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
        rpc_laddr: str = DEFAULT_RPC_LISTEN_ADDRESS,
        p2p_laddr: str = DEFAULT_P2P_LISTEN_ADDRESS,
        p2p_seeds: Optional[List[str]] = None,
        consensus_create_empty_blocks: bool = True,
        home: Optional[str] = None,
    ):
        """
        Initialize the parameters to the Tendermint node.

        :param proxy_app: ABCI address.
        :param rpc_laddr: RPC address.
        :param p2p_laddr: P2P address.
        :param p2p_seeds: P2P seeds.
        :param consensus_create_empty_blocks: if true, Tendermint node creates empty blocks.
        :param home: Tendermint's home directory.
        """
        self.proxy_app = proxy_app
        self.rpc_laddr = rpc_laddr
        self.p2p_laddr = p2p_laddr
        self.p2p_seeds = p2p_seeds
        self.consensus_create_empty_blocks = consensus_create_empty_blocks
        self.home = home

    def __str__(self) -> str:
        """Get the string representation."""
        return (
            f"{self.__class__.__name__}("
            f"    proxy_app={self.proxy_app},\n"
            f"    rpc_laddr={self.rpc_laddr},\n"
            f"    p2p_laddr={self.p2p_laddr},\n"
            f"    p2p_seeds={self.p2p_seeds},\n"
            f"    consensus_create_empty_blocks={self.consensus_create_empty_blocks},\n"
            f"    home={self.home},\n"
            ")"
        )


class TendermintNode:
    """A class to manage a Tendermint node."""

    def __init__(self, params: TendermintParams, logger: Optional[Logger] = None):
        """
        Initialize a Tendermint node.

        :param params: the parameters.
        :param logger: the logger.
        """
        self.params = params
        self._process: Optional[subprocess.Popen] = None
        self._monitoring: Optional[StoppableThread] = None
        self.logger = logger or logging.getLogger()
        self.log_file = os.environ.get("LOG_FILE", DEFAULT_TENDERMINT_LOG_FILE)

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
        p2p_seeds = ",".join(self.params.p2p_seeds) if self.params.p2p_seeds else ""
        cmd = [
            "tendermint",
            "node",
            f"--proxy_app={self.params.proxy_app}",
            f"--rpc.laddr={self.params.rpc_laddr}",
            f"--p2p.laddr={self.params.p2p_laddr}",
            f"--p2p.seeds={p2p_seeds}",
            f"--consensus.create_empty_blocks={str(self.params.consensus_create_empty_blocks).lower()}",
        ]
        if self.params.home is not None:  # pragma: nocover
            cmd += ["--home", self.params.home]
        return cmd

    def init(self) -> None:
        """Initialize Tendermint node."""
        cmd = self._build_init_command()
        subprocess.call(cmd)  # nosec

    def start(self, start_monitoring: bool = False) -> None:
        """Start a Tendermint node process."""
        self._start_tm_process()
        if start_monitoring:
            self._start_monitoring_thread()

    def _start_tm_process(self) -> None:
        """Start a Tendermint node process."""
        if self._process is not None:  # pragma: nocover
            return
        cmd = self._build_node_command()

        if platform.system() == "Windows":  # pragma: nocover
            self._process = (
                subprocess.Popen(  # nosec # pylint: disable=consider-using-with,W1509
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    bufsize=1,
                    universal_newlines=True,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,  # type: ignore
                )
            )
        else:
            self._process = (
                subprocess.Popen(  # nosec # pylint: disable=consider-using-with,W1509
                    cmd,
                    preexec_fn=os.setsid,
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

    def _stop_tm_process(self) -> None:
        """Stop a Tendermint node process."""
        if self._process is None:
            return

        if platform.system() == "Windows":
            os.kill(self._process.pid, signal.CTRL_C_EVENT)  # type: ignore  # pylint: disable=no-member
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:  # nosec
                os.kill(self._process.pid, signal.CTRL_BREAK_EVENT)  # type: ignore  # pylint: disable=no-member
        else:
            self._process.send_signal(signal.SIGTERM)
            self._process.wait(timeout=5)
            poll = self._process.poll()
            if poll is None:  # pragma: nocover
                self._process.terminate()
                self._process.wait(3)

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

    def prune_blocks(self) -> int:
        """Prune blocks from the Tendermint state"""
        return subprocess.call(  # nosec:
            ["tendermint", "--home", str(self.params.home), "unsafe-reset-all"]
        )

    def write_line(self, line: str) -> None:
        """Open and write a line to the log file."""
        with open(self.log_file, "a", encoding=ENCODING) as file:
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
            except Exception as e:  # pylint: disable=broad-except
                self.write_line(f"Error!: {str(e)}")
        self.write_line("Monitoring thread terminated\n")

    def reset_genesis_file(self, genesis_time: str, initial_height: str) -> None:
        """Reset genesis file."""

        genesis_file = Path(str(self.params.home), "config", "genesis.json")
        genesis_config = json.loads(genesis_file.read_text(encoding=ENCODING))
        genesis_config["genesis_time"] = genesis_time
        genesis_config["initial_height"] = initial_height
        genesis_file.write_text(json.dumps(genesis_config, indent=2), encoding=ENCODING)
