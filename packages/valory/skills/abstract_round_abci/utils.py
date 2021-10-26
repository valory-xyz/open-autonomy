# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021 Valory AG
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

"""This module contains utility functions for the 'abstract_round_abci' skill."""
import builtins
import importlib.util
import json
import logging
import os
import types
from importlib.machinery import ModuleSpec
from time import time
from typing import Any, Callable, Dict, List, Optional, Tuple

from packages.valory.skills.abstract_round_abci.behaviours import AbstractRoundBehaviour


def _get_module(spec: ModuleSpec) -> Optional[types.ModuleType]:
    """Try to execute a module. Return None if the attempt fail."""
    try:
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore
        return module
    except Exception:  # pylint: disable=broad-except
        return None


def locate(path: str) -> Any:
    """Locate an object by name or dotted save_path, importing as necessary."""
    parts = [part for part in path.split(".") if part]
    module, i = None, 0
    while i < len(parts):
        file_location = os.path.join(*parts[: i + 1])
        spec_name = ".".join(parts[: i + 1])
        module_location = os.path.join(file_location, "__init__.py")
        spec = importlib.util.spec_from_file_location(spec_name, module_location)
        nextmodule = _get_module(spec)  # type: ignore
        if nextmodule is None:
            module_location = file_location + ".py"
            spec = importlib.util.spec_from_file_location(spec_name, module_location)
            nextmodule = _get_module(spec)  # type: ignore

        if os.path.exists(file_location) or nextmodule:
            module, i = nextmodule, i + 1
        else:  # pragma: nocover
            break
    if module:
        object_ = module
    else:
        object_ = builtins
    for part in parts[i:]:
        try:
            object_ = getattr(object_, part)
        except AttributeError:
            return None
    return object_


class Benchmark:
    """Benchmark"""

    tick: float
    behaviour: AbstractRoundBehaviour
    consensus_time: List[Tuple[str, float]]

    def __init__(
        self,
        behaviour: AbstractRoundBehaviour,
        consensus_time: List[Tuple[str, float]],
        save_function: Callable,
    ) -> None:
        """Benchmark for single round."""
        self.behaviour = behaviour
        self.consensus_time = consensus_time
        self.save_function = save_function

    def __enter__(
        self,
    ) -> None:
        """Enter context."""
        self.tick = time()

    def __exit__(self, *args: List, **kwargs: Dict) -> None:
        """Exit context"""

        total_time = time() - self.tick
        self.consensus_time.append((self.behaviour.matching_round.round_id, total_time))
        self.save_function()


class BenchmarkRound:
    """TimeStamp to measure performance."""

    consensus_time: List[Tuple[str, float]]
    agent: Optional[str]
    agent_address: Optional[str]
    rounds: List[str]

    def __init__(
        self,
    ) -> None:
        """Benchmark tool for rounds behaviours."""
        self.agent = None
        self.agent_address = None
        self.consensus_time = []
        self.rounds = []

    def log(
        self,
    ) -> None:
        """Output log."""

        print(f"Agent : {self.agent}")
        print(f"Agent Address : {self.agent_address}")

        max_length = len(max(self.rounds)) + 4

        print(f"\nRound{' '*(max_length-5)}Time\n{'='*(max_length+20)}")
        for round_name, total_time in self.consensus_time:
            print(f"{round_name}{' '*(max_length-len(round_name))}{total_time}")

    def save(
        self,
    ) -> None:
        """Save logs to a file."""
        try:
            with open(
                f"/logs/{self.agent_address}.json", "w+", encoding="utf-8"
            ) as outfile:
                json.dump(
                    {
                        "agent_address": self.agent_address,
                        "agent": self.agent,
                        "data": dict(self.consensus_time),
                        "rounds": self.rounds,
                    },
                    outfile,
                )
        except (PermissionError, FileNotFoundError):
            logging.info("Error saving benchmark data.")

    def measure(self, behaviour: AbstractRoundBehaviour) -> Benchmark:
        """Measure time to complete round."""

        if self.agent is None:
            self.agent_address = behaviour.context.agent_address
            self.agent = behaviour.context.agent_name

        self.rounds.append(behaviour.matching_round.round_id)
        return Benchmark(behaviour, self.consensus_time, self.save)
