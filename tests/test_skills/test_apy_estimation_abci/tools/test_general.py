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

"""Test the `tools/general.py` module of the skill."""
import os
from pathlib import PosixPath

import pytest
from _pytest.monkeypatch import MonkeyPatch

from packages.valory.skills.abstract_round_abci.io.paths import create_pathdirs
from packages.valory.skills.apy_estimation_abci.tools.general import (
    filter_out_numbers,
    gen_unix_timestamps,
)


class TestGeneral:
    """Tests for general tools."""

    @staticmethod
    def test_gen_unix_timestamps(monkeypatch: MonkeyPatch) -> None:
        """Test get UNIX timestamps."""
        day_in_unix = 24 * 60 * 60
        n_months_to_check = 1
        days_in_month = 30

        timestamps = list(
            gen_unix_timestamps(
                day_in_unix * n_months_to_check * (days_in_month + 1), n_months_to_check
            )
        )

        expected = day_in_unix
        for timestamp in timestamps:
            assert isinstance(timestamp, int)
            assert timestamp == expected
            expected += day_in_unix

    @staticmethod
    @pytest.mark.parametrize(
        "test_path", ("", "file.extension", "folder/file.extension")
    )
    def test_create_pathdirs(tmp_path: PosixPath, test_path: str) -> None:
        """Test create pathdirs."""
        full_test_path = os.path.join(tmp_path, test_path)
        folder_name = os.path.dirname(test_path)

        if folder_name:
            path_to_folder = os.path.join(tmp_path, folder_name)
            expected_folders_amount = 1

        else:
            path_to_folder = tmp_path  # type: ignore
            expected_folders_amount = 0

        create_pathdirs(full_test_path)

        n_files_in_folder = len(
            [name for name in os.listdir(tmp_path) if os.path.isfile(name)]
        )
        n_folders_in_folder = len(
            [
                name
                for name in os.listdir(tmp_path)
                if os.path.isdir(os.path.join(tmp_path, name))
            ]
        )

        assert n_files_in_folder == 0
        assert n_folders_in_folder == expected_folders_amount
        assert os.path.isdir(path_to_folder)

    @staticmethod
    @pytest.mark.parametrize(
        "unfiltered_string,expected",
        (
            (
                "test0this1string",
                1,
            ),
            (
                "test0thi5s1string",
                51,
            ),
            (
                "345678",
                345678,
            ),
            (
                "1234test567this89number10here",
                123456789,
            ),
            (
                "test_this_string",
                None,
            ),
        ),
    )
    def test_filter_out_numbers(unfiltered_string: str, expected: int) -> None:
        """Test `filter_out_numbers`."""
        filtered_num = filter_out_numbers(unfiltered_string)
        assert filtered_num == expected
