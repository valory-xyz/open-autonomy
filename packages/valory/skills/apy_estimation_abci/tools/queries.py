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


"""Module for the queries building functions."""
import json
from typing import List, Optional


def finalize_q(query: str) -> bytes:
    """Finalize the given query string, i.e., add it under a `queries` key and convert it to bytes."""
    finalized_query = {"query": query}
    encoded_query = json.dumps(finalized_query, sort_keys=True).encode("utf-8")

    return encoded_query


def eth_price_usd_q(bundle_id: int, block: Optional[int] = None) -> bytes:
    """Create query to get current ETH price in USD.

    If `block` is given, then the query is being build for the corresponding block's price.

    :param bundle_id: the bundle id.
    :param block: the block for which the price will be fetched.
    :return: the built query.
    """

    if block is not None:
        query = (
            """
        {
            bundles(
                first: 1,
                block: {number: """
            + str(block)
            + """},
                where: {
                    id: """
            + str(bundle_id)
            + """
                }
            )
            {ethPrice}
        }
        """
        )

    else:
        query = (
            """
        {
            bundles(
                first: 1,
                where: {
                    id: """
            + str(bundle_id)
            + """
                }
            )
            {ethPrice}
        }
        """
        )

    return finalize_q(query)


def block_from_timestamp_q(timestamp: int) -> bytes:
    """Create query to get a block from a timestamp.

    :param timestamp: the timestamp for which the blocks will be fetched.
    :return: the built query.
    """
    query = (
        """
    {
        blocks(
            first: 1,
            orderBy: timestamp,
            orderDirection: asc,
            where: {
                timestamp_gte: """
        + str(timestamp)
        + """,
                timestamp_lte: """
        + str(timestamp + 600)
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

    return finalize_q(query)


def block_from_number_q(number: int) -> bytes:
    """Create query to get a block from a block number.

    :param number: the number of the block to be fetched.
    :return: the built query.
    """
    query = (
        """
    {
        blocks(
            first: 1,
            orderBy: timestamp,
            orderDirection: asc,
            where: {
                number: """
        + str(number)
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

    return finalize_q(query)


def latest_block_q() -> bytes:
    """Create query to get the latest block.

    :return: the built query.
    """
    query = """
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

    return finalize_q(query)


def top_n_pairs_q(top_n: int) -> bytes:
    """Create a query to get the first `top_n` pool ids based on their total liquidity.

    :param top_n: the top_n pools to be fetched based on their total liquidity.
    :return: the built query.
    """

    query = (
        """
    {
        pairs(
            first: """
        + str(top_n)
        + """,
            orderBy: trackedReserveETH,
            orderDirection: desc
        )
        {id}
    }
    """
    )

    return finalize_q(query)


def pairs_q(block: int, ids: List[str]) -> bytes:
    """Create a query to get data for the given pools based on their total liquidity.

    :param block: the block for which the data are going to be fetched.
    :param ids: the ids of the pools to be fetched.
    :return: the built query.
    """

    query = (
        """
    {
        pairs(
            where: {id_in:
            [\""""
        + '","'.join(ids)
        + """"]},
            block: {number: """
        + str(block)
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

    return finalize_q(query)
