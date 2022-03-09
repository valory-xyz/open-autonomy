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

from typing import Dict, Optional, Tuple, Union

import pandas as pd
import pandas.core.groupby
import pmdarima as pm


SingleIdToSplitType = Dict[str, pd.DataFrame]
TrainTestSplitType = Tuple[SingleIdToSplitType, SingleIdToSplitType]


def group_and_filter_pair_data(
    pairs_hist: pd.DataFrame, threshold: int = 5
) -> pandas.core.groupby.DataFrameGroupBy:
    """
    Filter the timeseries data to contain only the block's timestamp, the pair name and the APY and group by pair.

    :param pairs_hist: the pairs histories dataframe.
    :param threshold: acceptable threshold for the number of items that each pair contains.
        If less, raises a `ValueError`.
    :return: the filtered data grouped by pair.
    """
    # Group by pair.
    grouped_and_filtered = pairs_hist.groupby("id")[["blockTimestamp", "APY"]]

    # Count the number of items per pair.
    n_pair_items = grouped_and_filtered.size()
    pairs_fewer_than_threshold = n_pair_items.loc[n_pair_items < threshold]
    if not pairs_fewer_than_threshold.empty:
        raise ValueError(
            f"Cannot work with < {threshold} observations for: \n{pairs_fewer_than_threshold.to_string()}"
        )

    return grouped_and_filtered


def prepare_pair_data(
    pairs_hist: pd.DataFrame,
    test_size: Optional[Union[float, int]] = 0.25,
) -> TrainTestSplitType:
    """Prepare the timeseries data for all the pairs.

    :param pairs_hist: the pairs histories dataframe.
    :param test_size: float, int or None, optional (default=None)
        * If float, should be between 0.0 and 1.0 and represent the proportion of the dataset
        to include in the test split.
        * If int, represents the absolute number of test samples.
        * If None, the value is set to the complement of the train size.
        * If train_size is also None, it will be set to 0.25.
    :return: a dictionary with the pair ids as keys and their corresponding train-test splits.
    """
    grouped_and_filtered = group_and_filter_pair_data(pairs_hist)

    train_splits = {}
    test_splits = {}
    for pair_id, filtered_pair_data in grouped_and_filtered:
        # Get the pair's APY, set the block's timestamp as an index
        # and convert it to a pandas period to create the timeseries.
        y = filtered_pair_data.loc[:, ["blockTimestamp", "APY"]].set_index(
            "blockTimestamp"
        )
        y.index = y.index.to_period("D")
        # Perform a train test split.
        y_train, y_test = pm.model_selection.train_test_split(y, test_size=test_size)
        # Store the splits mapped to their ids.
        train_splits[f"{pair_id}.csv"] = y_train
        test_splits[f"{pair_id}.csv"] = y_test

    return train_splits, test_splits
