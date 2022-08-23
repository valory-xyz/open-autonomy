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

"""Watcher script and wrapper container for agent."""

import os
import shutil
import signal
import subprocess  # nosec
import sys
import time
from glob import glob
from pathlib import Path
from typing import Optional

import requests
from watchdog.events import EVENT_TYPE_CLOSED, FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer


ID = os.environ.get("ID")
MAX_PARTICIPANTS = int(os.environ.get("MAX_PARTICIPANTS", "0"))
ROOT = "/home/ubuntu"
AGENT_DIR = ROOT + "/agent"
PACKAGES_PATH = "/home/ubuntu/packages"
OPEN_AEA_PATH = "/open-aea"
BASE_START_FILE = "/home/ubuntu/start.sh"
TENDERMINT_COM_URL = os.environ.get("TENDERMINT_COM_URL", f"http://node{ID}:8080")


def write(line: str) -> None:
    """Write to console."""
    sys.stdout.write(line)
    sys.stdout.write("\n")
    sys.stdout.flush()


def call_vote() -> None:
    """
    Call vote.

    Since there's a lot of resource sharing between docker containers one of the
    environments can fallback during `base_setup` so to make sure there's no error
    caused by one of the agents left behind this method will help.
    """
    write("Calling vote.")
    with open(f"/logs/{ID}.vote", "w+") as fp:
        fp.write(str(ID))


def wait_for_votes() -> None:
    """Wait for all the agents to finish voting. (see `call_vote` method.)"""
    write("Waiting for votes.")
    votes = 0
    while True:
        votes = len(glob("/logs/*.vote"))
        write(f"Total votes: {votes}, Required votes: {MAX_PARTICIPANTS}")
        if votes == MAX_PARTICIPANTS:
            break
        time.sleep(1)


class AEARunner:
    """AEA Runner."""

    process: Optional[subprocess.Popen]  # nosec

    def __init__(self) -> None:
        """Initialize runner."""

        self.process = None

    @staticmethod
    def restart_tendermint() -> None:
        """Restart respective tendermint node."""
        write("Restarting Tendermint.")
        try:
            response = requests.get(TENDERMINT_COM_URL + "/hard_reset")
            if response.status_code != 200:
                write("Tendermint node not yet available.")
        except requests.exceptions.ConnectionError:
            write("Tendermint node not yet available.")

    def start(
        self,
    ) -> None:
        """Start AEA process."""

        if self.process is not None:
            return
        write("Starting Agent.")
        os.chdir(ROOT)
        if Path(AGENT_DIR).exists():
            shutil.rmtree(AGENT_DIR)
        self.process = subprocess.Popen(  # nosec
            ["/bin/bash", BASE_START_FILE], preexec_fn=os.setsid
        )

    def stop(
        self,
    ) -> None:
        """Stop AEA process."""
        if self.process is None:
            return
        write("Stopping Agent.")
        os.killpg(
            os.getpgid(self.process.pid), signal.SIGTERM
        )  # kills process instantly compared to process.terminate
        self.process = None


class EventHandler(FileSystemEventHandler):
    """Handle file updates."""

    def __init__(
        self, aea_runner: AEARunner, fingerprint_on_restart: bool = True
    ) -> None:
        """Initialize object."""
        super().__init__()
        self.aea = aea_runner
        self.fingerprint_on_restart = fingerprint_on_restart

    @staticmethod
    def fingerprint_item(src_path: str) -> None:
        """Fingerprint items."""
        cwd = os.curdir
        *_path, vendor, item_type, item_name, _ = src_path.split(os.path.sep)
        vendor_dir_str = os.path.sep.join([*_path, vendor])
        os.chdir(vendor_dir_str)
        subprocess.call(  # nosec
            [
                "python3",
                "-m",
                "aea.cli",
                "fingerprint",
                item_type[:-1],
                f"{vendor}/{item_name}",
            ]
        )
        os.chdir(cwd)

    @staticmethod
    def clean_up() -> None:
        """Clean up from previous run."""
        os.chdir(ROOT)
        if Path(AGENT_DIR).exists():
            write("removing aea dir.")
            shutil.rmtree(AGENT_DIR)

    def on_any_event(self, event: FileSystemEvent) -> None:
        """This method reloads the agent when a change is detected in *.py file."""
        if (
            not event.is_directory
            and event.event_type == EVENT_TYPE_CLOSED
            and event.src_path.endswith(".py")
        ):
            write("Change detected.")
            self.clean_up()
            if self.fingerprint_on_restart:
                self.fingerprint_item(event.src_path)

            self.aea.stop()
            self.aea.restart_tendermint()
            self.aea.start()


if __name__ == "__main__":
    aea_runner = AEARunner()

    package_observer = Observer()
    package_observer.schedule(
        EventHandler(aea_runner=aea_runner), PACKAGES_PATH, recursive=True
    )

    open_aea_observer = Observer()
    open_aea_observer.schedule(
        EventHandler(aea_runner=aea_runner, fingerprint_on_restart=False),
        OPEN_AEA_PATH,
        recursive=True,
    )

    try:
        aea_runner.start()
        package_observer.start()
        open_aea_observer.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        aea_runner.stop()
        package_observer.stop()
        open_aea_observer.stop()

    open_aea_observer.join()
    package_observer.join()
