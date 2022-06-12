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

import argparse
import itertools
import re
import shutil
import subprocess  # nosec
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterator, Optional, Tuple, cast


CURRENT_YEAR = datetime.now().year
GIT_PATH = shutil.which("git")
START_YEARS = (2021, 2022)
SHEBANG = "#!/usr/bin/env python3"
HEADER_REGEX = re.compile(
    r"""(#!/usr/bin/env python3
)?# -\*- coding: utf-8 -\*-
# ------------------------------------------------------------------------------
#
#   Copyright ((20\d\d)(-20\d\d)?) Valory AG
#
#   Licensed under the Apache License, Version 2\.0 \(the \"License\"\);
#   you may not use this file except in compliance with the License\.
#   You may obtain a copy of the License at
#
#       http://www\.apache\.org/licenses/LICENSE-2\.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an \"AS IS\" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied\.
#   See the License for the specific language governing permissions and
#   limitations under the License\.
#
# ------------------------------------------------------------------------------
""",
    re.MULTILINE,
)
HEADER_TEMPLATE = """# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
{copyright_string}
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


class ErrorTypes:  # pylint: disable=too-few-public-methods
    """Types of corrupt headers."""

    NO_ERROR = 0
    START_YEAR_NOT_ALLOWED = 1
    START_YEAR_GT_END_YEAR = 2
    END_YEAR_WRONG = 3
    END_YEAR_MISSING = 4


def get_modification_date(file: Path) -> datetime:
    """Returns modification date for the file."""
    (
        date_string,
        _,
    ) = subprocess.Popen(  # nosec  # pylint: disable=consider-using-with
        [str(GIT_PATH), "log", "-1", '--format="%ad"', "--", str(file)],
        stdout=subprocess.PIPE,
    ).communicate()
    date_string_ = date_string.decode().strip()
    if date_string_ == "":
        return datetime.now()
    return datetime.strptime(date_string_, '"%a %b %d %X %Y %z"')


def get_year_data(match: re.Match) -> Tuple[int, Optional[int]]:
    """Get year data from match."""
    _, year_string, *_ = match.groups()
    if "-" in year_string:
        return (*map(int, year_string.split("-")),)  # type: ignore
    return int(year_string), None


def _validate_years(
    file: Path,
    allowed_start_years: Tuple[int, ...],
    start_year: int,
    end_year: int,
    check_end_year: bool = True,
) -> Dict:
    """
    Given a file, check if the header stuff is in place.

    Return True if the files has the encoding header and the copyright notice,
    optionally prefixed by the shebang. Return False otherwise.

    :param file: the file to check.
    :param allowed_start_years: list of allowed start years
    :param start_year: year when the file was created
    :param end_year: year when the file was last modified
    :param check_end_year: whether to validate end year or not
    :return: True if the file is compliant with the checks, False otherwise.
    """

    modification_date = get_modification_date(file)
    check_info = {
        "check": True,
        "message": f"Start year {start_year} is not in the list of allowed years; {allowed_start_years}.",
        "start_year": start_year,
        "end_year": end_year,
        "last_modification": modification_date,
        "error_code": ErrorTypes.NO_ERROR,
    }

    # Start year is not in allowed start years list
    if start_year not in allowed_start_years:
        check_info["check"] = False
        check_info[
            "message"
        ] = f"Start year {start_year} is not in the list of allowed years; {allowed_start_years}."
        check_info["error_code"] = ErrorTypes.START_YEAR_NOT_ALLOWED
        return check_info

    # Specified year is 2021 but the file has been last modified in another later year (missing -202x)
    if end_year is not None and check_end_year:

        if start_year > end_year:
            check_info["check"] = False
            check_info["message"] = "End year should be greater then start year."
            check_info["error_code"] = ErrorTypes.START_YEAR_GT_END_YEAR
            return check_info

        if end_year != modification_date.year:
            check_info["check"] = False
            check_info[
                "message"
            ] = f"End year does not match the last modification year. Header has: {end_year}; Last Modified: {modification_date.year}"
            check_info["error_code"] = ErrorTypes.END_YEAR_WRONG
            return check_info

    if end_year is None and modification_date.year > start_year:
        check_info["check"] = False
        check_info["message"] = f"Missing later year ({start_year}-20..)"
        check_info["error_code"] = ErrorTypes.END_YEAR_MISSING
        return check_info

    return check_info


def fix_header(check_info: Dict) -> bool:
    """Fix currupt headers."""

    path = cast(Path, check_info.get("path"))
    content = path.read_text()
    copyright_string = ""
    is_update_needed = False

    if check_info["error_code"] in (
        ErrorTypes.END_YEAR_WRONG,
        ErrorTypes.END_YEAR_MISSING,
    ):
        copyright_string = "#   Copyright {start_year}-{end_year} Valory AG".format(
            start_year=check_info["start_year"],
            end_year=check_info["last_modification"].year,
        )
        is_update_needed = True

    elif check_info["error_code"] == ErrorTypes.START_YEAR_GT_END_YEAR:
        copyright_string = "#   Copyright {end_year}-{start_year} Valory AG".format(
            start_year=check_info["start_year"],
            end_year=check_info["last_modification"].year,
        )
        is_update_needed = True

    if is_update_needed:
        new_header = HEADER_TEMPLATE.format(copyright_string=copyright_string)
        if SHEBANG in content:
            new_header = SHEBANG + "\n" + new_header
        updated_content = HEADER_REGEX.sub(new_header, content)
        path.write_text(updated_content)

    return is_update_needed


def update_headers(files: Iterator[Path]) -> None:
    """Update headers."""

    needs_update = []

    for path in files:
        print("Checking {}".format(path))
        check_data = check_copyright(path)
        if not check_data["check"]:
            check_data["path"] = path
            needs_update.append(check_data)

    if len(needs_update) > 0:
        print("\n\nUpdating headers.\n")
        cannot_update = []
        for check_data in needs_update:
            print("Updating {}".format(check_data["path"]))
            if not fix_header(check_data):
                cannot_update.append(check_data)

        if len(cannot_update) > 0:
            print("\nFollowing files were not updated.\n")
            print("\n".join([str(check_data["path"]) for check_data in cannot_update]))
    else:
        print("No update needed.")


def check_copyright(file: Path) -> Dict:
    """
    Given a file, check if the header stuff is in place.

    Return True if the files has the encoding header and the copyright notice,
    optionally prefixed by the shebang. Return False otherwise.

    :param file: the file to check.
    :return: True if the file is compliant with the checks, False otherwise.
    """
    content = file.read_text()
    match = HEADER_REGEX.match(content)
    if match is not None:
        return _validate_years(file, START_YEARS, *get_year_data(match))  # type: ignore

    return {"check": False, "message": "Invalid copyright header."}


def run_check(files: Iterator[Path]) -> None:
    """Run copyright check."""
    bad_files = set()
    for path in files:
        print("Processing {}".format(path))
        check_data = check_copyright(path)
        if not check_data["check"]:
            bad_files.add((path, check_data["message"]))

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


def get_args() -> argparse.Namespace:
    """Get CLI arguments."""

    argparser = argparse.ArgumentParser()
    argparser.add_argument("--check", action="store_true")
    return argparser.parse_args()


def main() -> None:
    """Main function."""

    args = get_args()

    exclude_files = {Path("scripts", "whitelist.py")}
    python_files = filter(
        lambda x: x not in exclude_files,
        itertools.chain(
            Path("autonomy").glob("**/*.py"),
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
            Path("replay_scripts").glob("**/*.py"),
        ),
    )

    def _file_filter(file: Path) -> bool:
        """Filter for files."""
        file_str = str(file)

        # protocols are generated using generate_all_protocols.py
        return (
            not file_str.endswith("_pb2.py")
            and not file_str.endswith("_pb2_grpc.py")
            and (
                (
                    "protocols" not in file.parts
                    and "t_protocol" not in file.parts
                    and "t_protocol_no_ct" not in file.parts
                    and "build" not in file.parts
                )
            )
        )

    python_files_filtered = filter(_file_filter, python_files)
    if args.check:
        run_check(python_files_filtered)
    else:
        update_headers(python_files_filtered)


if __name__ == "__main__":
    main()
