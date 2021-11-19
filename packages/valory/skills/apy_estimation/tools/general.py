"""Tools for the APY skill."""
import time
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
