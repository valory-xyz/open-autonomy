"""Module for the queries building functions."""
import json
from typing import List, Optional


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

    return json.dumps(query).encode("utf-8")


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

    return json.dumps(query).encode("utf-8")


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

    return json.dumps(query).encode("utf-8")


def pairs_q(block: int, top_n_ids: List[str]) -> bytes:
    """Create a query to get data for the first `top_n` pools based on their total liquidity.

    :param block: the block for which the data are going to be fetched.
    :param top_n_ids: the ids of the top_n pools to be fetched.
    :return: the built query.
    """

    query = (
        """
    {
        pairs(
            where: {id_in: 
            [\""""
        + '","'.join(top_n_ids)
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

    return json.dumps(query).encode("utf-8")
