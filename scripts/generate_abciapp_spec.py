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
Generates the specification for a given ABCI app in YAML/JSON format using a simplified syntax for deterministic finite automata (DFA).

Example usage:

./generate_abciapp_spec.py -c packages.valory.skills.registration_abci.rounds.AgentRegistrationAbciApp -o output.yaml

optional arguments:
  -h, --help            show this help message and exit
  -o OUTFILE, --outfile OUTFILE
                        Output file name.
  -f {json,yaml}, --outformat {json,yaml}
                        Output format.

required arguments:
  -c CLASSFQN, --classfqn CLASSFQN
                        ABCI App class fully qualified name.
"""

import argparse
import importlib
import json
import logging
import re
import sys
from collections import Counter
from itertools import product
from pathlib import Path
from typing import Dict, Iterable, Tuple, Type

import yaml

from packages.valory.skills.abstract_round_abci.base import AbciApp


def ensure_unique(*containers: Iterable) -> None:
    """Verify that all are unique"""
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
        start_states: Iterable[str],
        final_states: Iterable[str],
        events: Iterable[str],
        transition_func: Dict[Tuple[str, str], str],
    ):  # pylint: disable=too-many-arguments
        """Initialize DFA object."""

        ensure_unique(states, start_states, final_states, events)

        self.label = label
        self.states = set(states)
        self.default_start_state = default_start_state
        self.start_states = set(start_states)
        self.final_states = set(final_states)
        self.events = set(events)
        self.transition_func = transition_func

        self.verify_conditions()

    def verify_conditions(self) -> None:
        """Basic validity check of the specification"""
        x0, x, xf = self.start_states, self.states, self.final_states
        tf_x, tf_events = map(set, zip(*self.transition_func.keys()))
        tf_x.update(self.transition_func.values())  # type: ignore

        x0def_in_x0 = self.default_start_state in x0
        unknown_x0 = x0 - x
        unknown_xf = xf - x
        orphan_x = x ^ (x0 | set(self.transition_func.values()))
        unknown_x = tf_x ^ x
        unknown_events = tf_events ^ self.events

        report = "\n".join(
            [
                f"Orphan states: {orphan_x}." if orphan_x else "",
                f"Unknown states: {unknown_x}." if unknown_x else "",
                f"Unknown input symbols: {unknown_events}." if unknown_events else "",
                "Default start state not in start states." if not x0def_in_x0 else "",
                f"Unknown start states: {unknown_x0}" if unknown_x0 else "",
                f"Unknown final states: {unknown_xf}" if unknown_xf else "",
            ]
        )
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

        :return: boolean
        """
        return set(product(self.states, self.events)) == set(self.transition_func)

    def __eq__(self, other: object) -> bool:
        """Compares two DFAs"""
        if not isinstance(other, DFA):
            return NotImplemented
        return self.__dict__ == other.__dict__

    def dump(self, file_path: str, file_format: str = "yaml") -> None:
        """Dumps this DFA spec. to a file in YAML/JSON format."""

        def sorted_and_formatted_dict(d: dict) -> dict:
            """Sort and format"""
            return dict(sorted((str(k).replace("'", ""), v) for k, v in d.items()))

        mapping = {set: sorted, dict: sorted_and_formatted_dict}
        content = self.__dict__.items()
        serialized = {k: mapping.get(type(v), lambda _: _)(v) for k, v in content}  # type: ignore

        with open(file_path, "w", encoding="utf8") as fp:
            if file_format == "json":
                json.dump(serialized, fp, indent=4)
            elif file_format == "yaml":
                yaml.safe_dump(serialized, fp, indent=4)
            else:
                raise ValueError(f"Unrecognized output format {format}.")
            logging.info(f"saved file to: {file_path}")

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
            logging.info(f"loaded from: {file_path}")

        def tuplify(k: str) -> Tuple[str, str]:
            match = re.search(r"\((\w*),\s(\w*)\)", k, re.DOTALL)
            if not match:
                raise DFASpecError(f"Invalid transition function key: {k}.")
            return match.groups()  # type: ignore

        tuplified_tf = {tuplify(k): v for k, v in dfa_specs["transition_func"].items()}
        dfa_specs["transition_func"] = tuplified_tf

        return cls(**dfa_specs)

    @classmethod
    def abci_to_dfa(cls, abci_app_cls: Type[AbciApp], label: str = "") -> "DFA":
        """Translates an AbciApp class into a DFA."""

        tf = abci_app_cls.transition_function

        label = label or abci_app_cls.__module__ + "." + abci_app_cls.__name__
        default_start_state = abci_app_cls.initial_round_cls.__name__
        x0 = {s.__name__ for s in abci_app_cls.initial_states}
        x0 = x0 or {default_start_state}
        xf = {s.__name__ for s in abci_app_cls.final_states}
        tf_sources = {k.__name__ for k in tf}
        tf_sinks = {s.__name__ for k in tf for s in tf[k].values()}
        x = tf_sources | tf_sinks
        tf_events = {str(s).rsplit(".", 1)[1] for v in tf.values() for s in v}
        tf_x = {
            (state_in.__name__, str(event).rsplit(".", 1)[1]): state_out.__name__
            for state_in, mapping in tf.items()
            for event, state_out in mapping.items()
        }

        return cls(label, x, default_start_state, x0, xf, tf_events, tf_x)


def parse_arguments() -> argparse.Namespace:
    """Parse the script arguments."""
    script_name = Path(__file__).name
    parser = argparse.ArgumentParser(
        script_name,
        description=f"Generates the specification for a given ABCI app in YAML/JSON format using a simplified syntax for "
        "deterministic finite automata (DFA). Example usage:\n"
        f"./{script_name} -c packages.valory.skills.registration_abci.rounds.AgentRegistrationAbciApp -o output.yaml",
    )
    required = parser.add_argument_group("required arguments")
    required.add_argument(
        "-c",
        "--classfqn",
        type=str,
        required=True,
        help="ABCI App class fully qualified name.",
    )
    parser.add_argument(
        "-f",
        "--file",
        type=str,
        required=False,
        default=sys.stdout,
        help="Output file name.",
    )
    parser.add_argument(
        "-format",
        "--format",
        type=str,
        choices=["json", "yaml"],
        default="yaml",
        help="Output format.",
    )
    return parser.parse_args()


def main() -> None:
    """Execute the script.

    example usage:
    scripts/generate_abciapp_spec.py -c packages.valory.skills.price_estimation_abci.composition.PriceEstimationAbciApp
    """
    logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)
    arguments = parse_arguments()
    abci_app = load_app(*arguments.classfqn.rsplit(".", 1))
    dfa = DFA.abci_to_dfa(abci_app)
    dfa.dump(arguments.outfile, arguments.outformat)
    logging.info("Done.")


if __name__ == "__main__":
    main()
