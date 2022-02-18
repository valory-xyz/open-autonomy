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

"""Test forecasting operations."""
import numpy as np
import pytest
from _pytest.monkeypatch import MonkeyPatch

from packages.valory.skills.apy_estimation_abci.ml.forecasting import (
    baseline,
    calc_metrics,
    init_forecaster,
    report_metrics,
)
from packages.valory.skills.apy_estimation_abci.ml.forecasting import (
    test_forecaster as _test_forecaster,
)
from packages.valory.skills.apy_estimation_abci.ml.forecasting import (
    train_forecaster,
    walk_forward_test,
)

from tests.test_skills.test_apy_estimation.conftest import DummyPipeline


class TestForecasting:
    """Tests for forecasting operations."""

    def setup(self) -> None:
        """Initialize class."""
        self._pipeline = DummyPipeline()

    @staticmethod
    def test_init_forecaster() -> None:
        """Test `init_forecaster`."""
        forecaster = init_forecaster(0, 0, 0, 0, 0)
        pipeline_steps = forecaster.get_params()["steps"]
        fourier_actual = pipeline_steps[0][1].get_params()
        arima_actual = pipeline_steps[1][1].get_params()

        fourier_expected = {"k": 0, "m": 0, "prefix": None}
        arima_expected = {
            "maxiter": 150,
            "method": "lbfgs",
            "order": (0, 0, 0),
            "out_of_sample_size": 0,
            "scoring": "mse",
            "scoring_args": None,
            "seasonal_order": (0, 0, 0, 0),
            "start_params": None,
            "suppress_warnings": True,
            "trend": None,
            "with_intercept": True,
        }

        assert fourier_actual == fourier_expected
        assert arima_actual == arima_expected

    @staticmethod
    def test_train_forecaster(observations: np.ndarray) -> None:
        """Test `train_forecaster`."""
        hyperparameters = 1, 1, 1, 3, 1
        forecaster = init_forecaster(*hyperparameters)
        forecaster_trained = train_forecaster(observations, *hyperparameters)
        assert type(forecaster) == type(
            forecaster_trained
        )  # must return the same type of object
        assert forecaster is not forecaster_trained  # object identity MUST be different

    @staticmethod
    def test_baseline() -> None:
        """Test `baseline`."""
        expected = np.asarray([0.1, 0.2, 0.3])
        actual = baseline(0.1, np.asarray([0.2, 0.3, 0.4]))
        assert np.array_equal(expected, actual)

    @staticmethod
    def test_calc_metrics(monkeypatch: MonkeyPatch) -> None:
        """Test `calc_metrics`."""
        metrics_to_patch = (
            "mean_pinball_loss",
            "smape",
            "explained_variance_score",
            "max_error",
            "mean_squared_error",
        )
        for metric_to_patch in metrics_to_patch:
            monkeypatch.setattr(
                f"packages.valory.skills.apy_estimation_abci.ml.forecasting.{metric_to_patch}",
                lambda *_: 0,
            )

        expected = {
            "mean pinball loss": 0,
            "SMAPE": 0,
            "Explained Variance": 0,
            "Max Error": 0,
            "MSE": 0,
        }

        actual = calc_metrics(np.empty(0), np.empty(0))

        assert actual == expected

    @staticmethod
    def test_report_metrics(monkeypatch: MonkeyPatch) -> None:
        """Test `report_metrics`."""
        metrics_res = {
            "mean pinball loss": 0,
            "SMAPE": 0,
            "Explained Variance": 0,
            "Max Error": 0,
            "MSE": 0,
        }
        monkeypatch.setattr(
            "packages.valory.skills.apy_estimation_abci.ml.forecasting.calc_metrics",
            lambda *_: metrics_res,
        )
        report = report_metrics(np.empty(0), np.empty(0), "test_name")
        assert isinstance(report, str)
        assert "test_name" in report
        assert any(metric_name in report for metric_name in metrics_res.keys())
        assert any(
            str(metric_value) in report for metric_value in set(metrics_res.values())
        )

    def test_walk_forward_test(self) -> None:
        """Test `walk_forward_test`."""
        # Check with `steps_forward < 1`.
        with pytest.raises(
            ValueError, match="Timesteps to predict in the future cannot be -2 < 1."
        ):
            walk_forward_test(self._pipeline, np.empty(5), -2)

        # Check with `steps_forward = 1`.
        predictions = walk_forward_test(self._pipeline, np.empty(5))
        assert isinstance(predictions, np.ndarray)
        assert len(predictions) == 5

        # Check with `steps_forward > 1`.
        steps_forward = 4
        predictions = walk_forward_test(self._pipeline, np.empty(5), steps_forward)
        assert isinstance(predictions, np.ndarray)

        assert len(predictions) == 8

    def test_test_forecaster(self, monkeypatch: MonkeyPatch) -> None:
        """Test `test_forecaster`."""
        for testing_method in ("baseline", "walk_forward_test"):
            monkeypatch.setattr(
                f"packages.valory.skills.apy_estimation_abci.ml.forecasting.{testing_method}",
                lambda *_: None,
            )

        monkeypatch.setattr(
            "packages.valory.skills.apy_estimation_abci.ml.forecasting.report_metrics",
            lambda *_: "Report results.",
        )

        actual = _test_forecaster(self._pipeline, np.empty((5, 2)), np.empty(2), "test")

        expected = {}
        for testing_model in ("Baseline", "ARIMA"):
            expected[testing_model] = "Report results."

        assert actual == expected
