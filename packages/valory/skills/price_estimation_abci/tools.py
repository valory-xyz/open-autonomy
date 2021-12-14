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
from typing import List, Tuple


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


def payload_to_hex(tx_hash: str, epoch_: int, round_: int, amount_: int) -> str:
    """Serialise to a hex string."""
    if len(tx_hash) != 64:  # should be exactly 32 bytes!
        raise ValueError("cannot encode tx_hash of non-32 bytes")  # pragma: nocover
    epoch_hex = epoch_.to_bytes(4, "big").hex()
    round_hex = round_.to_bytes(1, "big").hex()
    amount_hex = amount_.to_bytes(16, "big").hex()
    concatenated = tx_hash + epoch_hex + round_hex + amount_hex
    return concatenated


def hex_to_payload(payload: str) -> Tuple[str, int, int, int]:
    """Decode payload."""
    if len(payload) != 106:
        raise ValueError("cannot encode provided payload")  # pragma: nocover
    tx_hash = payload[:64]
    epoch_ = int.from_bytes(bytes.fromhex(payload[64:72]), "big")
    round_ = int.from_bytes(bytes.fromhex(payload[72:74]), "big")
    amount_ = int.from_bytes(bytes.fromhex(payload[74:]), "big")
    return (tx_hash, epoch_, round_, amount_)
