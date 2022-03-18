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

"""ETL related operations."""

from typing import Callable, Dict, List, Optional, Union, cast

import pandas as pd


ResponseItemType = List[Dict[str, Union[str, Dict[str, str]]]]

# Define a dictionary with the data types for each column of the historical data.
HIST_DTYPES = {
    "createdAtBlockNumber": int,
    "createdAtTimestamp": int,
    "id": str,
    "liquidityProviderCount": int,
    "reserve0": float,
    "reserve1": float,
    "reserveETH": float,
    "reserveUSD": float,
    "token0Price": float,
    "token1Price": float,
    "totalSupply": float,
    "trackedReserveETH": float,
    "untrackedVolumeUSD": float,
    "txCount": int,
    "volumeToken0": float,
    "volumeToken1": float,
    "volumeUSD": float,
    "forTimestamp": int,
    "blockNumber": int,
    "blockTimestamp": int,
    "ethPrice": float,
    "token0": object,
    "token1": object,
}

# Define a dictionary with the data types of the columns of the transformed historical data.
TRANSFORMED_HIST_DTYPES = HIST_DTYPES.copy()

NEW_STR_COLS = (
    "token0ID",
    "token0Name",
    "token0Symbol",
    "token1ID",
    "token1Name",
    "token1Symbol",
    "pairName",
)

NEW_FLOAT_COLS = ("updatedVolumeUSD", "updatedReserveUSD", "currentChange", "APY")

TOKEN_COL_NAMES = ("token0", "token1")

for new_str_col in NEW_STR_COLS:
    TRANSFORMED_HIST_DTYPES[new_str_col] = str

for new_float_col in NEW_FLOAT_COLS:
    TRANSFORMED_HIST_DTYPES[new_float_col] = float

for old_col in TOKEN_COL_NAMES:
    del TRANSFORMED_HIST_DTYPES[old_col]


def calc_change(volume_usd: pd.Series) -> pd.Series:
    """Calculate the change between two days. The series argument needs to be sorted by date!

    :param volume_usd: a series with volumes, sorted by date.
    :return: a new series with the current day's change for each date of the given `volume_usd` series.
    """
    return volume_usd - volume_usd.shift(1)


def calc_apy(x: pd.Series) -> Optional[float]:
    """Calculates the APY for a given pool's info.

    :param x: a series with historical data.
    :return: the daily APY.
    """
    res = None

    if x["updatedReserveUSD"]:
        res = (x["currentChange"] * 0.002 * 365 * 100) / x["updatedReserveUSD"]

    return res


def apply_hist_based_calculations(pairs_hist: pd.DataFrame) -> None:
    """Fill the given pairs' history with the current change in USD and APY values."""
    # Calculate the current change of volume in USD.
    pairs_hist["currentChange"] = pairs_hist.groupby("id")[
        "updatedVolumeUSD"
    ].transform(calc_change)

    # Drop NaN values (essentially, this is the first day's `current_change`, because we cannot calculate it).
    pairs_hist.dropna(subset=["currentChange"], inplace=True)

    if len(pairs_hist.index) == 0:
        raise ValueError(
            "APY cannot be calculated if there are not at least two observations for a pool!"
        )

    # Calculate APY.
    pairs_hist["APY"] = pairs_hist.apply(calc_apy, axis=1)
    # Drop rows with NaN APY values.
    pairs_hist.dropna(subset=["APY"], inplace=True)


def transform_hist_data(
    pairs_hist_raw: ResponseItemType, batch: bool = False
) -> pd.DataFrame:
    """Transform pairs' history into a dataframe and add extra fields.

    :param pairs_hist_raw: the pairs historical data non-transformed.
    :param batch: whether the input is a batch which contains single a data point per pool.
    :return: a dataframe with the given historical data, containing extra fields. These are:
         * [token0ID, token0Name, token0Symbol]: split from `token0`.
         * [token1ID, token1Name, token1Symbol]: split from `token1`.
         * pairName: the current's pair's name, which is derived by: 'token0_name - token1_name'.
         * updatedVolumeUSD: the tracked volume USD, but if it is 0, then the untracked volume USD.
         * updatedReserveUSD: the tracked reserve USD, but if it is 0, then the untracked reserve USD.
         * current_change: the current day's change in volume USD, only if `batch` is `False`.
         * APY: the APY, only if `batch` is `False`.

         The dataframe is also sorted by the block's timestamp and the pair's tokens' names,
         and the entries for which the APY cannot be calculated are being dropped.
    """
    # Convert history to a dataframe.
    pairs_hist = pd.DataFrame(pairs_hist_raw).astype(HIST_DTYPES)

    # Split the dictionary-like token cols.
    for token_col in TOKEN_COL_NAMES:
        pairs_hist[f"{token_col}ID"] = (
            pairs_hist[token_col].apply(lambda x: x["id"]).astype(str)
        )
        pairs_hist[f"{token_col}Name"] = (
            pairs_hist[token_col].apply(lambda x: x["name"]).astype(str)
        )
        pairs_hist[f"{token_col}Symbol"] = (
            pairs_hist[token_col].apply(lambda x: x["symbol"]).astype(str)
        )
    # Drop the original dictionary-like token cols.
    pairs_hist.drop(columns=list(TOKEN_COL_NAMES), inplace=True)

    # Create pair's name.
    pairs_hist["pairName"] = pairs_hist["token0Name"] + " - " + pairs_hist["token1Name"]

    # Create a volume USD and a reserve USD taking the untracked amount into consideration as well.
    pairs_hist["updatedVolumeUSD"] = pairs_hist["volumeUSD"]
    pairs_hist["updatedReserveUSD"] = (
        pairs_hist["trackedReserveETH"] * pairs_hist["ethPrice"]
    )

    # Create a mask for all the untracked cases.
    not_tracked_m = pairs_hist["updatedVolumeUSD"] == 0

    # Keep the untracked amount for the untracked cases.
    pairs_hist.loc[not_tracked_m, "updatedVolumeUSD"] = pairs_hist.loc[
        not_tracked_m, "untrackedVolumeUSD"
    ]
    pairs_hist.loc[not_tracked_m, "updatedReserveUSD"] = pairs_hist.loc[
        not_tracked_m, "reserveUSD"
    ]

    if not batch:
        apply_hist_based_calculations(pairs_hist)

    # Sort the dictionary.
    pairs_hist.sort_values(
        by=["blockTimestamp", "token0Symbol", "token1Symbol"],
        ascending=True,
        inplace=True,
    )

    return pairs_hist


def prepare_batch(
    previous_batch: pd.DataFrame, current_batch_raw: ResponseItemType
) -> pd.DataFrame:
    """Prepare a batch, using the currently fetched batch from the subgraph and the last utilized batch.

    :param previous_batch: the last utilized batch.
    :param current_batch_raw: the currently fetched data, non-transformed.
    :return: a dictionary with the pool ids, mapped to their current data point of the timeseries.
    """
    # Transform the current batch.
    current_batch = transform_hist_data(current_batch_raw, batch=True)
    # Append the current batch to the previous batch.
    batches = pd.concat([previous_batch, current_batch])
    # Calculate the last APY value per pool, using the batches.
    prepared_batches = []
    for pool_id, pool_batch in batches.groupby("id"):
        if len(pool_batch.index) < 2:
            raise ValueError(
                f"Could not find any previous history in {pool_batch} for pool `{pool_id}`!"
            )
        # Since we have concatenated the current batch after the previous batch
        # and `groupby` preserves the order of rows within each group,
        # then we do not need to worry about the sorting of the batches.
        apply_hist_based_calculations(pool_batch)
        prepared_batches.append(pool_batch)

    return pd.concat(prepared_batches)


def apply_revert_token_cols_wrapper(
    token_name: str,
) -> Callable[[pd.Series], Dict[str, str]]:
    """A wrapper to revert a token column as it was before the transformation.

    :param token_name: the token name for which we want to revert.
    :return: a dictionary of the initial representation.
    """

    def apply_revert_token_cols(x: pd.Series) -> Dict[str, str]:
        """Revert the token column as it was before the transformation.

        :param x: the input series row.
        :return: a dictionary of the initial representation.
        """
        return {
            "id": x[f"{token_name}ID"],
            "name": x[f"{token_name}Name"],
            "symbol": x[f"{token_name}Symbol"],
        }

    return apply_revert_token_cols


def revert_transform_hist_data(pairs_hist: pd.DataFrame) -> ResponseItemType:
    """Revert the transformation of pairs' history.

    :param pairs_hist: the transformed pairs' historical data.
    :return: the reverted historical data.
    """
    # Re-create the old data which have been dropped.
    for token_name in TOKEN_COL_NAMES:
        pairs_hist[token_name] = pairs_hist.apply(
            apply_revert_token_cols_wrapper(token_name), axis=1
        )

    # Drop columns that occur after the transformation.
    drop_cols = list(NEW_STR_COLS + NEW_FLOAT_COLS)
    for token_name in TOKEN_COL_NAMES:
        drop_cols.extend(
            [f"{token_name}ID", f"{token_name}Name", f"{token_name}Symbol"]
        )
    pairs_hist.drop(columns=drop_cols, inplace=True)

    # Convert timestamp to unix int.
    pairs_hist["blockTimestamp"] = pairs_hist["blockTimestamp"].view(int) / 10 ** 9

    # Convert history to a list of dicts.
    reverted_pairs_hist = pairs_hist.to_dict("records")

    return cast(ResponseItemType, reverted_pairs_hist)
