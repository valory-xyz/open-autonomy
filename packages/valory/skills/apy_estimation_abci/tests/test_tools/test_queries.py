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

"""Test the `tools/general.py` module of the skill."""

# pylint: skip-file

import json
from typing import Dict, Optional, Union

import pytest
from _pytest.monkeypatch import MonkeyPatch
from aea_test_autonomy.helpers.base import identity

from packages.valory.skills.apy_estimation_abci.tools import queries
from packages.valory.skills.apy_estimation_abci.tools.queries import (
    block_from_number_q,
    block_from_timestamp_q,
    eth_price_usd_q,
    existing_pairs_q,
    finalize_q,
    latest_block_q,
    pairs_q,
    top_n_pairs_q,
)


eth_q_parameterization = pytest.mark.parametrize(
    (
        "bundle_id",
        "block",
        "expected",
    ),
    [
        (
            0,
            0,
            """
            {
                bundles(
                    first: 1,
                    block: {number: 0},
                    where: {
                        id: 0
                    }
                )
                {ethPrice}
            }
            """,
        ),
        (
            0,
            None,
            """
            {
                bundles(
                    first: 1,
                    where: {
                        id: 0
                    }
                )
                {ethPrice}
            }
            """,
        ),
    ],
)


class TestQueries:
    """Tests for `Queries`."""

    @staticmethod
    def test_finalize_q() -> None:
        """Test `finalize_q`."""
        # Test result.
        test_string = "test_string: {test: value}"
        actual = finalize_q(test_string)
        expected: Union[Dict[str, str], bytes] = {"query": test_string}
        expected = json.dumps(expected).encode("utf-8")
        assert actual == expected

    @staticmethod
    @eth_q_parameterization
    def test_eth_price_usd_q(
        bundle_id: int, block: Optional[int], expected: str, monkeypatch: MonkeyPatch
    ) -> None:
        """Test `eth_price_usd_q`."""
        monkeypatch.setattr(
            queries,
            "finalize_q",
            identity,
        )
        actual = eth_price_usd_q(bundle_id, block)
        assert actual.split() == expected.split()

    @staticmethod
    def test_block_from_timestamp_q(monkeypatch: MonkeyPatch) -> None:
        """Test `block_from_timestamp_q`."""
        monkeypatch.setattr(
            queries,
            "finalize_q",
            identity,
        )
        actual = block_from_timestamp_q(100)
        expected = """
                   {
                   blocks(
                   first:
                   1, orderBy: timestamp, orderDirection: asc, where:
                       {
                           timestamp_gte: 100, timestamp_lte: 700
                       }
                       )
                       {
                           timestamp
                           number
                       }
                       }
                   """
        assert actual.split() == expected.split()

    @staticmethod
    def test_block_from_number_q(monkeypatch: MonkeyPatch) -> None:
        """Test `block_from_number_q`."""
        monkeypatch.setattr(
            queries,
            "finalize_q",
            identity,
        )
        actual = block_from_number_q(100)
        expected = """
                   {
                   blocks(
                   first:
                   1, orderBy: timestamp, orderDirection: asc, where:
                       {
                           number: 100
                       }
                       )
                       {
                           timestamp
                           number
                       }
                       }
                   """
        assert actual.split() == expected.split()

    @staticmethod
    def test_latest_block(monkeypatch: MonkeyPatch) -> None:
        """Test `latest_block`."""
        monkeypatch.setattr(
            queries,
            "finalize_q",
            identity,
        )
        actual = latest_block_q()
        expected = """
                   {
                        blocks(
                            first: 1,
                            orderBy: timestamp,
                            orderDirection: desc
                        )
                        {
                            timestamp
                            number
                        }
                    }
                   """
        assert actual.split() == expected.split()

    @staticmethod
    def test_top_n_pairs_q(monkeypatch: MonkeyPatch) -> None:
        """Test `top_n_pairs_q`."""
        monkeypatch.setattr(
            queries,
            "finalize_q",
            identity,
        )
        actual = top_n_pairs_q(0)
        expected = """
                   {
                       pairs(
                           first: 0, orderBy: trackedReserveETH,
                       orderDirection: desc
                       )
                       {id}
                   }
                   """
        assert actual.split() == expected.split()

    @staticmethod
    def test_pairs_q(monkeypatch: MonkeyPatch) -> None:
        """Test `pairs_q`."""
        monkeypatch.setattr(
            queries,
            "finalize_q",
            identity,
        )
        actual = pairs_q(0, ["x0", "x1", "x2"])
        expected = """
                   {
                       pairs(
                           where: {id_in: ["x0","x1","x2"]},
                           block: {number: 0}
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
        assert actual.split() == expected.split()

    @staticmethod
    def test_existing_pairs_q(monkeypatch: MonkeyPatch) -> None:
        """Test `existing_pairs_q`."""
        monkeypatch.setattr(
            queries,
            "finalize_q",
            identity,
        )
        actual = existing_pairs_q(["x0", "x1", "x2"])
        expected = """
                   {
                       pairs(
                           where: {id_in: ["x0","x1","x2"]},
                       ) {
                           id
                       }
                   }
                   """
        assert actual.split() == expected.split()
