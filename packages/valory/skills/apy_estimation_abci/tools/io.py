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

"""IO operations for the APY skill."""
import json
import os
from typing import Union

import joblib
import pandas as pd
from pmdarima.pipeline import Pipeline

from packages.valory.skills.apy_estimation_abci.ml.forecasting import TestReportType
from packages.valory.skills.apy_estimation_abci.ml.optimization import HyperParamsType
from packages.valory.skills.apy_estimation_abci.tools.etl import (
    ResponseItemType,
    TRANSFORMED_HIST_DTYPES,
)


StoredJSONType = Union[ResponseItemType, TestReportType, HyperParamsType]


def create_pathdirs(path: str) -> None:
    """Create the non-existing directories of a given path.

    :param path: the given path.
    """
    dirname = os.path.dirname(path)

    if dirname:
        os.makedirs(dirname, exist_ok=True)


def save_forecaster(path: str, forecaster: Pipeline) -> None:
    """Save a `pmdarima` forecaster.

    :param path: path to store the forecaster.
    :param forecaster: the `pmdarima` forecasting model.
    """
    joblib.dump(forecaster, path)


def load_forecaster(path: str) -> Pipeline:
    """Load a `pmdarima` forecaster.

    :param path: path to store the forecaster.
    :return: a `pmdarima.pipeline.Pipeline`.
    """
    return joblib.load(path)


def load_hist(path: str) -> pd.DataFrame:
    """Load the already fetched and transformed historical data.

    :param path: the path to the historical data.
    :return: a dataframe with the historical data.
    """
    pairs_hist = pd.read_csv(path).astype(TRANSFORMED_HIST_DTYPES)

    # Convert the `blockTimestamp` to a pandas datetime.
    pairs_hist["blockTimestamp"] = pd.to_datetime(
        pairs_hist["blockTimestamp"], unit="s"
    )

    return pairs_hist


def to_json_file(path: str, obj: StoredJSONType) -> None:
    """Dump a list to a json file.

    :param path: the path to store the json file.
    :param obj: the object to convert and store.
    """
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=4)


def read_json_file(path: str) -> StoredJSONType:
    """Read a json file.

    :param path: the path to retrieve the json file from.
    :return: the deserialized json file's content.
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
