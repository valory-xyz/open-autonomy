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
import numpy as np
import pandas as pd
import pytest

from packages.valory.skills.apy_estimation_abci.ml.preprocessing import (
    prepare_pair_data,
)


class TestPreprocessing:
    """Tests for preprocessing operations."""

    def test_prepare_pair_data(self, transformed_historical_data: pd.DataFrame) -> None:
        """Test `prepare_pair_data`."""
        # test with wrong (non-existing) id.
        with pytest.raises(ValueError, match="Given id `non-existing` does not exist."):
            prepare_pair_data(
                transformed_historical_data, pair_id="non-existing", test_size=0.2
            )

        # test with too few observations.
        with pytest.raises(ValueError, match="Cannot work with 1 < 5 observations."):
            prepare_pair_data(transformed_historical_data, pair_id="x2", test_size=0.2)

        # test with correct data.
        transformed_historical_data["blockTimestamp"] = pd.to_datetime(
            transformed_historical_data["blockTimestamp"], unit="s"
        )
        (y_train, y_test), pair_name = prepare_pair_data(
            transformed_historical_data,
            pair_id="0x2b4c76d0dc16be1c31d4c1dc53bf9b45987fc75c",
            test_size=0.2,
        )

        np.allclose(y_train, np.array([0.1, 0.6, 0.7, 0.8]))
        np.allclose(y_test, np.array([0.9, 1.1]))
        assert pair_name == "x - y"

        # test with wrong block timestamp.
        transformed_historical_data["blockTimestamp"] = transformed_historical_data[
            "blockTimestamp"
        ].view(int)
        with pytest.raises(
            AttributeError, match="'Int64Index' object has no attribute 'to_period'"
        ):
            prepare_pair_data(
                transformed_historical_data,
                pair_id="0x2b4c76d0dc16be1c31d4c1dc53bf9b45987fc75c",
                test_size=0.2,
            )
