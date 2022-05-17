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

"""Tests for abci sub command."""


import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Tuple

from aea.test_tools.click_testing import CliRunner
from click.testing import Result

from aea_swarm.cli import cli


TEST_LOGS = """[2022-04-14 17:44:43,323] [INFO] [agent] Entered in the 'registration_startup' behaviour state
[2022-04-14 17:45:41,128] [INFO] [agent] 'registration_startup' round is done with event: Event.FAST_FORWARD
[2022-04-14 17:45:41,128] [INFO] [agent] scheduling timeout of 7.0 seconds for event Event.ROUND_TIMEOUT with deadline 2022-04-14 17:45:46.527881
[2022-04-14 17:45:41,131] [INFO] [agent] Entered in the 'collect_observation' round for period 0
[2022-04-14 17:45:41,136] [INFO] [agent] Entered in the 'collect_observation' behaviour state
[2022-04-14 17:45:42,509] [INFO] [agent] 'collect_observation' round is done with event: Event.DONE
[2022-04-14 17:45:42,511] [INFO] [agent] scheduling timeout of 7.0 seconds for event Event.ROUND_TIMEOUT with deadline 2022-04-14 17:45:47.856572
[2022-04-14 17:45:42,512] [INFO] [agent] Entered in the 'estimate_consensus' round for period 0
[2022-04-14 17:45:42,514] [INFO] [agent] Entered in the 'estimate' behaviour state
[2022-04-14 17:45:43,959] [INFO] [agent] 'estimate_consensus' round is done with event: Event.DONE
[2022-04-14 17:45:43,960] [INFO] [agent] scheduling timeout of 7.0 seconds for event Event.ROUND_TIMEOUT with deadline 2022-04-14 17:45:49.269590
[2022-04-14 17:45:43,962] [INFO] [agent] Entered in the 'tx_hash' round for period 0
[2022-04-14 17:45:43,968] [INFO] [agent] Entered in the 'tx_hash' behaviour state
[2022-04-14 17:45:46,927] [INFO] [agent] 'tx_hash' round is done with event: Event.DONE
[2022-04-14 17:45:46,927] [INFO] [agent] scheduling timeout of 7.0 seconds for event Event.ROUND_TIMEOUT with deadline 2022-04-14 17:45:52.089382
[2022-04-14 17:45:46,927] [INFO] [agent] Entered in the 'randomness_transaction_submission' round for period 0
[2022-04-14 17:45:46,930] [INFO] [agent] Entered in the 'randomness_transaction_submission' behaviour state
[2022-04-14 17:45:51,155] [INFO] [agent] scheduling timeout of 7.0 seconds for event Event.ROUND_TIMEOUT with deadline 2022-04-14 17:45:56.464843
[2022-04-14 17:45:51,155] [INFO] [agent] Entered in the 'select_keeper_transaction_submission_a' round for period 0
[2022-04-14 17:45:51,156] [INFO] [agent] Entered in the 'select_keeper_transaction_submission_a' behaviour state
[2022-04-14 17:45:52,580] [INFO] [agent] 'select_keeper_transaction_submission_a' round is done with event: Event.DONE
[2022-04-14 17:45:52,581] [INFO] [agent] scheduling timeout of 7.0 seconds for event Event.ROUND_TIMEOUT with deadline 2022-04-14 17:45:57.940520
[2022-04-14 17:45:52,581] [INFO] [agent] Entered in the 'collect_signature' round for period 0
[2022-04-14 17:45:52,585] [INFO] [agent] Entered in the 'sign' behaviour state
[2022-04-14 17:45:53,846] [INFO] [agent] 'collect_signature' round is done with event: Event.DONE
[2022-04-14 17:45:53,847] [INFO] [agent] scheduling timeout of 7.0 seconds for event Event.ROUND_TIMEOUT with deadline 2022-04-14 17:45:59.266122
[2022-04-14 17:45:53,848] [INFO] [agent] Entered in the 'finalization' round for period 0
[2022-04-14 17:45:53,850] [INFO] [agent] Entered in the 'finalize' behaviour state
[2022-04-14 17:45:55,434] [INFO] [agent] 'finalization' round is done with event: Event.DONE
[2022-04-14 17:45:55,436] [INFO] [agent] Entered in the 'validate_transaction' round for period 0
[2022-04-14 17:45:55,438] [INFO] [agent] Entered in the 'validate_transaction' behaviour state
[2022-04-14 17:46:00,891] [INFO] [agent] 'validate_transaction' round is done with event: Event.DONE
[2022-04-14 17:46:00,898] [INFO] [agent] scheduling timeout of 305 seconds for event Event.RESET_AND_PAUSE_TIMEOUT with deadline 2022-04-14 17:51:04.2473390"""


EXPECTED_OUTPUT = """agent         period: 0     round: collect_observation                       event: Event.DONE
agent         period: 0     round: estimate_consensus                        event: Event.DONE
agent         period: 0     round: tx_hash                                   event: Event.DONE
agent         period: 0     round: randomness_transaction_submission         event: N/A
agent         period: 0     round: select_keeper_transaction_submission_a    event: Event.DONE
agent         period: 0     round: collect_signature                         event: Event.DONE
agent         period: 0     round: finalization                              event: Event.DONE
agent         period: 0     round: validate_transaction                      event: Event.DONE

ERRORS:
"""


class BaseAbciTest:
    """Test `swarm analyse abci` command."""

    cli_options: Tuple[str, ...] = ("analyse", "abci")
    cli_runner: CliRunner
    cwd: Path
    t: Path

    @classmethod
    def setup(
        cls,
    ) -> None:
        """Setup test."""

        cls.cli_runner = CliRunner()
        cls.cwd = Path.cwd().absolute()
        cls.t = Path(tempfile.mkdtemp())

    def run_cli(self, commands: Tuple[str, ...]) -> Result:
        """Run CLI."""
        return self.cli_runner.invoke(cli=cli, args=(*self.cli_options, *commands))

    @classmethod
    def teardown(
        cls,
    ) -> None:
        """Teardown method."""
        shutil.rmtree(str(cls.t))


class TestDocstrings:
    """Test `swarm analyse abci docstrings`."""


class TestLogParser(BaseAbciTest):
    """Test log parser."""

    log_file: Path

    @classmethod
    def setup(
        cls,
    ) -> None:
        """Setup class."""
        super().setup()

        os.chdir(cls.t)
        cls.log_file = cls.t / "log.txt"
        cls.log_file.write_text(TEST_LOGS, encoding="utf-8")

    def test_parser(
        self,
    ) -> None:
        """Test log parser."""

        result = self.run_cli(("logs", str(self.log_file)))
        output = re.sub(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])", "", result.stdout)

        (Path("/root/temp.l").write_text(output))

        assert output == EXPECTED_OUTPUT
