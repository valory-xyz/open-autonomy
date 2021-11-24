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

from typing import Optional

import pmdarima as pm
from pmdarima.pipeline import Pipeline


def init_forecaster(p: int, q: int, d: int, m: int, k: Optional[int] = None,
                    maxiter: int = 150, suppress_warnings: bool = True) -> pm.pipeline.Pipeline:
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
        ('fourier', pm.preprocessing.FourierFeaturizer(m, k)),
        ('arima', pm.arima.ARIMA(order, maxiter=maxiter, suppress_warnings=suppress_warnings))
    ])

    return forecaster
