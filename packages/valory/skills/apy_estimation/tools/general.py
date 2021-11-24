"""Tools for the APY skill."""
import json
import os
import time
from typing import Generator

from packages.valory.skills.apy_estimation.tools.etl import ResponseItemType


def gen_unix_timestamps(duration: int) -> Generator:
    """Generate the UNIX timestamps from `duration` months ago up to today.

    Args:
        duration: the duration of the timestamps to be returned, in months (more precisely, in 30 days).

    Returns:
        a list with the UNIX timestamps.
    """
    day_in_unix = 24 * 60 * 60

    now = int(time.time())
    duration_before = now - (duration * 30 * day_in_unix)

    for day in range(duration_before, now, day_in_unix):
        yield day


def create_pathdirs(path: str) -> None:
    """Create the non-existing directories of a given path.

    :param path: the given path.
    """
    dirname = os.path.dirname(path)

    if dirname:
        os.makedirs(dirname, exist_ok=True)


def list_to_json_file(path: str, li: ResponseItemType) -> None:
    """Dump a list to a json file.

    :param path: the path to store the json file.
    :param li: the list to convert and store.
    """
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(li, f, ensure_ascii=False, indent=4)


def read_json_list_file(path: str) -> ResponseItemType:
    """Dump a list to a json file.

    :param path: the path to store the json file.
    """
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)
