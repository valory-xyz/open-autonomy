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

"""
Handlers checker.

This script checks that all the handlers defined in the skill.yaml files of the repository
are also defined in the correspondent handlers.py file.

It is assumed the script is run from the repository root.
"""
import importlib
from pathlib import Path

import yaml


# Skills excluded from defining all the handlers in COMMON_HANDLERS
BASIC_SKILLS = ("abstract_abci", "counter", "counter_client", "hello_world_abci")

# Handlers that every non-basic skill must declare
COMMON_HANDLERS = ("abci", "http", "contract_api", "ledger_api", "signing")


def check_handlers():
    """Check handlers"""
    skill_yamls = [*Path("packages/").glob("**/skill.yaml")]

    for yaml_file in skill_yamls:
        handler_file_path = yaml_file.parent / "handlers.py"

        # Verify handler.py file exists
        if not handler_file_path.is_file():
            raise FileNotFoundError(f"File {handler_file_path} does not exist")

        # Load module
        module_name = str(handler_file_path).replace(".py", "").replace("/", ".")
        skill_name = module_name.split(".")[-2]
        print(f"Checking: {module_name}")
        try:
            module = importlib.import_module(module_name)
            module_attributes = dir(module)
        except ModuleNotFoundError as exc:
            raise FileNotFoundError(
                f"Handler file {module_name} does not exist"
            ) from exc

        # Load skill.yaml
        with open(str(yaml_file), mode="r", encoding="utf-8") as fp:
            config = yaml.safe_load(fp)

            # Check for the common handlers
            if skill_name not in BASIC_SKILLS:
                for common_handler in COMMON_HANDLERS:
                    assert (
                        common_handler in config["handlers"].keys()
                    ), f"Common handler '{common_handler}' is not defined in {yaml_file}"

            # Check for missing handlers
            for handler_info in config["handlers"].values():
                assert (
                    handler_info["class_name"] in module_attributes
                ), f"Handler {handler_info['class_name']} declared in {yaml_file} is missing from {handler_file_path}"

    print("Check successful.")


if __name__ == "__main__":
    check_handlers()
