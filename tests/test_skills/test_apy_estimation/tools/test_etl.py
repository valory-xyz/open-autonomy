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

"""Tests for ETL."""
from typing import Any, Dict, List, Optional, Union

import pandas as pd
import pytest
from _pytest.monkeypatch import MonkeyPatch

from packages.valory.skills.apy_estimation_abci.tools.etl import (
    HIST_DTYPES,
    TRANSFORMED_HIST_DTYPES,
    calc_apy,
    calc_change,
    load_hist,
    transform_hist_data,
)


class TestProcessing:
    """Tests for `Preprocessing`."""

    @staticmethod
    def test_calc_change() -> None:
        """Test `calc_change`."""
        test_series = pd.Series([1, 2, 3, 4, 5])
        expected_li: List[Optional[int]] = [1] * 4
        expected_li.insert(0, None)
        expected = pd.Series(expected_li)
        actual = calc_change(test_series)

        pd.testing.assert_series_equal(actual, expected)

    @staticmethod
    @pytest.mark.parametrize(
        "updated_reserve_usd,current_change,unrelated,expected",
        (
            (None, 1, 5.462345, None),
            (5, 1, "test", 14.6),
            (2, 10.3456, b"test", 377.6144),
            (7.34556, 1.45, 845, 14.410065400051186),
        ),
    )
    def test_calc_apy(
        updated_reserve_usd: Optional[float],
        current_change: float,
        unrelated: Any,
        expected: float,
    ) -> None:
        """Test `calc_apy`."""
        test_series = pd.Series(
            [updated_reserve_usd, current_change, unrelated],
            ["updatedReserveUSD", "current_change", "unrelated"],
        )
        actual = calc_apy(test_series)

        if expected is None:
            assert pd.isna(actual)
        else:
            assert actual == expected

    @staticmethod
    def test_transform_hist_data(transformed_history: pd.DataFrame) -> None:
        """Test `transform_hist_data`."""
        # test with missing columns
        with pytest.raises(
            KeyError,
            match="Only a column name can be used for the key in a dtype mappings argument.",
        ):
            transform_hist_data([])

        # test with invalid types
        invalid_types: Dict[str, Union[int, str, Dict[str, str]]] = {
            key: 10 for key in HIST_DTYPES.keys()
        }
        with pytest.raises(TypeError):
            transform_hist_data([invalid_types])  # type: ignore

        # test with only one row, which leads to invalid `current_change`.
        invalid_current_change = invalid_types.copy()
        for i in range(2):
            invalid_current_change[f"token{i}"] = {
                "id": "x",
                "name": "x",
                "symbol": "X",
            }
        with pytest.raises(
            ValueError, match="Wrong number of items passed 31, placement implies 1"
        ):
            transform_hist_data([invalid_current_change])  # type: ignore

        # test with normal input.
        data = invalid_current_change.copy()
        data["volumeUSD"] = 10
        test_pair_hist_raw = [data] * 2
        actual = transform_hist_data(test_pair_hist_raw)  # type: ignore
        pd.testing.assert_frame_equal(
            actual, transformed_history.astype(TRANSFORMED_HIST_DTYPES)
        )

    @staticmethod
    def test_load_hist(
        monkeypatch: MonkeyPatch, transformed_history: pd.DataFrame
    ) -> None:
        """Test `load_hist`."""
        monkeypatch.setattr(pd, "read_csv", lambda _: transformed_history)
        actual = load_hist("")

        actual_timestamp = actual.loc[1, "block_timestamp"]
        expected_timestamp = pd.Timestamp(
            transformed_history.loc[1, "block_timestamp"], unit="s"
        )
        assert expected_timestamp == actual_timestamp

        transformed_history = transformed_history.astype(TRANSFORMED_HIST_DTYPES)
        for df in (actual, transformed_history):
            df.drop(columns="block_timestamp", inplace=True)
        pd.testing.assert_frame_equal(actual, transformed_history)
