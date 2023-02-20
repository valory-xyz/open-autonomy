# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023 Valory AG
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


"""Tests for the `autonomy analyse logs` command"""

import contextlib
import os
from typing import Tuple

from autonomy.analyse.logs.base import LOGS_DB
from autonomy.deploy.constants import WARNING

from tests.conftest import DATA_DIR
from tests.test_autonomy.test_cli.base import BaseCliTest


LOGS_DIR = DATA_DIR / "logs"
LOGS_DB_FILE = LOGS_DIR / LOGS_DB

AVAILABLE_ROUNDS = (
    "registration_startup",
    "new_tokens",
    "leaderboard_observation",
    "image_code_calculation",
    "image_generation",
    "db_update",
    "reset_and_pause",
)


class BaseLogAnalyserTest(BaseCliTest):
    """Base test class for the log analyser."""

    cli_options: Tuple[str, ...] = ("analyse", "logs")

    @classmethod
    def teardown_class(cls) -> None:
        """Teardown class."""

        with contextlib.suppress(PermissionError):
            if LOGS_DB_FILE.exists():
                os.remove(LOGS_DB_FILE)


class TestAnalyseLogs(BaseLogAnalyserTest):
    """Test `autonomy analyse logs`"""

    def test_agent_options(self) -> None:
        """Test print agent options."""

        result = self.run_cli(commands=("--from-dir", str(LOGS_DIR)))

        assert result.exit_code == 1, result.stdout
        assert "Available agents: ['aea_0']" in result.output

    def test_logs_table(self) -> None:
        """Test print agent options."""

        result = self.run_cli(commands=("--from-dir", str(LOGS_DIR), "-a", "aea_0"))

        assert result.exit_code == 0, result.stdout
        assert "Entered in the 'registration_startup' behaviour" in result.output

    def test_log_level_filter(self) -> None:
        """Test print agent options."""

        result = self.run_cli(
            commands=(
                "--from-dir",
                str(LOGS_DIR),
                "-a",
                "aea_0",
                "--log-level",
                WARNING,
            )
        )

        assert result.exit_code == 0, result.stdout
        assert "[WARNING]" in result.output
        assert "[INFO]" not in result.output

    def test_start_time_filter(self) -> None:
        """Test print agent options."""

        result = self.run_cli(
            commands=(
                "--from-dir",
                str(LOGS_DIR),
                "-a",
                "aea_0",
                "--start-time",
                "2023-01-23 15:39:20,424",  # actual timestamp from the logs file
            )
        )

        assert result.exit_code == 0, result.stdout

        # actual timestamps from the logs file
        assert "2023-01-23 15:39:21.441000" in result.output
        assert "2023-01-23 15:39:19.686000" not in result.output

    def test_end_time_filter(self) -> None:
        """Test print agent options."""

        result = self.run_cli(
            commands=(
                "--from-dir",
                str(LOGS_DIR),
                "-a",
                "aea_0",
                "--end-time",
                "2023-01-23 15:39:20,424",  # actual timestamp from the logs file
            )
        )

        assert result.exit_code == 0, result.stdout

        # actual timestamps from the logs file
        assert "2023-01-23 15:39:21.441000" not in result.output
        assert "2023-01-23 15:39:19.686000" in result.output

    def test_period_filter(self) -> None:
        """Test print agent options."""

        result = self.run_cli(
            commands=(
                "--from-dir",
                str(LOGS_DIR),
                "-a",
                "aea_0",
                "--period",
                "1",
            )
        )

        assert result.exit_code == 0, result.stdout

        assert "period 0" not in result.output
        assert "period 1" in result.output
        assert "period 2" not in result.output

    def test_round_filter(self) -> None:
        """Test print agent options."""

        round_name = "new_tokens"
        result = self.run_cli(
            commands=(
                "--from-dir",
                str(LOGS_DIR),
                "-a",
                "aea_0",
                "--round",
                round_name,
            )
        )
        assert result.exit_code == 0, result.stdout

        assert round_name in result.output
        assert all([_round not in result.output for _round in AVAILABLE_ROUNDS[2:]])

    def test_include_regex_filter(self) -> None:
        """Test print agent options."""

        result = self.run_cli(
            commands=(
                "--from-dir",
                str(LOGS_DIR),
                "-a",
                "aea_0",
                "-ir",
                ".*Entered in the.*",
            )
        )
        assert result.exit_code == 0, result.stdout
        assert "Entered in the" in result.output
        assert "arrived block with timestamp" not in result.output

    def test_exclude_regex_filter(self) -> None:
        """Test print agent options."""

        result = self.run_cli(
            commands=(
                "--from-dir",
                str(LOGS_DIR),
                "-a",
                "aea_0",
                "-er",
                ".*Entered in the.*",
            )
        )
        assert result.exit_code == 0, result.stdout
        assert "Entered in the" not in result.output
        assert "arrived block with timestamp" in result.output

    def test_fsm_path(self) -> None:
        """Test print agent options."""

        result = self.run_cli(
            commands=(
                "--from-dir",
                str(LOGS_DIR),
                "-a",
                "aea_0",
                "--fsm",
            )
        )
        assert result.exit_code == 0, result.stdout
        assert all(
            [
                f"|_ {_round} | Event.DONE" in result.output
                for _round in AVAILABLE_ROUNDS
            ]
        )

    def test_empty_logs_dir(self) -> None:
        """Test print agent options."""

        result = self.run_cli(
            commands=(
                "--from-dir",
                str(LOGS_DIR.parent),
                "-a",
                "aea_0",
                "--fsm",
            )
        )
        assert result.exit_code == 1, result.stdout
        assert "Cannot find agent log data in" in result.output
