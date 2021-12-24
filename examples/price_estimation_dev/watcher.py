import os
import signal
import subprocess
import sys
import time
from glob import glob
from typing import Optional

import requests
from watchdog.events import EVENT_TYPE_CLOSED, FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer


ID = os.environ.get("ID")
MAX_PARTICIPANTS = int(os.environ.get("MAX_PARTICIPANTS"))
PACKAGES_PATH = "/packages/hashes.csv"
BASH_FILE = f"/configure_agents/abci{ID}.sh"
BASE_SETUP_FILE = f"/configure_agents/base_setup.sh"
TENDERMINT_COM_URL = os.environ.get("TENDERMINT_COM_URL", f"http://node{ID}:8080")


def write(line: str) -> None:
    """Write to console."""
    sys.stdout.write(line)
    sys.stdout.write("\n")
    sys.stdout.flush()


def base_setup() -> None:
    """Base setup."""
    subprocess.call(["/bin/bash", BASE_SETUP_FILE])


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
        response = requests.get(TENDERMINT_COM_URL + "/hard_reset")
        assert response.status_code == 200

    def start(
        self,
    ) -> None:
        """Start AEA process."""

        if self.process is not None:
            return

        self.process = subprocess.Popen(["/bin/bash", BASH_FILE], preexec_fn=os.setsid)

    def stop(
        self,
    ) -> None:
        """Stop AEA process."""
        if self.process is None:
            return

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

    def on_any_event(self, event: FileSystemEvent):
        """Event handler."""
        if not event.is_directory and event.event_type == EVENT_TYPE_CLOSED:
            write("Change detected.")
            write("Stopping Agent.")
            self.aea.stop()
            write("Restarting Tendermint.")
            self.aea.restart_tendermint()
            write("Restarting Agent.")
            self.aea.start()


if __name__ == "__main__":
    write("Calling base setup.")
    base_setup()
    write("Calling vote.")
    call_vote()
    write("Waiting for votes.")
    wait_for_votes()
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
