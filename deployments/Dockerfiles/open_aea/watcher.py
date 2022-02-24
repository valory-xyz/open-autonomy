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
import subprocess
import sys
import time
from glob import glob
from pathlib import Path
from typing import Optional

import requests
from watchdog.events import EVENT_TYPE_CLOSED, FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer


ID = os.environ.get("ID")
MAX_PARTICIPANTS = int(os.environ.get("MAX_PARTICIPANTS"))
ROOT = "/home/ubuntu"
AGENT_DIR = ROOT + "agent"
PACKAGES_PATH = "/home/ubuntu/packages"
BASE_START_FILE = "/home/ubuntu/start.sh"
ENV_SETUP_FILE = "/home/ubuntu/env_start.sh"
TENDERMINT_COM_URL = os.environ.get("TENDERMINT_COM_URL", f"http://node{ID}:8080")


def write(line: str) -> None:
    """Write to console."""
    sys.stdout.write(line)
    sys.stdout.write("\n")
    sys.stdout.flush()


def base_setup() -> None:
    """
    This script will be called only once at the startup. This can be configured
    in `env_script_templates.py` using `BASE_SETUP`.
    """
    subprocess.call(["/bin/bash", ENV_SETUP_FILE])
    return


def call_vote() -> None:
    """
    Since there's a lot of resource sharing between docker containers one of the
    environments can fallback during `base_setup` so to make sure there's no error
    caused by one of the agents left behind this method will help.
    """
    with open(f"/logs/{ID}.vote", "w+") as fp:
        fp.write(str(ID))


def wait_for_votes() -> None:
    """
    Wait for all the agents to finish voting. (see `call_vote` method.)
    """

    votes = 0
    while True:
        votes = len(glob("/logs/*.vote"))
        write(f"Total votes: {votes}, Required votes: {MAX_PARTICIPANTS}")
        if votes == MAX_PARTICIPANTS:
            break
        time.sleep(1)


class AEARunner:
    """AEA Runner."""

    process: Optional[subprocess.Popen]

    def __init__(self) -> None:
        """Initialize runner."""

        self.process = None

    @staticmethod
    def restart_tendermint() -> None:
        """Restart respective tendermint node."""
        write("Restarting Tendermint.")
        response = requests.get(TENDERMINT_COM_URL + "/hard_reset")
        assert response.status_code == 200

    def start(
        self,
    ) -> None:
        """Start AEA process."""

        if self.process is not None:
            return
        write("Restarting Agent.")
        os.chdir(ROOT)
        if Path(AGENT_DIR).exists():
            shutil.rmtree(AGENT_DIR)
        self.process = subprocess.Popen(["/bin/bash", BASE_START_FILE], preexec_fn=os.setsid)

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


class RestartAEA(FileSystemEventHandler):
    """Handle file updates."""

    def __init__(self) -> None:
        """Initialize object."""
        super().__init__()
        self.aea = AEARunner()
        self.aea.start()

    @staticmethod
    def fingerprint_item(src_path: str) -> None:
        """Fingerprint items."""
        cwd = os.curdir
        *_path, vendor, item_type, item_name, _ = src_path.split(os.path.sep)
        vendor_dir_str = os.path.sep.join([*_path, vendor])
        os.chdir(vendor_dir_str)
        subprocess.call(
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

    def on_any_event(self, event: FileSystemEvent):
        """
        This method reloads the agent when a change is detected in `hashes.csv`
        file.
        """
        if (
            not event.is_directory
            and event.event_type == EVENT_TYPE_CLOSED
            and event.src_path.endswith(".py")
        ):

            write("Change detected.")
            self.fingerprint_item(event.src_path)
            self.aea.stop()
            self.aea.restart_tendermint()
            self.aea.start()


if __name__ == "__main__":
    write("Calling base setup.")
    base_setup()
    write("Calling vote.")
    # call_vote()
    # write("Waiting for votes.")
    # wait_for_votes()
    event_handler = RestartAEA()
    observer = Observer()
    observer.schedule(event_handler, PACKAGES_PATH, recursive=True)
    try:
        observer.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
