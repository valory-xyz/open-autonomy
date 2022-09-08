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

"""Test preprocessing operations."""

# pylint: skip-file

import platform

import numpy as np
import pandas as pd
import pytest

from packages.valory.skills.apy_estimation_abci.ml.preprocessing import (
    group_and_filter_pair_data,
    prepare_pair_data,
)


class TestPreprocessing:
    """Tests for preprocessing operations."""

    @staticmethod
    def test_group_and_filter_pair_data(
        transformed_historical_data: pd.DataFrame,
    ) -> None:
        """Test `group_and_filter_pair_data`."""
        # test with too few observations.
        with pytest.raises(ValueError, match="Cannot work with < 5 observations for: "):
            not_enough_data = transformed_historical_data[
                transformed_historical_data["id"].isin(["x2", "x3"])
            ]
            group_and_filter_pair_data(not_enough_data)

        # test with correct number of data.
        id_with_enough_observations = "0x2b4c76d0dc16be1c31d4c1dc53bf9b45987fc75c"
        pool1_data = transformed_historical_data.loc[
            transformed_historical_data["id"] == id_with_enough_observations
        ]
        pool2_data = pool1_data.copy()
        pool2_data["id"] = "test_id"
        test_data = pd.concat([pool1_data, pool2_data])
        grouped_and_filtered = group_and_filter_pair_data(test_data)

        filtering_columns = ["blockTimestamp", "APY"]
        pd.testing.assert_frame_equal(
            grouped_and_filtered.get_group(id_with_enough_observations),
            pool1_data[filtering_columns],
        )
        pd.testing.assert_frame_equal(
            grouped_and_filtered.get_group("test_id"), pool2_data[filtering_columns]
        )

    @pytest.mark.skipif(
        platform.system() == "Windows", reason="Need to be investigated."
    )
    def test_prepare_pair_data(self, transformed_historical_data: pd.DataFrame) -> None:
        """Test `prepare_pair_data`."""
        id_with_enough_observations = "0x2b4c76d0dc16be1c31d4c1dc53bf9b45987fc75c"
        pool1_data = transformed_historical_data.loc[
            transformed_historical_data["id"] == id_with_enough_observations
        ]
        pool2_data = pool1_data.copy()
        pool2_data["id"] = "test_id"
        test_data = pd.concat([pool1_data, pool2_data])

        train_splits, test_splits = prepare_pair_data(
            test_data,
            test_size=0.2,
        )

        assert len(train_splits.keys()) == len(test_splits.keys())

        for (id_train, y_train), (id_test, y_test) in zip(
            train_splits.items(), test_splits.items()
        ):
            np.allclose(y_train, np.array([0.1, 0.6, 0.7, 0.8]))
            np.allclose(y_test, np.array([0.9, 1.1]))
            assert id_train == id_test
            assert id_train in (
                "0x2b4c76d0dc16be1c31d4c1dc53bf9b45987fc75c.csv",
                "test_id.csv",
            )

        # test with wrong block timestamp.
        test_data["blockTimestamp"] = test_data["blockTimestamp"].view(int)
        with pytest.raises(
            AttributeError, match="'Int64Index' object has no attribute 'to_period'"
        ):
            prepare_pair_data(
                test_data,
                test_size=0.2,
            )
