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
Check, Generate or Compare the implementation and specification of an ABCIApp.

Example usage:

1. check
./check_abciapp_spec.py packages.valory.skills.registration_abci.rounds.AgentRegistrationAbciApp
2. generate
./check_abciapp_spec.py packages.valory.skills.registration_abci.rounds.AgentRegistrationAbciApp -o output_file.yaml
3. compare
./check_abciapp_spec.py packages.valory.skills.registration_abci.rounds.AgentRegistrationAbciApp -i output_file.yaml

optional arguments:
  -h, --help            Show this help message and exit
  -i INFILE,  --infile INFILE
                        Output file name.
  -o OUTFILE, --outfile OUTFILE
                        Output file name.
  -f {json, yaml}, --format {json, yaml}
                        Output format.
"""

import argparse
import importlib
import json
import logging
import re
from collections import Counter
from itertools import product
from pathlib import Path
from typing import Dict, Iterable, Tuple, Type

import yaml

from packages.valory.skills.abstract_round_abci.base import AbciApp


def ensure_unique(*containers: Iterable) -> None:
    """Verify that items in each container are unique"""

    for identifiers in containers:
        duplicates = {k for k, v in Counter(identifiers).items() if v > 1}
        if duplicates:
            raise ValueError(f"duplicates found: {duplicates}")


def load_app(module_name: str, class_name: str) -> Type[AbciApp]:
    """Load ABCIApp class from module"""

    module = importlib.import_module(module_name)
    if not hasattr(module, class_name):
        raise Exception(f'Class "{class_name}" is not in "{module_name}".')
    return getattr(module, class_name)


class DFASpecError(Exception):
    """Simple class to raise errors when parsing a DFA."""


class DFA:
    """Simple specification of a deterministic finite automaton (DFA)."""

    def __init__(
        self,
        label: str,
        states: Iterable[str],
        default_start_state: str,
        initial_states: Iterable[str],
        final_states: Iterable[str],
        events: Iterable[str],
        transition_func: Dict[Tuple[str, str], str],
    ):  # pylint: disable=too-many-arguments
        """Initialize DFA object."""

        ensure_unique(states, initial_states, final_states, events)

        self.label = label
        self.states = set(states)
        self.default_start_state = default_start_state
        self.initial_states = set(initial_states)
        self.final_states = set(final_states)
        self.events = set(events)
        self.transition_func = transition_func

        self.verify_conditions()

    def verify_conditions(self) -> None:  # pylint: disable-msg=too-many-locals
        """Basic validity check of the specification"""

        x0, x, xf = self.initial_states, self.states, self.final_states
        tf_x0, tf_events = map(set, zip(*self.transition_func.keys()))
        tf_xf = set(self.transition_func.values())
        tf_x = tf_x0 | tf_xf

        x0def_in_x0 = self.default_start_state in x0
        unknown_x0 = x0 - x
        unknown_xf = xf - x
        orphan_x = x - (x0 | tf_xf)
        unknown_x = tf_x ^ x
        unknown_events = tf_events ^ self.events
        xf_out = xf & tf_x0
        x0_in_xf = x0 & xf

        lines = [
            f"Orphan states: {orphan_x}" if orphan_x else "",
            f"Unknown states: {unknown_x}" if unknown_x else "",
            f"Unknown input symbols: {unknown_events}" if unknown_events else "",
            "Default initial state not in initial states" if not x0def_in_x0 else "",
            f"Unknown initial states: {unknown_x0}" if unknown_x0 else "",
            f"Unknown final states: {unknown_xf}" if unknown_xf else "",
            f"Final states with outgoing transition: {xf_out}" if xf_out else "",
            f"Overlap initial and final states: {x0_in_xf}" if x0_in_xf else "",
        ]

        report = "\n".join(filter(None, lines))
        if report:
            raise DFASpecError(report)

    @property
    def is_transition_func_total(self) -> bool:
        """
        Outputs True if the transition function of the DFA is total.

        A transition function is total when it explicitly defines all the transitions
        for all the possible pairs (state, input_symbol). By convention, when a transition
        (state, input_symbol) is not defined for a certain input_symbol, it will be
        automatically regarded as a self-transition to the same state.

        :return: bool
        """
        return set(product(self.states, self.events)) == set(self.transition_func)

    def dump(self, file_path: str, output_format: str = "yaml") -> None:
        """Dumps this DFA spec. to a file in YAML/JSON format."""

        def sorted_and_formatted_dict(d: dict) -> dict:
            """Sort and format"""
            return dict(sorted((str(k).replace("'", ""), v) for k, v in d.items()))

        mapping = {set: sorted, dict: sorted_and_formatted_dict}
        content = self.__dict__.items()
        serialized = {k: mapping.get(type(v), lambda _: _)(v) for k, v in content}  # type: ignore

        with open(file_path, "w", encoding="utf8") as fp:
            if output_format == "json":
                json.dump(serialized, fp, indent=4)
            elif output_format == "yaml":
                yaml.safe_dump(serialized, fp, indent=4)
            else:
                raise ValueError(f"Unrecognized output format {output_format}.")
            logging.info(f"saved: {file_path}")

    @classmethod
    def load(cls, file_path: str, input_format: str = "yaml") -> "DFA":
        """Loads a DFA specification from file."""

        with open(file_path, "r", encoding="utf8") as fp:
            if input_format == "json":
                dfa_specs = json.load(fp)
            elif input_format == "yaml":
                dfa_specs = yaml.safe_load(fp)
            else:
                raise ValueError(f"Unrecognized input format {input_format}.")
            logging.info(f"loaded: {file_path}")

        def tuplify(k: str) -> Tuple[str, str]:
            match = re.search(r"\((\w*),\s(\w*)\)", k, re.DOTALL)
            if not match:
                raise DFASpecError(f"Invalid transition function key: {k}.")
            return match.groups()  # type: ignore

        tuplified_tf = {tuplify(k): v for k, v in dfa_specs["transition_func"].items()}
        dfa_specs["transition_func"] = tuplified_tf

        return cls(**dfa_specs)

    @classmethod
    def abci_to_dfa(cls, abci_app_cls: Type[AbciApp]) -> "DFA":
        """Translates an AbciApp class into a DFA."""

        app_tf = abci_app_cls.transition_function

        label = abci_app_cls.__module__ + "." + abci_app_cls.__name__
        default_initial_state = abci_app_cls.initial_round_cls.__name__
        x0 = {s.__name__ for s in abci_app_cls.initial_states}
        x0 = x0 or {default_initial_state}
        xf = {s.__name__ for s in abci_app_cls.final_states}
        tf_sources = {k.__name__ for k in app_tf}
        tf_sinks = {s.__name__ for k in app_tf for s in app_tf[k].values()}
        tf_x = tf_sources | tf_sinks
        tf_events = {event.value.upper() for v in app_tf.values() for event in v}
        tf = {
            (state_in.__name__, event.value.upper()): state_out.__name__
            for state_in, transitions in app_tf.items()
            for event, state_out in transitions.items()
        }

        return cls(label, tf_x, default_initial_state, x0, xf, tf_events, tf)

    def __eq__(self, other: object) -> bool:
        """Compares two DFAs"""
        if not isinstance(other, DFA):
            return NotImplemented
        return self.__dict__ == other.__dict__


def parse_arguments() -> argparse.Namespace:
    """Parse the script arguments."""

    this_path = Path(__file__)
    example_abci_app_path = (
        "packages.valory.skills.registration_abci.rounds.AgentRegistrationAbciApp"
    )
    check_command = f"./{this_path.name} {example_abci_app_path}"
    parser = argparse.ArgumentParser(
        this_path.name,
        description="Check the specification of an ABCIApp implementation. "  # 1. check conditions only
        "A YAML or JSON specification can also be generated using a simplified human-readable "
        "syntax for deterministic finite automata (DFA). "  # 2. also generate YAML or JSON
        "Such a specification may also be provided by the user for comparison of the intended "
        "and actual implementation of an ABCIApp.",  # 3. compare to YAML / JSON
        epilog=f"Example usage:\n\n"
        f"To check:\n{check_command}\n"
        f"To generate:\n{check_command} -o output_file.yaml\n"
        f"To compare:\n{check_command} -i input_file.yaml\n",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    required = parser.add_argument_group("required arguments")
    required.add_argument(
        "class_path",
        type=str,
        help="ABCIApp class fully qualified name",
    )
    parser.add_argument(
        "-i",
        "--infile",
        type=str,
        required=False,
        help="Input file name",
    )
    parser.add_argument(
        "-o",
        "--outfile",
        type=str,
        required=False,
        help="Output file name",
    )
    parser.add_argument(
        "-f",
        "--format",
        type=str,
        required=False,
        choices=["json", "yaml"],
        default="yaml",
        help="File type",
    )
    return parser.parse_args()


def main() -> None:
    """Main"""

    logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)

    args = parse_arguments()
    if args.infile and args.outfile:
        raise AttributeError("Can only provide `--infile` or `--outfile`, not both")

    module_name, class_name = args.class_path.rsplit(".", 1)
    abci_app = load_app(module_name, class_name)
    dfa = DFA.abci_to_dfa(abci_app)

    if args.infile:
        dfa_from_specs = DFA.load(args.infile, args.format)
        if dfa == dfa_from_specs:
            logging.info("ABCIApp Implementation matches specification.")
        else:  # TODO: report differences
            logging.info("ABCIApp Implementation DOES NOT match specification.")
    elif args.outfile:
        dfa.dump(args.outfile, args.format)
        logging.info(f"ABCIApp Specification written to:\n{args.outfile}")
    else:
        logging.info(f"ABCIApp conditions check passed for `{class_name}`")


if __name__ == "__main__":
    main()
