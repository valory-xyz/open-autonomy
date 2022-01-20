# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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


"""Tools for the APY skill."""
import json
import os
from typing import Any, Dict, Iterator, Optional, Union

from packages.valory.skills.apy_estimation_abci.ml.forecasting import TestReportType
from packages.valory.skills.apy_estimation_abci.tools.etl import ResponseItemType


HyperParamsType = Dict[str, Any]
StoredJSONType = Union[ResponseItemType, TestReportType, HyperParamsType]


def gen_unix_timestamps(synced_now: int, duration: int) -> Iterator[int]:
    """Generate the UNIX timestamps from `duration` months ago up to today.

    :param synced_now: the synced time across the agents.
    :param duration: the duration of the timestamps to be returned, in months (more precisely, in 30 days).
    :yields: the UNIX timestamps.
    """
    day_in_unix = 24 * 60 * 60

    duration_before = synced_now - (duration * 30 * day_in_unix)

    for day in range(duration_before, synced_now, day_in_unix):
        yield day


def create_pathdirs(path: str) -> None:
    """Create the non-existing directories of a given path.

    :param path: the given path.
    """
    dirname = os.path.dirname(path)

    if dirname:
        os.makedirs(dirname, exist_ok=True)


def to_json_file(path: str, obj: StoredJSONType) -> None:
    """Dump a list to a json file.

    :param path: the path to store the json file.
    :param obj: the object to convert and store.
    """
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=4)


def read_json_file(path: str) -> Union[ResponseItemType, HyperParamsType]:
    """Read a json `ResponseItemType` file.

    :param path: the path to retrieve the json file from.
    :return: the deserialized json file's content.
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def filter_out_numbers(string: str) -> Optional[int]:
    """Filter out all the numbers from a string.

    :param string: the string to filter.
    :return: a filtered out integer.
    """
    numeric_filter = filter(str.isdigit, string)
    numeric_string = "".join(numeric_filter)

    if numeric_string == "":
        filtered_result = None
    else:
        filtered_result = int(numeric_string)
        # Get only the first 9 digits, because the seed cannot be > 2**32 -1
        filtered_result = int(str(filtered_result)[:9])

    return filtered_result
