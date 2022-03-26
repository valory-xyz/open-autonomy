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

"""Optimization operations"""

from typing import Any, Callable, Dict, Optional, Tuple, Union

import numpy as np
import optuna
import pandas as pd
import pmdarima as pm
from sklearn.metrics import mean_pinball_loss

from packages.valory.skills.apy_estimation_abci.ml.forecasting import (
    HyperParamsType,
    init_forecaster,
)


ScoringFuncType = Callable[[np.ndarray, np.ndarray], float]
ScoringType = Union[ScoringFuncType, str]
HyperParamsWithStatusType = Tuple[HyperParamsType, bool]
PoolToHyperParamsWithStatusType = Dict[str, HyperParamsWithStatusType]


def pinball_loss_scorer(alpha: float = 0.25) -> ScoringFuncType:
    """Scoring function for mean pinball loss.

    :param alpha: the pinball loss' alpha value.
    :return: a mean pinball loss scoring function, which accepts y_true and y_pred and returns a score.
    """

    def pinball_loss(y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Define mean pinball loss."""
        return mean_pinball_loss(y_true, y_pred, alpha=alpha)

    return pinball_loss


class Objective:  # pylint: disable=too-few-public-methods
    """Class for the objective function that `optuna` will optimize."""

    def __init__(
        self, y: np.ndarray, scoring: ScoringType, window_size: Optional[int] = None
    ) -> None:
        """Init function for the Objective.

        :param y: the timeseries data, based on which the Cross-Validated optimization will be performed.
        :param scoring: The scoring metric to use.
            If a callable, must adhere to the signature `metric(true, predicted)`.
            Valid string scoring metrics include:
               * ‘smape’
               * ‘mean_absolute_error’
               * ‘mean_squared_error’
        :param window_size: The size of the rolling window to use.
            If None, a rolling window of size n_samples // 5 will be used.
        """
        self.__y = y
        self.__scoring = scoring
        self.__window_size = window_size

    def __call__(self, trial: optuna.trial.Trial) -> float:
        """Define the optimization objective function.

        :param trial: an optuna Trial.
        :return: the average score of the cross validation results.
        """
        # Create hyperparameter suggestions.
        p = trial.suggest_int("p", 1, 4)
        q = trial.suggest_int("q", 1, 4)
        d = trial.suggest_int("d", 1, 2)

        m = trial.suggest_int("m", 8, 20)
        # k must be a positive integer not greater than m//2.
        k = trial.suggest_int("k", 1, m // 2)

        # Generate the forecaster with the suggestions.
        forecaster = init_forecaster(p, q, d, m, k)

        # Perform CV and get the average of the results.
        cv = pm.model_selection.SlidingWindowForecastCV(window_size=self.__window_size)

        try:
            scores = pm.model_selection.cross_val_score(
                forecaster, self.__y, scoring=self.__scoring, cv=cv
            )
            average_score = np.average(scores)

        except ValueError:  # pragma: nocover
            average_score = np.nan

        return average_score


def optimize_single_pool(  # pylint: disable=too-many-arguments
    y: np.ndarray,
    seed: int,
    n_trials: Optional[int] = None,
    timeout: Optional[float] = None,
    n_jobs: int = 1,
    show_progress_bar: bool = True,
    scoring: ScoringType = "pinball",
    alpha: Optional[float] = None,
    window_size: Optional[int] = None,
) -> optuna.study.Study:
    """Run the optimizer for a single pool.

    :param y: the data with which the optimization will be done.
    :param seed: Seed for random number generator.
    :param n_trials: the number of trials. If this argument is set to None,
        there is no limitation on the number of trials. If timeout is also set to None,
        the study continues to create trials until it receives a termination signal such as Ctrl+C or SIGTERM.
    :param timeout: stop study after the given number of second(s).
        * If this argument is set to None, the study is executed without time limitation.
        * If n_trials is also set to None, the study continues to create trials
            until it receives a termination signal such as Ctrl+C or SIGTERM.
    :param n_jobs: the number of parallel jobs. If this argument is set to -1, the number is set to CPU count.
    :param show_progress_bar: flag to show progress bars or not. To disable progress bar, set this to False.
        Currently, progress bar is experimental feature in `optuna` and disabled when n_jobs != 1.
    :param scoring: The scoring metric to use. If a callable, must adhere to the signature `metric(true, predicted)`.
        Valid string scoring metrics include:
            * ‘smape’
            * ’pinball’
            * ‘mean_absolute_error’
            * ‘mean_squared_error’
    :param alpha: Parameter for the pinball scoring function. If another scoring fn is used, then it is ignored.
    :param window_size: The size of the rolling window to use.
        If None, a rolling window of size n_samples // 5 will be used.
    :return: the `optuna` study.
    """
    if scoring == "pinball":
        if alpha is not None:
            scoring = pinball_loss_scorer(alpha)
        else:
            scoring = pinball_loss_scorer()

    # Make the sampler behave in a deterministic way.
    sampler = optuna.samplers.TPESampler(seed=seed)
    # Create a study.
    study = optuna.create_study(sampler=sampler)
    # Create the Objective function.
    objective_func = Objective(y, scoring, window_size)

    # Start the optimization of the study.
    study.optimize(
        objective_func, n_trials, timeout, n_jobs, show_progress_bar=show_progress_bar
    )

    return study


def get_best_params(
    study: optuna.study.Study, safely: bool = True
) -> HyperParamsWithStatusType:
    """Get the best parameters from a study.

    :param study: the study from which we want to get the best parameters.
    :param safely: whether we want to get random parameters if no trial has finished from the given study.
        Otherwise, a ValueError is raised.
    :return: a tuple with 1. the best parameters and 2. if the study has at least one finished trial.
    """
    try:
        return study.best_params, True

    except ValueError as e:
        if not safely:
            raise e
        # If no trial finished, set random params as best.
        return study.trials[0].params, False


def optimize(
    pools_data: Dict[str, pd.DataFrame],
    *args: Any,
    **kwargs: Any,
) -> PoolToHyperParamsWithStatusType:
    """Run the optimizer for all the pools."""
    best_params = {}
    for pool_id, pool_y in pools_data.items():
        study = optimize_single_pool(pool_y.values.ravel(), *args, **kwargs)
        best_params[pool_id] = get_best_params(study)
    return best_params
