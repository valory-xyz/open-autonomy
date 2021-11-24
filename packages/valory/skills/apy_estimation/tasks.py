"""Contains the background tasks of the APY estimation skill."""
from typing import Any

from aea.skills.tasks import Task

from packages.valory.skills.apy_estimation.tools.etl import transform_hist_data, ResponseItemType


class TransformTask(Task):
    """Transform historical data."""

    def execute(self, pairs_hist: ResponseItemType) -> Any:
        """Execute the task"""
        transform_hist_data(pairs_hist)
