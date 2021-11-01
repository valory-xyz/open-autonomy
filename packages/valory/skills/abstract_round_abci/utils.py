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
from typing import Any, Dict, List, Optional

from packages.valory.skills.abstract_round_abci.behaviour_utils import BaseState


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


class BenchmarkBlockTypes:  # pylint: disable=too-few-public-methods
    """Benchmark block types."""

    LOCAL = "local"
    CONSENSUS = "consensus"
    TOTAL = "total"


class BenchmarkBlock:
    """Benchmark"""

    start: float
    total_time: float
    block_type: str

    def __init__(self, block_type: str) -> None:
        """Benchmark for single round."""
        self.block_type = block_type

    def __enter__(
        self,
    ) -> None:
        """Enter context."""
        self.start = time()

    def __exit__(self, *args: List, **kwargs: Dict) -> None:
        """Exit context"""
        self.total_time = time() - self.start


class BenchmarkBehaviour:
    """Benchmark a behaviour."""

    behaviour: BaseState
    local_data: Dict[str, BenchmarkBlock]

    def __init__(self, behaviour: BaseState) -> None:
        """Initialize Benchmark behaviour object."""

        self.behaviour = behaviour
        self.local_data = {}

    def _measure(self, block_type: str) -> BenchmarkBlock:
        """Returns a BenchmarkBlock object."""

        if block_type not in self.local_data:
            self.local_data[block_type] = BenchmarkBlock(block_type)

        return self.local_data[block_type]

    def local(
        self,
    ) -> BenchmarkBlock:
        """Measure local block."""
        return self._measure(BenchmarkBlockTypes.LOCAL)

    def consensus(
        self,
    ) -> BenchmarkBlock:
        """Measure consensus block."""
        return self._measure(BenchmarkBlockTypes.CONSENSUS)


class BenchmarkTool:
    """TimeStamp to measure performance."""

    benchmark_data: Dict[str, BenchmarkBehaviour]
    agent: Optional[str]
    agent_address: Optional[str]
    behaviours: List[str]

    def __init__(
        self,
    ) -> None:
        """Benchmark tool for rounds behaviours."""
        self.agent = None
        self.agent_address = None
        self.benchmark_data = {}
        self.behaviours = []

    @property
    def data(
        self,
    ) -> Dict:
        """Returns formatted data."""
        return {
            "agent_address": self.agent_address,
            "agent": self.agent,
            "data": [
                {
                    "behaviour": behaviour,
                    "data": dict(
                        [
                            (key, value.total_time)
                            for key, value in self.benchmark_data[
                                behaviour
                            ].local_data.items()
                        ]
                        + [
                            (
                                BenchmarkBlockTypes.TOTAL,
                                sum(
                                    [
                                        value.total_time
                                        for value in self.benchmark_data[
                                            behaviour
                                        ].local_data.values()
                                    ]
                                ),
                            )
                        ]
                    ),
                }
                for behaviour in self.behaviours
            ],
        }

    def log(
        self,
    ) -> None:
        """Output log."""

        logging.info(f"Agent : {self.agent}")
        logging.info(f"Agent Address : {self.agent_address}")

    def save(
        self,
    ) -> None:
        """Save logs to a file."""

        try:
            with open(
                f"/logs/{self.agent_address}.json", "w+", encoding="utf-8"
            ) as outfile:
                json.dump(self.data, outfile)
        except (PermissionError, FileNotFoundError):
            logging.info("Error saving benchmark data.")

    def measure(self, behaviour: BaseState) -> BenchmarkBehaviour:
        """Measure time to complete round."""

        if self.agent is None:
            self.agent_address = behaviour.context.agent_address
            self.agent = behaviour.context.agent_name

        if behaviour.state_id not in self.benchmark_data:
            self.benchmark_data[behaviour.state_id] = BenchmarkBehaviour(behaviour)

        if behaviour.state_id not in self.behaviours:
            self.behaviours.append(behaviour.state_id)

        return self.benchmark_data[behaviour.state_id]
