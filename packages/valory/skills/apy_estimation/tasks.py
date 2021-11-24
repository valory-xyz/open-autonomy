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

from packages.valory.skills.apy_estimation.ml.optimization import optimize, ScoringType
from packages.valory.skills.apy_estimation.tools.etl import transform_hist_data, ResponseItemType


class TransformTask(Task):
    """Transform historical data."""

    def execute(self, pairs_hist: ResponseItemType) -> pd.DataFrame:
        """Execute the task."""
        return transform_hist_data(pairs_hist)


class OptimizeTask(Task):
    """Run an optimization study."""

    def execute(self, y: np.ndarray, n_trials: Optional[int] = None, timeout: Optional[float] = None, n_jobs: int = 1,
                show_progress_bar: bool = False, scoring: ScoringType = 'pinball', alpha: Optional[float] = None,
                seed: Optional[int] = None) -> Study:
        """Execute the task."""
        return optimize(y, n_trials, timeout, n_jobs, show_progress_bar, scoring, alpha, seed)
