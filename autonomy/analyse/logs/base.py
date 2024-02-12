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

"""Tools for analysing logs."""


import re
from datetime import datetime
from typing import Tuple


LOGS_DB = "logs.db"
TIME_FORMAT = "%Y-%m-%d %H:%M:%S,%f"
TIMESTAMP_REGEX = re.compile(r"^(\[(\d+-\d+-\d+ \d+:\d+:\d+,\d+)\])")
LOG_ROW_REGEX = re.compile(
    r"\[(\d+-\d+-\d+ \d+:\d+:\d+,\d+)\] \[([A-Z]+)\]( \[agent\])? ((.|\n)*)"
)
ENTER_BEHAVIOUR_REGEX = re.compile(r"Entered in the \'([a-z_]+)\' behaviour")
ENTER_ROUND_REGEX = re.compile(r"Entered in the \'([a-z_]+)\' round for period (\d+)")
EXIT_ROUND_REGEX = re.compile(r"'([a-z_]+)' round is done with event: (Event\.[A-Z_]+)")

LogRow = Tuple[datetime, str, str, int, str, str]
