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

"""Log streams"""


import re
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Generator, List, Optional, TextIO, Tuple, cast

from autonomy.analyse.logs.base import (
    ENTER_BEHAVIOUR_REGEX,
    ENTER_ROUND_REGEX,
    LOG_ROW_REGEX,
    LogRow,
    TIMESTAMP_REGEX,
    TIME_FORMAT,
)
from autonomy.analyse.logs.db import AgentLogsDB


class LogCollection(ABC):
    """Collection of logs."""

    def __init__(self) -> None:
        """Initialize object."""

        self.agents = self.get_avilable_agents()
        self.n_agents = len(self.agents)

    @abstractmethod
    def get_avilable_agents(self) -> List[str]:
        """Returns a list of agent names."""

    @abstractmethod
    def create_agent_db(
        self,
        agent: str,
        db: AgentLogsDB,
        reset: bool = False,
    ) -> "LogCollection":
        """Create logs database."""

    @staticmethod
    def get_next_log_block(
        fp: TextIO,
        prev_line: Optional[str],
    ) -> Tuple[Optional[str], Optional[str]]:
        """Get next log block."""
        if prev_line is None:
            return None, None

        line = prev_line
        while True:
            _line = fp.readline()
            if _line == "":
                return prev_line, None
            if TIMESTAMP_REGEX.match(_line) is not None:
                return line, _line
            line += _line

    @classmethod
    def parse(cls, file: Path) -> Generator[LogRow, None, None]:
        """Parse logs and yield rows."""
        with file.open(mode="r", encoding="utf-8") as fp:
            prev_line: Optional[str] = fp.readline()
            current_period = 0
            current_round = "agent_startup"
            current_behaviour = "agent_startup"
            while True:
                line, prev_line = cls.get_next_log_block(fp=fp, prev_line=prev_line)
                if line is None and prev_line is None:
                    break

                match = LOG_ROW_REGEX.match(string=cast(str, line))
                _timestamp, log_level, _, log_block, _ = cast(re.Match, match).groups()
                timestamp = datetime.strptime(_timestamp, TIME_FORMAT)
                match = ENTER_BEHAVIOUR_REGEX.match(string=log_block)
                if match is not None:
                    (current_behaviour,) = match.groups()

                match = ENTER_ROUND_REGEX.match(string=log_block)
                if match is not None:
                    (current_round, current_period) = cast(
                        Tuple[str, int], match.groups()
                    )

                yield timestamp, log_level, log_block, current_period, current_round, current_behaviour


class FromDirectory(LogCollection):
    """Log stream from directory."""

    def __init__(self, directory: Path) -> None:
        """Initialize object."""
        self.directory = directory

        super().__init__()

    def get_avilable_agents(self) -> List[str]:
        """Returns a list of agent names."""
        return list(
            map(lambda x: x.name.replace(".txt", ""), self.directory.glob("aea_*.txt"))
        )

    def create_agent_db(
        self,
        agent: str,
        db: AgentLogsDB,
        reset: bool = False,
    ) -> "FromDirectory":
        """Create logs table for agent."""

        log_file = self.directory / f"{agent}.txt"
        db.create(reset=reset)
        db.insert_many(
            logs=self.parse(
                file=log_file,
            )
        )
        return self
