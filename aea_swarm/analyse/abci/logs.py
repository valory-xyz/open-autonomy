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

"""Tools to parse agent logs."""

import re
from enum import Enum
from typing import Any, Dict


PERIOD_REGEX = r".*\[(?P<agent_id>.*)\] Entered in the '(?P<round_id>.*)' round for period (?P<period>\d+)"
EVENT_REGEX = r".*\[(?P<agent_id>.*)\]\s'(?P<round_id>.*)' round is done with event: (?P<event_id>.*)"
ERROR_REGEX = r".*E\s+AssertionError:\s(?P<message>.*)"


class Color(Enum):
    """Standard terminal color codes."""

    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    RESET = "\033[39m"


AGENT_COLORS = [
    Color.BLUE.value,
    Color.MAGENTA.value,
    Color.CYAN.value,
    Color.WHITE.value,
]


def parse_file(  # pylint: disable=too-many-locals
    filename: str,
) -> None:
    """Parses a log file, e2e or single agent."""
    periods: Dict[str, Any] = {}
    errors = []
    _id = 0
    with open(filename, "r", encoding="utf-8") as log:
        for line in log.readlines():

            m = re.match(PERIOD_REGEX, line)
            if m:
                agent_id = m.groupdict()["agent_id"]
                if agent_id not in periods.keys():
                    periods[agent_id] = []
                periods[agent_id].append(m.groupdict())
                continue

            m = re.match(EVENT_REGEX, line)
            if m:
                agent_id = m.groupdict()["agent_id"]
                if agent_id not in periods.keys():
                    periods[agent_id] = []
                periods[agent_id].append(m.groupdict())
                continue

            m = re.match(ERROR_REGEX, line, re.DOTALL)
            if m:
                errors.append(m.groupdict())
                continue

    for agent_id, period_list in periods.items():
        try:
            num_id = int(agent_id.replace("agent_", ""))
        except Exception:  # pylint: disable=broad-except
            num_id = _id
            _id += 1
        agent_color = AGENT_COLORS[num_id]
        for i, period in enumerate(period_list):

            # Check that this is a new period message
            if "period" not in period.keys():
                continue

            # Check that the next message is an event one
            event: str = ""
            if i < len(period_list) - 1 and "event_id" in period_list[i + 1].keys():
                event = period_list[i + 1]["event_id"]
                color: str = Color.GREEN.value if "DONE" in event else Color.RED.value
                event = color + event + Color.RESET.value
            else:
                event = Color.YELLOW.value + "N/A" + Color.RESET.value

            # Print the period info
            print(
                f"{agent_color}{period['agent_id']:<12}{Color.RESET.value}  period: {period['period']:<4}  round: {period['round_id']:<40}  event: {event}"
            )

    print("\nERRORS:")
    for error in errors:
        print(Color.RED.value + error["message"] + Color.RESET.value)
