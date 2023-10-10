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


"""This module contains the tools for autoupdating ipfs hashes in the documentation."""

import argparse
import itertools
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

import requests
import yaml
from aea.cli.packages import get_package_manager
from aea.configurations.data_types import PackageId
from aea.helpers.base import IPFS_HASH_REGEX, SIMPLE_ID_REGEX


CLI_REGEX = r"(?P<cli>aea|autonomy)"
# CMD_REGEX should be r"(?P<cmd>(\S+\s(\s--\S+)*)+)",
# but python implementation differs from others and does not match it properly
CMD_REGEX = r"(?P<cmd>.*)"
VENDOR_REGEX = rf"(?P<vendor>{SIMPLE_ID_REGEX})"
PACKAGE_REGEX = rf"(?P<package>{SIMPLE_ID_REGEX})"
VERSION_REGEX = r"(?P<version>\d+\.\d+\.\d+)"
FLAGS_REGEX = r"(?P<flags>(\s--.*)?)"
PACKAGE_TYPE_REGEX = (
    r"(?P<package_type>(skill|protocol|connection|contract|agent|service))"
)

AEA_COMMAND_REGEX = rf"(?P<full_cmd>{CLI_REGEX} {CMD_REGEX} (?:{VENDOR_REGEX}\/{PACKAGE_REGEX}:{VERSION_REGEX}?:?)?(?P<hash>{IPFS_HASH_REGEX}){FLAGS_REGEX})"
FULL_PACKAGE_REGEX = rf"(?P<full_package>(?:{VENDOR_REGEX}\/{PACKAGE_REGEX}:{VERSION_REGEX}?:?)?(?P<hash>{IPFS_HASH_REGEX}))"
PACKAGE_TABLE_REGEX = rf"\|\s*{PACKAGE_TYPE_REGEX}\/{VENDOR_REGEX}\/{PACKAGE_REGEX}\/{VERSION_REGEX}\s*\|\s*`(?P<hash>{IPFS_HASH_REGEX})`\s*\|"
PACKAGE_MAPPING_REGEX = rf"(?P<package_mapping>(?:\"{PACKAGE_TYPE_REGEX}\/{VENDOR_REGEX}\/{PACKAGE_REGEX}\/{VERSION_REGEX}\":)\s*\"(?P<hash>{IPFS_HASH_REGEX})\")"

ROOT_DIR = Path(__file__).parent.parent
HASH_SKIPS = [
    "Qmbh9SQLbNRawh9Km3PMEDSxo77k1wib8fYZUdZkhPBiev",  # Testing image used in tutorials/examples.
    "bafybei0000000000000000000000000000000000000000000000000000",  # Placeholder hash used in tutorials/examples.
]


def read_file(filepath: str) -> str:
    """Loads a file into a string"""
    with open(filepath, "r", encoding="utf-8") as file_:
        file_str = file_.read()
    return file_str


def get_packages() -> Dict[str, str]:
    """Get packages."""
    data = get_package_manager(Path("packages").relative_to(".")).json
    if "dev" in data:
        return {**data["dev"], **data["third_party"]}
    return data


def get_packages_from_repository(repo_url: str) -> Dict[str, str]:
    """Retrieve packages.json from the latest release from a repository."""
    repo_url = repo_url.strip("/").replace("https://github.com/", "")
    repo_api_url = f"https://api.github.com/repos/{repo_url}/releases/latest"
    response = requests.get(repo_api_url)

    if response.status_code == 200:
        repo_info = response.json()
        latest_release_tag = repo_info["tag_name"]
        url = f"https://raw.githubusercontent.com/{repo_url}/{latest_release_tag}/packages/packages.json"
    else:
        raise Exception(
            f"Failed to fetch repository information from GitHub API for: {repo_url}"
        )

    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if "dev" in data:
            return {**data["dev"], **data["third_party"]}
        return data

    raise Exception(f"Failed to fetch data from URL: {url}")


class Package:  # pylint: disable=too-few-public-methods
    """Class that represents a package in packages.json"""

    def __init__(
        self,
        package_id_str: str,
        package_hash: str,
        ignore_file_load_errors: bool = False,
    ) -> None:
        """Constructor"""

        self.package_id = PackageId.from_uri_path(package_id_str)
        self.vendor = self.package_id.author
        self.type = self.package_id.package_type.to_plural()
        self.name = self.package_id.name
        self.hash = package_hash
        self.ignore_file_load_errors = ignore_file_load_errors

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
                f"Package: unknown package type in packages.json: {self.type}"
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

        try:
            with open(yaml_file_path, "r", encoding="utf-8") as file:
                content = yaml.load_all(file, Loader=yaml.FullLoader)
                for resource in content:
                    if "version" in resource:
                        self.last_version = resource["version"]
                        break
        except Exception:  # pylint: disable=broad-except
            if not self.ignore_file_load_errors:
                raise
            self.last_version = self.package_id.version

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
    """Class that represents the packages in packages.json"""

    def __init__(self) -> None:
        """Constructor"""
        packages = get_packages()
        self.packages = [Package(key, value) for key, value in packages.items()]

        package_json_urls = [
            "https://github.com/valory-xyz/hello-world",
        ]

        for url in package_json_urls:
            packages_from_url = get_packages_from_repository(url)
            packages.update(packages_from_url)
            self.packages.extend(
                [Package(key, value, True) for key, value in packages_from_url.items()]
            )

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
                f"PackageHashManager: hash search for {package_hash} returned more than 1 result in packages.json"
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
                    f"[{target_file}]: line '{package_line}' does not match an autonomy/aea command or package format"
                )
                return None
            m = m_command or m_package
            d = m.groupdict()  # type: ignore

            # Underspecified commands that only use the hash
            # In this case we cannot infer the package type, just check whether or not the hash exists in packages.json
            if not d["vendor"] and not d["package"]:
                package = self.get_package_by_hash(d["hash"])

                # This hash exists in packages.json
                if package:
                    return package.hash

                # This hash does not exist in packages.json
                print(
                    f"[{target_file}]: unknown IPFS hash in line '{package_line}'. Can't fix because this command just uses the hash"
                )
                return None

            # Complete command, succesfully retrieved or complete packages

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

    def get_hash_by_attributes(
        self, package_type: str, vendor: str, package_name: str
    ) -> str:
        """Get a package hash give the package information"""
        return self.package_tree[vendor][package_type][package_name].hash


def check_ipfs_hashes(  # pylint: disable=too-many-locals,too-many-statements
    paths: Optional[List[Path]] = None, fix: bool = False
) -> None:
    """Fix ipfs hashes in the docs"""

    paths = paths or [Path("docs")]

    all_md_files = itertools.chain.from_iterable([path.rglob("*.md") for path in paths])
    errors = False
    hash_mismatches = False
    old_to_new_hashes = {}
    package_manager = PackageHashManager()
    matches = 0

    # Fix hashes in docs
    for md_file in all_md_files:
        content = read_file(str(md_file))

        # Fix full commands in docs
        for match in [m.groupdict() for m in re.finditer(AEA_COMMAND_REGEX, content)]:
            matches += 1
            doc_full_cmd = match["full_cmd"]
            doc_cmd = match["cmd"]
            doc_hash = match["hash"]
            flags = match["flags"]

            if doc_hash in HASH_SKIPS:
                continue

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
                content = content.replace(doc_full_cmd, new_command)

                with open(str(md_file), "w", encoding="utf-8") as qs_file:
                    qs_file.write(content)
                print(f"Fixed an IPFS hash in doc file {md_file}")
                old_to_new_hashes[doc_hash] = expected_hash
            else:
                print(
                    f"IPFS hash mismatch in doc file {md_file}.\n"
                    f"\tCommand string: {doc_full_cmd}\n"
                    f"\tExpected: {expected_hash}\n"
                    f"\tFound: {doc_hash}\n"
                )

        # Fix package mappings in docs
        for match in [
            m.groupdict() for m in re.finditer(PACKAGE_MAPPING_REGEX, content)
        ]:
            matches += 1
            package_mapping = match["package_mapping"]
            package_hash = match["hash"]

            if package_hash in HASH_SKIPS:
                continue

            expected_hash = package_manager.get_hash_by_attributes(
                match["package_type"], match["vendor"], match["package"]
            )

            if package_hash == expected_hash:
                continue

            hash_mismatches = True

            if fix:
                new_package_mapping = package_mapping.replace(
                    package_hash, expected_hash
                )
                content = content.replace(package_mapping, new_package_mapping)

                with open(str(md_file), "w", encoding="utf-8") as qs_file:
                    qs_file.write(content)
                print(f"Fixed an IPFS hash in doc file {md_file}")
                old_to_new_hashes[package_hash] = expected_hash
            else:
                print(
                    f"IPFS hash mismatch in doc file {md_file}.\n"
                    f"\tMapping string: {package_mapping}\n"
                    f"\tExpected: {expected_hash}\n"
                    f"\tFound: {package_hash}\n"
                )

    # Fix packages in python files
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
                content = content.replace(full_package, new_package)

                with open(str(py_file), "w", encoding="utf-8") as qs_file:
                    qs_file.write(content)
                print(f"Fixed an IPFS hash in doc file {py_file}")
                old_to_new_hashes[py_hash] = expected_hash
            else:
                print(
                    f"IPFS hash mismatch on file {py_file}.\n"
                    f"\tPackage: {full_package}\n"
                    f"\tExpected: {expected_hash}\n,"
                    f"\tFound: {py_hash}:\n"
                )

    # Fix hashes in package list
    package_list_file = Path(ROOT_DIR, "docs", "package_list.md")
    content = read_file(str(package_list_file))

    for match in [m.groupdict() for m in re.finditer(PACKAGE_TABLE_REGEX, content)]:
        expected_hash = package_manager.get_hash_by_attributes(
            match["package_type"], match["vendor"], match["package"]
        )
        package_hash = match["hash"]

        if package_hash == expected_hash:
            continue

        print(
            f"IPFS hash mismatch in doc file {package_list_file}.\n"
            f'\tPackage: {match["package_type"]}/{match["vendor"]}/{match["package"]}\n'
            f"\tExpected: {expected_hash},\n"
            f"\tFound: {package_hash}\n"
        )
        hash_mismatches = True

        # Overwrite with new hash
        if fix:
            content = content.replace(package_hash, expected_hash)

    if fix:
        with open(str(package_list_file), "w", encoding="utf-8") as p_file:
            p_file.write(content)
        print(f"Fixed some IPFS hashes in doc file {package_list_file}")

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

    print("Checking doc IPFS hashes finished successfully.")


if __name__ == "__main__":
    print("Start checking doc IPFS hashes.")
    parser = argparse.ArgumentParser()
    parser.add_argument("--fix", action="store_true")
    parser.add_argument("-p", "--paths", type=Path, nargs="*", default=[Path("docs")])
    args = parser.parse_args()
    check_ipfs_hashes(paths=args.paths, fix=args.fix)
