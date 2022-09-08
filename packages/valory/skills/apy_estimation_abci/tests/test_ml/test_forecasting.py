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

# pylint: skip-file

import platform
import re
from copy import deepcopy
from typing import Any

import numpy as np
import pandas as pd
import pytest
from _pytest.monkeypatch import MonkeyPatch
from pmdarima import ARIMA
from pmdarima.pipeline import Pipeline
from pmdarima.preprocessing import FourierFeaturizer

from packages.valory.skills.apy_estimation_abci.ml import forecasting
from packages.valory.skills.apy_estimation_abci.ml.forecasting import (
    PoolIdToTrainDataType,
    baseline,
    calc_metrics,
    estimate_apy_per_pool,
    init_forecaster,
    predict_safely,
    report_metrics,
)
from packages.valory.skills.apy_estimation_abci.ml.forecasting import (
    test_forecaster as _test_forecaster,
)
from packages.valory.skills.apy_estimation_abci.ml.forecasting import (
    test_forecaster_per_pool as _test_forecaster_per_pool,
)
from packages.valory.skills.apy_estimation_abci.ml.forecasting import (
    train_forecaster,
    train_forecaster_per_pool,
    update_forecaster_per_pool,
    walk_forward_test,
)
from packages.valory.skills.apy_estimation_abci.tests.conftest import DummyPipeline


class TestForecasting:
    """Tests for forecasting operations."""

    def setup(self) -> None:
        """Initialize class."""
        self._pipeline = DummyPipeline()

    @staticmethod
    def test_init_forecaster(hyperparameters: Any) -> None:
        """Test `init_forecaster`."""
        forecaster = init_forecaster(**hyperparameters)
        pipeline_steps = forecaster.get_params()["steps"]
        fourier_actual = pipeline_steps[0][1].get_params()
        arima_actual = pipeline_steps[1][1].get_params()

        fourier_expected = {
            "k": hyperparameters["k"],
            "m": hyperparameters["m"],
            "prefix": None,
        }
        arima_expected = {
            "maxiter": 150,
            "method": "lbfgs",
            "order": (hyperparameters["p"], hyperparameters["q"], hyperparameters["d"]),
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
    def test_train_forecaster(observations: np.ndarray, hyperparameters: Any) -> None:
        """Test `train_forecaster`."""
        forecaster = init_forecaster(**hyperparameters)
        forecaster_trained = train_forecaster(observations, **hyperparameters)
        assert type(forecaster) == type(
            forecaster_trained
        )  # must return the same type of object
        assert forecaster is not forecaster_trained  # object identity MUST be different

    @staticmethod
    def test_train_forecaster_per_pool(
        train_task_input: PoolIdToTrainDataType,
        trained_forecaster: Pipeline,
        monkeypatch: MonkeyPatch,
    ) -> None:
        """Test `train_forecaster_per_pool`."""
        monkeypatch.setattr(
            forecasting,
            "train_forecaster",
            lambda _, **__: trained_forecaster,
        )
        forecasters = train_forecaster_per_pool(
            train_task_input, dict.fromkeys(train_task_input, {})
        )
        assert len(forecasters) == len(train_task_input)
        for (id_actual, forecaster_actual), id_expected in zip(
            forecasters.items(), train_task_input.keys()
        ):
            assert id_actual == id_expected.replace(".csv", ".joblib")
            assert type(forecaster_actual) == Pipeline
            # must return the trained forecaster received from `train_forecaster`
            assert forecaster_actual == trained_forecaster

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
                forecasting,
                metric_to_patch,
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
            forecasting,
            "calc_metrics",
            lambda *_: metrics_res,
        )
        report = report_metrics(np.empty(0), np.empty(0), "test_name")
        assert isinstance(report, str)
        assert "test_name" in report
        assert any(metric_name in report for metric_name in metrics_res.keys())
        assert any(
            str(metric_value) in report for metric_value in set(metrics_res.values())
        )

    @pytest.mark.parametrize("steps_forward", (-2, 1, 6, 8))
    def test_walk_forward_test(self, steps_forward: int) -> None:
        """Test `walk_forward_test`."""
        test_size = 5
        params = self._pipeline, np.empty(test_size), steps_forward
        expected_output_len = test_size if steps_forward <= test_size else steps_forward
        if steps_forward < 0:
            with pytest.raises(
                ValueError, match="Timesteps to predict in the future cannot be -2 < 1."
            ):
                walk_forward_test(*params)
        else:
            if expected_output_len > test_size:
                with pytest.warns(
                    UserWarning,
                    match="Timesteps to predict in the future are larger than the number of test samples "
                    f"while using the Direct Multi-step Forecast Strategy: {steps_forward} > {test_size}",
                ):
                    predictions = walk_forward_test(*params)
            else:
                predictions = walk_forward_test(*params)

            assert isinstance(predictions, np.ndarray)
            assert len(predictions) == expected_output_len

    def test_test_forecaster_per_pool(
        self,
        train_task_input: PoolIdToTrainDataType,
        trained_forecaster: Pipeline,
        monkeypatch: MonkeyPatch,
    ) -> None:
        """Test `_test_forecaster_per_pool`."""
        monkeypatch.setattr(
            forecasting,
            "test_forecaster",
            lambda forecaster_, y_train_, y_test_, pair_name, _: {pair_name: "test"},
        )
        dummy_forecasters = {id_: trained_forecaster for id_ in train_task_input.keys()}
        _test_forecaster_per_pool(dummy_forecasters, train_task_input, train_task_input)

    def test_test_forecaster(self, monkeypatch: MonkeyPatch) -> None:
        """Test `test_forecaster`."""
        for testing_method in ("baseline", "walk_forward_test"):
            monkeypatch.setattr(
                forecasting,
                testing_method,
                lambda *_: None,
            )

        monkeypatch.setattr(
            forecasting,
            "report_metrics",
            lambda *_: "Report results.",
        )

        actual = _test_forecaster(self._pipeline, np.empty((5, 2)), np.empty(2), "test")

        expected = {}
        for testing_model in ("Baseline", "ARIMA"):
            expected[testing_model] = "Report results."

        assert actual == expected

    @pytest.mark.parametrize("id_mismatch", (True, False))
    def test_update_forecaster_per_pool(
        self,
        prepare_batch_task_result: pd.DataFrame,
        monkeypatch: MonkeyPatch,
        id_mismatch: bool,
    ) -> None:
        """Test `update_forecaster_per_pool`."""
        mismatch = "test" if id_mismatch else ""
        dummy_pipelines = {
            pool_id + mismatch: deepcopy(self._pipeline)
            for pool_id in prepare_batch_task_result["id"].values
        }

        if mismatch:
            update_forecaster_per_pool(prepare_batch_task_result, dummy_pipelines)
            assert not any(pipeline.updated for pipeline in dummy_pipelines.values())

        else:
            update_forecaster_per_pool(prepare_batch_task_result, dummy_pipelines)
            assert all(pipeline.updated for pipeline in dummy_pipelines.values())

    @pytest.mark.parametrize("steps_forward", (0, 1, 5))
    def test_estimate_apy_per_pool(
        self,
        monkeypatch: MonkeyPatch,
        steps_forward: int,
    ) -> None:
        """Test `estimate_apy_per_pool`."""
        dummy_pipelines = {
            f"pool{pool_id}": deepcopy(self._pipeline) for pool_id in range(3)
        }

        estimates = estimate_apy_per_pool(dummy_pipelines, steps_forward)
        expected_estimates = pd.DataFrame(
            {f"pool{pool_id}": np.ones(steps_forward) for pool_id in range(3)},
            index=[f"Step{i + 1} into the future" for i in range(steps_forward)],
        )
        pd.testing.assert_frame_equal(estimates, expected_estimates)

    def test_predict_safely(self) -> None:
        """
        Test `predict_safely`.

        Also prove that it is useful because of https://github.com/alkaline-ml/pmdarima/issues/404.
        """
        model = Pipeline(
            steps=[
                ("fourier", FourierFeaturizer(k=7, m=18)),
                (
                    "arima",
                    ARIMA(maxiter=150, order=(2, 3, 1), suppress_warnings=True),
                ),
            ]
        )
        y = np.array(
            [
                54.45259405,
                39.58028345,
                112.03066299,
                83.96699996,
                71.94854887,
                64.0529859,
                62.5824148,
                63.28134798,
                58.36879572,
                64.20712075,
                47.35538343,
                42.33252369,
                31.86261839,
                109.74997567,
                51.63416935,
                36.53481234,
                39.73377418,
                50.0544746,
                39.7898384,
                35.02107716,
                49.87511512,
            ]
        )
        steps_forward = 1

        # Fit model with data.
        model.fit(y)

        # issue not present in Mac
        if platform.system() != "Darwin":
            # Prove that the `pmdarima` would raise.
            with pytest.raises(
                ValueError,
                match=re.escape("Input contains NaN"),
            ):
                model.predict(steps_forward)

            # Prove that `predict_safely` works as intended.
            y_hat = predict_safely(model, steps_forward)
            assert np.isnan(y_hat)

        else:
            model.predict(steps_forward)
