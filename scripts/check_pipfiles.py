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
"""
This script checks that the pipfile of the repository meets the requirements.

In particular:
- Avoid the usage of "*"

It is assumed the script is run from the repository root.
"""
import re
import sys
from pathlib import Path


UNPINNED_PACKAGE_REGEX = r'(?P<package_name>.*)\s?=\s?"\*"'


def check_pipfile(pipfile_path: Path) -> bool:
    """Check a Pipfile"""

    print(f"Checking {pipfile_path.joinpath()}... ", end="")
    with open(pipfile_path, "r", encoding="utf-8") as pipfile:
        lines = pipfile.readlines()
        unpinned = []
        for line in lines:
            m = re.match(UNPINNED_PACKAGE_REGEX, line)
            if m:
                unpinned.append(m.groupdict()["package_name"])
        if unpinned:
            print(
                f"\nThe packages {unpinned} have not been pinned in {pipfile_path.joinpath()}"
            )
            return False
    print("OK")
    return True


if __name__ == "__main__":
    root_path = Path(".")
    for file_path in root_path.rglob("*Pipfile*"):
        if not check_pipfile(pipfile_path=file_path):
            sys.exit(1)
