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

"""Tests for the loading functionality of abstract round abci."""

# pylint: skip-file

import json
from typing import Optional, cast

import pytest

from packages.valory.skills.abstract_round_abci.io_.load import (
    CustomLoaderType,
    JSONLoader,
    Loader,
    SupportedLoaderType,
)
from packages.valory.skills.abstract_round_abci.io_.store import SupportedFiletype


class TestLoader:
    """Tests for the `Loader`."""

    def setup(self) -> None:
        """Setup the tests."""
        self.json_loader = Loader(SupportedFiletype.JSON, None)

    def __dummy_custom_loader(self) -> None:
        """A dummy custom loading function to use for the tests."""

    @staticmethod
    @pytest.mark.parametrize(
        "filetype, custom_loader, expected_loader",
        (
            (None, None, None),
            (SupportedFiletype.JSON, None, JSONLoader.load_single_object),
            (
                SupportedFiletype.JSON,
                __dummy_custom_loader,
                JSONLoader.load_single_object,
            ),
            (None, __dummy_custom_loader, __dummy_custom_loader),
        ),
    )
    def test__get_loader_from_filetype(
        filetype: Optional[SupportedFiletype],
        custom_loader: CustomLoaderType,
        expected_loader: Optional[SupportedLoaderType],
    ) -> None:
        """Test `_get_loader_from_filetype`."""
        if all(
            test_arg is None for test_arg in (filetype, custom_loader, expected_loader)
        ):
            with pytest.raises(
                ValueError,
                match="Please provide either a supported filetype or a custom loader function.",
            ):
                Loader(filetype, custom_loader)._get_single_loader_from_filetype()

        else:
            expected_loader = cast(SupportedLoaderType, expected_loader)
            loader = Loader(filetype, custom_loader)
            assert (
                loader._get_single_loader_from_filetype().__code__.co_code
                == expected_loader.__code__.co_code
            )

    def test_load(self) -> None:
        """Test `load`."""
        expected_object = dummy_object = {"test": "test"}
        filename = "test"
        serialized_object = json.dumps(dummy_object)
        actual_object = self.json_loader.load({filename: serialized_object})
        assert expected_object == actual_object

    def test_no_object(self) -> None:
        """Test `load` throws error when no object is provided."""
        with pytest.raises(
            ValueError,
            match='"serialized_objects" does not contain any objects',
        ):
            self.json_loader.load({})

    def test_load_multiple_objects(self) -> None:
        """Test `load` when multiple objects are to be deserialized."""
        dummy_object = {"test": "test"}
        serialized_object = json.dumps(dummy_object)
        serialized_objects = {
            "obj1": serialized_object,
            "obj2": serialized_object,
        }
        expected_objects = {
            "obj1": dummy_object,
            "obj2": dummy_object,
        }
        actual_objects = self.json_loader.load(serialized_objects)
        assert expected_objects == actual_objects
