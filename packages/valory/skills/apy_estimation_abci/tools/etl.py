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


def transform_hist_data(pairs_hist_raw: ResponseItemType) -> pd.DataFrame:
    """Transform pairs' history into a dataframe and add extra fields.

    :param pairs_hist_raw: the pairs historical data non-transformed.
    :return: a dataframe with the given historical data, containing extra fields. These are:
         * [token0ID, token0Name, token0Symbol]: split from `token0`.
         * [token1ID, token1Name, token1Symbol]: split from `token1`.
         * pairName: the current's pair's name, which is derived by: 'token0_name - token1_name'.
         * updatedVolumeUSD: the tracked volume USD, but if it is 0, then the untracked volume USD.
         * updatedReserveUSD: the tracked reserve USD, but if it is 0, then the untracked reserve USD.
         * current_change: the current day's change in volume USD.
         * APY: the APY.

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

    # Sort the dictionary.
    pairs_hist.sort_values(
        by=["blockTimestamp", "token0Symbol", "token1Symbol"],
        ascending=True,
        inplace=True,
    )

    return pairs_hist


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
    pairs_hist.drop(columns=drop_cols)

    # Convert timestamp to unix int.
    pairs_hist["blockTimestamp"] = pairs_hist["blockTimestamp"].view(int) / 10 ** 9

    # Convert history to a list of dicts.
    reverted_pairs_hist = pairs_hist.to_dict("records")

    return cast(ResponseItemType, reverted_pairs_hist)


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
