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

"""Test the `tools/general.py` module of the skill."""
import json

import pytest

from packages.valory.skills.apy_estimation.tools.queries import (
    eth_price_usd_q,
    block_from_timestamp_q,
    top_n_pairs_q,
    pairs_q,
)

eth_q_parameterization = pytest.mark.parametrize(
    (
        'bundle_id',
        'block',
        'expected',
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
            """
        )
    ]
)


class TestQueries:
    @staticmethod
    @eth_q_parameterization
    def test_eth_price_usd_q(bundle_id, block, expected):
        actual = eth_price_usd_q(bundle_id, block)
        assert str(json.loads(actual)).split() == expected.split()

    @staticmethod
    def test_block_from_timestamp_q():
        actual = block_from_timestamp_q(100)
        expected = """
                   {blocks(first: 1, orderBy: timestamp, orderDirection: asc, where: 
                       {
                           timestamp_gte: 100, timestamp_lte: 700
                       })
                       {
                           timestamp
                           number
                       }
                       }
                   """
        assert str(json.loads(actual)).split() == expected.split()

    @staticmethod
    def test_top_n_pairs_q():
        actual = top_n_pairs_q(0)
        expected = """
                   {
                       pairs(
                           first: 0, orderBy: trackedReserveETH, 
                       orderDirection: desc) 
                       {id}
                   }
                   """
        assert str(json.loads(actual)).split() == expected.split()

    @staticmethod
    def test_pairs_q():
        actual = pairs_q(0, ['x0', 'x1', 'x2'])
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
        assert str(json.loads(actual)).split() == expected.split()
