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

"""This module contains a tool for generating release announcements."""

import re
from pathlib import Path


DEFAULT_SOURCE_PATH = Path("HISTORY.md")
DEFAULT_TARGET_PATH = Path("announcement.md")


VERSION_REGEX = r"(?P<version>\d+\.\d+(\.\d+)?(\.\w+)?)"
VERSION_REGEX_2 = VERSION_REGEX.replace(
    "version", "version_2"
)  # We need to avoid group redefinition
DATE_REGEX = r"\(\d{4}-\d{2}-\d{2}\)"
RELEASE_HEADER_REGEX = rf"{VERSION_REGEX} {DATE_REGEX}\n"
RELEASE_HEADER_REGEX_2 = rf"{VERSION_REGEX_2} {DATE_REGEX}\n"
RELEASE_DATA_REGEX = (
    rf"{RELEASE_HEADER_REGEX}(?P<data>(.|\n)*?){RELEASE_HEADER_REGEX_2}"
)


def generate_release_data(
    source_path: Path = DEFAULT_SOURCE_PATH, target_path: Path = DEFAULT_TARGET_PATH
) -> None:
    """Generates the release announcement for Discord

    :param source_path: source file path
    :param target_path: target file path
    :return: None
    """

    # Load HISTORY.md content
    with open(source_path, mode="r", encoding="utf-8") as history:
        content = history.read()

    if not content:
        print(f"Error opening file {str(source_path)}")
        return

    release_data = re.search(RELEASE_DATA_REGEX, content)

    if not release_data:
        print(f"No release data found in {str(source_path)}")
        return

    # Split the content into its sections
    version = release_data.groupdict()["version"]

    sections = {}

    for section in release_data.groupdict()["data"].split("\n\n"):
        parts = section.split("\n-")
        section_name = parts[0].replace("#", "").strip()

        if not section_name:
            continue

        section_entries = [p.strip() for p in parts[1:]]
        sections[section_name] = section_entries

    # Generate the announcement text
    release_text = f"""
```yaml
Open Autonomy {version}
```"""

    for section, entries in sections.items():
        release_text += f"""
```fix
{section.upper()}
```
"""
        for entry in entries:
            release_text += f"• {entry}\n"

    release_text += f"""
```fix
LINKS
```
Github release
https://github.com/valory-xyz/open-autonomy/releases/tag/v{version}

Pypi packages
https://pypi.org/project/open-autonomy/{version}/
https://pypi.org/project/open-aea-test-autonomy/{version}/
"""

    # Write the announcement to file
    with open(target_path, mode="w", encoding="utf-8") as target_file:
        target_file.write(release_text)
        print(f"Content written to {str(target_path)}")


if __name__ == "__main__":
    generate_release_data()
