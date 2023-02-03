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

"""Database schemas and helpers"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Iterator, List, Optional

from autonomy.analyse.logs.base import LogRow


TIMESTAMP = "timestamp"
LOG_LEVEL = "log_level"
MESSAGE = "message"

QUERY_CREATE_LOG_TABLE = (
    "CREATE TABLE {agent} (timestamp TIMESTAMP, log_level TEXT, message TEXT);"
)
QUERY_CHECK_TABLE_EXISTS = (
    "SELECT name FROM sqlite_master WHERE type='table' AND name=?;"
)
QUERY_DROP_TABLE = "DROP TABLE {agent};"
QUERY_INSERT_LOG = "INSERT INTO {agent} VALUES (?, ?, ?);"


class AgentLogsDB:
    """Logs DB"""

    _db: sqlite3.Connection

    def __init__(self, agent: str, file: Path) -> None:
        """Initialize object."""

        self.agent = agent
        self._db_path = file
        self._db = sqlite3.connect(
            database=self._db_path,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
        )

    def select(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[LogRow]:
        """Build select query."""

        query = f"SELECT * from {self.agent}"
        paramaters = []

        def _append_condition(_query: str, condition: str) -> str:
            """Append condition at the end of the query."""
            if "WHERE" in query:
                return query + " AND " + condition
            return query + " WHERE " + condition

        if start_time is not None:
            query = _append_condition(_query=query, condition=f"{TIMESTAMP}>?")
            paramaters.append(start_time)

        if end_time is not None:
            query = _append_condition(_query=query, condition=f"{TIMESTAMP}<?")
            paramaters.append(end_time)

        query += ";"
        return self.cursor.execute(query, paramaters).fetchall()

    @property
    def cursor(self) -> sqlite3.Cursor:
        """Creates and returns a database cursor."""
        return self._db.cursor()

    def exists(self) -> bool:
        """Check if table already exists."""

        return (
            self.cursor.execute(QUERY_CHECK_TABLE_EXISTS, (self.agent,)).fetchone()
            is not None
        )

    def delete(self) -> "AgentLogsDB":
        """Delete table"""
        self.cursor.execute(QUERY_DROP_TABLE.format(agent=self.agent))
        return self

    def create(self, reset: bool = False) -> "AgentLogsDB":
        """Create agent table"""

        exists = self.exists()
        if exists and not reset:
            return self

        if exists and reset:
            self.delete()

        self.cursor.execute(QUERY_CREATE_LOG_TABLE.format(agent=self.agent))
        self._db.commit()

        return self

    def insert_one(
        self, timestamp: datetime, log_level: str, message: str
    ) -> "AgentLogsDB":
        """Insert a record"""
        self.cursor.execute(
            QUERY_INSERT_LOG,
            (timestamp, log_level, message),
        )
        self._db.commit()

        return self

    def insert_many(
        self,
        logs: Iterator[LogRow],
    ) -> "AgentLogsDB":
        """Insert a record"""
        for timestamp, log_level, message in logs:
            self.cursor.execute(
                QUERY_INSERT_LOG.format(agent=self.agent),
                (timestamp, log_level, message),
            )
        self._db.commit()
        return self
