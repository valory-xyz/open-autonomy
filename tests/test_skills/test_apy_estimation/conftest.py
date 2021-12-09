# -*- coding: utf-8 -*-
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


"""Configurations for APY skill's tests."""

import warnings
from dataclasses import dataclass
from typing import Any, Callable, Dict, Tuple, Union
from unittest import mock

import numpy as np
import optuna
import pandas as pd
import pytest
from aea.skills.base import SkillContext
from optuna.distributions import UniformDistribution
from optuna.exceptions import ExperimentalWarning

from packages.valory.skills.apy_estimation.ml.forecasting import train_forecaster
from packages.valory.skills.apy_estimation.models import SharedState


HeaderType = Dict[str, str]
SpecsType = Dict[str, Union[str, int, HeaderType, SkillContext]]


@pytest.fixture
def _common_specs() -> SpecsType:
    return {
        "headers": {"Content-Type": "application/json"},
        "method": "POST",
        "name": "spooky_api",
        "skill_context": SkillContext(),
        "response_key": "data",
        "response_type": "list",
        "retries": 5,
    }


@pytest.fixture
def spooky_specs(_common_specs: SpecsType) -> SpecsType:
    """Spooky specs fixture."""
    return {
        **_common_specs,
        **{
            "api_id": "spookyswap",
            "bundle_id": 1,
            "top_n_pools": 100,
            "url": "https://api.thegraph.com/subgraphs/name/eerieeight/spookyswap",
        },
    }


@pytest.fixture
def fantom_specs(_common_specs: SpecsType) -> SpecsType:
    """Fantom specs fixture"""
    return {
        **_common_specs,
        **{
            "api_id": "fantom",
            "url": "https://api.thegraph.com/subgraphs/name/matthewlilley/fantom-blocks",
        },
    }


@pytest.fixture
def eth_price_usd_q() -> str:
    """Query string for fetching ethereum price in USD from SpookySwap."""
    return (
            """
        {
            bundles(
                first: 1,
                block: {number: """
            + str(3830367)
            + """},
                where: {
                    id: """
            + str(1)
            + """
                }
            )
            {ethPrice}
        }
        """
        )


@pytest.fixture
def block_from_timestamp_q() -> str:
    """Query string to get a block from a timestamp."""

    return """
    {
        blocks(
            first: 1,
            orderBy: timestamp,
            orderDirection: asc,
            where: {
                timestamp_gte: 1618735147,
                timestamp_lte: 1618735747
            }
        )
        {
            timestamp
            number
        }
    }
    """


@pytest.fixture
def top_n_pairs_q() -> str:
    """Query to get the first `top_n` pool ids based on their total liquidity."""

    return """
    {
        pairs(
            first: 100,
            orderBy: trackedReserveETH,
            orderDirection: desc
        )
        {id}
    }
    """


@pytest.fixture
def pairs_q() -> str:
    """Query to get data for the first `top_n` pools based on their total liquidity."""

    return (
        """
    {
        pairs(
            where: {id_in:
            [\""""
        + '","'.join(["0xec454eda10accdd66209c57af8c12924556f3abd"])
        + """"]},
            block: {number: """
        + str(3830367)
        + """}
        ) {
            id
            token0 {
                id
                symbol
                name
            }
            token1 {
                id
                symbol
                name
            }
            reserve0
            reserve1
            totalSupply
            reserveETH
            reserveUSD
            trackedReserveETH
            token0Price
            token1Price
            volumeToken0
            volumeToken1
            volumeUSD
            untrackedVolumeUSD
            txCount
            createdAtTimestamp
            createdAtBlockNumber
            liquidityProviderCount
        }
    }
    """
    )


@pytest.fixture
def pool_fields() -> Tuple[str, ...]:
    """The fields of a pool."""
    return (
        "createdAtBlockNumber",
        "createdAtTimestamp",
        "id",
        "liquidityProviderCount",
        "reserve0",
        "reserve1",
        "reserveETH",
        "reserveUSD",
        "token0Price",
        "token1Price",
        "totalSupply",
        "trackedReserveETH",
        "untrackedVolumeUSD",
        "txCount",
        "volumeToken0",
        "volumeToken1",
        "volumeUSD",
        "token0",
        "token1",
    )


@pytest.fixture
def shared_state() -> SharedState:
    """Initialize a test shared state."""
    return SharedState(name="", skill_context=mock.MagicMock())


@pytest.fixture
def no_action() -> Callable[[Any], None]:
    """Create a no-action function."""
    return lambda *_, **__: None


@dataclass
class TaskResult:
    """A dummy Task Result."""

    result: Any


@pytest.fixture
def transform_task_result() -> TaskResult:
    """Create a result of the `TransformTask`.

    :return: a dummy `Task` Result.
    """
    result = pd.DataFrame()

    return TaskResult(result)


@pytest.fixture
def optimize_task_result() -> TaskResult:
    """Create a result of the `OptimizeTask`.

    :return: a dummy `Task` Result.
    """
    study = optuna.create_study()

    warnings.filterwarnings("ignore", category=ExperimentalWarning)

    trial = optuna.trial.create_trial(
        params={"x": 2.0},
        distributions={"x": UniformDistribution(0, 10)},
        value=4.0,
    )

    study.add_trial(trial)

    return TaskResult(study)


@pytest.fixture
def observations() -> np.ndarray:
    """Observations of a timeseries."""
    return np.asarray([0] * 20)


@pytest.fixture
def train_task_result(observations: np.ndarray) -> TaskResult:
    """Create a result of the `TrainTask`.

    :param observations: the observations for the training.
    :return: a dummy `Task` Result.
    """
    hyperparameters = 1, 1, 1, 3, 1
    forecaster = train_forecaster(observations, *hyperparameters)

    return TaskResult(forecaster)


@pytest.fixture
def test_task_result() -> TaskResult:
    """Create a result of the `TestTask`.

    :return: a dummy `Task` Result.
    """
    result = {"test": "test"}

    return TaskResult(result)


@pytest.fixture
def test_task_result_non_serializable() -> TaskResult:
    """Create a non-serializable result of the `TestTask`.

    :return: a dummy `Task` Result.
    """
    result = b"non-serializable"

    return TaskResult(result)


@pytest.fixture
def transformed_historical_data() -> pd.DataFrame:
    """Create dummy transformed historical data"""
    return pd.DataFrame(
        {
            "createdAtBlockNumber": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "createdAtTimestamp": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "id": [
                "0x2b4c76d0dc16be1c31d4c1dc53bf9b45987fc75c",
                "x2",
                "x3",
                "x4",
                "x5",
                "0x2b4c76d0dc16be1c31d4c1dc53bf9b45987fc75c",
                "0x2b4c76d0dc16be1c31d4c1dc53bf9b45987fc75c",
                "0x2b4c76d0dc16be1c31d4c1dc53bf9b45987fc75c",
                "0x2b4c76d0dc16be1c31d4c1dc53bf9b45987fc75c",
                "0x2b4c76d0dc16be1c31d4c1dc53bf9b45987fc75c",
            ],
            "liquidityProviderCount": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "reserve0": [1.4, 2.4, 3.4, 4.4, 5.4, 6.4, 7.4, 8.0, 9.4, 10.7],
            "reserve1": [1.4, 2.4, 3.4, 4.4, 5.4, 6.4, 7.4, 8.0, 9.4, 10.7],
            "reserveETH": [1.4, 2.4, 3.4, 4.4, 5.4, 6.4, 7.4, 8.0, 9.4, 10.7],
            "reserveUSD": [1.4, 2.4, 3.4, 4.4, 5.4, 6.4, 7.4, 8.0, 9.4, 10.7],
            "token0Price": [1.4, 2.4, 3.4, 4.4, 5.4, 6.4, 7.4, 8.0, 9.4, 10.7],
            "token1Price": [1.4, 2.4, 3.4, 4.4, 5.4, 6.4, 7.4, 8.0, 9.4, 10.7],
            "totalSupply": [1.4, 2.4, 3.4, 4.4, 5.4, 6.4, 7.4, 8.0, 9.4, 10.7],
            "trackedReserveETH": [1.4, 2.4, 3.4, 4.4, 5.4, 6.4, 7.4, 8.0, 9.4, 10.7],
            "untrackedVolumeUSD": [1.4, 2.4, 3.4, 4.4, 5.4, 6.4, 7.4, 8.0, 9.4, 10.7],
            "txCount": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "volumeToken0": [1.2, 2.4, 3.0, 4.6, 5.8, 6.3, 7.5, 8.2, 9.1, 10.7],
            "volumeToken1": [1.2, 2.4, 3.0, 4.6, 5.8, 6.3, 7.5, 8.2, 9.1, 10.7],
            "volumeUSD": [1.2, 2.4, 3.0, 4.6, 5.8, 6.3, 7.5, 8.2, 9.1, 10.7],
            "for_timestamp": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "block_number": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "block_timestamp": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "eth_price": [1.2, 2.3, 3.4, 4.45634, 5.2, 6.0, 7.246, 8.26, 9.123, 10.56],
            "token0_id": ["x", "k", "l", "t", "v", "x", "x", "x", "x", "x"],
            "token0_name": ["x", "k", "l", "t", "v", "x", "x", "x", "x", "x"],
            "token0_symbol": ["x", "k", "l", "t", "v", "x", "x", "x", "x", "x"],
            "token1_id": ["y", "m", "r", "y", "b", "y", "y", "y", "y", "y"],
            "token1_name": ["y", "m", "r", "y", "b", "y", "y", "y", "y", "y"],
            "token1_symbol": ["y", "m", "r", "y", "b", "y", "y", "y", "y", "y"],
            "pairName": [
                "x - y",
                "k - m",
                "l - r",
                "t - y",
                "v - b",
                "x - y",
                "x - y",
                "x - y",
                "x - y",
                "x - y",
            ],
            "updatedVolumeUSD": [1.2, 2.4, 3.0, 4.6, 5.8, 6.3, 7.5, 8.2, 9.1, 10.7],
            "updatedReserveUSD": [
                1.68,
                5.52,
                11.559999999999999,
                19.607896,
                28.080000000000002,
                38.400000000000006,
                53.620400000000004,
                66.08,
                85.75619999999999,
                112.992,
            ],
            "current_change": [None, None, None, None, None, 5.1, 1.2, 0.7, 0.9, 1.6],
            "APY": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.1],
        }
    )


class DummyPipeline:
    """A dummy pipeline."""

    @staticmethod
    def predict(steps_forward: int) -> np.ndarray:
        """Predict `steps_forward` timesteps in the future.

        :param steps_forward: how many timesteps the model will be predicting in the future.
        :return: a `numpy` array with the dummy predictions.
        """
        return np.zeros(steps_forward)

    @staticmethod
    def update(_y: np.ndarray) -> None:
        """Update the dummy pipeline.

        :param _y: The time-series data to add to the endogenous samples on which the
            `DummyPipeline` was previously fit.
        """
        pass


def is_list_of_strings(lst: Any) -> bool:
    """Check if arg is a list of strings."""
    res = False

    if lst and isinstance(lst, list):
        res = all(isinstance(elem, str) for elem in lst)

    return res
