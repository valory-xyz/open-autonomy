# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2026 Valory AG
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
# pylint: disable=protected-access

"""Unit tests for the EIP-712 encode helpers."""

from typing import Any, Dict
from unittest import mock

import pytest

from packages.valory.contracts.gnosis_safe.encode import (
    create_schema,
    create_schema_hash,
    create_struct_definition,
    create_struct_hash,
    encode,
    encode_data,
    encode_typed_data,
    encode_value,
    find_dependencies,
    scan_bin,
    sha3,
    sha3_256,
    to_string,
)


def _fake_ledger() -> mock.Mock:
    """Build a LedgerApi stub whose keccak and codec are deterministic fakes."""
    ledger = mock.Mock()
    ledger.api.keccak = lambda b: b"k:" + b
    ledger.api.codec._registry.get_encoder = lambda typ: (
        lambda v: f"{typ}:{v!r}".encode()
    )
    return ledger


def test_encode_forwards_to_codec_registry() -> None:
    """`encode` resolves an encoder from the codec registry and calls it."""
    ledger = _fake_ledger()
    assert encode(ledger, "uint256", 1) == b"uint256:1"


def test_to_string_bytes_passthrough() -> None:
    """`to_string` leaves a bytes input untouched."""
    assert to_string(b"abc") == b"abc"


def test_to_string_str_encodes_utf8() -> None:
    """`to_string` encodes a str input as UTF-8."""
    assert to_string("abc") == b"abc"


def test_to_string_int_encodes_as_decimal_digits() -> None:
    """`to_string` renders an int as its decimal UTF-8 string."""
    assert to_string(42) == b"42"


def test_to_string_rejects_unsupported_type() -> None:
    """`to_string` raises on unsupported types (mirrors original)."""
    with pytest.raises(ValueError, match="Invalid data"):
        to_string(1.5)  # type: ignore[arg-type]


def test_sha3_256_delegates_to_ledger_keccak() -> None:
    """`sha3_256` calls `ledger_api.api.keccak`."""
    ledger = _fake_ledger()
    assert sha3_256(ledger, b"x") == b"k:x"


def test_sha3_coerces_to_bytes_before_keccak() -> None:
    """`sha3` runs the seed through `to_string` before hashing."""
    ledger = _fake_ledger()
    assert sha3(ledger, "ab") == b"k:ab"
    assert sha3(ledger, 7) == b"k:7"


def test_scan_bin_handles_str_0x_prefix() -> None:
    """`scan_bin` strips a leading ``0x`` before hex decoding."""
    assert scan_bin("0xabcd") == b"\xab\xcd"


def test_scan_bin_handles_unprefixed_hex() -> None:
    """`scan_bin` accepts hex without a ``0x`` prefix."""
    assert scan_bin("abcd") == b"\xab\xcd"


def test_create_struct_definition_formats_fields() -> None:
    """`create_struct_definition` formats ``Name(type name,...)``."""
    out = create_struct_definition(
        "Mail", [{"type": "address", "name": "to"}, {"type": "string", "name": "msg"}]
    )
    assert out == "Mail(address to,string msg)"


def test_find_dependencies_returns_reachable_types() -> None:
    """`find_dependencies` adds every reachable named type."""
    types = {
        "Mail": [
            {"name": "to", "type": "Person"},
            {"name": "body", "type": "string"},
        ],
        "Person": [
            {"name": "wallet", "type": "address"},
            {"name": "name", "type": "string"},
        ],
    }
    deps: set = set()
    find_dependencies("Mail", types, deps)
    assert deps == {"Mail", "Person"}


def test_find_dependencies_stops_on_already_seen() -> None:
    """A type already in the set is not re-traversed (early return)."""
    deps = {"Mail"}
    # Passing a type already in `dependencies` early-returns immediately.
    find_dependencies("Mail", {"Mail": [{"name": "to", "type": "Person"}]}, deps)
    assert deps == {"Mail"}


def test_find_dependencies_stops_on_unknown_name() -> None:
    """Non-registered types short-circuit without adding to the set."""
    deps: set = set()
    find_dependencies("address", {}, deps)
    assert deps == set()


def test_create_schema_builds_sorted_definition() -> None:
    """`create_schema` joins the primary + sorted dependency definitions."""
    types = {
        "Mail": [
            {"name": "from", "type": "Person"},
            {"name": "to", "type": "Person"},
            {"name": "body", "type": "string"},
        ],
        "Person": [
            {"name": "wallet", "type": "address"},
            {"name": "name", "type": "string"},
        ],
    }
    schema = create_schema("Mail", types)
    assert schema.startswith("Mail(")
    assert "Person(address wallet,string name)" in schema


def test_create_schema_handles_array_type_names() -> None:
    """Array type names (``Foo[]``) are stripped before lookup."""
    types = {"Foo": [{"name": "x", "type": "uint256"}]}
    schema = create_schema("Foo[]", types)
    assert schema == "Foo(uint256 x)"


def test_create_schema_hash_composes_encode_and_sha3() -> None:
    """`create_schema_hash` returns ``encode("bytes32", keccak(schema))``."""
    ledger = _fake_ledger()
    out = create_schema_hash(ledger, "Foo", {"Foo": [{"name": "x", "type": "uint256"}]})
    assert out.startswith(b"bytes32:")
    assert b"k:Foo(uint256 x)" in out


def test_encode_value_string_branch() -> None:
    """A ``string`` field is hashed then encoded as ``bytes32``."""
    ledger = _fake_ledger()
    out = encode_value(ledger, "string", "hello", {})
    assert out.startswith(b"bytes32:")
    assert b"k:hello" in out


def test_encode_value_bytes_branch_goes_through_scan_bin() -> None:
    """A ``bytes`` field is hex-decoded via ``scan_bin`` before hashing."""
    ledger = _fake_ledger()
    out = encode_value(ledger, "bytes", "0xdeadbeef", {})
    assert out.startswith(b"bytes32:")
    assert b"k:" in out


def test_encode_value_struct_branch() -> None:
    """A custom struct type recurses through ``encode_data``."""
    ledger = _fake_ledger()
    types = {"Inner": [{"name": "v", "type": "uint256"}]}
    out = encode_value(ledger, "Inner", {"v": 7}, types)
    assert out.startswith(b"bytes32:")


def test_encode_value_array_branch() -> None:
    """A ``T[]`` field encodes each element then hashes the concatenation."""
    ledger = _fake_ledger()
    types = {"Inner": [{"name": "v", "type": "uint256"}]}
    out = encode_value(ledger, "Inner[]", [{"v": 1}, {"v": 2}], types)
    assert out.startswith(b"bytes32:")


def test_encode_value_primitive_fallback() -> None:
    """Primitive ABI types fall through to the default ``encode`` path."""
    ledger = _fake_ledger()
    assert encode_value(ledger, "uint256", 123, {}) == b"uint256:123"


def test_encode_data_concats_schema_hash_and_field_values() -> None:
    """Test that `encode_data` prefixes field encodings with the schema hash."""
    ledger = _fake_ledger()
    types = {"Foo": [{"name": "n", "type": "uint256"}]}
    data: Dict[str, Any] = {"n": 1}
    out = encode_data(ledger, "Foo", data, types)
    # schema hash prefix + field encoding
    assert out.startswith(b"bytes32:")


def test_create_struct_hash_runs_sha3_over_encode_data() -> None:
    """Test that `create_struct_hash` is `sha3(encode_data(...))`."""
    ledger = _fake_ledger()
    types = {"Foo": [{"name": "n", "type": "uint256"}]}
    data: Dict[str, Any] = {"n": 1}
    out = create_struct_hash(ledger, "Foo", data, types)
    assert out.startswith(b"k:")


def test_encode_typed_data_assembles_eip712_digest() -> None:
    """`encode_typed_data` returns ``sha3(0x19 01 || domainHash || messageHash)``."""
    ledger = _fake_ledger()
    data = {
        "types": {
            "EIP712Domain": [{"name": "n", "type": "string"}],
            "Mail": [{"name": "body", "type": "string"}],
        },
        "primaryType": "Mail",
        "domain": {"n": "app"},
        "message": {"body": "hi"},
    }
    out = encode_typed_data(ledger, data)
    # Outer wrapper is a single keccak call; the fake ledger prepends "k:".
    assert out.startswith(b"k:\x19\x01")
