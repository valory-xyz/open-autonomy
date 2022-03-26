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
import os.path
from pathlib import PosixPath
from typing import Dict, Union, cast

import pandas as pd
import pytest

from packages.valory.skills.abstract_round_abci.io.ipfs import IPFSInteract
from packages.valory.skills.abstract_round_abci.io.store import (
    SupportedFiletype,
    SupportedMultipleObjectsType,
    SupportedSingleObjectType,
)


ipfs_daemon = pytest.mark.usefixtures("ipfs_daemon")


@ipfs_daemon
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
        dummy_obj: pd.DataFrame,
        dummy_multiple_obj: Dict[str, pd.DataFrame],
    ) -> None:
        """Test store -> send -> download -> read of objects."""
        obj: Union[pd.DataFrame, Dict[str, pd.DataFrame]]
        if multiple:
            obj = dummy_multiple_obj
            filepath = str(tmp_path)
        else:
            obj = dummy_obj
            filepath = os.path.join(tmp_path, "test_file.csv")

        hash_ = self.ipfs_interact.store_and_send(
            filepath, obj, multiple, SupportedFiletype.CSV
        )
        result = self.ipfs_interact.get_and_read(
            hash_, str(tmp_path), multiple, "test_file.csv", SupportedFiletype.CSV
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
            for actual_frame, expected_frame in zip(
                result.values(), dummy_multiple_obj.values()
            ):
                # assert loaded frame with expected.
                pd.testing.assert_frame_equal(actual_frame, expected_frame)

        else:
            result = cast(SupportedSingleObjectType, result)
            # assert loaded frame with expected.
            pd.testing.assert_frame_equal(result, dummy_obj)
