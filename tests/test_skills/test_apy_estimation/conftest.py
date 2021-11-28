"""Configurations for APY skill's tests."""

from typing import Any, Dict, Tuple, Union
from unittest import mock

import pandas as pd
import pytest
from aea.skills.base import SkillContext

from packages.valory.skills.apy_estimation.models import SharedState


HeaderType = Dict[str, str]
SpecsType = Dict[str, Union[str, int, HeaderType]]


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
    return """
            {
                bundles(
                    first: 1,
                    block: {number: 3830367},
                    where: {
                        id: 1
                    }
                )
                {ethPrice}
            }
            """


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

    return """
    {
        pairs(
            where: {id_in: ["0xec454eda10accdd66209c57af8c12924556f3abd"]},
            block: {number: 3830367}
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
def shared_state():
    """Initialize a test shared state."""
    return SharedState(name="", skill_context=mock.MagicMock())


def is_list_of_strings(lst: Any) -> bool:
    """Check if arg is a list of strings."""
    res = False

    if lst and isinstance(lst, list):
        res = all(isinstance(elem, str) for elem in lst)

    return res
