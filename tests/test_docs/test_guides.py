# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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

"""This module contains the tests for the guides in the documentation."""
import os
import subprocess  # nosec
import tempfile
from pathlib import Path
from typing import Callable, Dict, List, Optional, Union

import pytest
from aea.test_tools.utils import remove_test_directory

from tests.conftest import ROOT_DIR


SNIPPET_PATH = Path(ROOT_DIR, "docs", "guides", "snippets")

# Some commands need Ctrl + C. For those we use a timeout
DEFAULT_TIMEOUT = 30


class GuideTest:
    """Guide test class.

    Guide tests are expected to find alphabetically ordered txt files containing one command per line.
    Those files will be read, commands grouped, run and checked for errors.
    """

    snippet_path: Path  # path where the snippets live
    execution_path: Path  # root path where the commands are executed
    pre_callbacks: Dict[
        str, Dict[str, Union[str, Callable]]
    ] = {}  # methods executed before a command
    placeholders: Dict[str, str]  # old to new value mapping for palceholder code
    teardown_commands: List[str] = []  # commands that are run on teardown

    def setup(self) -> None:
        """Setup"""
        # Create the execution directory
        if not hasattr(self, "execution_path"):
            self.execution_path = Path(tempfile.TemporaryDirectory().name)

        if not os.path.isdir(self.execution_path):
            os.makedirs(str(self.execution_path))

    def test_run(self) -> None:
        """Run the test"""
        self.load_commands()
        self.run_commands()

    def load_commands(self) -> None:
        """Load commands from the files at the snippet directory"""

        txt_files = sorted(list(self.snippet_path.rglob("*.txt")))

        self.commands = []

        for txt_file in txt_files:
            with open(txt_file, "r", encoding="utf-8") as fp:
                self.commands += [line.strip() for line in fp.readlines()]

    def run_commands(self, commands: Optional[List[str]] = None) -> None:
        """Run commands"""

        print(f"\nSet execution path to in {self.execution_path}")
        os.chdir(self.execution_path)

        if not commands:
            commands = self.commands

        # Command loop
        for cmd in commands:
            try:
                print(f"> {cmd}")

                # Replace placeholders
                for old_value, new_value in self.placeholders.items():
                    cmd = cmd.replace(old_value, new_value)

                # Run pre-callbacks
                pre_callback = self.pre_callbacks.get(cmd, None)
                if pre_callback:
                    print(f">  Running pre-callback: {pre_callback['name']}")
                    pre_callback["callback"]()  # type: ignore

                # Treat cd commands separately
                if cmd.startswith("cd "):
                    os.chdir(cmd[3:])
                    continue

                # Treat pipes separately
                if "|" in cmd:
                    cmds = [i.strip() for i in cmd.split("|")]
                    assert len(cmds) == 2, "Only piping two commands is supported"
                    process = subprocess.Popen(  # nosec
                        cmds[0].split(" "), stdout=subprocess.PIPE
                    )
                    subprocess.check_output(  # nosec
                        cmds[1].split(" "), stdin=process.stdout
                    )
                    process.wait()
                    assert (
                        process.returncode == 0
                    ), f"Guide execution has failed at command '{cmd}'\n{process.returncode}"
                    continue

                # Run command
                process = subprocess.run(cmd.split(" "), timeout=DEFAULT_TIMEOUT)  # type: ignore  # nosec
                assert (
                    process.returncode == 0
                ), f"Guide execution has failed at command '{cmd}'\n{process.returncode}"

            except subprocess.TimeoutExpired:
                # We expect some commands to never end (for example running a service)
                # so we allow for timeouts
                continue

            except Exception as e:
                raise AssertionError(
                    f"Guide execution has failed at command '{cmd}'\n{e}"
                )

    def teardown(self) -> None:
        """Teardown"""
        # Remove execution directory
        remove_test_directory(str(self.execution_path))

        # Run teardown commands
        self.run_commands(self.teardown_commands)


@pytest.mark.e2e
class TestQuickstart(GuideTest):
    """Quickstart guide test"""

    snippet_path = Path(SNIPPET_PATH, "quick_start")
    placeholders = {"<container_id>": "abci0"}
    teardown_commands = ["docker stop abci0 abci1 abci2 abci3 node0 node1 node2 node3"]

    def setup(self) -> None:
        """Setup"""
        super().setup()

        # The quickstart requires that we generate the keys file before building the deployment
        self.pre_callbacks = {
            "autonomy deploy build keys.json --aev": {
                "name": "Create keys",
                "callback": self.write_keys,
            }
        }

    def write_keys(self) -> None:
        """Setup"""
        keys_content = """
[
  {
      "address": "0x15d34AAf54267DB7D7c367839AAf71A00a2C6A65",
      "private_key": "0x47e179ec197488593b187f80a00eb0da91f1b9d0b13f8733639f19c30a34926a"
  },
  {
      "address": "0x9965507D1a55bcC2695C58ba16FB37d819B0A4dc",
      "private_key": "0x8b3a350cf5c34c9194ca85829a2df0ec3153be0318b5e2d3348e872092edffba"
  },
  {
      "address": "0x976EA74026E726554dB657fA54763abd0C3a0aa9",
      "private_key": "0x92db14e403b83dfe3df233f83dfa3a0d7096f21ca9b0d6d6b8d88b2b4ec1564e"
  },
  {
      "address": "0x14dC79964da2C08b23698B3D3cc7Ca32193d9955",
      "private_key": "0x4bbbf85ce3377467afe5d46f804f221813b2bb87f24d81f60f1fcdbf7cbf4356"
  }
]
"""
        keys_file = Path(self.execution_path, "hello_world", "keys.json")

        with open(keys_file, "w", encoding="utf-8") as keys_file:  # type: ignore
            keys_file.write(keys_content)  # type: ignore
