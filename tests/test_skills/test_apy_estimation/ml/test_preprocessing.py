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

"""Test preprocessing operations."""
import numpy as np
import pandas as pd
import pytest

from packages.valory.skills.apy_estimation.ml.preprocessing import prepare_pair_data


class TestPreprocessing:
    """Tests for preprocessing operations."""

    def test_prepare_pair_data(self) -> None:
        """Test `prepare_pair_data`."""
        pairs_hist = pd.DataFrame(
            {
                "id": ["x1", "x2", "x3", "x4", "x5", "x1", "x1", "x1", "x1", "x1"],
                "pairName": [
                    "x - y",
                    "k - m",
                    "l - r",
                    "t - y",
                    "v - b",
                    "x - y",
                    "x - y",
                    "x - y",
                    "x - y",
                    "x - y",
                ],
                "block_timestamp": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                "APY": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.1],
            }
        )

        # test with wrong (non-existing) id.
        with pytest.raises(ValueError, match="Given id `non-existing` does not exist."):
            prepare_pair_data(pairs_hist, pair_id="non-existing", test_size=0.2)

        # test with too few observations.
        with pytest.raises(ValueError, match="Cannot work with 1 < 5 observations."):
            prepare_pair_data(pairs_hist, pair_id="x2", test_size=0.2)

        # test with wrong block timestamp.
        with pytest.raises(
            AttributeError, match="'Int64Index' object has no attribute 'to_period'"
        ):
            prepare_pair_data(pairs_hist, pair_id="x1", test_size=0.2)

        # test with correct data.
        pairs_hist["block_timestamp"] = pd.to_datetime(
            pairs_hist["block_timestamp"], unit="s"
        )
        (y_train, y_test), pair_name = prepare_pair_data(
            pairs_hist, pair_id="x1", test_size=0.2
        )

        np.allclose(y_train, np.array([0.1, 0.6, 0.7, 0.8]))
        np.allclose(y_test, np.array([0.9, 1.1]))
        assert pair_name == "x - y"
