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

"""This module contains a tool to export contract packages from their corresponding json build files."""

import json
from datetime import date
from typing import Dict, Tuple

from cookiecutter.main import (  # type: ignore # pylint: disable=import-error
    cookiecutter,
)


# Type equivalence between solidity and python
TYPE_EQUIVALENCE = {
    "address": "str",
    "uint256": "int",
    "bytes32": "bytes",
    "uint8": "int",
    "bool": "bool",
}


def extract_functions_from_build(contract_build_path: str) -> Tuple[Dict, Dict]:
    """Loads information about solidity methods: name, inputs and input types"""

    with open(contract_build_path, "r", encoding="utf-8") as abi_file:
        abi = json.load(abi_file)

        functions = list(
            filter(
                lambda x: x["type"] == "function"
                and not x["name"].isupper(),  # skip DOMAIN_SEPARATOR, PERMIT_TYPEHASH
                abi["abi"],
            )
        )

        read_functions = {
            f["name"]: {i["name"]: TYPE_EQUIVALENCE[i["type"]] for i in f["inputs"]}
            for f in functions
            if f["stateMutability"] == "view"
        }
        write_functions = {
            f["name"]: {i["name"]: TYPE_EQUIVALENCE[i["type"]] for i in f["inputs"]}
            for f in functions
            if f["stateMutability"] not in ("view", "pure")
        }
        return read_functions, write_functions


def generate_package(config_file_path: str = "scripts/contract_config.json"):
    """Generates a contract package using the given configuration"""

    # Load contract configuration
    with open(config_file_path, "r", encoding="utf-8") as config_file:
        contract_config = json.load(config_file)

        # Load contract method information
        read_functions, write_functions = extract_functions_from_build(
            contract_config["build_path"]
        )

        # Add extra information to the configuration
        contract_config["read_functions"] = read_functions
        contract_config["write_functions"] = write_functions
        contract_config["year"] = date.today().year

    # Run cookiecutter
    cookiecutter(
        template="contract_template/",
        extra_context=contract_config,  # overwrite config
        output_dir=contract_config["output_dir"],
        overwrite_if_exists=True,
        no_input=True,  # avoid prompt
    )


if __name__ == "__main__":
    generate_package()
