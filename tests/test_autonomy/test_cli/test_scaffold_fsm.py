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

"""Test 'scaffold fsm' subcommand."""
from pathlib import Path
from typing import Tuple

from aea.configurations.constants import PACKAGES, SKILLS
from aea.test_tools.test_cases import AEATestCaseEmpty

# trigger population of autonomy commands
import autonomy.cli.core  # noqa

from tests.conftest import ROOT_DIR


class TestScaffoldFSM(AEATestCaseEmpty):
    """Test `scaffold fsm` subcommand."""

    fsm_spec_file = (
        Path(PACKAGES)
        / "valory"
        / SKILLS
        / "registration_abci"
        / "fsm_specification.yaml"
    )
    cli_options: Tuple[str, ...] = (
        "--registry-path",
        str(Path(ROOT_DIR) / Path(PACKAGES)),
        "scaffold",
        "fsm",
        "myskill",
        "--local",
        "--spec",
    )
    packages_dir: Path

    def test_run(
        self,
    ) -> None:
        """Test run."""
        self.set_agent_context(self.agent_name)
        path_to_spec_file = Path(ROOT_DIR) / self.fsm_spec_file
        args = [*self.cli_options, path_to_spec_file]
        result = self.run_cli_command(*args, cwd=self._get_cwd())
        assert result.exit_code == 0
