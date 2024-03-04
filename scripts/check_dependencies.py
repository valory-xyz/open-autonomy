#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022-2024 Valory AG
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

import os
import subprocess  # nosec
import sys
from pathlib import Path
from typing import Any, Dict

import toml
from aea.configurations.data_types import Dependency, PackageType
from aea.package_manager.base import load_configuration
from aea.package_manager.v1 import PackageManagerV1


def load_pipfile(pipfile_path: str = "./Pipfile") -> dict:
    """Load the Pipfile file contents."""

    # Load the Pipfile file
    with open(pipfile_path, "r", encoding="utf-8") as toml_file:
        toml_data = toml.load(toml_file)

    # Get the [dev-packages] section
    dependencies = toml_data.get("dev-packages", {})
    dependencies.update(toml_data.get("packages", {}))

    return dependencies


def get_package_dependencies() -> Dict[str, Any]:
    """Returns a list of package dependencies."""
    package_manager = PackageManagerV1.from_dir(
        Path(os.environ.get("PACKAGES_DIR", str(Path.cwd() / "packages")))
    )
    dependencies: Dict[str, Dependency] = {}
    for package in package_manager.iter_dependency_tree():
        if package.package_type == PackageType.SERVICE:
            continue
        _dependencies = load_configuration(
            package_type=package.package_type,
            package_path=package_manager.package_path_from_package_id(
                package_id=package
            ),
        ).dependencies
        for key, value in _dependencies.items():
            if key not in dependencies:
                dependencies[key] = value
            else:
                if value.version == "":
                    continue
                if dependencies[key].version == "":
                    dependencies[key] = value
                elif value == dependencies[key]:
                    continue
                else:
                    print(
                        f"Non-matching dependency versions for {key}: {value} vs {dependencies[key]}"
                    )

    return {package.name: package.version for package in dependencies.values()}


def warnings(listed_package_dependencies: dict, new_package_dependencies: dict) -> None:
    """Warn about mismatches."""

    for key, value in new_package_dependencies.items():
        if key in ["open-aea-test-autonomy"]:
            continue
        if key not in listed_package_dependencies:
            print(f"Package {key} not found in Pipfile")
            sys.exit(1)
        if (
            key in listed_package_dependencies
            and value == ""
            and listed_package_dependencies[key] == "*"
        ):
            continue
        if (
            key in listed_package_dependencies
            and value != listed_package_dependencies[key]
        ):
            print(
                f"Package {key} has version {listed_package_dependencies[key]} in Pipfile and {value} in packages."
            )
            sys.exit(1)


def update_tox_ini(
    new_package_dependencies: dict, tox_ini_path: str = "./tox.ini"
) -> None:
    """Update the tox.ini file with the new package dependencies."""
    for key, value in new_package_dependencies.items():
        if isinstance(value, str) and len(value) == 1 and "*" == value[0]:
            new_package_dependencies[key] = ""
        if isinstance(value, dict):
            if "extras" in value:
                value_ = "["
                for it in value["extras"]:
                    value_ += it
                    value_ += ","
                value_ = value_[:-1]
                value_ += "]"
                new_package_dependencies[key] = value_ + value["version"]
            elif "git" in value:
                new_package_dependencies[key] = (
                    "git+"
                    + value["git"]
                    + "@"
                    + value.get("ref", "None")
                    + "#egg="
                    + key
                )
            else:
                raise ValueError(value)
    with open(tox_ini_path, "r", encoding="utf-8") as file:
        lines = file.readlines()

    # Find the [deps-packages] section and replace the deps value
    start_line = None
    end_line = None
    for i, line in enumerate(lines):
        if line.strip() == "[deps-packages]":
            start_line = i + 1
            break

    if start_line is not None:
        for i in range(start_line, len(lines)):
            if lines[i].strip().startswith("["):
                end_line = i
                break
        else:
            end_line = len(lines)

        updated_lines = ["deps =\n"] + ["    {[deps-tests]deps}\n"]
        for key, value in new_package_dependencies.items():
            if str(value).startswith("git+"):
                updated_lines.append(f"    {value}\n")
            else:
                updated_lines.append(f"    {key}{value}\n")
        updated_lines.extend(["\n"])

        lines[start_line:end_line] = updated_lines

    # Write the modified content back to the tox.ini file
    with open(tox_ini_path, "w", encoding="utf-8") as file:
        file.writelines(lines)


def check_for_no_changes(
    pyproject_toml_path: str = "./pyproject.toml", tox_ini_path: str = "./tox.ini"
) -> bool:
    """Check if there are any changes in the current repository."""

    # Check if there are any changes
    result = subprocess.run(  # pylint: disable=W1510 # nosec
        ["git", "diff", "--quiet", "--", pyproject_toml_path, tox_ini_path],
        capture_output=True,
        text=True,
    )

    return result.returncode == 0


if __name__ == "__main__":
    update = len(sys.argv[1:]) > 0
    package_dependencies = get_package_dependencies()
    # TOFIX - anchorpy has a conflict with tomte[tests]
    package_dependencies.pop("open-aea-ledger-solana")
    package_dependencies.pop("solders")
    listed_package_dependencies_ = load_pipfile()
    warnings(listed_package_dependencies_, package_dependencies)
    update_tox_ini(listed_package_dependencies_)
    if not update and not check_for_no_changes():
        print(
            "There are mismatching package dependencies in the pyproject.toml file and the packages."
        )
        sys.exit(1)
