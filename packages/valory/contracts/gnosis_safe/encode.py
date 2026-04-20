# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023-2026 Valory AG
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

"""ETH encoder."""

import typing as t

from aea_ledger_ethereum import EthereumApi


def encode(ledger_api: EthereumApi, typ: t.Any, arg: t.Any) -> bytes:
    """Encode a single value of the given ABI type.

    web3 bundles ``eth_abi`` and exposes its default codec via
    ``ledger_api.api.codec``; reaching through to the codec's
    ``_registry`` gives us the same per-type encoder the contract
    used to import directly from ``eth_abi.default_codec._registry``,
    without adding ``eth-abi`` as a declared dep.
    """
    encoder = (
        ledger_api.api.codec._registry.get_encoder(  # pylint: disable=protected-access
            typ
        )
    )
    return encoder(arg)


def to_string(value: t.Union[bytes, str, int]) -> bytes:
    """Convert to byte string."""
    if isinstance(value, bytes):
        return value
    if isinstance(value, str):
        return bytes(value, "utf-8")
    if isinstance(value, int):
        return bytes(str(value), "utf-8")
    raise ValueError("Invalid data")


def sha3_256(ledger_api: EthereumApi, x: bytes) -> bytes:
    """Calculate keccak-256 hash (Ethereum's SHA3 variant)."""
    return ledger_api.api.keccak(x)


def sha3(ledger_api: EthereumApi, seed: t.Union[bytes, str, int]) -> bytes:
    """Calculate keccak-256 hash over *seed* (coerced to bytes)."""
    return sha3_256(ledger_api, to_string(seed))


def scan_bin(v: str) -> bytes:
    """Scan bytes."""
    if v[:2] in ("0x", b"0x"):
        return bytes.fromhex(v[2:])
    return bytes.fromhex(v)


def create_struct_definition(name: str, schema: t.List[t.Dict[str, str]]) -> str:
    """Create the struct definition string."""
    schema_types = [
        (schema_type["type"] + " " + schema_type["name"]) for schema_type in schema
    ]
    return name + "(" + ",".join(schema_types) + ")"


def find_dependencies(
    name: str, types: t.Dict[str, t.Any], dependencies: t.Set
) -> None:
    """Find dependencies."""
    if name in dependencies:
        return
    schema = types.get(name)
    if not schema:
        return
    dependencies.add(name)
    for schema_type in schema:
        find_dependencies(schema_type["type"], types, dependencies)


def create_schema(name: str, types: t.Dict) -> str:
    """Create schema."""
    array_start = name.find("[")
    clean_name = name if array_start < 0 else name[:array_start]
    dependencies: t.Set = set()
    find_dependencies(clean_name, types, dependencies)
    dependencies.discard(clean_name)
    dependency_definitions = [
        create_struct_definition(dependency, types[dependency])
        for dependency in sorted(dependencies)
        if types.get(dependency)
    ]
    return create_struct_definition(clean_name, types[clean_name]) + "".join(
        dependency_definitions
    )


def create_schema_hash(ledger_api: EthereumApi, name: str, types: t.Dict) -> bytes:
    """Create schema hash."""
    return encode(ledger_api, "bytes32", sha3(ledger_api, create_schema(name, types)))


def encode_value(
    ledger_api: EthereumApi, data_type: str, value: t.Any, types: t.Dict
) -> bytes:
    """Encode value."""
    if data_type == "string":
        return encode(ledger_api, "bytes32", sha3(ledger_api, value))
    if data_type == "bytes":
        return encode(ledger_api, "bytes32", sha3(ledger_api, scan_bin(value)))
    if types.get(data_type):
        return encode(
            ledger_api,
            "bytes32",
            sha3(ledger_api, encode_data(ledger_api, data_type, value, types)),
        )
    if data_type.endswith("]"):
        arrayType = data_type[: data_type.index("[")]
        return encode(
            ledger_api,
            "bytes32",
            sha3(
                ledger_api,
                b"".join(
                    [
                        encode_data(ledger_api, arrayType, arrayValue, types)
                        for arrayValue in value
                    ]
                ),
            ),
        )
    return encode(ledger_api, data_type, value)


def encode_data(
    ledger_api: EthereumApi,
    name: str,
    data: t.Dict[str, t.Dict[str, str]],
    types: t.Dict,
) -> bytes:
    """Encode data."""
    return create_schema_hash(ledger_api, name, types) + b"".join(
        [
            encode_value(
                ledger_api, schema_type["type"], data[schema_type["name"]], types
            )
            for schema_type in types[name]
        ]
    )


def create_struct_hash(
    ledger_api: EthereumApi,
    name: str,
    data: t.Dict[str, t.Dict[str, str]],
    types: t.Dict,
) -> bytes:
    """Create struct hash."""
    return sha3(ledger_api, encode_data(ledger_api, name, data, types))


def encode_typed_data(ledger_api: EthereumApi, data: t.Dict[str, t.Any]) -> bytes:
    """Encode typed data."""
    types = t.cast(t.Dict, data.get("types"))
    primary_type = t.cast(str, data.get("primaryType"))
    domain = t.cast(t.Dict[str, t.Dict[str, str]], data.get("domain"))
    message = t.cast(t.Dict[str, t.Any], data.get("message"))
    domain_hash = create_struct_hash(ledger_api, "EIP712Domain", domain, types)
    message_hash = create_struct_hash(ledger_api, primary_type, message, types)
    return sha3(
        ledger_api,
        bytes.fromhex("19") + bytes.fromhex("01") + domain_hash + message_hash,
    )
