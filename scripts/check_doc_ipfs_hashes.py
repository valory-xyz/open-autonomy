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

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, Optional

import yaml
from aea.helpers.base import IPFS_HASH_REGEX, SIMPLE_ID_REGEX


CLI_REGEX = r"(?P<cli>aea|autonomy)"
CMD_REGEX = r"(?P<cmd>.*)"
VENDOR_REGEX = rf"(?P<vendor>{SIMPLE_ID_REGEX})"
PACKAGE_REGEX = rf"(?P<package>{SIMPLE_ID_REGEX})"
VERSION_REGEX = r"(?P<version>\d+\.\d+\.\d+)"
FLAGS_REGEX = r"(?P<flags>(\s--.*)?)"

AEA_COMMAND_REGEX = rf"(?P<full_cmd>{CLI_REGEX} {CMD_REGEX} (?:{VENDOR_REGEX}\/{PACKAGE_REGEX}:{VERSION_REGEX}?:?)?(?P<hash>{IPFS_HASH_REGEX}){FLAGS_REGEX})"
FULL_PACKAGE_REGEX = rf"(?P<full_package>(?:{VENDOR_REGEX}\/{PACKAGE_REGEX}:{VERSION_REGEX}?:?)?(?P<hash>{IPFS_HASH_REGEX}))"

ROOT_DIR = Path(__file__).parent.parent


def read_file(filepath: str) -> str:
    """Loads a file into a string"""
    with open(filepath, "r", encoding="utf-8") as file_:
        file_str = file_.read()
    return file_str


class Package:  # pylint: disable=too-few-public-methods
    """Class that represents a package in hashes.csv"""

    CSV_HASH_REGEX = r"(?P<vendor>.*)\/(?P<type>.*)\/(?P<name>.*),(?P<hash>.*)(?:\n|$)"

    def __init__(self, package_line: str) -> None:
        """Constructor"""
        m = re.match(self.CSV_HASH_REGEX, package_line)
        if not m:
            raise ValueError(
                f"PackageHashManager: the line:\n    {package_line}\ndoes not match the package format {self.CSV_HASH_REGEX}"
            )
        self.vendor = m.groupdict()["vendor"]
        self.type = m.groupdict()["type"]
        self.name = m.groupdict()["name"]
        self.hash = m.groupdict()["hash"]

        if self.name == "scaffold":
            return

        if self.type not in (
            "connections",
            "agents",
            "protocols",
            "services",
            "skills",
            "contracts",
        ):
            raise ValueError(
                f"Package: unknown package type in hashes.csv: {self.type}"
            )
        self.type = self.type[:-1]  # remove last s

        self.last_version = None
        yaml_file_path = Path(
            ROOT_DIR,
            "packages",
            self.vendor,
            self.type + "s",
            self.name,
            f"{'aea-config' if self.type == 'agent' else self.type}.yaml",
        )
        with open(yaml_file_path, "r", encoding="utf-8") as file:
            content = yaml.load_all(file, Loader=yaml.FullLoader)
            for resource in content:
                if "version" in resource:
                    self.last_version = resource["version"]
                    break

    def get_command(
        self, cmd: str, include_version: bool = True, flags: str = ""
    ) -> str:
        """
        Get the corresponding command.

        :param cmd: the command
        :param include_version: whether or not to include the version
        :param flags: command flags
        :return: the full command
        """
        version = (
            ":" + self.last_version if include_version and self.last_version else ""
        )
        return f"autonomy {cmd} {self.vendor}/{self.name}{version}:{self.hash}{flags}"


class PackageHashManager:
    """Class that represents the packages in hashes.csv"""

    def __init__(self) -> None:
        """Constructor"""
        hashes_file = Path("packages", "hashes.csv").relative_to(".")
        with open(hashes_file, "r", encoding="utf-8") as file_:
            self.packages = [Package(line) for line in file_.readlines()]
            self.packages = [p for p in self.packages if p.name != "scaffold"]

        self.package_tree: Dict = {}
        for p in self.packages:
            self.package_tree.setdefault(p.vendor, {})
            self.package_tree[p.vendor].setdefault(p.type, {})
            self.package_tree[p.vendor][p.type].setdefault(p.name, p)
            assert re.match(IPFS_HASH_REGEX, p.hash)  # detect wrong regexes

    def get_package_by_hash(self, package_hash: str) -> Optional[Package]:
        """Get a package given its hash"""
        packages = list(filter(lambda p: p.hash == package_hash, self.packages))
        if not packages:
            return None
        if len(packages) > 1:
            raise ValueError(
                f"PackageHashManager: hash search for {package_hash} returned more than 1 result in hashes.csv"
            )
        return packages[0]

    def get_hash_by_package_line(
        self, package_line: str, target_file: str
    ) -> Optional[str]:
        """Get a hash given its package line"""

        try:
            m_command = re.match(AEA_COMMAND_REGEX, package_line)
            m_package = re.match(FULL_PACKAGE_REGEX, package_line)

            # No match
            if not m_command and not m_package:
                print(
                    f"[{target_file}]: line '{package_line}' does not match an aea command or package format"
                )
                return None
            m = m_command or m_package
            d = m.groupdict()  # type: ignore

            # Underspecified commands that only use the hash
            # In this case we cannot infer the package type, just check whether or not the hash exists in hashes.csv
            if not d["vendor"] and not d["package"]:
                package = self.get_package_by_hash(d["hash"])

                # This hash exists in hashes.csv
                if package:
                    return package.hash

                # This hash does not exist in hashes.csv
                print(
                    f"[{target_file}]: unknown IPFS hash in line '{package_line}'. Can't fix because this command just uses the hash"
                )
                return None

            # Complete command, succesfully retrieved

            # Guess the package type (agent, service, contract...). First try to find the package in the package_tree
            potential_package_types = []
            for package_type, packages in self.package_tree[d["vendor"]].items():
                if d["package"] in packages.keys():
                    potential_package_types.append(package_type)

            # If only 1 match has been found we can be sure about the package type
            if len(potential_package_types) == 1:
                package_type = potential_package_types[0]
            else:
                # Try to guess the package type from the command
                package_type = None

                # Fetch option is only available for agents and services
                if d["cmd"] == "fetch":
                    package_type = (
                        "service" if "--service" in d["full_cmd"] else "agent"
                    )

                # Deployments are always services
                if "deployment" in d["cmd"]:
                    package_type = "service"

                # Add commands always specify the package type
                if d["cmd"].startswith("add"):
                    package_type = d["cmd"].split(" ")[-1]  # i.e.: aea add connection

                if not package_type:
                    raise ValueError(
                        f"[{target_file}]: could not infer the package type for line '{package_line}'\nPlease update the hash manually."
                    )

            return self.package_tree[d["vendor"]][package_type][d["package"]].hash

        # Otherwise log the error
        except KeyError:
            print(
                f"[{target_file}]: could not find the corresponding hash for line '{package_line}'"
            )
            return None


def check_ipfs_hashes(  # pylint: disable=too-many-locals,too-many-statements
    fix: bool = False,
) -> None:
    """Fix ipfs hashes in the docs"""

    all_md_files = Path("docs").rglob("*.md")
    errors = False
    hash_mismatches = False
    old_to_new_hashes = {}
    package_manager = PackageHashManager()
    matches = 0

    # Fix full commands on docs
    for md_file in all_md_files:
        content = read_file(str(md_file))
        for match in [m.groupdict() for m in re.finditer(AEA_COMMAND_REGEX, content)]:
            matches += 1
            doc_full_cmd = match["full_cmd"]
            doc_cmd = match["cmd"]
            doc_hash = match["hash"]
            flags = match["flags"]

            expected_hash = package_manager.get_hash_by_package_line(
                doc_full_cmd, str(md_file)
            )
            if not expected_hash:
                errors = True
                continue
            expected_package = package_manager.get_package_by_hash(expected_hash)
            if not expected_package:
                errors = True
                continue

            new_command = expected_package.get_command(cmd=doc_cmd, flags=flags)

            # Overwrite with new hash
            if doc_hash == expected_hash:
                continue

            hash_mismatches = True

            if fix:
                new_content = content.replace(doc_full_cmd, new_command)

                with open(str(md_file), "w", encoding="utf-8") as qs_file:
                    qs_file.write(new_content)
                print(f"Fixed an IPFS hash on doc file {md_file}")
                old_to_new_hashes[doc_hash] = expected_hash
            else:
                print(
                    f"IPFS hash mismatch on doc file {md_file}. Expected {expected_hash}, got {doc_hash}:\n    {doc_full_cmd}"
                )

    # Fix packages on python files
    all_py_files = [Path("autonomy", "constants.py")]
    for py_file in all_py_files:
        content = read_file(str(py_file))
        for match in [m.groupdict() for m in re.finditer(FULL_PACKAGE_REGEX, content)]:
            full_package = match["full_package"]
            py_hash = match["hash"]
            expected_hash = package_manager.get_hash_by_package_line(
                full_package, str(py_file)
            )
            if not expected_hash:
                errors = True
                continue
            expected_package = package_manager.get_package_by_hash(expected_hash)
            if not expected_package:
                errors = True
                continue

            new_package = (":").join(full_package.split(":")[:-1] + [expected_hash])

            # Overwrite with new hash
            if py_hash == expected_hash:
                continue

            hash_mismatches = True

            if fix:
                new_content = content.replace(full_package, new_package)

                with open(str(py_file), "w", encoding="utf-8") as qs_file:
                    qs_file.write(new_content)
                print(f"Fixed an IPFS hash on doc file {py_file}")
                old_to_new_hashes[py_hash] = expected_hash
            else:
                print(
                    f"IPFS hash mismatch on file {py_file}. Expected {expected_hash}, got {py_hash}:\n    {full_package}"
                )

    if fix and errors:
        raise ValueError(
            "There were some errors while fixing IPFS hashes. Check the logs."
        )

    if not fix and (hash_mismatches or errors):
        print("There are mismatching IPFS hashes in the docs.")
        sys.exit(1)

    if matches == 0:
        print(
            "No commands were found in the docs. The command regex is probably outdated."
        )
        sys.exit(1)

    print("OK")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--fix", action="store_true")
    args = parser.parse_args()
    check_ipfs_hashes(fix=args.fix)
