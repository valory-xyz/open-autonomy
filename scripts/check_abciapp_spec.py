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
Checks that a given ABCI app matches a specification in YAML/JSON format using a simplified syntax for deterministic finite automata (DFA).

Example usage:

./check_abciapp_spec.py -c packages.valory.skills.registration_abci.rounds.AgentRegistrationAbciApp -i input.yaml

optional arguments:
  -h, --help            show this help message and exit
  -f {json,yaml}, --informat {json,yaml}
                        Input format.

required arguments:
  -c CLASSFQN, --classfqn CLASSFQN
                        ABCI App class fully qualified name.
  -i INFILE, --infile INFILE
                        Input file name.
"""

import argparse
import importlib
import sys
from pathlib import Path
from typing import Dict, Optional

import yaml

from scripts.generate_abciapp_spec import DFA


def parse_arguments() -> argparse.Namespace:
    """Parse the script arguments."""
    script_name = Path(__file__).name
    parser = argparse.ArgumentParser(
        script_name,
        description=f"Checks that a given ABCI app matches a specification in YAML/JSON format using a simplified syntax for "
        "deterministic finite automata (DFA). Example usage:\n"
        f"./{script_name} -c packages.valory.skills.registration_abci.rounds.AgentRegistrationAbciApp -i input.yaml",
    )
    required = parser.add_argument_group("required arguments")
    required.add_argument(
        "-c",
        "--classfqn",
        type=str,
        required=True,
        help="ABCI App class fully qualified name.",
    )
    required.add_argument(
        "-i",
        "--infile",
        type=argparse.FileType("r"),
        required=True,
        help="Input file name.",
    )
    parser.add_argument(
        "-f",
        "--informat",
        type=str,
        choices=["json", "yaml"],
        default="yaml",
        help="Input format.",
    )
    arguments_ = parser.parse_args()
    return arguments_


def check_one(arguments: Optional[Dict] = None) -> bool:
    """Check for one."""

    if arguments is None:
        arguments = dict(
            parse_arguments()._get_kwargs()  # pylint: disable=protected-access
        )

    print(f"Checking : {arguments['classfqn']}")

    module_name, class_name = arguments["classfqn"].rsplit(".", 1)
    module = importlib.import_module(module_name)
    if not hasattr(module, class_name):
        raise Exception(f'Class "{class_name}" is not in "{module_name}".')

    abci_app_cls = getattr(module, class_name)
    dfa1 = DFA.abci_to_dfa(abci_app_cls, arguments["classfqn"])
    dfa2 = DFA.load(arguments["infile"], arguments["informat"])
    return dfa1 == dfa2


def check_all() -> None:
    """Check all the available definitions."""

    did_not_match = []
    fsm_specifications = Path("packages/").glob("**/fsm_specification.yaml")
    for spec_file in fsm_specifications:
        with open(str(spec_file), mode="r", encoding="utf-8") as fp:
            specs = yaml.safe_load(fp)
            arguments = {
                "informat": "yaml",
                "infile": open(  # pylint: disable=consider-using-with
                    str(spec_file), mode="r", encoding="utf-8"
                ),
                "classfqn": specs.pop("label"),
            }
            if not check_one(arguments):
                did_not_match.append(arguments["classfqn"])

    if len(did_not_match) > 0:
        print("\nSpecifications did not match for following definitions.\n")
        print("\n".join(did_not_match))
        sys.exit(1)

    print("Check successful.")


if __name__ == "__main__":

    if "--check-all" in sys.argv:
        check_all()
    else:
        check_one()
