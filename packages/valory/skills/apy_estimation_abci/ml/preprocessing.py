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

"""Preprocessing operations."""

from typing import Optional, Tuple, Union

import pandas as pd
import pmdarima as pm


TrainTestSplitType = Tuple[pd.DataFrame, pd.DataFrame]


def filter_pair_data(
    pairs_hist: pd.DataFrame,
    pair_id: str,
) -> Tuple[pd.DataFrame, str, int]:
    """Filter the timeseries data to contain only the block's timestamp and the APY for a specific pair.

    :param pairs_hist: the pairs histories dataframe.
    :param pair_id: the id of the pair that its data should be filtered.
    :return: the filtered data for the specific pair, the pair's name and the number of the pair's observations.
    """
    # Create mask for the given pair.
    pair_m = pairs_hist["id"] == pair_id
    n_pair_items = pair_m.sum()

    if n_pair_items == 0:
        raise ValueError(f"Given id `{pair_id}` does not exist!")

    # Get the pair's name.
    pair_name = pairs_hist.loc[pair_m, "pairName"].iloc[0]

    # Get the pair's APY, set the block's timestamp as an index
    # and convert it to a pandas period to create the timeseries.
    y = pairs_hist.loc[pair_m, ["block_timestamp", "APY"]].set_index("block_timestamp")
    y.index = y.index.to_period("D")

    return y, pair_name, n_pair_items


def prepare_pair_data(
    pairs_hist: pd.DataFrame,
    pair_id: str,
    test_size: Optional[Union[float, int]] = 0.25,
) -> Tuple[TrainTestSplitType, str]:
    """Prepare the timeseries data for a specific pair.

    :param pairs_hist: the pairs histories dataframe.
    :param pair_id: the id of the pair that its data should be prepared.
    :param test_size: float, int or None, optional (default=None)
        * If float, should be between 0.0 and 1.0 and represent the proportion of the dataset
        to include in the test split.
        * If int, represents the absolute number of test samples.
        * If None, the value is set to the complement of the train size.
        * If train_size is also None, it will be set to 0.25.
    :return: the train-test split for the specific pair and the pair's name.
    """
    y, pair_name, n_pair_items = filter_pair_data(pairs_hist, pair_id)

    threshold = 5
    if n_pair_items < threshold:
        raise ValueError(f"Cannot work with {n_pair_items} < {threshold} observations.")

    # Perform a train test split.
    y_train, y_test = pm.model_selection.train_test_split(y, test_size=test_size)

    return (y_train, y_test), pair_name
