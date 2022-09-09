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

"""Tests for the storing functionality of abstract round abci."""

# pylint: skip-file

import json
import os.path
from itertools import product
from pathlib import PosixPath
from typing import Dict, Optional, cast

import pytest

from packages.valory.skills.abstract_round_abci.io_.store import (
    CustomStorerType,
    JSONStorer,
    StoredJSONType,
    Storer,
    SupportedFiletype,
    SupportedStorerType,
)


class TestStorer:
    """Tests for the `Storer`."""

    def __dummy_custom_storer(self) -> None:
        """A dummy custom storing function to use for the tests."""

    @staticmethod
    @pytest.mark.parametrize(
        "filetype, custom_storer, expected_storer",
        (
            (None, None, None),
            (SupportedFiletype.JSON, None, JSONStorer.store_single_file),
            (
                SupportedFiletype.JSON,
                __dummy_custom_storer,
                JSONStorer.store_single_file,
            ),
            (None, __dummy_custom_storer, __dummy_custom_storer),
        ),
    )
    def test__get_single_storer_from_filetype(
        filetype: Optional[SupportedFiletype],
        custom_storer: Optional[CustomStorerType],
        expected_storer: Optional[SupportedStorerType],
        tmp_path: PosixPath,
    ) -> None:
        """Test `_get_single_storer_from_filetype`."""
        if all(
            test_arg is None for test_arg in (filetype, custom_storer, expected_storer)
        ):
            with pytest.raises(
                ValueError,
                match="Please provide either a supported filetype or a custom storing function.",
            ):
                Storer(
                    filetype, custom_storer, str(tmp_path)
                )._get_single_storer_from_filetype()

        else:
            expected_storer = cast(SupportedStorerType, expected_storer)
            storer = Storer(filetype, custom_storer, str(tmp_path))
            assert (
                storer._get_single_storer_from_filetype().__code__.co_code
                == expected_storer.__code__.co_code
            )

    @staticmethod
    @pytest.mark.parametrize("multiple, index", product((True, False), repeat=2))
    def test_store(
        multiple: bool,
        index: bool,
        tmp_path: PosixPath,
        dummy_obj: StoredJSONType,
        dummy_multiple_obj: Dict[str, StoredJSONType],
    ) -> None:
        """Test `store`."""
        if multiple:
            storer = Storer(SupportedFiletype.JSON, None, str(tmp_path))
            storer.store(dummy_multiple_obj, multiple, index=index)
            for filename, expected_json in dummy_multiple_obj.items():
                filepath = os.path.join(tmp_path, filename)
                with open(filepath, "r") as outfile:
                    saved_json = json.load(outfile)
                assert saved_json, expected_json

        else:
            filepath = os.path.join(tmp_path, "test_obj.csv")
            storer = Storer(SupportedFiletype.JSON, None, filepath)
            storer.store(dummy_obj, multiple, index=index)
            with open(filepath, "r") as outfile:
                saved_json = json.load(outfile)
            assert saved_json == dummy_obj
