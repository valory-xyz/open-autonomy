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
import tempfile
from contextlib import suppress
from pathlib import Path
from typing import Optional, Tuple

from aea.test_tools.click_testing import CliRunner
from click.testing import Result

from autonomy.cli import cli


class BaseCliTest:
    """Test `autonomy analyse abci` command."""

    t: Path
    cwd: Path
    cli_runner: CliRunner
    cli_options: Tuple[str, ...]

    @classmethod
    def setup(
        cls,
    ) -> None:
        """Setup test."""

        cls.cli_runner = CliRunner()
        cls.cwd = Path.cwd().absolute()
        cls.t = Path(tempfile.mkdtemp())
        cls.t.mkdir(exist_ok=True)

    def run_cli(self, commands: Optional[Tuple[str, ...]] = None) -> Result:
        """Run CLI."""
        if commands is None:
            return self.cli_runner.invoke(cli=cli, args=self.cli_options)

        return self.cli_runner.invoke(cli=cli, args=(*self.cli_options, *commands))

    @classmethod
    def teardown(
        cls,
    ) -> None:
        """Teardown method."""
        os.chdir(cls.cwd)
        with suppress(OSError, FileExistsError, PermissionError):
            shutil.rmtree(str(cls.t))
