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

"""Test log parser."""

import re
import tempfile
from pathlib import Path
from typing import Tuple

from tests.test_autonomy.test_cli.base import BaseCliTest


TEST_LOGS = """[2022-04-14 17:45:43,962] [INFO] [agent] Entered in the 'registration_startup' round for period 0
[2022-04-14 17:44:43,323] [INFO] [agent] Entered in the 'registration_startup' behaviour state
[2022-04-14 17:45:41,128] [INFO] [agent] 'registration_startup' round is done with event: Event.FAST_FORWARD
[2022-04-14 17:45:41,128] [INFO] [agent] scheduling timeout of 7.0 seconds for event Event.ROUND_TIMEOUT with deadline 2022-04-14 17:45:46.527881
[2022-04-14 17:45:41,131] [INFO] [agent] Entered in the 'collect_observation' round for period 0
[2022-04-14 17:45:41,136] [INFO] [agent] Entered in the 'collect_observation' behaviour state
[2022-04-14 17:45:42,509] [INFO] [agent] 'collect_observation' round is done with event: Event.DONE
[2022-04-14 17:45:42,511] [INFO] [agent] scheduling timeout of 7.0 seconds for event Event.ROUND_TIMEOUT with deadline 2022-04-14 17:45:47.856572
"""

TEST_LOGS_WITH_MISSING_EVENTS = """
[2022-04-14 17:45:42,512] [INFO] [agent] Entered in the 'estimate_consensus' round for period 0
[2022-04-14 17:45:42,514] [INFO] [agent] Entered in the 'estimate' behaviour state
[2022-04-14 17:45:43,959] [INFO] [agent] 'estimate_consensus' round is done with event: Event.DONE
[2022-04-14 17:45:43,960] [INFO] [agent] scheduling timeout of 7.0 seconds for event Event.ROUND_TIMEOUT with deadline 2022-04-14 17:45:49.269590
[2022-04-14 17:45:43,962] [INFO] [agent] Entered in the 'tx_hash' round for period 0
[2022-04-14 17:45:43,968] [INFO] [agent] Entered in the 'tx_hash' behaviour state
[2022-04-14 17:45:46,927] [INFO] [agent] scheduling timeout of 7.0 seconds for event Event.ROUND_TIMEOUT with deadline 2022-04-14 17:45:52.089382
"""

TEST_LOGS_ERROR = """[2022-04-14 17:45:43,962] [INFO] [agent] Entered in the 'registration_startup' round for period 0
E AssertionError: error
"""

TEST_LOGS_WITH_EVENT = """
[2022-04-14 17:45:43,959] [INFO] [agent] 'estimate_consensus' round is done with event: Event.DONE
"""


EXPECTED_OUTPUT = (
    "agent         period: 0     round: registration_startup                      event: Event.FAST_FORWARD\n"
    "agent         period: 0     round: collect_observation                       event: Event.DONE\n"
    "\n"
    "ERRORS:\n"
)

EXPECTED_OUTPUT_WITH_MISSING_EVENTS = (
    "agent         period: 0     round: estimate_consensus                        event: Event.DONE\n"
    "agent         period: 0     round: tx_hash                                   event: N/A\n"
    "\n"
    "ERRORS:\n"
)

EXPECTED_OUTPUT_ERROR = (
    "agent         period: 0     round: registration_startup                      event: N/A\n"
    "\n"
    "ERRORS:\n"
    "error\n\n"
)

EXPECTED_OUTPUT_EVENT = "\nERRORS:\n"


ANSI_COLOR_CHARACTERS_REGEX = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


class TestLogParser(BaseCliTest):
    """Test log parser."""

    cli_options: Tuple[str, ...] = ("analyse", "abci", "logs")

    def _check_output(self, logs: str, expected_output: str) -> None:
        """Check outputs."""

        with tempfile.TemporaryDirectory() as temp:
            log_file = Path(temp) / "log.txt"
            log_file.write_text(logs, encoding="utf-8")
            result = self.run_cli((str(log_file),))
            output = ANSI_COLOR_CHARACTERS_REGEX.sub("", result.stdout)
            assert output == expected_output

    def test_parser(
        self,
    ) -> None:
        """Test log parser."""

        self._check_output(TEST_LOGS, EXPECTED_OUTPUT)

    def test_parser_with_missing_events(
        self,
    ) -> None:
        """Test log parser."""

        self._check_output(
            TEST_LOGS_WITH_MISSING_EVENTS, EXPECTED_OUTPUT_WITH_MISSING_EVENTS
        )

    def test_parser_errors(
        self,
    ) -> None:
        """Test log parser."""

        self._check_output(TEST_LOGS_ERROR, EXPECTED_OUTPUT_ERROR)

    def test_parser_event(
        self,
    ) -> None:
        """Test log parser."""

        self._check_output(TEST_LOGS_WITH_EVENT, EXPECTED_OUTPUT_EVENT)
