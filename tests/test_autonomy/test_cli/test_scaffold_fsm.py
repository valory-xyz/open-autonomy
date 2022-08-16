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

from autonomy.cli import cli
from autonomy.test_tools.helpers.base import cd

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
    cli_options: Tuple[str, ...] = ("scaffold", "fsm", "myskill", "--spec")
    packages_dir: Path

    def test_run(
        self,
    ) -> None:
        """Test run."""
        self.set_agent_context(self.agent_name)
        path_to_spec_file = Path(ROOT_DIR) / self.fsm_spec_file
        with cd(self._get_cwd()):
            result = self.runner.invoke(
                cli=cli, args=self.cli_options + (path_to_spec_file,)
            )

        assert result.exit_code == 0, result.stdout
