#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022-2023 Valory AG
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

"""Script to generate a markdown package table."""
from pathlib import Path
from typing import Dict

import yaml
from aea.cli.packages import get_package_manager


COL_WIDTH = 61

PACKAGE_TYPE_TO_CONFIG = {
    "agent": "aea-config.yaml",
    "connection": "connection.yaml",
    "contract": "contract.yaml",
    "service": "service.yaml",
    "skill": "skill.yaml",
    "protocol": "protocol.yaml",
}


def get_package_description(package: str) -> str:
    """Load the package description from its configuration file."""
    package_type, author, package_name, _ = package.split("/")
    config_path = Path(
        "packages",
        author,
        f"{package_type}s",
        package_name,
        PACKAGE_TYPE_TO_CONFIG[package_type],
    )
    with open(config_path, "r", encoding="utf-8") as config_file:
        print(config_path)
        config = yaml.load_all(config_file, Loader=yaml.FullLoader)
        return list(config)[0]["description"]


def get_packages() -> Dict[str, str]:
    """Get packages."""
    data = get_package_manager(Path("packages").relative_to(".")).json
    if "dev" in data:
        return {**data["dev"], **data["third_party"]}
    return data


def generate_table() -> None:
    """Generates a markdown table containing a package list"""

    data = get_packages()

    # Table header
    content = (
        f"| {'Package name'.ljust(COL_WIDTH, ' ')} | {'Package hash'.ljust(COL_WIDTH, ' ')} | {'Description'.ljust(COL_WIDTH * 2, ' ')} |\n"
        f"| {'-'*COL_WIDTH} | {'-'*COL_WIDTH} | {'-'*COL_WIDTH * 2} |\n"
    )

    # Table rows
    for package, package_hash in data.items():
        package_cell = package.ljust(COL_WIDTH, " ")
        hash_cell = f"`{package_hash}`".ljust(COL_WIDTH, " ")
        description = get_package_description(package)
        description_cell = f"{description}".ljust(COL_WIDTH * 2, " ")
        content += f"| {package_cell} | {hash_cell} | {description_cell} |\n"

    # Write table
    with open(
        Path("docs", "package_list.md"), mode="w", encoding="utf-8"
    ) as packages_list:
        packages_list.write(content)


if __name__ == "__main__":
    generate_table()
