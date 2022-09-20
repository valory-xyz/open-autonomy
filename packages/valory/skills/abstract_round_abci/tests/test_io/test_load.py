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

"""Tests for the loading functionality of abstract round abci."""

# pylint: skip-file

import json
import os.path
from pathlib import PosixPath
from typing import Dict, Optional, cast

import pytest

from packages.valory.skills.abstract_round_abci.io_.load import (
    CustomLoaderType,
    JSONLoader,
    Loader,
    SupportedLoaderType,
)
from packages.valory.skills.abstract_round_abci.io_.store import (
    StoredJSONType,
    SupportedFiletype,
    SupportedMultipleObjectsType,
)


class TestLoader:
    """Tests for the `Loader`."""

    def __dummy_custom_loader(self) -> None:
        """A dummy custom loading function to use for the tests."""

    @staticmethod
    @pytest.mark.parametrize(
        "filetype, custom_loader, expected_loader",
        (
            (None, None, None),
            (SupportedFiletype.JSON, None, JSONLoader.load_single_file),
            (
                SupportedFiletype.JSON,
                __dummy_custom_loader,
                JSONLoader.load_single_file,
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

    @staticmethod
    @pytest.mark.parametrize("multiple", (True, False))
    def test_load(
        multiple: bool,
        tmp_path: PosixPath,
        dummy_obj: StoredJSONType,
        dummy_multiple_obj: Dict[str, StoredJSONType],
    ) -> None:
        """Test `load`."""
        loader = Loader(SupportedFiletype.JSON, None)

        if multiple:
            # test with non-directory path
            with pytest.raises(
                ValueError,
                match="Cannot load multiple files from `non_directory_path`! "
                "Please make sure that the path is a folder containing the files.",
            ):
                loader.load("non_directory_path", multiple)

            # create a dummy folder to store multiple dummy objects to test the loader with them.
            dummy_folder_path = os.path.join(tmp_path, "dummy_folder")
            os.mkdir(dummy_folder_path)
            # store dummy objects.
            for name, obj in dummy_multiple_obj.items():
                path = os.path.join(dummy_folder_path, name)
                with open(path, "w") as outfile:
                    json.dump(obj, outfile)

            # load with loader.
            loaded_objects = cast(
                SupportedMultipleObjectsType, loader.load(dummy_folder_path, multiple)
            )
            assert len(loaded_objects) == len(
                dummy_multiple_obj
            ), "loaded objects length and dummy objects length do not match."
            assert set(loaded_objects.keys()) == set(
                dummy_multiple_obj.keys()
            ), "loaded objects and dummy objects filenames do not match."

            # iterate through the loaded objects and their filenames and the dummy objects and their filenames.
            for actual_json, expected_json in zip(
                loaded_objects.values(), dummy_multiple_obj.values()
            ):
                # assert loaded json with expected.
                assert actual_json == expected_json

        else:
            # store dummy object.
            path = os.path.join(tmp_path, "dummy_obj.csv")
            with open(path, "w") as outfile:
                json.dump(dummy_obj, outfile)
            # load with loader.
            loaded_obj = loader.load(path, multiple)
            # assert loaded json with expected.
            assert loaded_obj == dummy_obj
