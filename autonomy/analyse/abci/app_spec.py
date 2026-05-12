# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022-2026 Valory AG
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
"""Generates the specification for a given ABCI app in YAML/JSON/Mermaid format.

JSON output is deprecated and will be removed in a future release; use YAML
or Mermaid instead.
"""

import inspect
import json
import logging
import re
import textwrap
import warnings
from collections import OrderedDict, defaultdict, deque
from enum import Enum
from itertools import product
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Set, Tuple, Type

import yaml
from aea.helpers.io import open_file
from aea.helpers.json_schema import Draft4Validator

from autonomy.configurations.constants import (
    DEFAULT_FSM_SPEC_JSON,
    DEFAULT_FSM_SPEC_MERMAID,
    DEFAULT_FSM_SPEC_YAML,
    SCHEMAS_DIR,
)

FSM_SCHEMA_FILE = "fsm_specification_schema.json"
ROUND_CLASS_POST_FIX = "Round"
ABCI_APP_CLASS_POST_FIX = "AbciApp"

EVENT_PATTERN = re.compile(r"Event\.(\w+)", re.DOTALL)
# Lines like ``done_event = Event.DONE`` or ``none_event: Enum = Event.X`` at
# class-body indentation.  These are resolved by attribute lookup rather than
# textually, so we strip them before regex-scanning the rest of the source.
EVENT_ATTR_ASSIGN_PATTERN = re.compile(
    r"^[ \t]+[a-z_]+_event\s*[:=][^\n]*$", re.MULTILINE
)
# ``# fsm-specs: returns(EVENT1, EVENT2)`` annotation -- declares events a
# round emits dynamically (e.g. ``Event(payload_value)``) where the regex
# scan has no signal.
FSM_SPECS_RETURNS_PATTERN = re.compile(r"#\s*fsm-specs:\s*returns\s*\(([^)]*)\)")
ROUND_TIMEOUT_EVENTS = {"ROUND_TIMEOUT"}


class _AbciAppLike(Protocol):  # pylint: disable=too-few-public-methods
    """Structural type for AbciApp class objects used by the spec loader.

    Matches the attributes of ``AbciApp`` accessed by ``dump_mermaid``
    and ``_build_round_to_subapp``. Uses ``Any`` for nested types to
    avoid coupling to the ``packages.*`` class hierarchy.
    """

    transition_function: Dict[Any, Dict[Any, Any]]
    initial_states: Set[Any]
    final_states: Set[Any]


def validate_fsm_spec(data: Dict) -> None:
    """Validate FSM specificaiton file."""
    with open_file(SCHEMAS_DIR / FSM_SCHEMA_FILE) as fp:
        fsm_schema = json.load(fp=fp)

    validator = Draft4Validator(schema=fsm_schema)
    validator.validate(data)


class DFASpecificationError(Exception):
    """Simple class to raise errors when parsing a DFA."""


class FSMSpecificationLoader:
    """FSM specification loader utilities."""

    class OutputFormats:  # pylint: disable=too-few-public-methods
        """Output formats."""

        JSON = "json"
        YAML = "yaml"
        MERMAID = "mermaid"
        ALL = (JSON, YAML, MERMAID)

        default_output_files = {
            JSON: DEFAULT_FSM_SPEC_JSON,
            YAML: DEFAULT_FSM_SPEC_YAML,
            MERMAID: DEFAULT_FSM_SPEC_MERMAID,
        }

    @staticmethod
    def from_yaml(file: Path) -> Dict:
        """Load from yaml."""
        with open_file(file, mode="r", encoding="utf-8") as fp:
            data = yaml.safe_load(fp)
        return data

    @staticmethod
    def from_json(file: Path) -> Dict:
        """Load from json."""
        with open_file(file, mode="r", encoding="utf-8") as fp:
            data = json.load(fp=fp)
        return data

    @classmethod
    def load(
        cls,
        file: Path,
        spec_format: str = OutputFormats.YAML,
    ) -> Dict:
        """Load FSM specification."""

        if spec_format == cls.OutputFormats.JSON:
            data = cls.from_json(file)
        elif spec_format == cls.OutputFormats.YAML:
            data = cls.from_yaml(file)
        else:
            raise ValueError(f"Unrecognized input format {spec_format}.")

        validate_fsm_spec(data)
        return data

    @staticmethod
    def dump_json(dfa: "DFA", file: Path) -> None:
        """Dump to a json file (deprecated).

        JSON output is deprecated; prefer YAML or Mermaid. The
        ``DeprecationWarning`` is emitted by ``dump()`` so that
        ``stacklevel`` always points at the external caller.

        :param dfa: DFA object to serialize.
        :param file: Output file path.
        """
        with open_file(file, "w", encoding="utf-8") as fp:
            json.dump(dfa.generate(), fp, indent=4)

    @staticmethod
    def dump_yaml(dfa: "DFA", file: Path) -> None:
        """Dump to a yaml file."""
        with open_file(file, "w", encoding="utf-8") as fp:
            yaml.safe_dump(dfa.generate(), fp, indent=4)

    @staticmethod
    def dump_mermaid(
        dfa: "DFA",
        file: Path,
        abci_app_cls: Optional[_AbciAppLike] = None,
        dev_skills: Optional[Set[str]] = None,
    ) -> None:
        """Dumps this DFA spec. to a file in Mermaid format.

        When ``abci_app_cls`` is supplied AND its rounds span more than one
        sub-app, the diagram collapses every THIRD-PARTY sub-app into a
        single node (one box per sub-app), and leaves dev sub-apps expanded
        with their atomic rounds. ``dev_skills`` is the set of skill names
        the local repo authored (typically derived from the ``dev`` section
        of ``packages/packages.json``); any sub-app not in this set is
        treated as third-party and collapsed.

        Falls back to the flat per-round diagram when ``abci_app_cls`` is
        ``None``, when ``dev_skills`` is empty or ``None`` (i.e. no
        packages.json info available), or when all rounds belong to a
        single sub-app.

        :param dfa: DFA object to render.
        :param file: Output file path.
        :param abci_app_cls: Optional composed AbciApp class used to classify
            rounds by sub-app for the composition-aware view.
        :param dev_skills: Optional set of dev skill names (from
            ``packages.json``); sub-apps not in this set are collapsed.
        """
        # A dev sub-app collapses like third-party when it has no internal
        # transitions (typical for single-round shared recovery skills).
        round_to_subapp = FSMSpecificationLoader._build_round_to_subapp(abci_app_cls)
        internal_counts: Dict[str, int] = {}
        for (s1, _), s2 in dfa.transition_func.items():
            s1_sub = round_to_subapp.get(s1)
            s2_sub = round_to_subapp.get(s2)
            if s1_sub is not None and s1_sub == s2_sub:
                internal_counts[s1_sub] = internal_counts.get(s1_sub, 0) + 1

        dev_subapps: Set[str] = set()
        third_party_subapps: Set[str] = set()
        for sub_app in set(round_to_subapp.values()):
            is_dev = dev_skills is not None and sub_app in dev_skills
            if is_dev and internal_counts.get(sub_app, 0) > 0:
                dev_subapps.add(sub_app)
            else:
                third_party_subapps.add(sub_app)

        flatten = (
            abci_app_cls is None
            or not dev_skills
            or len(round_to_subapp) == 0
            or (len(dev_subapps) + len(third_party_subapps)) <= 1
        )
        if flatten and abci_app_cls is not None:
            reasons = []
            if not dev_skills:
                reasons.append("no dev_skills info (packages.json not found)")
            if len(round_to_subapp) == 0:
                reasons.append("no rounds could be classified by sub-app")
            if (len(dev_subapps) + len(third_party_subapps)) <= 1:
                reasons.append("all rounds belong to a single sub-app")
            logging.warning(
                "Composition-aware view not available, using flat diagram: %s",
                "; ".join(reasons) if reasons else "unknown",
            )

        def _display(state: str) -> str:
            """Collapse third-party rounds to their sub-app name."""
            if flatten:
                return state
            sub = round_to_subapp.get(state)
            if sub in third_party_subapps:
                return sub
            return state

        internal_per_subapp: Dict[str, Dict[Tuple[str, str], Set[str]]] = {}
        top_level: Dict[Tuple[str, str], Set[str]] = {}
        for (s1, t), s2 in dfa.transition_func.items():
            s1_sub = round_to_subapp.get(s1)
            s2_sub = round_to_subapp.get(s2)
            if not flatten and s1_sub is not None and s1_sub == s2_sub:
                if s1_sub in dev_subapps:
                    internal_per_subapp.setdefault(s1_sub, {}).setdefault(
                        (s1, s2), set()
                    ).add(t)
                continue
            top_level.setdefault((_display(s1), _display(s2)), set()).add(t)

        start_states = {_display(s) for s in dfa.start_states}

        with open_file(file, "w", encoding="utf-8") as fp:
            # Fenced Markdown block so the file renders inline on GitHub /
            # VS Code / docs sites.
            print("```mermaid", file=fp)
            print("stateDiagram-v2", file=fp)

            # Sub-apps needing an invisible placeholder child so Mermaid
            # still draws the outer frame (`state X { }` is rejected).
            hidden_subapps: Set[str] = set()
            if not flatten:
                dev_rounds_per_subapp: Dict[str, Set[str]] = {}
                for round_name, sub_app in round_to_subapp.items():
                    if sub_app in dev_subapps:
                        dev_rounds_per_subapp.setdefault(sub_app, set()).add(round_name)

                for sub_app in sorted(dev_subapps):
                    # dev_subapps only contains sub-apps with at least one
                    # internal transition, so dev_rounds_per_subapp[sub_app]
                    # is guaranteed non-empty here.
                    rounds = sorted(dev_rounds_per_subapp[sub_app])
                    internal = internal_per_subapp.get(sub_app, {})
                    print(f"    state {sub_app} {{", file=fp)
                    # `state "X" as X` (alias form) -- bare `state X`
                    # triggers Mermaid's missing "roundedWithTitle" shape
                    # error.
                    for round_name in rounds:
                        print(
                            f'        state "{round_name}" as {round_name}',
                            file=fp,
                        )
                    for (s1, s2), events in sorted(internal.items()):
                        label = "<br />".join(sorted(events))
                        print(
                            f"        {s1} --> {s2}: <center>{label}</center>",
                            file=fp,
                        )
                    print("    }", file=fp)

                for sub_app in sorted(third_party_subapps):
                    print(f"    state {sub_app} {{", file=fp)
                    print(f'        state " " as {sub_app}_hidden', file=fp)
                    print("    }", file=fp)
                    hidden_subapps.add(sub_app)

            # Two passes for deterministic output: start states first.
            for (s1, s2), events in sorted(top_level.items()):
                if s1 in start_states:
                    label = "<br />".join(sorted(events))
                    print(
                        f"    {s1} --> {s2}: <center>{label}</center>",
                        file=fp,
                    )
            for (s1, s2), events in sorted(top_level.items()):
                if s1 not in start_states:
                    label = "<br />".join(sorted(events))
                    print(
                        f"    {s1} --> {s2}: <center>{label}</center>",
                        file=fp,
                    )

            if not flatten and dev_subapps:
                print(
                    "    classDef devGroup "
                    "fill:#f5f9f5,"
                    "stroke:#2e7d32,"
                    "stroke-width:2px,"
                    "font-weight:bold",
                    file=fp,
                )
                print(
                    f"    class {','.join(sorted(dev_subapps))} devGroup",
                    file=fp,
                )
            if not flatten and third_party_subapps:
                print(
                    "    classDef macro "
                    "fill:#f5f9f5,"
                    "stroke:#2e7d32,"
                    "stroke-width:3px,"
                    "font-weight:bold",
                    file=fp,
                )
                print(
                    f"    class {','.join(sorted(third_party_subapps))} macro",
                    file=fp,
                )
            if not flatten and hidden_subapps:
                print(
                    "    classDef hiddenInner "
                    "fill:transparent,"
                    "stroke:transparent,"
                    "color:transparent",
                    file=fp,
                )
                print(
                    "    class "
                    + ",".join(f"{s}_hidden" for s in sorted(hidden_subapps))
                    + " hiddenInner",
                    file=fp,
                )
            print("```", file=fp)

    @staticmethod
    def _build_round_to_subapp(
        abci_app_cls: Optional[_AbciAppLike],
    ) -> Dict[str, str]:
        """Map each round class name to its owning sub-app skill name.

        e.g. ``packages.valory.skills.market_manager_abci.rounds``
        contains ``UpdateBetsRound`` -> ``market_manager_abci``.
        Returns ``{}`` when ``abci_app_cls`` is ``None``.

        :param abci_app_cls: Composed AbciApp class to inspect, or ``None``.
        :return: Mapping from round class name to owning sub-app skill name.
        """
        if abci_app_cls is None:
            return {}

        round_classes: Set[Any] = set()
        for src, transitions in abci_app_cls.transition_function.items():
            round_classes.add(src)
            for dst in transitions.values():
                round_classes.add(dst)
        for init_cls in getattr(abci_app_cls, "initial_states", set()) or set():
            round_classes.add(init_cls)
        for final_cls in getattr(abci_app_cls, "final_states", set()) or set():
            round_classes.add(final_cls)

        # Sort by class name first so collision resolution is deterministic
        # (set iteration order is unstable across runs / sub-app pairs).
        result: Dict[str, str] = {}
        for cls in sorted(round_classes, key=lambda c: (c.__name__, c.__module__)):
            module = getattr(cls, "__module__", "")
            sub_app = FSMSpecificationLoader._extract_skill_name(module)
            if not sub_app:
                continue
            name = cls.__name__
            if name in result and result[name] != sub_app:
                logging.warning(
                    "Round name collision: %s in %s and %s; keeping %s",
                    name,
                    result[name],
                    sub_app,
                    result[name],
                )
                continue
            result[name] = sub_app

        unclassified = {c.__name__ for c in round_classes if c.__name__ not in result}
        if unclassified:
            logging.warning(
                "Unclassified rounds (no `skills` segment in __module__): %s",
                sorted(unclassified),
            )

        return result

    @staticmethod
    def _extract_skill_name(module_path: str) -> Optional[str]:
        """Pull the skill name out of a ``packages.<author>.skills.<skill>...`` path.

        :param module_path: Dotted module path string.
        :return: The skill name segment, or ``None`` if the path has
            no ``skills`` segment.
        """
        parts = module_path.split(".")
        try:
            idx = parts.index("skills")
        except ValueError:
            return None
        if idx + 1 >= len(parts):
            return None
        return parts[idx + 1]

    @classmethod
    def dump(
        cls,
        dfa: "DFA",
        file: Path,
        spec_format: str = OutputFormats.YAML,
        abci_app_cls: Optional[_AbciAppLike] = None,
        dev_skills: Optional[Set[str]] = None,
    ) -> None:
        """Dumps this DFA spec. to a file in YAML/JSON/Mermaid format.

        ``abci_app_cls`` and ``dev_skills`` are only used by the Mermaid
        renderer to collapse third-party sub-apps into single nodes while
        keeping dev sub-apps expanded (see ``dump_mermaid``). Other
        formats ignore them.

        :param dfa: DFA object to serialize.
        :param file: Output file path.
        :param spec_format: One of ``OutputFormats.YAML``, ``JSON``, or
            ``MERMAID``.
        :param abci_app_cls: Optional composed AbciApp class (Mermaid only).
        :param dev_skills: Optional set of dev skill names (Mermaid only).
        """

        validate_fsm_spec(dfa.generate())

        if spec_format == cls.OutputFormats.JSON:
            warnings.warn(
                "fsm-specs JSON output is deprecated and will be removed "
                "in a future release; use --yaml or --mermaid instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            cls.dump_json(dfa, file)
        elif spec_format == cls.OutputFormats.YAML:
            cls.dump_yaml(dfa, file)
        elif spec_format == cls.OutputFormats.MERMAID:
            cls.dump_mermaid(
                dfa, file, abci_app_cls=abci_app_cls, dev_skills=dev_skills
            )
        else:
            raise ValueError(f"Unrecognized input format {spec_format}.")


class DFA:
    """Simple specification of a deterministic finite automaton (DFA)."""

    def __init__(
        self,
        label: str,
        states: Set[str],
        default_start_state: str,
        start_states: Set[str],
        final_states: Set[str],
        alphabet_in: Set[str],
        transition_func: Dict[Tuple[str, str], str],
    ):
        """Initialize DFA object."""
        transition_func_in_states, transition_func_alphabet_in = map(
            set, zip(*transition_func.keys())
        )

        transition_func_states = transition_func_in_states.copy()
        transition_func_states.update(transition_func.values())  # type: ignore

        reachable_states = DFA._get_reachable_states(start_states, transition_func)
        unreachable_states = states - reachable_states

        error_strings = []
        if unreachable_states:
            error_strings.append(
                f" - DFA spec. contains unreachable states: {unreachable_states}."
            )
        if not transition_func_states.issubset(states):
            error_strings.append(
                f" - Transition function contains unexpected states: {transition_func_states - states}."  # type: ignore
            )
        if not transition_func_alphabet_in.issubset(alphabet_in):
            error_strings.append(
                " - Transition function contains unexpected input symbols: "
                f"{transition_func_alphabet_in - alphabet_in}."  # type: ignore
            )
        if not alphabet_in.issubset(transition_func_alphabet_in):
            error_strings.append(
                f" - Unused input symbols: {alphabet_in - transition_func_alphabet_in}."  # type: ignore
            )
        if default_start_state not in start_states:
            error_strings.append(" - Default start state is not in start states set.")
        if not start_states.issubset(states):
            error_strings.append(
                f" - Start state set contains unexpected states: {start_states - states}."
            )
        if not final_states.issubset(states):
            error_strings.append(
                f" - Final state set contains unexpected states: {final_states - states}."
            )
        if start_states & final_states:
            error_strings.append(
                f" - Final state set contains start states: {start_states & final_states}."
            )
        if transition_func_in_states & final_states:
            error_strings.append(
                f" - Transitions out from final states: {transition_func_in_states & final_states}."
            )

        if len(error_strings) > 0:
            raise DFASpecificationError(
                "DFA spec has the following issues:\n" + "\n".join(error_strings)
            )

        self.label = label
        self.states = states
        self.default_start_state = default_start_state
        self.start_states = start_states
        self.final_states = final_states
        self.alphabet_in = alphabet_in
        self.transition_func = transition_func

        self.validate_naming_conventions()

    def validate_naming_conventions(self) -> None:
        """
        Validate state names to see if they follow the naming conventions below

        - A round name should end with `Round`
        - ABCI app class name should end with `AbciApp`
        """

        if not self.label.endswith(ABCI_APP_CLASS_POST_FIX):
            raise DFASpecificationError(
                f"ABCI app class name should end in `AbciApp`; ABCI app name found `{self.label}`"
            )

        for state in self.states:
            if not state.endswith(ROUND_CLASS_POST_FIX):
                raise DFASpecificationError(
                    f"Round class name should end in `Round`; Round app name found `{state}`"
                )

    def is_transition_func_total(self) -> bool:
        """
        Outputs True if the transition function of the DFA is total.

        A transition function is total when it explicitly defines all the transitions
        for all the possible pairs (state, input_symbol). By convention, when a transition
        (state, input_symbol) is not defined for a certain input_symbol, it will be
        automatically regarded as a self-transition to the same state.

        :return: True if the transition function is total. False otherwise.
        """
        return set(product(self.states, self.alphabet_in)) == set(
            self.transition_func.keys()
        )

    def get_transitions(self, input_sequence: List[str]) -> List[str]:
        """Runs the DFA given the input sequence of symbols, and outputs the list of state transitions."""
        state = self.default_start_state
        transitions = [state]
        for t in input_sequence:
            if t not in self.alphabet_in:
                logging.warning(
                    f"Input sequence contains a symbol {t} (ignored) "
                    f"not belonging to the DFA alphabet {self.alphabet_in}."
                )
            else:
                state = self.transition_func.get((state, t), state)
                transitions.append(state)
        return transitions

    def parse_transition_func(self) -> Dict[str, Dict[str, str]]:
        """Parse the transition function from the spec to a nested dictionary."""

        result: Dict[str, Dict[str, str]] = {}
        for (round_cls_name, event_name), value in self.transition_func.items():
            result.setdefault(round_cls_name, {})[f"Event.{event_name}"] = value
        for state in self.states:
            if state not in result:
                result[state] = {}
        return result

    def __eq__(self, other: object) -> bool:
        """Compares two DFAs"""
        if not isinstance(other, DFA):
            return NotImplemented  # Try reflected operation
        return self.__dict__ == other.__dict__

    def generate(self) -> Dict[str, Any]:
        """Retrieves an exportable representation for YAML/JSON dump of this DFA."""
        dfa_export: Dict[str, Any] = {}
        for k, v in self.__dict__.items():
            if isinstance(v, Set):
                dfa_export[k] = sorted(v)
            elif isinstance(v, Dict):
                dfa_export[k] = dict(
                    OrderedDict(
                        [(str(k2).replace("'", ""), v2) for k2, v2 in v.items()]
                    )
                )
            else:
                dfa_export[k] = v
        return dfa_export

    @classmethod
    def _get_reachable_states(
        cls,
        start_states: Set[str],
        transition_func: Dict[Tuple[str, str], str],
    ) -> Set[str]:
        """Performs a BFS-like search returning the reachable set of states departing from the set of start states."""

        graph: Dict[str, Set[str]] = defaultdict(set)
        for (s1, _), s2 in transition_func.items():
            graph[s1].add(s2)

        visited: Set[str] = start_states.copy()
        queue = deque(start_states)

        while queue:
            s = queue.popleft()

            for neighbour in graph[s]:
                if neighbour not in visited:
                    visited.add(neighbour)
                    queue.append(neighbour)

        return visited

    @classmethod
    def _norep_list_to_set(cls, lst: List[str]) -> Set[str]:
        """Converts a list to a set and ensures that it does not contain repetitions."""
        if not isinstance(lst, List):
            raise DFASpecificationError(f"DFA spec. object {lst} is not of type List.")
        if len(lst) != len(set(lst)):
            raise DFASpecificationError(
                f"DFA spec. List {lst} contains repeated values."
            )
        return set(lst)

    @classmethod
    def _str_to_tuple(cls, k: str) -> Tuple[str, str]:
        """Converts a string in format "(a, b)" to a tuple ("a", "b")."""
        match = re.search(r"\((\w+),\s*(\w+)\)", k, re.DOTALL)

        if match is None:
            raise DFASpecificationError(
                f"DFA spec. JSON file contains an invalid transition function key: {k}."
            )

        return match.group(1), match.group(2)

    @classmethod
    def load(
        cls, file: Path, spec_format: str = FSMSpecificationLoader.OutputFormats.YAML
    ) -> "DFA":
        """Loads a DFA JSON specification from file."""

        dfa_data = FSMSpecificationLoader.load(file=file, spec_format=spec_format)

        label = dfa_data.pop("label")
        states = DFA._norep_list_to_set(dfa_data.pop("states"))
        default_start_state = dfa_data.pop("default_start_state")
        start_states = DFA._norep_list_to_set(dfa_data.pop("start_states"))
        final_states = DFA._norep_list_to_set(dfa_data.pop("final_states"))
        alphabet_in = DFA._norep_list_to_set(dfa_data.pop("alphabet_in"))
        transition_func = {
            DFA._str_to_tuple(k): v for k, v in dfa_data.pop("transition_func").items()
        }

        return cls(
            label,
            states,
            default_start_state,
            start_states,
            final_states,
            alphabet_in,
            transition_func,
        )

    @classmethod
    def abci_to_dfa(cls, abci_app_cls: Any, label: str = "") -> "DFA":
        """Translates an AbciApp class into a DFA."""

        trf = abci_app_cls.transition_function

        label = label if label != "" else abci_app_cls.__name__
        default_start_state = abci_app_cls.initial_round_cls.__name__
        start_states = DFA._norep_list_to_set(
            [s.__name__ for s in abci_app_cls.initial_states]
        )
        start_states = start_states if start_states else {default_start_state}
        final_states = DFA._norep_list_to_set(
            [s.__name__ for s in abci_app_cls.final_states]
        )
        states = (
            DFA._norep_list_to_set([k.__name__ for k in trf])
            | {s.__name__ for k in trf for s in trf[k].values()}
            | start_states
            | final_states
        )
        alphabet_in = {str(s).rsplit(".", 1)[1] for k in trf for s in trf[k].keys()}
        transition_func = {
            (k.__name__, str(s).rsplit(".", 1)[1]): trf[k][s].__name__
            for k in trf
            for s in trf[k]
        }
        transition_func = OrderedDict(sorted(transition_func.items()))
        return cls(
            label,
            states,
            default_start_state,
            start_states,
            final_states,
            alphabet_in,
            transition_func,
        )


def _resolved_event_attr_names(round_cls: Any) -> Set[str]:
    """Return the names of ``*_event`` Enum values effectively bound on the round.

    Walks the MRO leaf-first and resolves each ``<name>_event`` class
    attribute (``done_event``, ``none_event``, ``no_majority_event``,
    ``fail_event``, ``negative_event``, ...) to the value defined by the
    most-derived class that introduces it, then returns the set of
    ``Enum.name`` values.  Parent-class re-definitions overridden by a
    subclass are ignored, matching Python's attribute lookup semantics.

    :param round_cls: Round class to inspect.
    :return: Set of effective ``Enum.name`` values for ``*_event`` attrs.
    """
    seen: Dict[str, Any] = {}
    for base in inspect.getmro(round_cls):
        if base.__module__ == "builtins":
            continue
        for name, value in vars(base).items():
            if name.endswith("_event") and name not in seen:
                seen[name] = value
    return {v.name for v in seen.values() if isinstance(v, Enum)}


def _abci_app_event_enum(abci_app_cls: Any) -> Optional[Type[Enum]]:
    """Return the Event enum class used by the given AbciApp, if discoverable.

    The transitions dict maps each round to ``{Event: NextRound}``; we sniff
    one Event member to recover its class.  Falls back to inspecting
    ``event_to_timeout`` if no transition has entries, and returns ``None``
    if neither yields an Event member.

    :param abci_app_cls: AbciApp class to inspect.
    :return: The ``Event`` Enum class, or ``None`` if it can't be determined.
    """
    for transitions in abci_app_cls.transition_function.values():
        for event in transitions:
            if isinstance(event, Enum):
                return type(event)
    for event in getattr(abci_app_cls, "event_to_timeout", {}):
        if isinstance(event, Enum):
            return type(event)
    return None


def check_unreferenced_events(abci_app_cls: Any) -> List[str]:
    """Check for unreferenced events in the AbciApp.

    For every round in the transition function, computes the set of events
    the round can effectively emit and compares it to the events the FSM
    expects.  An event is considered emitted if it is either:

    1. The effective value of a ``*_event`` class attribute, resolved
       leaf-first through the MRO (so an override masks the parent value).
    2. Referenced as ``Event.X`` in the source of the round or any of its
       non-builtin superclasses, with ``*_event = Event.X`` attribute
       definitions stripped out (those are covered by case 1, and a
       parent-class definition would otherwise be reported even after the
       subclass overrides the attribute).  When the AbciApp's Event enum
       can be identified, names absent from that enum are dropped to avoid
       cross-skill collisions (e.g. ``market_manager.Event.FETCH_ERROR``
       referenced from a parent class living in a different skill).
    3. Declared via a ``# fsm-specs: returns(EVENT_NAME, ...)`` annotation
       on the round class -- the supported syntax for rounds that build
       events dynamically (e.g. ``Event(payload_value)``).

    :param abci_app_cls: AbciApp to check unreferenced events.
    :return: List of error strings.
    """
    error_strings = []
    abci_app_timeout_events = {k.name for k in abci_app_cls.event_to_timeout.keys()}
    own_enum = _abci_app_event_enum(abci_app_cls)
    own_enum_names: Optional[Set[str]] = (
        set(own_enum.__members__) if own_enum is not None else None
    )

    for round_cls, round_transitions in abci_app_cls.transition_function.items():
        round_transition_events = set(map(lambda x: x.name, round_transitions))
        referenced_events: Set[str] = _resolved_event_attr_names(round_cls)
        for base in inspect.getmro(round_cls):
            if base.__module__ == "builtins":
                continue
            try:
                src = textwrap.dedent(inspect.getsource(base))
            except (OSError, TypeError):  # pragma: no cover
                continue
            scan_src = EVENT_ATTR_ASSIGN_PATTERN.sub("", src)
            for match in EVENT_PATTERN.findall(scan_src):
                if own_enum_names is None or match in own_enum_names:
                    referenced_events.add(match)
            for annotation in FSM_SPECS_RETURNS_PATTERN.findall(src):
                referenced_events.update(
                    name.strip() for name in annotation.split(",") if name.strip()
                )

        # Referenced in the the class definition, missing from transition func
        missing_from_transition_func = referenced_events - round_transition_events
        if len(missing_from_transition_func) > 0:
            error_strings.append(
                f"Events {missing_from_transition_func} are present in the `{round_cls.__name__}` "
                f"but missing from transition function"
            )

        # Events that appear in a round's transition function but are never returned from
        # end_block are assumed to be timeout-triggered; they must therefore be declared in
        # `event_to_timeout`. If the developer actually intends to return such an event,
        # wiring it up in that round's end_block is the fix.
        timeout_events = round_transition_events - referenced_events
        missing_timeout_events = timeout_events - abci_app_timeout_events
        if len(missing_timeout_events) > 0:
            error_strings.append(
                f"Events {missing_timeout_events} are listed in the transition function of "
                f"`{round_cls.__name__}` but are never returned from any round's `end_block`. "
                f"Either return them from `end_block`, or declare them in `event_to_timeout` "
                f"if they are meant to be triggered by a round timeout."
            )

    return error_strings
