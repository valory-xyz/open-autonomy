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

"""Test the `tools/general.py` module of the skill."""
import json
import os
from pathlib import PosixPath

import pytest
from _pytest.monkeypatch import MonkeyPatch

from packages.valory.skills.apy_estimation_abci.tools.general import (
    aggregate_agent_times,
    create_pathdirs,
    filter_out_numbers,
    gen_unix_timestamps,
    read_json_file,
    to_json_file,
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
    def test_to_json_file(tmp_path: PosixPath) -> None:
        """Test list to json file."""
        test_list = [{"key0": "1", "key1": "test"}, {"": "2"}, {"test": "test"}]

        # test non-existing path.
        path = os.path.join("non_existing_path", "file.json")
        with pytest.raises(FileNotFoundError):
            to_json_file(path, test_list)

        # test existing path with serializable list.
        path = os.path.join(tmp_path, "file.json")
        to_json_file(path, test_list)
        with open(path, "r", encoding="utf-8") as f:
            li = json.load(f)
            assert li == test_list

        # test existing path with non-serializable list.
        test_list.append(b"non-serializable")  # type: ignore
        with pytest.raises(TypeError):
            to_json_file(path, test_list)  # type: ignore

    @staticmethod
    def test_read_json_file(tmp_path: PosixPath) -> None:
        """Test `read_json_file`."""
        # test non-existing path.
        filepath = "non-existing"
        with pytest.raises(FileNotFoundError):
            read_json_file(filepath)

        # test existing path with serializable list.
        expected = [{"key0": "1", "key1": "test"}, {"": "2"}, {"test": "test"}]
        filepath = os.path.join(tmp_path, "test.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(expected, f, ensure_ascii=False, indent=4)

        actual = read_json_file(filepath)
        assert actual == expected

        # test existing path with non-serializable list.
        with open(filepath, "wb") as fb:
            fb.write(b"non-serializable")

        with pytest.raises(json.JSONDecodeError):
            read_json_file(filepath)  # type: ignore

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

    @staticmethod
    def test_aggregate_agent_times() -> None:
        """Test `aggregate_agent_times` function."""

        assert aggregate_agent_times((1, 2, 3, 4, 5)) == 3.0
