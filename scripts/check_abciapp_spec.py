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

required arguments:
  -c CLASSFQN, --classfqn CLASSFQN
                        ABCI App class fully qualified name.
  -i INFILE, --infile INFILE
                        Input file name.

optional arguments:
  -h, --help            show this help message and exit
  -f {json,yaml}, --informat {json,yaml}
                        Input format.
"""

import logging
import sys

from scripts.generate_abciapp_spec import DFA, load_app, parse_arguments


def main() -> None:
    """Execute the script."""

    logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)
    arguments = parse_arguments()
    abci_app = load_app(*arguments.classfqn.rsplit(".", 1))
    dfa = DFA.abci_to_dfa(abci_app)
    dfa2 = DFA.load(arguments.infile, arguments.informat)
    if dfa == dfa2:
        logging.info("ABCI App matches specification.")
        sys.exit(0)
    else:
        logging.error("ABCI App does NOT match specification.")
        sys.exit(1)


if __name__ == "__main__":
    main()
