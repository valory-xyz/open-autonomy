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

"""Optimization operations"""

from typing import Callable, Optional, Union

import numpy as np
import optuna
import pmdarima as pm
from sklearn.metrics import mean_pinball_loss

from packages.valory.skills.apy_estimation.ml.forecasting import init_forecaster


ScoringFuncType = Callable[[np.ndarray, np.ndarray], float]
ScoringType = Union[ScoringFuncType, str]


def pinball_loss_scorer(alpha: float = 0.25) -> ScoringFuncType:
    """Scoring function for mean pinball loss.

    Args:
        alpha: the pinball loss' alpha value.

    Returns:
        a mean pinball loss scoring function, which accepts y_true and y_pred and returns a score.
    """

    def pinball_loss(y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Define mean pinball loss."""
        return mean_pinball_loss(y_true, y_pred, alpha=alpha)

    return pinball_loss


class Objective:
    """Class for the objective function that `optuna` will optimize."""

    def __init__(self, y: np.ndarray, scoring: ScoringType) -> None:
        """Init function for the Objective.

        Args:
            y: the timeseries data, based on which the Cross-Validated optimization will be performed.
            scoring: The scoring metric to use. If a callable, must adhere to the signature `metric(true, predicted)`.
             Valid string scoring metrics include:
              * ‘smape’
              * ‘mean_absolute_error’
              * ‘mean_squared_error’
        """
        self.__y = y
        self.__scoring = scoring

    def __call__(self, trial: optuna.trial.Trial) -> float:
        """Define the optimization objective function.

        Args:
            trial: an optuna Trial.

        Returns:
            the average score of the cross validation results.
        """
        # Create hyperparameter suggestions.
        p = trial.suggest_int("p", 1, 4)
        q = trial.suggest_int("q", 1, 4)
        d = trial.suggest_int("d", 1, 2)

        m = trial.suggest_int("m", 8, 20)
        k = trial.suggest_int("k", 1, 6)

        # Generate the forecaster with the suggestions.
        forecaster = init_forecaster(p, q, d, m, k)

        # Perform CV and get the average of the results.
        cv = pm.model_selection.SlidingWindowForecastCV(window_size=120)
        scores = pm.model_selection.cross_val_score(
            forecaster, self.__y, scoring=self.__scoring, cv=cv
        )
        average_score = np.average(scores)

        return average_score


def optimize(
    y: np.ndarray,
    seed: int,
    n_trials: Optional[int] = None,
    timeout: Optional[float] = None,
    n_jobs: int = 1,
    show_progress_bar: bool = True,
    scoring: ScoringType = "pinball",
    alpha: Optional[float] = None,
) -> optuna.study.Study:
    """Run the optimizer.

    Args:
        y: the data with which the optimization will be done.
        n_trials: the number of trials. If this argument is set to None,
         there is no limitation on the number of trials. If timeout is also set to None,
         the study continues to create trials until it receives a termination signal such as Ctrl+C or SIGTERM.
        timeout: stop study after the given number of second(s).
         If this argument is set to None, the study is executed without time limitation.
         If n_trials is also set to None, the study continues to create trials
         until it receives a termination signal such as Ctrl+C or SIGTERM.
        n_jobs: the number of parallel jobs. If this argument is set to -1, the number is set to CPU count.
        show_progress_bar: flag to show progress bars or not. To disable progress bar, set this to False.
        Currently, progress bar is experimental feature in `optuna` and disabled when n_jobs != 1.
        scoring: The scoring metric to use. If a callable, must adhere to the signature `metric(true, predicted)`.
         Valid string scoring metrics include:
          * ‘smape’
          * ’pinball’
          * ‘mean_absolute_error’
          * ‘mean_squared_error’
        alpha: Parameter for the pinball scoring function. If another scoring fn is used, then it is ignored.
        seed: Seed for random number generator.
    Raises:
        RuntimeError: if nested invocation of this method occurs.

    Returns:
        the `optuna` study.
    """
    if scoring == "pinball":
        scoring = pinball_loss_scorer(alpha)

    # Make the sampler behave in a deterministic way.
    sampler = optuna.samplers.TPESampler(seed=seed)
    # Create a study.
    study = optuna.create_study(sampler=sampler)
    # Create the Objective function.
    objective_func = Objective(y, scoring)

    # Start the optimization of the study.
    study.optimize(
        objective_func, n_trials, timeout, n_jobs, show_progress_bar=show_progress_bar
    )

    return study
