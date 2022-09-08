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
"""Test the serializer.py module of the skill."""

# pylint: skip-file

import math
import shutil
import sys
from collections import defaultdict
from contextlib import suppress
from pathlib import Path
from typing import Any, Dict, Generator

import hypothesis.strategies as st
import pytest
from google.protobuf.struct_pb2 import Struct
from hypothesis import given

from packages.valory.skills.abstract_round_abci import serializer
from packages.valory.skills.abstract_round_abci.serializer import (
    DictProtobufStructSerializer,
)


try:
    import atheris  # type: ignore
except (ImportError, ModuleNotFoundError):
    pytestmark = pytest.mark.skip


PACKAGE_DIR = Path(__file__).parent.parent


@pytest.fixture(scope="session", autouse=True)
def hypothesis_cleanup() -> Generator:
    """Fixture to remove hypothesis directory after tests."""
    yield
    hypothesis_dir = PACKAGE_DIR / ".hypothesis"
    if hypothesis_dir.exists():
        with suppress(OSError, PermissionError):
            shutil.rmtree(hypothesis_dir)


def test_encode_decode_i() -> None:
    """Test encode decode logic."""
    case = {
        "key1": True,
        "key2": 0.12,
        "key3": 100,
        "key4": "some string",
        "key5": b"some bytes string",
        "key6": Struct(),
        "_need_patch": {},
    }
    encoded = DictProtobufStructSerializer.encode(case)
    assert isinstance(encoded, bytes)
    decoded = DictProtobufStructSerializer.decode(encoded)
    assert case == decoded


def test_encode_decode_ii() -> None:
    """Test encode decode logic."""
    case = {
        "key1": True,
        "key2": 0.12,
        "key3": 100,
        "key4": "some string",
        "key5": b"some bytes string",
        "key6": {"key1": True, "key2": 0.12},
    }
    encoded = DictProtobufStructSerializer.encode(case)
    assert isinstance(encoded, bytes)
    decoded = DictProtobufStructSerializer.decode(encoded)
    assert case == decoded


# utility functions
def node() -> defaultdict:
    """Recursive defaultdict"""
    return defaultdict(node)


def to_dict(dd: Dict[str, Any]) -> Dict[str, Any]:
    """Recursive defaultdict to dict"""
    return {k: to_dict(v) for k, v in dd.items()} if isinstance(dd, defaultdict) else dd


def types_of(d: Dict[str, Any]) -> Dict[str, Any]:
    """Get `key: type(value)` mapping, recursively."""
    return {k: types_of(v) if isinstance(v, dict) else type(v) for k, v in d.items()}


def is_decodable(b: bytes) -> bool:
    """Check if bytes can be decoded"""
    try:
        b.decode(serializer.ENCODING)
        return True
    except UnicodeDecodeError:
        return False


def is_serializer_compatible(data: Dict) -> bool:
    """Check whether the serializer can reconstitute the data"""
    serialized = serializer.to_bytes(data)
    assert isinstance(serialized, bytes)
    deserialized = serializer.from_bytes(serialized)
    return data == deserialized and types_of(data) == types_of(deserialized)


# tests
@pytest.mark.parametrize(
    "unsupported_type",
    [bool, int, float, tuple, frozenset],
)
def test_unsupported_key_types(unsupported_type: Any) -> None:
    """Python accepted key-types not compatible with protobuf"""
    data = {unsupported_type(): "value"}
    with pytest.raises(Exception):
        serializer.to_bytes(data)


@pytest.mark.parametrize(
    "unsupported_type",
    [tuple, list, set, frozenset],
)
def test_unsupported_value_type(unsupported_type: Any) -> None:
    """Not implemented."""
    data = {"key": unsupported_type()}
    with pytest.raises(NotImplementedError):
        serializer.to_bytes(data)


@pytest.mark.parametrize(
    "value",
    [True, 1 << 256, 3.14, "string", b"bytes", {}],
)
def test_single_values(value: Any) -> None:
    """Single value type test"""
    assert is_serializer_compatible({"key": value})


def test_nested_mapping() -> None:
    """Nested mapping test"""
    root = node()
    root["a"]["0"] = {}
    root["a"]["1"] = False
    root["a"]["2"] = -(1 << 256)
    root["a"]["3"]["i"] = -3.141592653589793
    root["a"]["3"]["ii"] = b"bytes"
    root["a"]["3"]["iii"] = "string"
    assert is_serializer_compatible(to_dict(root))


# randomized hypothesis testing
value_strategy = st.one_of(
    st.booleans(),
    st.integers(),
    st.floats(allow_nan=False),  # because `nan != nan`
    st.text(),
    st.binary().filter(is_decodable),
)


@given(st.builds(zip, st.lists(st.text(), unique=True), st.lists(value_strategy)))
def test_randomized_mapping(zipper: Any) -> None:
    """Test randomized mappings"""
    assert is_serializer_compatible(dict(zipper))


@given(st.recursive(value_strategy, lambda trees: st.dictionaries(st.text(), trees)))
def test_randomized_nested_mapping(data: Any) -> None:
    """Test randomized nested mappings"""
    assert is_serializer_compatible({"key": data})


def test_encode_nan() -> None:
    """Test encode Nan."""
    case = {
        "key": float("nan"),
    }
    serialized = serializer.DictProtobufStructSerializer.encode(case)
    deserialized = serializer.DictProtobufStructSerializer.decode(serialized)
    assert math.isnan(deserialized["key"])


@pytest.mark.skip
def test_fuzz_encode() -> None:
    """Fuzz test for serializer. Run directly as a function, not through pytest"""

    @atheris.instrument_func
    def test_encode(input_bytes: bytes) -> None:
        """Test encode decode logic."""
        fdp = atheris.FuzzedDataProvider(input_bytes)
        case = {
            "key1": fdp.ConsumeBool(),
            "key2": fdp.ConsumeFloat(),
            "key3": fdp.ConsumeInt(4),
            "key4": fdp.ConsumeString(12),
            "key5": fdp.ConsumeBytes(12),
            "key6": Struct(),
            "_need_patch": {},
        }
        serializer.to_bytes(case)

    atheris.instrument_all()
    atheris.Setup(sys.argv, test_encode)
    atheris.Fuzz()


def test_encode_non_unicode_raises() -> None:
    """Test encode non unicode."""
    case = {
        "key": b"\xb2\xda\xda\x1a",
    }
    with pytest.raises(UnicodeDecodeError):
        serializer.DictProtobufStructSerializer.encode(case)


def test_sentinel_raises() -> None:
    """Test SENTINEL."""
    case = {
        "SENTINEL": 1,
    }
    with pytest.raises(ValueError):
        serializer.to_bytes(case)
