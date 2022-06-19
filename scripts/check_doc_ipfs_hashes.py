#!/usr/bin/env python3
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

"""This module contains the tools for autoupdating ipfs hashes in the documentation."""

import re
from pathlib import Path
from typing import Dict


FETCH_COMMAND_REGEX = r"aea fetch valory\/hello_world:(?P<hash>Q.*) \-\-remote"


def read_file(filepath: str) -> str:
    """Loads a file into a string"""
    with open(filepath, "r", encoding="utf-8") as file_:
        file_str = file_.read()
    return file_str


def get_hashes() -> Dict[str, str]:
    """Get a dictionary with all packages and their hashes"""
    CSV_HASH_REGEX = r"(?P<vendor>.*)\/(?P<type>.*)\/(?P<name>.*),(?P<hash>.*)\n"
    hashes_file = Path("packages", "hashes.csv").relative_to(".")
    hashes_content = read_file(str(hashes_file))
    hashes = {}
    for match in re.findall(CSV_HASH_REGEX, hashes_content):
        hashes[f"{match[0]}/{match[1]}/{match[2]}"] = match[3]
    return hashes


def fix_ipfs_hashes() -> None:
    """Fix ipfs hashes in the docs"""
    hashes = get_hashes()
    # Find and check (and optionally fix) hashes in the docs
    quickstart_file = Path("docs", "quick_start.md").relative_to(".")
    quickstart_content = read_file(str(quickstart_file))
    new_command = (
        f"aea fetch valory/hello_world:{hashes['valory/agents/hello_world']} --remote"
    )
    quickstart_content = re.sub(
        FETCH_COMMAND_REGEX, new_command, quickstart_content, count=0, flags=0
    )

    with open(str(quickstart_file), "w", encoding="utf-8") as qs_file:
        qs_file.write(quickstart_content)


if __name__ == "__main__":
    fix_ipfs_hashes()
