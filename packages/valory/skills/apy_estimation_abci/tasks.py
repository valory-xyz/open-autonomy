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

"""Contains the background tasks of the APY estimation skill."""

from typing import Any, Dict

import pandas as pd
from aea.skills.tasks import Task
from optuna import Study
from pmdarima.pipeline import Pipeline

from packages.valory.skills.apy_estimation_abci.ml.forecasting import (
    TestReportType,
    test_forecaster,
    train_forecaster,
)
from packages.valory.skills.apy_estimation_abci.ml.optimization import optimize
from packages.valory.skills.apy_estimation_abci.ml.preprocessing import (
    TrainTestSplitType,
    prepare_pair_data,
)
from packages.valory.skills.apy_estimation_abci.tools.etl import (
    prepare_batch,
    transform_hist_data,
)


class TransformTask(Task):
    """Transform historical data."""

    def execute(self, *args: Any, **kwargs: Any) -> pd.DataFrame:
        """Execute the task."""
        return transform_hist_data(*args, **kwargs)


class PreprocessTask(Task):
    """Preprocess historical data."""

    def execute(self, *args: Any, **kwargs: Any) -> TrainTestSplitType:
        """Execute the task."""
        return prepare_pair_data(*args, **kwargs)


class PrepareBatchTask(Task):
    """Prepare a batch."""

    def execute(self, *args: Any, **kwargs: Any) -> Dict[str, pd.DataFrame]:
        """Execute the task."""
        return prepare_batch(*args, **kwargs)


class OptimizeTask(Task):
    """Run an optimization study."""

    def execute(self, *args: Any, **kwargs: Any) -> Study:
        """Execute the task."""
        return optimize(*args, **kwargs)


class TrainTask(Task):
    """Train a forecaster."""

    def execute(self, *args: Any, **kwargs: Any) -> Pipeline:
        """Execute the task."""
        return train_forecaster(*args, **kwargs)


class TestTask(Task):
    """Test a forecaster."""

    def execute(self, *args: Any, **kwargs: Any) -> TestReportType:
        """Execute the task."""
        return test_forecaster(*args, **kwargs)
