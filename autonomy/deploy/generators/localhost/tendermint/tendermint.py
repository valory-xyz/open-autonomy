# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2023 Valory AG
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
import sys
from logging import Logger
from pathlib import Path
from threading import Event, Thread
from typing import Any, Dict, List, Optional


_TCP = "tcp://"
ENCODING = "utf-8"
DEFAULT_P2P_LISTEN_ADDRESS = f"{_TCP}0.0.0.0:26656"
DEFAULT_RPC_LISTEN_ADDRESS = f"{_TCP}0.0.0.0:26657"
DEFAULT_TENDERMINT_LOG_FILE = "tendermint.log"


class StoppableThread(
    Thread,
):
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
        use_grpc: bool = False,
    ):
        """
        Initialize the parameters to the Tendermint node.

        :param proxy_app: ABCI address.
        :param rpc_laddr: RPC address.
        :param p2p_laddr: P2P address.
        :param p2p_seeds: P2P seeds.
        :param consensus_create_empty_blocks: if true, Tendermint node creates empty blocks.
        :param home: Tendermint's home directory.
        :param use_grpc: Whether to use a gRPC server, or TCP
        """

        self.proxy_app = proxy_app
        self.rpc_laddr = rpc_laddr
        self.p2p_laddr = p2p_laddr
        self.p2p_seeds = p2p_seeds
        self.consensus_create_empty_blocks = consensus_create_empty_blocks
        self.home = home
        self.use_grpc = use_grpc

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

    def build_node_command(self, debug: bool = False) -> List[str]:
        """Build the 'node' command."""
        p2p_seeds = ",".join(self.p2p_seeds) if self.p2p_seeds else ""
        cmd = [
            "tendermint",
            "node",
            f"--proxy_app={self.proxy_app}",
            f"--rpc.laddr={self.rpc_laddr}",
            f"--p2p.laddr={self.p2p_laddr}",
            f"--p2p.seeds={p2p_seeds}",
            f"--consensus.create_empty_blocks={str(self.consensus_create_empty_blocks).lower()}",
            f"--abci={'grpc' if self.use_grpc else 'socket'}",
        ]
        if debug:
            cmd.append("--log_level=debug")
        if self.home is not None:  # pragma: nocover
            cmd += ["--home", self.home]
        return cmd

    @staticmethod
    def get_node_command_kwargs() -> Dict:
        """Get the node command kwargs"""
        kwargs = {
            "bufsize": 1,
            "universal_newlines": True,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.STDOUT,
        }
        if platform.system() == "Windows":  # pragma: nocover
            kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore
        else:
            kwargs["preexec_fn"] = os.setsid  # type: ignore
        return kwargs


class TendermintNode:
    """A class to manage a Tendermint node."""

    def __init__(
        self,
        params: TendermintParams,
        logger: Optional[Logger] = None,
        write_to_log: bool = False,
    ):
        """
        Initialize a Tendermint node.

        :param params: the parameters.
        :param logger: the logger.
        :param write_to_log: Write to log file.
        """
        self.params = params
        self._process: Optional[subprocess.Popen] = None
        self._monitoring: Optional[StoppableThread] = None
        self._stopping = False
        self.logger = logger or logging.getLogger()
        self.log_file = os.environ.get("LOG_FILE", DEFAULT_TENDERMINT_LOG_FILE)
        self.write_to_log = write_to_log

    def _build_init_command(self) -> List[str]:
        """Build the 'init' command."""
        cmd = [
            "tendermint",
            "init",
        ]
        if self.params.home is not None:  # pragma: nocover
            cmd += ["--home", self.params.home]
        return cmd

    def init(self) -> None:
        """Initialize Tendermint node."""
        cmd = self._build_init_command()
        subprocess.call(cmd)  # nosec

    def _monitor_tendermint_process(
        self,
    ) -> None:
        """Check server status."""
        if self._monitoring is None:
            raise ValueError("Monitoring is not running")
        self.log("Monitoring thread started\n")
        while not self._monitoring.stopped():
            try:
                if self._process is not None and self._process.stdout is not None:
                    line = self._process.stdout.readline()
                    self.log(line)
                    for trigger in [
                        # this occurs when we lose connection from the tm side
                        "RPC HTTP server stopped",
                        # whenever the node is stopped because of a closed connection
                        # from on any of the tendermint modules (abci, p2p, rpc, etc)
                        # we restart the node
                        "Stopping abci.socketClient for error: read message: EOF",
                    ]:
                        if self._monitoring.stopped():
                            break
                        if line.find(trigger) >= 0:
                            self._stop_tm_process()
                            # we can only reach this step if monitoring was activated
                            # so we make sure that after reset the monitoring continues
                            self._start_tm_process()
                            self.log(
                                f"Restarted the HTTP RPC server, as a connection was dropped with message:\n\t\t {line}\n"
                            )
            except Exception as e:  # pylint: disable=broad-except
                self.log(f"Error!: {str(e)}")
        self.log("Monitoring thread terminated\n")

    def _start_tm_process(self, debug: bool = False) -> None:
        """Start a Tendermint node process."""
        if self._process is not None or self._stopping:  # pragma: nocover
            return
        cmd = self.params.build_node_command(debug)
        kwargs = self.params.get_node_command_kwargs()
        self.log(f"Starting Tendermint: {cmd}\n")
        self._process = (
            subprocess.Popen(  # nosec # pylint: disable=consider-using-with,W1509
                cmd, **kwargs
            )
        )
        self.log("Tendermint process started\n")

    def _start_monitoring_thread(self) -> None:
        """Start a monitoring thread."""
        self._monitoring = StoppableThread(target=self._monitor_tendermint_process)
        self._monitoring.start()

    def start(self, debug: bool = False) -> None:
        """Start a Tendermint node process."""
        self._start_tm_process(debug)
        self._start_monitoring_thread()

    def _stop_tm_process(self) -> None:
        """Stop a Tendermint node process."""
        if self._process is None or self._stopping:
            return

        self._stopping = True
        if platform.system() == "Windows":
            self._win_stop_tm()
        else:
            # this will raise an exception if the process
            # is not terminated within the specified timeout
            self._unix_stop_tm()

        self._stopping = False
        self._process = None
        self.log("Tendermint process stopped\n")

    def _win_stop_tm(self) -> None:
        """Stop a Tendermint node process on Windows."""
        os.kill(self._process.pid, signal.CTRL_C_EVENT)  # type: ignore  # pylint: disable=no-member
        try:
            self._process.wait(timeout=5)  # type: ignore
        except subprocess.TimeoutExpired:  # nosec
            os.kill(self._process.pid, signal.CTRL_BREAK_EVENT)  # type: ignore  # pylint: disable=no-member

    def _unix_stop_tm(self) -> None:
        """Stop a Tendermint node process on Unix."""
        self._process.send_signal(signal.SIGTERM)  # type: ignore
        try:
            self._process.wait(timeout=5)  # type: ignore
        except subprocess.TimeoutExpired:  # nosec
            self.log("Tendermint process did not stop gracefully\n")

        # if the process is still running poll will return None
        poll = self._process.poll()  # type: ignore
        if poll is not None:
            return

        self._process.terminate()  # type: ignore
        self._process.wait(3)  # type: ignore

    def _stop_monitoring_thread(self) -> None:
        """Stop a monitoring process."""
        if self._monitoring is not None:
            self._monitoring.stop()  # set stop event
            self._monitoring.join()

    def stop(self) -> None:
        """Stop a Tendermint node process."""
        self._stop_tm_process()
        self._stop_monitoring_thread()

    @staticmethod
    def _write_to_console(line: str) -> None:
        """Write line to console."""
        sys.stdout.write(str(line))
        sys.stdout.flush()

    def _write_to_file(self, line: str) -> None:
        """Write line to console."""
        with open(self.log_file, "a", encoding=ENCODING) as file:
            file.write(line)

    def log(self, line: str) -> None:
        """Open and write a line to the log file."""
        self._write_to_console(line=line)
        if self.write_to_log:
            self._write_to_file(line=line)

    def prune_blocks(self) -> int:
        """Prune blocks from the Tendermint state"""
        return subprocess.call(  # nosec:
            ["tendermint", "--home", str(self.params.home), "unsafe-reset-all"]
        )

    def reset_genesis_file(
        self, genesis_time: str, initial_height: str, period_count: str
    ) -> None:
        """Reset genesis file."""

        genesis_file = Path(str(self.params.home), "config", "genesis.json")
        genesis_config = json.loads(genesis_file.read_text(encoding=ENCODING))
        genesis_config["genesis_time"] = genesis_time
        genesis_config["initial_height"] = initial_height
        # chain id should be max 50 chars.
        # this means that the app would theoretically break when a 40-digit period is reached
        genesis_config["chain_id"] = f"autonolas-{period_count}"
        genesis_file.write_text(json.dumps(genesis_config, indent=2), encoding=ENCODING)
