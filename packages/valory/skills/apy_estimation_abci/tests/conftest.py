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


"""Configurations for APY skill's tests."""

# pylint: skip-file

import warnings
from typing import Any, Callable, Dict, List, Tuple, Union
from unittest import mock
from unittest.mock import MagicMock, PropertyMock

import numpy as np
import optuna
import pandas as pd
import pytest
from aea.skills.base import SkillContext
from optuna.distributions import UniformDistribution
from optuna.exceptions import ExperimentalWarning
from optuna.trial import TrialState
from pmdarima import ARIMA
from pmdarima.pipeline import Pipeline
from pmdarima.preprocessing import FourierFeaturizer
from statsmodels.tools.sm_exceptions import ConvergenceWarning

from packages.valory.skills.apy_estimation_abci.ml.forecasting import (
    PoolIdToForecasterType,
    PoolIdToTestReportType,
    PoolIdToTrainDataType,
)
from packages.valory.skills.apy_estimation_abci.ml.optimization import (
    PoolToHyperParamsWithStatusType,
)
from packages.valory.skills.apy_estimation_abci.models import SharedState
from packages.valory.skills.apy_estimation_abci.tools.etl import ResponseItemType
from packages.valory.skills.apy_estimation_abci.tools.queries import SAFE_BLOCK_TIME


try:
    from typing import TypedDict  # >=3.8
except ImportError:
    from mypy_extensions import TypedDict  # <=3.7


HeaderType = Dict[str, str]
SpecsType = Dict[str, Union[str, int, HeaderType, SkillContext]]


_ETH_PRICE_USD_Q_PARAMS: Dict[str, Union[int, float]] = {
    "block": 15178691,
    "id": 1,
    "spooky_expected_result": 0.5723397498919842,
    "uni_expected_result": 1547.0711519143858,
}


_PAIRS_Q_PARAMS: Dict[str, Union[int, str]] = {
    "block": 15178691,
    "spooky_id": "0xec454eda10accdd66209c57af8c12924556f3abd",
    "uni_id": "0x00004ee988665cdda9a1080d5792cecd16dc1220",
}


class _BlockQParamsType(TypedDict):
    given_timestamp: int
    given_number: int
    expected_keys: List[str]
    fantom_timestamp_expected_result: Dict[str, str]
    eth_timestamp_expected_result: Dict[str, str]
    fantom_number_expected_result: Dict[str, str]
    eth_number_expected_result: Dict[str, str]


_BLOCK_Q_PARAMS: _BlockQParamsType = {
    "given_timestamp": 1652544875,
    "given_number": 3730360,
    "expected_keys": ["number", "timestamp"],
    "fantom_timestamp_expected_result": {
        "timestamp": "1652544875",
        "number": "38234191",
    },
    "eth_timestamp_expected_result": {"timestamp": "1652544889", "number": "14774596"},
    "fantom_number_expected_result": {"timestamp": "1618485988", "number": "3730360"},
    "eth_number_expected_result": {"timestamp": "1495162291", "number": "3730360"},
}


@pytest.fixture
def _common_specs() -> SpecsType:
    return {
        "headers": {"Content-Type": "application/json"},
        "method": "POST",
        "name": "api",
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
            "name": "spooky_subgraph",
            "api_id": "spookyswap",
            "chain_subgraph": "test",
            "bundle_id": 1,
            "url": "https://api.thegraph.com/subgraphs/name/eerieeight/spookyswap",
        },
    }


@pytest.fixture
def uni_specs(spooky_specs: SpecsType) -> SpecsType:
    """Uniswap specs fixture."""
    uni_specs = spooky_specs.copy()
    uni_specs["name"] = "uniswap_subgraph"
    uni_specs["api_id"] = "uniswap"
    uni_specs["url"] = "https://api.thegraph.com/subgraphs/name/ianlapham/uniswapv2"
    return uni_specs


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
def eth_specs(_common_specs: SpecsType) -> SpecsType:
    """ETH specs fixture"""
    return {
        **_common_specs,
        **{
            "api_id": "eth",
            "url": "https://api.thegraph.com/subgraphs/name/blocklytics/ethereum-blocks",
        },
    }


def _response_key_extension(specs: SpecsType, extension: str) -> SpecsType:
    """Extend specs for block queries."""
    extended = specs.copy()
    assert isinstance(extended["response_key"], str)
    extended["response_key"] += extension
    return extended


@pytest.fixture
def fantom_specs_blocks_extended(fantom_specs: SpecsType) -> SpecsType:
    """Fantom specs fixture, extended for blocks queries."""
    return _response_key_extension(fantom_specs, ":blocks")


@pytest.fixture
def eth_specs_blocks_extended(eth_specs: SpecsType) -> SpecsType:
    """ETH specs fixture, extended for blocks queries."""
    return _response_key_extension(eth_specs, ":blocks")


@pytest.fixture
def spooky_specs_price_extended(spooky_specs: SpecsType) -> SpecsType:
    """Spooky specs fixture, extended for price queries."""
    return _response_key_extension(spooky_specs, ":bundles")


@pytest.fixture
def uni_specs_price_extended(uni_specs: SpecsType) -> SpecsType:
    """Uniswap specs fixture, extended for price queries."""
    return _response_key_extension(uni_specs, ":bundles")


@pytest.fixture
def spooky_specs_pairs_extended(spooky_specs: SpecsType) -> SpecsType:
    """Spooky specs fixture, extended for pairs queries."""
    return _response_key_extension(spooky_specs, ":pairs")


@pytest.fixture
def uni_specs_pairs_extended(uni_specs: SpecsType) -> SpecsType:
    """Uniswap specs fixture, extended for pairs queries."""
    return _response_key_extension(uni_specs, ":pairs")


@pytest.fixture
def eth_price_usd_q() -> str:
    """Query string for fetching ethereum price in USD."""
    return (
        """
        {
            bundles(
                first: 1,
                block: {number: """
        + str(_ETH_PRICE_USD_Q_PARAMS["block"])
        + """},
                where: {
                    id: """
        + str(_ETH_PRICE_USD_Q_PARAMS["id"])
        + """
                }
            )
            {ethPrice}
        }
        """
    )


@pytest.fixture
def spooky_expected_eth_price_usd() -> float:
    """The expected result of the `eth_price_usd_q` query on SpookySwap."""
    return _ETH_PRICE_USD_Q_PARAMS["spooky_expected_result"]


@pytest.fixture
def uni_expected_eth_price_usd() -> float:
    """The expected result of the `eth_price_usd_q` query on Uniswap."""
    return _ETH_PRICE_USD_Q_PARAMS["uni_expected_result"]


@pytest.fixture
def largest_acceptable_block_number() -> int:
    """The largest acceptable block number."""
    return 2147483647


@pytest.fixture
def eth_price_usd_raising_q(
    eth_price_usd_q: str, largest_acceptable_block_number: int
) -> str:
    """Query string for fetching ethereum price in USD, which raises a non-indexed error."""
    # replace the block number with a huge one, so that we get a not indexed error
    return eth_price_usd_q.replace(
        str(_ETH_PRICE_USD_Q_PARAMS["block"]), str(largest_acceptable_block_number)
    )


@pytest.fixture(scope="session")
def timestamp_gte() -> str:
    """Get the timestamp_gte value."""
    return str(_BLOCK_Q_PARAMS["given_timestamp"])


@pytest.fixture(scope="session")
def timestamp_lte() -> str:
    """Get the timestamp_lte value."""
    return str(_BLOCK_Q_PARAMS["given_timestamp"] + SAFE_BLOCK_TIME)


@pytest.fixture(scope="session")
def block_from_timestamp_q(timestamp_gte: str, timestamp_lte: str) -> str:
    """Query string to get a block from a timestamp."""

    return (
        """
    {
        blocks(
            first: 1,
            orderBy: timestamp,
            orderDirection: asc,
            where: {
                timestamp_gte: """
        + timestamp_gte
        + """,
                timestamp_lte: """
        + timestamp_lte
        + """
            }
        )
        {
            timestamp
            number
        }
    }
    """
    )


@pytest.fixture
def expected_block_q_res_keys() -> List[str]:
    """The expected keys of the result of any `block_from_number_q` query."""
    return _BLOCK_Q_PARAMS["expected_keys"]


@pytest.fixture
def expected_fantom_block_from_timestamp() -> Dict[str, str]:
    """The expected result of the `block_from_timestamp_q` query on Fantom."""
    return _BLOCK_Q_PARAMS["fantom_timestamp_expected_result"]


@pytest.fixture
def expected_eth_block_from_timestamp() -> Dict[str, str]:
    """The expected result of the `block_from_timestamp_q` query on ETH."""
    return _BLOCK_Q_PARAMS["eth_timestamp_expected_result"]


@pytest.fixture
def given_number() -> str:
    """The given number for the `block_from_number_q` query."""
    return str(_BLOCK_Q_PARAMS["given_number"])


@pytest.fixture
def block_from_number_q(given_number: str) -> str:
    """Query string to get a block from a timestamp."""

    return (
        """
    {
        blocks(
            first: 1,
            orderBy: timestamp,
            orderDirection: asc,
            where: {
                number: """
        + given_number
        + """
            }
        )
        {
            timestamp
            number
        }
    }
    """
    )


@pytest.fixture
def expected_fantom_block_from_number() -> Dict[str, str]:
    """The expected result of the `block_from_number_q` query on Fantom."""
    return _BLOCK_Q_PARAMS["fantom_number_expected_result"]


@pytest.fixture
def expected_eth_block_from_number() -> Dict[str, str]:
    """The expected result of the `block_from_number_q` query on ETH."""
    return _BLOCK_Q_PARAMS["eth_number_expected_result"]


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


def _pairs_q(dex_id_name: str) -> str:
    """Query to get data for the pool corresponding to the `dex_id_name` at a specific block."""

    return (
        """
    {
        pairs(
            where: {id_in:
            [\""""
        + '","'.join([str(_PAIRS_Q_PARAMS[dex_id_name])])
        + """"]},
            block: {number: """
        + str(_PAIRS_Q_PARAMS["block"])
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
def spooky_pairs_q() -> str:
    """Query to get data for a SpookySwap pool at a specific block."""
    return _pairs_q("spooky_id")


@pytest.fixture
def uni_pairs_q() -> str:
    """Query to get data for a Uniswap pool at a specific block."""
    return _pairs_q("uni_id")


def _existing_pairs_q(dex_id_name: str) -> str:
    """Query to get ids for the pools corresponding to the `dex_id_name`."""

    return (
        """
    {
        pairs(
            where: {id_in:
            [\""""
        + '","'.join([str(_PAIRS_Q_PARAMS[dex_id_name])])
        + """"]},
        ) {
            id
        }
    }
    """
    )


@pytest.fixture
def spooky_existing_pairs_q() -> str:
    """Query to get the id for a SpookySwap pool."""
    return _existing_pairs_q("spooky_id")


@pytest.fixture
def uni_existing_pairs_q() -> str:
    """Query to get the id for a Uniswap pool."""
    return _existing_pairs_q("uni_id")


@pytest.fixture(scope="session")
def pairs_ids() -> Dict[str, List[str]]:
    """Sample DEXs' pair ids for testing."""
    return {
        "uniswap_subgraph": [str(_PAIRS_Q_PARAMS["uni_id"])],
        "spooky_subgraph": [str(_PAIRS_Q_PARAMS["spooky_id"])],
    }


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


@pytest.fixture
def prepare_batch_task_result() -> pd.DataFrame:
    """Create a dummy prepare batch task result."""
    return pd.DataFrame({"id": ["pool1", "pool2"], "APY": [13.234, 42.34]})


@pytest.fixture
def study() -> MagicMock:
    """Create a dummy optuna Study which has no trials finished."""
    study = MagicMock(trials=(MagicMock(params={"x": 2.0}),))
    type(study).best_params = PropertyMock(
        side_effect=ValueError("Study has no trials finished!")
    )
    return study


@pytest.fixture
def optimize_task_result() -> PoolToHyperParamsWithStatusType:
    """Create a result of the `OptimizeTask`.

    :return: a dummy `Task` Result.
    """
    return {"test1": ({"x": 2.0}, False), "test2": ({"x": 2.4}, True)}


@pytest.fixture
def optimize_task_result_empty() -> optuna.Study:
    """Create an empty result of the `OptimizeTask`.

    :return: a dummy `Task` Result.
    """
    study = optuna.create_study()

    warnings.filterwarnings("ignore", category=ExperimentalWarning)

    trial = optuna.trial.create_trial(
        state=TrialState.WAITING,
        params={"x": 2.0},
        distributions={"x": UniformDistribution(0, 10)},
        value=4.0,
    )

    study.add_trial(trial)

    return study


@pytest.fixture
def optimize_task_result_non_serializable() -> optuna.Study:
    """Create a non-serializable result of the `OptimizeTask`.

    :return: a dummy `Task` Result.
    """
    study = optuna.create_study()

    warnings.filterwarnings("ignore", category=ExperimentalWarning)

    trial = optuna.trial.create_trial(
        params={b"x": 2.0},  # type: ignore
        distributions={b"x": UniformDistribution(0, 10)},  # type: ignore
        value=4.0,
    )

    study.add_trial(trial)

    return study


@pytest.fixture
def observations() -> np.ndarray:
    """Observations of a timeseries."""
    return np.asarray([0] * 20)


@pytest.fixture
def hyperparameters() -> Dict[str, Union[bool, int]]:
    """Hyperparameters for a pipeline."""
    return {
        "p": 1,
        "q": 1,
        "d": 1,
        "m": 3,
        "k": 1,
        "suppress_warnings": True,
    }


@pytest.fixture
def forecaster(hyperparameters: Dict[str, Union[bool, int]]) -> Pipeline:
    """Create a dummy, untrained Pipeline."""
    order = (hyperparameters["p"], hyperparameters["q"], hyperparameters["d"])

    dummy_forecaster = Pipeline(
        [
            ("fourier", FourierFeaturizer(hyperparameters["m"])),
            (
                "arima",
                ARIMA(order),
            ),
        ]
    )

    return dummy_forecaster


@pytest.fixture
def trained_forecaster(forecaster: Pipeline, observations: np.ndarray) -> Pipeline:
    """Create a dummy, trained Pipeline."""
    warnings.filterwarnings("ignore", category=ConvergenceWarning)
    forecaster.fit(observations)

    return forecaster


@pytest.fixture
def train_task_input(observations: np.ndarray) -> PoolIdToTrainDataType:
    """Create an input of the `TrainTask`."""
    return {f"pool{i}.csv": observations for i in range(3)}


@pytest.fixture
def train_task_result(trained_forecaster: Pipeline) -> PoolIdToForecasterType:
    """Create a result of the `TrainTask`.

    :param trained_forecaster: a trained, dummy forecaster.
    :return: a dummy `TrainTask` Result.
    """
    return {f"pool{i}.joblib": trained_forecaster for i in range(3)}


@pytest.fixture
def _test_task_result() -> PoolIdToTestReportType:
    """Create a result of the `TestTask`.

    :return: a dummy `Task` Result.
    """
    return {f"pool{i}": {"test": "test"} for i in range(3)}


@pytest.fixture
def _test_task_result_non_serializable() -> bytes:
    """Create a non-serializable result of the `TestTask`.

    :return: a dummy `Task` Result.
    """
    return b"non-serializable"


@pytest.fixture
def historical_data() -> Dict[str, List[Union[None, Dict[str, str], int, str, float]]]:
    """Create dummy transformed historical data"""
    return {
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
        "forTimestamp": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        "blockNumber": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        "blockTimestamp": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        "ethPrice": [1.2, 2.3, 3.4, 4.45634, 5.2, 6.0, 7.246, 8.26, 9.123, 10.56],
        "token0": [
            {"id": "x", "name": "x", "symbol": "x"},
            {"id": "k", "name": "k", "symbol": "k"},
            {"id": "l", "name": "l", "symbol": "l"},
            {"id": "t", "name": "t", "symbol": "t"},
            {"id": "v", "name": "v", "symbol": "v"},
            {"id": "x", "name": "x", "symbol": "x"},
            {"id": "x", "name": "x", "symbol": "x"},
            {"id": "x", "name": "x", "symbol": "x"},
            {"id": "x", "name": "x", "symbol": "x"},
            {"id": "x", "name": "x", "symbol": "x"},
        ],
        "token1": [
            {"id": "y", "name": "y", "symbol": "y"},
            {"id": "m", "name": "m", "symbol": "m"},
            {"id": "r", "name": "r", "symbol": "r"},
            {"id": "y", "name": "y", "symbol": "y"},
            {"id": "b", "name": "b", "symbol": "b"},
            {"id": "y", "name": "y", "symbol": "y"},
            {"id": "y", "name": "y", "symbol": "y"},
            {"id": "y", "name": "y", "symbol": "y"},
            {"id": "y", "name": "y", "symbol": "y"},
            {"id": "y", "name": "y", "symbol": "y"},
        ],
    }


@pytest.fixture
def transformed_historical_data_no_datetime_conversion(
    historical_data: Dict[str, List[Union[None, Dict[str, str], int, str, float]]]
) -> pd.DataFrame:
    """Create dummy transformed historical data"""
    data_copy = historical_data.copy()
    data_copy.update(
        {
            "APY": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.1],
            "currentChange": [None, None, None, None, None, 5.1, 1.2, 0.7, 0.9, 1.6],
            "token0ID": ["x", "k", "l", "t", "v", "x", "x", "x", "x", "x"],
            "token0Name": ["x", "k", "l", "t", "v", "x", "x", "x", "x", "x"],
            "token0Symbol": ["x", "k", "l", "t", "v", "x", "x", "x", "x", "x"],
            "token1ID": ["y", "m", "r", "y", "b", "y", "y", "y", "y", "y"],
            "token1Name": ["y", "m", "r", "y", "b", "y", "y", "y", "y", "y"],
            "token1Symbol": ["y", "m", "r", "y", "b", "y", "y", "y", "y", "y"],
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
        }
    )

    for i in range(2):
        del data_copy[f"token{i}"]

    return pd.DataFrame(data_copy)


@pytest.fixture
def transformed_historical_data(
    transformed_historical_data_no_datetime_conversion: pd.DataFrame,
) -> pd.DataFrame:
    """Create dummy transformed historical data"""
    transformed_historical_data_no_datetime_conversion[
        "blockTimestamp"
    ] = pd.to_datetime(
        transformed_historical_data_no_datetime_conversion["blockTimestamp"], unit="s"
    )

    return transformed_historical_data_no_datetime_conversion


@pytest.fixture
def batch() -> ResponseItemType:
    """Create a dummy batch of data."""
    pool1_batch: Dict[str, Union[str, Dict[str, str]]] = {
        "createdAtBlockNumber": "1",
        "createdAtTimestamp": "1",
        "id": "0x2b4c76d0dc16be1c31d4c1dc53bf9b45987fc75c",
        "liquidityProviderCount": "1",
        "reserve0": "1.4",
        "reserve1": "1.4",
        "reserveETH": "1.4",
        "reserveUSD": "1.4",
        "token0Price": "1.4",
        "token1Price": "1.4",
        "totalSupply": "1.4",
        "trackedReserveETH": "1.4",
        "untrackedVolumeUSD": "1.4",
        "txCount": "1",
        "volumeToken0": "1.2",
        "volumeToken1": "1.2",
        "volumeUSD": "1.2",
        "forTimestamp": "1",
        "blockNumber": "1",
        "blockTimestamp": "100000000",
        "ethPrice": "1.2",
        "token0ID": "x",
        "token0Name": "x",
        "token0Symbol": "x",
        "token1ID": "y",
        "token1Name": "y",
        "token1Symbol": "y",
        "pairName": "x - y",
        "updatedVolumeUSD": "1.2",
        "updatedReserveUSD": "1.68",
        "APY": "0.1",
        "token0": {"id": "x", "name": "x", "symbol": "x"},
        "token1": {"id": "y", "name": "y", "symbol": "y"},
    }
    pool2_batch = pool1_batch.copy()
    pool2_batch["id"] = "x3"
    return [pool1_batch, pool2_batch]


class DummyPipeline(Pipeline):
    """A dummy pipeline."""

    def __init__(self) -> None:
        """Initialize Dummy Pipeline."""
        super().__init__([])
        self.updated: bool = False

    def _validate_steps(self) -> None:
        """Dummy steps validation."""

    @staticmethod
    def predict(*args: Any) -> np.ndarray:
        """Predict `steps_forward` timesteps in the future.

        :param args: the args accepted by `pmdarima.Pipeline.predict`.
        :return: a `numpy` array with the dummy predictions.
        """
        return np.ones(args[0])

    def update(self, *args: Any) -> None:
        """Update the dummy pipeline."""
        if len(args[0]):
            self.updated = True


def is_list_of_strings(lst: Any) -> bool:
    """Check if arg is a list of strings."""
    res = False

    if lst and isinstance(lst, list):
        res = all(isinstance(elem, str) for elem in lst)

    return res
