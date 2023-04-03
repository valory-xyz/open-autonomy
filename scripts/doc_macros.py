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


"""This module contains the macros used in docs."""

import json
import math
import os

import requests


# Get Open Autonomy and latest tag Open AEA packages
response = requests.get(
    "https://api.github.com/repos/valory-xyz/open-aea/releases/latest"
)
response.raise_for_status()
latest_tag = response.json()["tag_name"]
response = requests.get(
    f"https://github.com/valory-xyz/open-aea/raw/{latest_tag}/packages/packages.json"
)
response.raise_for_status()
aea_packages_json = json.loads(response.text)

with open("./packages/packages.json") as f:
    autonomy_packages_json = json.load(f)

packages = aea_packages_json["dev"].copy()
packages.update(autonomy_packages_json["dev"])


def define_env(env):
    """
    This is the hook for defining variables, macros and filters

    - variables: the dictionary that contains the environment variables
    - macro: a decorator function, to declare a macro.
    - filter: a function with one of more arguments,
        used to perform a transformation
    """

    @env.macro
    def get_packages_entry(key):
        return '"{}": "{}"'.format(key, packages[key])
