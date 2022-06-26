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
"""Check dependencies."""
import re
import shutil
import subprocess  # nosec
from itertools import islice
from typing import Iterable, List, Pattern, Tuple


ERROR_MESSAGE_TEMPLATE_BINARY_NOT_FOUND = (
    "'{command}' is required by the "
    "abci connection, but it is not installed, "
    "or it is not accessible from the system path."
)
ERROR_MESSAGE_TEMPLATE_VERSION_TOO_LOW = (
    "The installed version of '{command}' "
    "is too low: expected at least {lower_bound}; "
    "found {actual_version}."
)

# for the purposes of this script,
# a version is a tuple of integers: (major, minor, patch)
VERSION = Tuple[int, int, int]
MINIMUM_TENDERMINT_VERSION: VERSION = (0, 34, 19)


def nth(iterable: Iterable, index: int, default: int = 0) -> int:
    """Returns the item at position 'index' or a default value"""
    return next(islice(iterable, index, None), default)


def get_version(*args: int) -> VERSION:
    """
    Get the version from a list of arguments.

    Set to '0' if there are not enough arguments.

    :param args: positional arguments
    :return: the version
    """
    major = nth(args, 0, 0)
    minor = nth(args, 1, 0)
    patch = nth(args, 2, 0)
    return major, minor, patch


def version_to_string(version: VERSION) -> str:
    """
    Transform version to string.

    :param version: the version.
    :return: the string representation.
    """
    return ".".join(map(str, version))


def print_ok_message(
    binary_name: str, actual_version: VERSION, version_lower_bound: VERSION
) -> None:  # pragma: nocover
    """
    Print OK message.

    :param binary_name: the binary binary_name.
    :param actual_version: the actual version.
    :param version_lower_bound: the version lower bound.
    """
    print(
        f"check '{binary_name}'>={version_to_string(version_lower_bound)}, "
        f"found {version_to_string(actual_version)}"
    )


def check_binary(
    binary_name: str,
    args: List[str],
    version_regex: Pattern,
    version_lower_bound: VERSION,
    only_warning: bool = False,
) -> None:  # pragma: nocover
    """
    Check a binary is accessible from the terminal.

    It breaks down in:
    1) check if the binary is reachable from the system path;
    2) check that the version number is higher or equal than the minimum required version.

    :param binary_name: the name of the binary.
    :param args: the arguments to provide to the binary to retrieve the version.
    :param version_regex: the regex used to extract the version from the output.
    :param version_lower_bound: the minimum required version.
    :param only_warning: if True, don't raise error but print a warning message
    """
    path = shutil.which(binary_name)
    if not path:
        message = ERROR_MESSAGE_TEMPLATE_BINARY_NOT_FOUND.format(command=binary_name)
        if only_warning:
            print("Warning: ", message)
            return
        raise ValueError(message)

    version_getter_command = [binary_name, *args]
    stdout = subprocess.check_output(version_getter_command).decode("utf-8")  # nosec
    version_match = version_regex.search(stdout)
    if version_match is None:
        print(
            f"Warning: cannot parse '{binary_name}' version "
            f"from command: {version_getter_command}. stdout: {stdout}"
        )
        return
    actual_version: VERSION = get_version(*map(int, version_match.groups(default="0")))
    if actual_version < version_lower_bound:
        message = ERROR_MESSAGE_TEMPLATE_VERSION_TOO_LOW.format(
            command=binary_name,
            lower_bound=version_to_string(version_lower_bound),
            actual_version=version_to_string(actual_version),
        )
        if only_warning:
            print(f"Warning: {message}")
            return
        raise ValueError(message)

    print_ok_message(binary_name, actual_version, version_lower_bound)


def check_versions() -> None:  # pragma: nocover
    """Check versions."""
    check_binary(
        "tendermint",
        ["version"],
        re.compile(r"([0-9]+)\.([0-9]+)\.([0-9]+)"),
        MINIMUM_TENDERMINT_VERSION,
        only_warning=True,
    )


def main() -> None:  # pragma: nocover
    """The main entrypoint of the script."""
    check_versions()


if __name__ == "__main__":
    main()  # pragma: nocover
