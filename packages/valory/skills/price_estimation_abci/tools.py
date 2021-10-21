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

"""This module contains the model to aggregate the price observations deterministically."""
import json
import statistics
from math import floor
from time import time
from typing import Dict, List, Optional, Tuple

from packages.valory.skills.abstract_round_abci.behaviours import AbstractRoundBehaviour


def aggregate(*observations: float) -> float:
    """Aggregate a list of observations."""
    return statistics.mean(observations)


def random_selection(elements: List[str], randomness: float) -> str:
    """
    Select a random element from a list.

    :param: elements: a list of elements to choose among
    :param: randomness: a random number in the [0,1) interval
    :return: a randomly chosen element
    """
    random_position = floor(randomness * len(elements))
    return elements[random_position]


class Benchmark:
    """Benchmark"""

    tick: float
    behaviour: AbstractRoundBehaviour
    consensus_time: List[Tuple[str, float]]

    def __init__(
        self, behaviour: AbstractRoundBehaviour, consensus_time: List[Tuple[str, float]]
    ) -> None:
        """Benchmark for single round."""
        self.behaviour = behaviour
        self.consensus_time = consensus_time

    def __enter__(
        self,
    ) -> None:
        """Enter context."""
        self.tick = time()

    def __exit__(self, *args: List, **kwargs: Dict) -> None:
        """Exit context"""

        total_time = time() - self.tick
        self.consensus_time.append((self.behaviour.matching_round.round_id, total_time))


class BenchmarkRound:
    """TimeStamp to measure performance."""

    consensus_time: List[Tuple[str, float]]
    agent: Optional[str]
    agent_address: Optional[str]

    def __init__(
        self,
    ) -> None:
        """Benchmark tool for rounds behaviours."""
        self.agent = None
        self.agent_address = None
        self.consensus_time = []

    def log(
        self,
    ) -> None:
        """Output log."""

        print(f"Agent : {self.agent}")
        print(f"Agent Address : {self.agent_address}")

        max_length = len(max(self.consensus_time, key=lambda x: len(x[0]))[0]) + 4

        print(f"\nRound{' '*(max_length-5)}Time\n{'='*(max_length+20)}")
        for round_name, total_time in self.consensus_time:
            print(f"{round_name}{' '*(max_length-len(round_name))}{total_time}")

    def save(
        self,
    ) -> None:
        """Save logs to a file."""
        with open(
            f"/logs/{self.agent_address}.json", "w+", encoding="utf-8"
        ) as outfile:
            json.dump(
                {
                    "agent_address": self.agent_address,
                    "agent": self.agent,
                    "logs": self.consensus_time,
                },
                outfile,
            )

    def measure(self, behaviour: AbstractRoundBehaviour) -> Benchmark:
        """Measure time to complete round."""

        if self.agent is None:
            self.agent_address = behaviour.context.agent_address
            self.agent = behaviour.context.agent_name

        return Benchmark(behaviour, self.consensus_time)
