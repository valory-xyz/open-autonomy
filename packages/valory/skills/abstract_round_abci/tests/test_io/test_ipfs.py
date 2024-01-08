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

"""This module contains tests for the `IPFS` interactions."""

# pylint: skip-file

import os
from pathlib import PosixPath
from typing import Any, Dict, cast
from unittest import mock

import pytest

from packages.valory.skills.abstract_round_abci.io_.ipfs import (
    IPFSInteract,
    IPFSInteractionError,
)
from packages.valory.skills.abstract_round_abci.io_.load import AbstractLoader
from packages.valory.skills.abstract_round_abci.io_.store import (
    AbstractStorer,
    StoredJSONType,
    SupportedFiletype,
)


use_ipfs_daemon = pytest.mark.usefixtures("ipfs_daemon")


class TestIPFSInteract:
    """Test `IPFSInteract`."""

    def setup(self) -> None:
        """Setup test class."""
        self.ipfs_interact = IPFSInteract()

    @pytest.mark.parametrize("multiple", (True, False))
    def test_store_and_send_and_back(
        self,
        multiple: bool,
        dummy_obj: StoredJSONType,
        dummy_multiple_obj: Dict[str, StoredJSONType],
        tmp_path: PosixPath,
    ) -> None:
        """Test store -> send -> download -> read of objects."""
        obj: StoredJSONType
        if multiple:
            obj = dummy_multiple_obj
            filepath = "dummy_dir"
        else:
            obj = dummy_obj
            filepath = "test_file.json"

        filepath = str(tmp_path / filepath)
        serialized_objects = self.ipfs_interact.store(
            filepath, obj, multiple, SupportedFiletype.JSON
        )
        expected_objects = obj
        actual_objects = cast(
            Dict[str, Any],
            self.ipfs_interact.load(
                serialized_objects,
                SupportedFiletype.JSON,
            ),
        )
        if multiple:
            # here we manually remove the trailing the dir from the name.
            # This is done by the IPFS connection under normal circumstances.
            actual_objects = {os.path.basename(k): v for k, v in actual_objects.items()}

        assert actual_objects == expected_objects

    def test_store_fails(self, dummy_multiple_obj: Dict[str, StoredJSONType]) -> None:
        """Tests when "store" fails."""
        dummy_filepath = "dummy_dir"
        multiple = False
        with mock.patch.object(
            AbstractStorer,
            "store",
            side_effect=ValueError,
        ), pytest.raises(IPFSInteractionError):
            self.ipfs_interact.store(
                dummy_filepath, dummy_multiple_obj, multiple, SupportedFiletype.JSON
            )

    def test_load_fails(self, dummy_multiple_obj: Dict[str, StoredJSONType]) -> None:
        """Tests when "load" fails."""
        dummy_object = {"test": "test"}
        with mock.patch.object(
            AbstractLoader,
            "load",
            side_effect=ValueError,
        ), pytest.raises(IPFSInteractionError):
            self.ipfs_interact.load(dummy_object)
