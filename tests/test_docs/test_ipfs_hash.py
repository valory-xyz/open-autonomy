# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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

"""This module contains the tests for checking ipfs hashes in the documentation."""

import re
from pathlib import Path

from tests.conftest import ROOT_DIR
from tests.test_docs.helper import read_file  # type: ignore


FETCH_COMMAND_REGEX = r"aea fetch valory\/hello_world:(?P<hash>Q.*) \-\-remote"
HELLO_WORLD_HASH_REGEX = r"valory\/agents\/hello_world,(?P<hash>Q.*)"


def test_hello_world() -> None:
    """Check hello_world ipfs hash"""
    quick_start_file = Path(ROOT_DIR, "docs", "quick_start.md").relative_to(ROOT_DIR)
    hashes_file = Path(ROOT_DIR, "packages", "hashes.csv").relative_to(ROOT_DIR)

    quick_start = read_file(str(quick_start_file))
    hashes = read_file(str(hashes_file))

    match_cmd = re.findall(FETCH_COMMAND_REGEX, quick_start)
    match_hash = re.findall(HELLO_WORLD_HASH_REGEX, hashes)

    assert (
        match_cmd and match_hash and match_cmd[0] == match_hash[0]
    ), f"IPFS hash not matching in docs/quickstart.md. Expected {match_hash[0]}, got {match_cmd[0]}"
