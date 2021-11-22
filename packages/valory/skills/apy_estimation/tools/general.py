"""Tools for the APY skill."""
import json
import time
from pathlib import Path
from typing import Generator, List

import pandas as pd


def transform(observations: List) -> pd.DataFrame:
    """Transforms the observations."""
    raise NotImplementedError()


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
    return Path(path).mkdir(parents=True, exist_ok=True)


def list_to_json_file(path: str, li: List) -> None:
    """Dump a list to a json file.

    :param path: the path to store the json file.
    :param li: the list to convert and store.
    """
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(li, f, ensure_ascii=False, indent=4)
