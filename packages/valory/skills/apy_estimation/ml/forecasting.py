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

"""Forecasting operations"""

from typing import Optional, Dict

import numpy as np
from pmdarima import ARIMA
from pmdarima.metrics import smape
from pmdarima.pipeline import Pipeline
from pmdarima.preprocessing import FourierFeaturizer
from sklearn.metrics import mean_pinball_loss, explained_variance_score, max_error, mean_squared_error

MetricsType = Dict[str, float]
TestReportType = Dict[str, str]


def init_forecaster(p: int, q: int, d: int, m: int, k: Optional[int] = None,
                    maxiter: int = 150, suppress_warnings: bool = True) -> Pipeline:
    """Initialize a forecasting model.

    Args:
        m : the seasonal periodicity of the endogenous vector, y.
        k : the number of sine and cosine terms (each) to include.
         I.e., if k is 2, 4 new features will be generated. k must not exceed m/2,
         which is the default value if not set. The value of k can be selected by minimizing the AIC.
        p: the order (number of time lags) of the autoregressive model (AR).
        q: the order of the moving-average model (MA).
        d: the degree of differencing (the number of times the data have had past values subtracted) (I).
        maxiter: the maximum number of function evaluations. Default is 150.
        suppress_warnings: many warnings might be thrown inside of `statsmodels` - which is used by `pmdarima` - .
         If suppress_warnings is True, all of these warnings will be squelched. Default is True.

    Returns:
        a `pmdarima` pipeline, consisting of a fourier featurizer and an ARIMA model.
    """
    order = (p, q, d)

    forecaster = Pipeline([
        ('fourier', FourierFeaturizer(m, k)),
        ('arima', ARIMA(order, maxiter=maxiter, suppress_warnings=suppress_warnings))
    ])

    return forecaster


def train_forecaster(y_train: np.ndarray, p: int, q: int, d: int, m: int, k: Optional[int] = None,
                     maxiter: int = 150, suppress_warnings: bool = True) -> Pipeline:
    """Train a forecasting model.

    Args:
        y_train: the training timeseries.
        m : the seasonal periodicity of the endogenous vector, y.
        k : the number of sine and cosine terms (each) to include.
         I.e., if k is 2, 4 new features will be generated. k must not exceed m/2,
         which is the default value if not set. The value of k can be selected by minimizing the AIC.
        p: the order (number of time lags) of the autoregressive model (AR).
        q: the order of the moving-average model (MA).
        d: the degree of differencing (the number of times the data have had past values subtracted) (I).
        maxiter: the maximum number of function evaluations. Default is 150.
        suppress_warnings: many warnings might be thrown inside of `statsmodels` - which is used by `pmdarima` - .
         If suppress_warnings is True, all of these warnings will be squelched. Default is True.

    Returns:
        a trained `pmdarima` pipeline, consisting of a fourier featurizer and an ARIMA model.
    """
    forecaster = init_forecaster(p, q, d, m, k, maxiter, suppress_warnings)
    forecaster.fit(y_train)

    return forecaster


def baseline(t0: float, y_test: np.ndarray) -> np.ndarray:
    """Create the baseline model's 'predictions'.
    Given a timeseries, the baseline model will be "predicting" at each step $t_n$ the value of $t_{n-1}$.

    Args:
        t0: the current timestep, i.e., the last value of the training set.
        y_test: the test values.

    Returns:
        the "predictions" of the baseline model.
    """
    # TODO consider walk_forward arg as well and pass a t0 of equal len.
    y_test = np.insert(y_test, 0, t0)

    return y_test[:-1]


def calc_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> MetricsType:
    """Calculate various regression metrics. These are:
     * Mean Pinball Loss
     * SMAPE
     * Explained Variance
     * Max Error
     * MSE

    Args:
        y_true: ground truth (correct) target values.
        y_pred: estimated target values.

    Returns:
        a dictionary with the names of the metrics mapped to their values.
    """
    metrics = {
        'mean pinball loss': mean_pinball_loss(y_true, y_pred),
        'SMAPE': smape(y_true, y_pred),
        'Explained Variance': explained_variance_score(y_true, y_pred),
        'Max Error': max_error(y_true, y_pred),
        'MSE': mean_squared_error(y_true, y_pred)
    }

    return metrics


def report_metrics(y_true: np.ndarray, y_pred: np.ndarray, pair_name: str, model_name: Optional[str] = None) -> str:
    """Calculate and report various regression metrics. These are:
     * Mean Pinball Loss
     * SMAPE
     * Explained Variance
     * Max Error
     * MSE

    Args:
        y_true: ground truth (correct) target values.
        y_pred: estimated target values.
        pair_name: the name of the pool for which the metrics are reported.
        model_name: the name of the model for which the metrics are reported.
         The model's name will appear in the report's title.

    Returns:
        a report string.
    """
    metrics = calc_metrics(y_true, y_pred)

    title = f'Pool {pair_name} metrics report'
    title += ':' if model_name is None else f' for {model_name}:'

    separator = '-' * len([letter for letter in title])

    report = f'\n{separator}\n{title}\n{separator}\n'

    for name, value in metrics.items():
        report += f'\t{name}: {value}'

    return report


def walk_forward_test(forecaster: Pipeline, y_test: np.ndarray, steps_forward: int = 1) -> np.ndarray:
    """Test the given forecasting model, using the Direct Multi-step Forecast Strategy.

    Args:
        forecaster: a `pmdarima` pipeline model.
        y_test: the test timeseries.
        steps_forward: how many timesteps the model will be predicting in the future.

    Returns:
        a `numpy` array with the forecaster's predictions.
    """
    y_pred = []

    for i in range(0, len(y_test), steps_forward):
        y_hat = forecaster.predict(steps_forward)

        if steps_forward == 1:
            y_pred.append(y_hat)
        else:
            y_pred.extend(y_hat)

        forecaster.update(y_test[i:i + steps_forward])

    return np.asarray(y_pred)


def test_forecaster(forecaster: Pipeline, y_train: np.ndarray,
                    y_test: np.ndarray, pair_name: str, steps_forward: int = 1) -> TestReportType:
    """Test the trained forecaster.

    Args:
        forecaster: a `pmdarima` pipeline model.
        y_train: the train timeseries.
        y_test: the test timeseries.
        pair_name: the pair's name.
        steps_forward: how many timesteps the model will be predicting in the future.
    """
    # Get the current timestep, i.e., the last value of the training set.
    t0 = y_train[-1][0]

    # Get baseline's and model's predictions.
    report = {
        'Baseline': baseline(t0, y_test),
        'ARIMA': walk_forward_test(forecaster, y_test, steps_forward)
    }

    # Report baseline's and model's metrics.
    for reporting_model, model_predictions in report.items():
        report[reporting_model] = report_metrics(y_test, model_predictions, pair_name, reporting_model)

    return report
