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

"""Test base."""

import os
import shutil
import subprocess  # nosec
import sys
import tempfile
from contextlib import suppress
from pathlib import Path
from typing import Optional, Sequence, Tuple

import pytest
from _pytest.capture import CaptureFixture  # type: ignore
from aea.test_tools.click_testing import CliRunner
from click.testing import Result

from autonomy.cli import cli


class BaseCliTest:
    """Test `autonomy analyse abci` command."""

    @pytest.fixture(autouse=True)
    def set_capfd_on_cli_runner(self, capfd: CaptureFixture) -> None:
        """Set pytest capfd on CLI runner"""
        self.cli_runner.capfd = capfd

    t: Path
    cwd: Path
    cli_runner: CliRunner
    cli_options: Tuple[str, ...]

    @classmethod
    def setup_class(cls) -> None:
        """Setup test class."""
        cls.cli_runner = CliRunner()
        cls.cwd = Path.cwd().absolute()

    def setup(
        self,
    ) -> None:
        """Setup test."""
        self.t = Path(tempfile.mkdtemp())

    def run_cli(self, commands: Optional[Tuple[str, ...]] = None) -> Result:
        """Run CLI."""
        if commands is None:
            return self.cli_runner.invoke(cli=cli, args=self.cli_options)

        return self.cli_runner.invoke(cli=cli, args=(*self.cli_options, *commands))

    def run_cli_subprocess(
        self, commands: Sequence[str], timeout: float = 60.0
    ) -> Tuple[int, str, str]:
        """Run CLI using subprocess."""
        process = subprocess.Popen(  # nosec
            [sys.executable, "-m", "autonomy.cli"]
            + list(self.cli_options)
            + list(commands),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout_bytes, stderr_bytes = process.communicate(timeout=timeout)
        stdout, stderr = stdout_bytes.decode(), stderr_bytes.decode()

        # for Windows
        if sys.platform == "win32":
            stdout = stdout.replace("\r", "")
            stderr = stderr.replace("\r", "")
        return process.returncode, stdout, stderr

    def teardown(
        self,
    ) -> None:
        """Teardown method."""
        os.chdir(self.cwd)
        with suppress(OSError, FileExistsError, PermissionError):
            shutil.rmtree(str(self.t))
