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
import statistics
from math import floor
from typing import List


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


def to_int(most_voted_estimate: float, decimals: int) -> int:
    """Convert to int."""
    most_voted_estimate_ = str(most_voted_estimate)
    decimal_places = most_voted_estimate_[::-1].find(".")
    if decimal_places > decimals:
        most_voted_estimate_ = most_voted_estimate_[: -(decimal_places - decimals)]
    most_voted_estimate = float(most_voted_estimate_)
    int_value = int(most_voted_estimate * (10 ** decimals))
    return int_value
