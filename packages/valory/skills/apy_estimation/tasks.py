# ------------------------------------------------------------------------------
#
#   Copyright 2021 Valory AG
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

"""Contains the background tasks of the APY estimation skill."""

from typing import Optional

import numpy as np
import pandas as pd
from aea.skills.tasks import Task
from optuna import Study
from pmdarima.pipeline import Pipeline

from packages.valory.skills.apy_estimation.ml.forecasting import (
    TestReportType,
    test_forecaster,
    train_forecaster,
)
from packages.valory.skills.apy_estimation.ml.optimization import ScoringType, optimize
from packages.valory.skills.apy_estimation.tools.etl import (
    ResponseItemType,
    transform_hist_data,
)


class TransformTask(Task):
    """Transform historical data."""

    def execute(self, pairs_hist: ResponseItemType) -> pd.DataFrame:
        """Execute the task."""
        return transform_hist_data(pairs_hist)


class OptimizeTask(Task):
    """Run an optimization study."""

    def execute(
        self,
        y: np.ndarray,
        n_trials: Optional[int] = None,
        timeout: Optional[float] = None,
        n_jobs: int = 1,
        show_progress_bar: bool = False,
        scoring: ScoringType = "pinball",
        alpha: Optional[float] = None,
        seed: Optional[int] = None,
    ) -> Study:
        """Execute the task."""
        return optimize(
            y, n_trials, timeout, n_jobs, show_progress_bar, scoring, alpha, seed
        )


class TrainTask(Task):
    """Train a forecaster."""

    def execute(
        self,
        y_train: np.ndarray,
        p: int,
        q: int,
        d: int,
        m: int,
        k: Optional[int] = None,
        maxiter: int = 150,
        suppress_warnings: bool = True,
    ) -> Pipeline:
        """Execute the task."""
        return train_forecaster(y_train, p, q, d, m, k, maxiter, suppress_warnings)


class TestTask(Task):
    """Test a forecaster."""

    def execute(
        self,
        forecaster,
        y_train: np.ndarray,
        y_test: np.ndarray,
        pair_name: str,
        steps_forward: int = 1,
    ) -> TestReportType:
        """Execute the task."""
        return test_forecaster(forecaster, y_train, y_test, pair_name, steps_forward)
