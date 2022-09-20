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

"""Test optimization operations."""

# pylint: skip-file

from typing import Any, Callable
from unittest.mock import MagicMock

import numpy as np
import optuna
import pandas as pd
import pmdarima.model_selection
import pytest
from _pytest.monkeypatch import MonkeyPatch
from sklearn.metrics import mean_pinball_loss

from packages.valory.skills.apy_estimation_abci.ml import optimization
from packages.valory.skills.apy_estimation_abci.ml.optimization import (
    Objective,
    get_best_params,
    optimize,
    optimize_single_pool,
    pinball_loss_scorer,
)


class TestOptimization:
    """Tests for the optimization operations."""

    @staticmethod
    @pytest.mark.parametrize(
        "y_true,y_pred,alpha",
        (
            (
                np.asarray([4.45, 4.434, 8.45, 0.342, 7.34, 6346.3475, 3.0]),
                np.asarray([4.45, 5.434, 34.23, 0.345634, 2.34, 633456.3475, 3.0]),
                0.1,
            ),
            (
                np.asarray([6.45, 3.434, 7.45, 0.45342, 37.34, 0.3475, 36]),
                np.asarray([445, 5434, 34.3, 0.344, 2.3, 633456.475, 3.0]),
                0.4,
            ),
            (
                np.asarray([4.45, 4.434, 8.45, 0.342, 7.34, 6346.3475, 3.0]),
                np.asarray([4.45, 4.434, 8.45, 0.342, 7.34, 6346.3475, 3.0]),
                0.1,
            ),
            (
                np.asarray([4, 65, 2, 677, 7, 6]),
                np.asarray([7, 7, 7, 7, 7, 7]),
                0.9,
            ),
        ),
    )
    def test_pinball_loss_scorer(
        y_true: np.ndarray, y_pred: np.ndarray, alpha: float
    ) -> None:
        """Test `pinball_loss_scorer`."""
        actual = pinball_loss_scorer(0.1)(y_true, y_pred)
        expected = mean_pinball_loss(y_true, y_pred, alpha=0.1)

        assert actual == expected

    @staticmethod
    @pytest.mark.parametrize("alpha", (None, 0.3))
    def test_optimize_single_pool(
        monkeypatch: MonkeyPatch,
        observations: np.ndarray,
        no_action: Callable[[Any], None],
        alpha: float,
    ) -> None:
        """Test `optimize_single_pool`."""
        monkeypatch.setattr(optuna.Study, "optimize", no_action)
        res = optimize_single_pool(observations, 0, alpha=alpha)
        assert isinstance(res, optuna.Study)

    @staticmethod
    @pytest.mark.parametrize("safely", (True, False))
    def test_get_best_params(study: MagicMock, safely: bool) -> None:
        """Test `get_best_params`."""
        if safely:
            res = get_best_params(study, safely)
            assert res == ({"x": 2.0}, False)
        else:
            with pytest.raises(ValueError, match="Study has no trials finished!"):
                get_best_params(study, safely)

    @staticmethod
    def test_optimize(
        monkeypatch: MonkeyPatch,
        observations: np.ndarray,
        no_action: Callable[[Any], None],
    ) -> None:
        """Test `optimize`."""
        monkeypatch.setattr(
            optimization, "optimize_single_pool", lambda *_, **__: MagicMock()
        )
        monkeypatch.setattr(
            optimization, "get_best_params", lambda _: {"test_param": 0.23}
        )
        assert optimize({"test1": pd.DataFrame()}) == {"test1": {"test_param": 0.23}}


class TestObjective:
    """Tests for `Objective`."""

    @staticmethod
    def test__call__(monkeypatch: MonkeyPatch, observations: np.ndarray) -> None:
        """Test `__call__`."""
        # Make the sampler behave in a deterministic way.
        sampler = optuna.samplers.TPESampler(seed=0)
        # Create a study.
        study = optuna.create_study(sampler=sampler)

        # Create the Objective function.
        monkeypatch.setattr(
            pmdarima.model_selection,
            "cross_val_score",
            lambda *_, **__: [1, 2, 3, 4, 5],
        )
        objective_func = Objective(observations, "smape")

        # Start the optimization of the study.
        study.optimize(objective_func, n_trials=1)
        assert study.best_value == 3
        assert study.best_params == {"p": 3, "q": 3, "d": 2, "m": 15, "k": 3}
