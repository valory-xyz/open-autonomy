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

"""This module contains tests for the `IPFS` interactions."""

# pylint: skip-file

import os.path
from pathlib import PosixPath
from typing import Dict, Iterator, cast

import pytest
from aea_cli_ipfs.ipfs_utils import IPFSDaemon

from packages.valory.skills.abstract_round_abci.io_.ipfs import IPFSInteract
from packages.valory.skills.abstract_round_abci.io_.store import (
    StoredJSONType,
    SupportedFiletype,
    SupportedMultipleObjectsType,
    SupportedSingleObjectType,
)


use_ipfs_daemon = pytest.mark.usefixtures("ipfs_daemon")


@pytest.fixture(scope="module")
def ipfs_daemon() -> Iterator[bool]:
    """Starts an IPFS daemon for the tests."""
    print("Starting IPFS daemon...")
    daemon = IPFSDaemon()
    daemon.start()
    yield daemon.is_started()
    print("Tearing down IPFS daemon...")
    daemon.stop()


@use_ipfs_daemon
class TestIPFSInteract:
    """Test `IPFSInteract`."""

    def setup(self) -> None:
        """Setup test class."""
        self.ipfs_interact = IPFSInteract("/dns/localhost/tcp/5001/http")

    @pytest.mark.parametrize("multiple", (True, False))
    def test_store_and_send_and_back(
        self,
        multiple: bool,
        tmp_path: PosixPath,
        dummy_obj: StoredJSONType,
        dummy_multiple_obj: Dict[str, StoredJSONType],
    ) -> None:
        """Test store -> send -> download -> read of objects."""
        obj: StoredJSONType
        if multiple:
            obj = dummy_multiple_obj
            filepath = str(tmp_path)
        else:
            obj = dummy_obj
            filepath = os.path.join(tmp_path, "test_file.json")

        hash_ = self.ipfs_interact.store_and_send(
            filepath, obj, multiple, SupportedFiletype.JSON
        )
        result = self.ipfs_interact.get_and_read(
            hash_, str(tmp_path), multiple, "test_file.json", SupportedFiletype.JSON
        )

        if multiple:
            result = cast(SupportedMultipleObjectsType, result)
            assert len(result) == len(
                dummy_multiple_obj
            ), "loaded objects length and dummy objects length do not match."
            assert set(result.keys()) == set(
                dummy_multiple_obj.keys()
            ), "loaded objects and dummy objects filenames do not match."

            # iterate through the loaded objects and their filenames and the dummy objects and their filenames.
            for actual_json, expected_json in zip(
                result.values(), dummy_multiple_obj.values()
            ):
                # assert loaded json with expected.
                assert actual_json == expected_json

        else:
            result = cast(SupportedSingleObjectType, result)
            # assert loaded json with expected.
            assert result == dummy_obj
