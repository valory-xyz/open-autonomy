# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2023 Valory AG
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
from pathlib import Path, PosixPath
from typing import Optional, cast

import pytest

from packages.valory.skills.abstract_round_abci.io_.store import (
    CustomStorerType,
    JSONStorer,
    Storer,
    SupportedFiletype,
    SupportedStorerType,
)


class TestStorer:
    """Tests for the `Storer`."""

    def setup(self) -> None:
        """Setup the tests."""
        self.path = "tmp"
        self.json_storer = Storer(SupportedFiletype.JSON, None, self.path)

    def __dummy_custom_storer(self) -> None:
        """A dummy custom storing function to use for the tests."""

    @staticmethod
    @pytest.mark.parametrize(
        "filetype, custom_storer, expected_storer",
        (
            (None, None, None),
            (SupportedFiletype.JSON, None, JSONStorer.serialize_object),
            (
                SupportedFiletype.JSON,
                __dummy_custom_storer,
                JSONStorer.serialize_object,
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

    def test_store(self) -> None:
        """Test `store`."""
        dummy_object = {"test": "test"}
        expected_object = {self.path: json.dumps(dummy_object, indent=4)}
        actual_object = self.json_storer.store(dummy_object, False)
        assert expected_object == actual_object

    def test_store_multiple(self) -> None:
        """Test `store` when multiple files are present."""
        dummy_object = {"test": "test"}
        dummy_filename = "test"
        expected_path = Path(f"{self.path}/{dummy_filename}").__str__()
        expected_object = {expected_path: json.dumps(dummy_object, indent=4)}
        actual_object = self.json_storer.store({dummy_filename: dummy_object}, True)
        assert expected_object == actual_object
