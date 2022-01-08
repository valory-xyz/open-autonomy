#!/usr/bin/env python3
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

"""
This script checks that all the Python files of the repository have the copyright notice.

In particular:
- (optional) the Python shebang
- the encoding header;
- the copyright and license notices;

It is assumed the script is run from the repository root.
"""

import itertools
import re
import shutil
import subprocess  # nosec
import sys
from datetime import datetime
from pathlib import Path
from typing import Tuple


GIT_PATH = shutil.which("git")
HEADER_REGEX = re.compile(
    r"""(#!/usr/bin/env python3
)?# -\*- coding: utf-8 -\*-
# ------------------------------------------------------------------------------
#
#   Copyright ((2021|2022)(-202\d)?) Valory AG
#
#   Licensed under the Apache License, Version 2\.0 \(the "License"\);
#   you may not use this file except in compliance with the License\.
#   You may obtain a copy of the License at
#
#       http:\/\/www\.apache\.org\/licenses\/LICENSE-2\.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied\.
#   See the License for the specific language governing permissions and
#   limitations under the License\.
#
# ------------------------------------------------------------------------------
""",
    re.MULTILINE,
)


def check_copyright(file: Path) -> Tuple[bool, str]:
    """
    Given a file, check if the header stuff is in place.

    Return True if the files has the encoding header and the copyright notice,
    optionally prefixed by the shebang. Return False otherwise.

    :param file: the file to check.
    :return: True if the file is compliant with the checks, False otherwise.
    """
    content = file.read_text()

    match = re.match(HEADER_REGEX, content)

    # No match
    if match is None:
        return False, "Invalid copyright header."

    copyright_years_str = match.groups(0)[1]  # type: ignore
    copyright_years = tuple(int(i) for i in copyright_years_str.split("-"))
    date_string, _ = subprocess.Popen(  # pylint: disable=consider-using-with  # nosec
        [str(GIT_PATH), "log", "-1", '--format="%ad"', "--", str(file)],
        stdout=subprocess.PIPE,
    ).communicate()
    date_string_ = date_string.decode().strip()
    if date_string_ == "":
        modification_date = datetime.now()
    else:
        modification_date = datetime.strptime(date_string_, '"%a %b %d %X %Y %z"')

    # Start year is not 2021 or 2022
    if copyright_years[0] not in [2021, 2022]:
        return False, "Start year is not 2021 or 2022."

    # Specified year is 2021 but the file has been last modified in another later year (missing -202x)
    if (
        copyright_years[0] == 2021
        and len(copyright_years) == 1
        and copyright_years[0] < modification_date.year
    ):
        return (
            False,
            f"Specified year is 2021 but the file has been last modified in another later year (missing -202x), date last modified {date_string_}",
        )

    # Specified year is 2022 but the file has been modified in an earlier year
    if (
        copyright_years[0] == 2022
        and len(copyright_years) == 1
        and copyright_years[0] > modification_date.year
    ):
        return (
            False,
            f"Specified year is 2022 but the file has been last modified in an earlier year, date last modified {date_string_}",
        )

    # End year does not match the last modification year
    if len(copyright_years) > 1 and copyright_years[1] != modification_date.year:
        return False, "End year does not match the last modification year."

    return True, ""


if __name__ == "__main__":
    exclude_files = {Path("scripts", "whitelist.py")}
    python_files = filter(
        lambda x: x not in exclude_files,
        itertools.chain(
            Path("aea_consensus_algorithm").glob("**/*.py"),
            Path("benchmark").glob("**/*.py"),
            Path("examples").glob("**/*.py"),
            Path("tests").glob("**/*.py"),
            Path("packages", "valory", "agents").glob("**/*.py"),
            Path("packages", "valory", "connections").glob("**/*.py"),
            Path("packages", "valory", "contracts").glob("**/*.py"),
            Path("packages", "valory", "skills").glob("**/*.py"),
            Path("tests").glob("**/*.py"),
            Path("scripts").glob("**/*.py"),
        ),
    )
    python_files = filter(lambda x: not str(x).endswith("_pb2.py"), python_files)

    bad_files = set()
    for path in python_files:
        print("Processing {}".format(path))
        result, message = check_copyright(path)
        if not result:
            bad_files.add((path, message))

    if len(bad_files) > 0:
        print("The following files are not well formatted:")
        print(
            "\n".join(
                map(
                    lambda x: f"File: {x[0]}\nReason: {x[1]}\n",
                    sorted(bad_files, key=lambda x: x[0]),
                )
            )
        )
        sys.exit(1)
    else:
        print("OK")
        sys.exit(0)
