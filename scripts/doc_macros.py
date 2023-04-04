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


"""This module contains macros used with the mkdocs-macros package."""

import configparser
import json
import re
from pathlib import Path

import requests
from jinja2 import Environment


OPEN_AUTONOMY_ROOT = Path(__file__).parent.parent

# Get Open Autonomy and referenced tag of Open AEA packages
pipfile = configparser.ConfigParser()
pipfile.read(Path(OPEN_AUTONOMY_ROOT, "Pipfile"))
match = re.search(r"version\s*=\s*\"==(.+?)\"", pipfile["packages"]["open-aea"])

if match is None:
    raise RuntimeError("Failed to read open-aea version from Pipfile.")

open_aea_version = match.group(1)
response = requests.get(
    f"https://github.com/valory-xyz/open-aea/raw/v{open_aea_version}/packages/packages.json"
)
response.raise_for_status()
aea_packages_json = json.loads(response.text)

with open(Path(OPEN_AUTONOMY_ROOT, "packages", "packages.json"), encoding="utf-8") as f:
    autonomy_packages_json = json.load(f)

packages = aea_packages_json["dev"].copy()
packages.update(aea_packages_json["third_party"])
packages.update(autonomy_packages_json["dev"])
packages.update(autonomy_packages_json["third_party"])


def define_env(env: Environment) -> None:
    """
    This is the mkdocs-macros hook for defining variables, macros and filters.

    :param env: Jinja2 environment.
    """

    @env.macro
    def get_packages_entry(key: str) -> str:
        """
        Returns the packages.json entry for a specified key.

        Example:
        "agent/valory/hello_world/0.1.0": "bafybei0000000000000000000000000000000000000000000000000000"

        :param key: Key of the packages.json file (`dev` or `third_party`).
        :return: Formatted entry as "key: value".
        """

        return '"{}": "{}"'.format(key, packages[key])
