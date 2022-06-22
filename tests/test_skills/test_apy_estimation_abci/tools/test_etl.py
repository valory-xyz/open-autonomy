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

"""Tests for ETL."""
import platform
from typing import Any, Dict, List, Optional, Union

import pandas as pd
import pytest
from _pytest.monkeypatch import MonkeyPatch

from packages.valory.skills.apy_estimation_abci.tools.etl import (
    HIST_DTYPES,
    ResponseItemType,
    apply_revert_token_cols_wrapper,
    calc_apy,
    calc_change,
    prepare_batch,
    revert_transform_hist_data,
    transform_hist_data,
)
from packages.valory.skills.apy_estimation_abci.tools.io import (
    TRANSFORMED_HIST_DTYPES,
    load_hist,
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
            ["updatedReserveUSD", "currentChange", "unrelated"],
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
            ValueError,
            match="APY cannot be calculated if there are not at least two observations for a pool!",
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

        actual_timestamp = actual.loc[1, "blockTimestamp"]
        expected_timestamp = pd.Timestamp(
            transformed_history.loc[1, "blockTimestamp"], unit="s"
        )
        assert expected_timestamp == actual_timestamp

        transformed_history = transformed_history.astype(TRANSFORMED_HIST_DTYPES)
        for df in (actual, transformed_history):
            df.drop(columns="blockTimestamp", inplace=True)
        pd.testing.assert_frame_equal(actual, transformed_history)

    @staticmethod
    def test_load_hist_file_not_found(
        monkeypatch: MonkeyPatch, transformed_history: pd.DataFrame
    ) -> None:
        """Test `load_hist` when file is not found."""
        with pytest.raises(IOError):
            load_hist("non_existing")

    @staticmethod
    @pytest.mark.parametrize("invalid", (True, False))
    def test_prepare_batch(
        monkeypatch: MonkeyPatch,
        transformed_historical_data_no_datetime_conversion: pd.DataFrame,
        batch: ResponseItemType,
        invalid: bool,
    ) -> None:
        """Test `prepare_batch`."""
        previous_batch = transformed_historical_data_no_datetime_conversion.iloc[
            [0, 2]
        ].reset_index(drop=True)

        if invalid:
            invalid_pool_item = batch[0].copy()
            non_existing_id = "non_existing"
            invalid_pool_item["id"] = non_existing_id
            batch.append(invalid_pool_item)
            with pytest.raises(
                ValueError, match="Could not find any previous history in "
            ):
                prepare_batch(previous_batch, batch)

        else:
            prepared_batches = prepare_batch(previous_batch, batch).groupby("id")
            assert len(prepared_batches) == 2
            expected_ids = {"0x2b4c76d0dc16be1c31d4c1dc53bf9b45987fc75c", "x3"}
            assert expected_ids == set(prepared_batches.groups.keys())
            for id_ in expected_ids:
                assert len(prepared_batches.get_group(id_).index) == 1

    @staticmethod
    def test_apply_revert_token_cols_wrapper() -> None:
        """Test `apply_revert_token_cols_wrapper`."""
        test_series = pd.Series(
            {
                "xID": 0,
                "xName": "test",
                "xSymbol": "T",
            }
        )
        res = apply_revert_token_cols_wrapper("x")(test_series)
        assert res == {
            "id": 0,
            "name": "test",
            "symbol": "T",
        }

    @staticmethod
    @pytest.mark.skipif(
        platform.system() == "Windows", reason="Need to be investigated."
    )
    def test_revert_transform_hist_data(
        transformed_historical_data: pd.DataFrame,
        historical_data: Dict[str, List[Union[None, Dict[str, str], int, str, float]]],
    ) -> None:
        """Test `revert_transform_hist_data`."""
        reverted_pairs_hist = revert_transform_hist_data(transformed_historical_data)

        # Convert list of dicts into dict of lists.
        actual_reverted_pairs_hist: Dict[
            str, List[Union[None, Dict[str, str], int, str, float]]
        ] = {k: [] for k in reverted_pairs_hist[0].keys()}
        for (
            d
        ) in reverted_pairs_hist:  # you can list as many input dicts as you want here
            for key, value in d.items():
                actual_reverted_pairs_hist[key].append(value)

        assert actual_reverted_pairs_hist == historical_data
