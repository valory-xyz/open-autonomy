# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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
from hashlib import sha256
from importlib.machinery import ModuleSpec
from time import time
from typing import Any, Dict, List, Optional, Tuple, Union, cast

from aea.skills.base import SkillContext
from eth_typing.bls import BLSPubkey, BLSSignature
from py_ecc.bls import G2Basic as bls  # type: ignore

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
    """
    Benchmark

    This class represents logic to measure the code block using a
    context manager.
    """

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
    """
    BenchmarkBehaviour

    This class represents logic to benchmark a single behaviour.
    """

    behaviour: BaseState
    local_data: Dict[str, BenchmarkBlock]

    def __init__(self, behaviour: BaseState) -> None:
        """
        Initialize Benchmark behaviour object.

        :param behaviour: behaviour that will be measured.
        """

        self.behaviour = behaviour
        self.local_data = {}

    def _measure(self, block_type: str) -> BenchmarkBlock:
        """
        Returns a BenchmarkBlock object.

        :param block_type: type of block (e.g. local, consensus, request)
        :return: BenchmarkBlock
        """

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
    """
    BenchmarkTool

    Tool to benchmark price estimation agents execution time with
    different contexts.
    """

    benchmark_data: Dict[str, BenchmarkBehaviour]
    logger: logging.Logger

    def __init__(
        self,
    ) -> None:
        """Benchmark tool for rounds behaviours."""
        self._context: Optional[SkillContext] = None
        self.benchmark_data = {}
        self.logger = logging.getLogger()

    @property
    def context(self) -> SkillContext:
        """Get skill context"""
        if not self._context:
            raise AttributeError("Benchmark has not measured any behaviour yet")
        return self._context

    @property
    def data(
        self,
    ) -> List:
        """Returns formatted data."""

        behavioural_data = []
        for behaviour, tool in self.benchmark_data.items():
            data = {k: v.total_time for k, v in tool.local_data.items()}
            data[BenchmarkBlockTypes.TOTAL] = sum(data.values())
            behavioural_data.append({"behaviour": behaviour, "data": data})

        return behavioural_data

    def save(
        self,
    ) -> None:
        """Save logs to a file."""

        agent_dir = self.context._get_agent_context().data_dir  # pylint: disable=W0212
        data_dir = os.path.join(agent_dir, "logs")
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)

        filepath = os.path.join(data_dir, "benchmark.json")
        try:
            with open(filepath, "w+", encoding="utf-8") as outfile:
                json.dump(self.data, outfile)
            self.logger.info(f"Agent data appended to:\n{filepath}")
        except PermissionError as e:
            self.logger.info(f"Error saving benchmark data:\n{e}")

    def measure(self, behaviour: BaseState) -> BenchmarkBehaviour:
        """Measure time to complete round."""

        if self._context is None:
            self._context = behaviour.context

        if behaviour.state_id not in self.benchmark_data:
            self.benchmark_data[behaviour.state_id] = BenchmarkBehaviour(behaviour)

        return self.benchmark_data[behaviour.state_id]


class VerifyDrand:  # pylint: disable=too-few-public-methods
    """
    Tool to verify Randomness retrieved from various external APIs.

    The ciphersuite used is BLS_SIG_BLS12381G2_XMD:SHA-256_SSWU_RO_NUL_

    https://drand.love/docs/specification/#cryptographic-specification
    https://github.com/ethereum/py_ecc
    """

    @classmethod
    def _int_to_bytes_big(cls, value: int) -> bytes:
        """Convert int to bytes."""
        return int.to_bytes(value, 8, byteorder="big", signed=False)

    @classmethod
    def _verify_randomness_hash(cls, randomness: bytes, signature: bytes) -> bool:
        """Verify randomness hash."""
        return sha256(signature).digest() == randomness

    @classmethod
    def _verify_signature(
        cls,
        pubkey: Union[BLSPubkey, bytes],
        message: bytes,
        signature: Union[BLSSignature, bytes],
    ) -> bool:
        """Verify randomness signature."""
        return bls.Verify(
            cast(BLSPubkey, pubkey), message, cast(BLSSignature, signature)
        )

    def verify(self, data: Dict, pubkey: str) -> Tuple[bool, Optional[str]]:
        """
        Verify drand value retried from external APIs.

        :param data: dictionary containing drand parameters.
        :param pubkey: league of entropy public key
                       https://drand.love/developer/http-api/#public-endpoints
        :returns: bool, error message
        """

        encoded_pubkey = bytes.fromhex(pubkey)
        try:
            randomness = data["randomness"]
            signature = data["signature"]
            round_value = int(data["round"])
        except KeyError as e:
            return False, f"DRAND dict is missing value for {e}"

        previous_signature = data.pop("previous_signature", "")
        encoded_randomness = bytes.fromhex(randomness)
        encoded_signature = bytes.fromhex(signature)
        int_encoded_round = self._int_to_bytes_big(round_value)
        encoded_previous_signature = bytes.fromhex(previous_signature)

        if not self._verify_randomness_hash(encoded_randomness, encoded_signature):
            return False, "Failed randomness hash check."

        msg_b = encoded_previous_signature + int_encoded_round
        msg_hash_b = sha256(msg_b).digest()

        if not self._verify_signature(encoded_pubkey, msg_hash_b, encoded_signature):
            return False, "Failed bls.Verify check."

        return True, None
