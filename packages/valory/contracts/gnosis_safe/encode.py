# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023 Valory AG
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

from Crypto.Hash import keccak  # nosec
from eth_abi.abi import default_codec  # nosec
from eth_utils import decode_hex


def encode(typ: t.Any, arg: t.Any) -> bytes:
    """Encode by type."""
    encoder = default_codec._registry.get_encoder(  # pylint: disable=protected-access
        typ
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


def sha3_256(x: bytes) -> bytes:
    """Calculate SHA3-256 hash."""
    return keccak.new(digest_bits=256, data=x).digest()


def sha3(seed: t.Union[bytes, str, int]) -> bytes:
    """Calculate SHA3-256 hash."""
    return sha3_256(to_string(seed))


def scan_bin(v: str) -> bytes:
    """Scan bytes."""
    if v[:2] in ("0x", b"0x"):
        return decode_hex(v[2:])
    return decode_hex(v)


def create_struct_definition(name: str, schema: t.List[t.Dict[str, str]]) -> str:
    """Create method struction defintion."""
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


def create_schema_hash(name: str, types: t.Dict) -> bytes:
    """Create schema hash."""
    return encode("bytes32", sha3(create_schema(name, types)))


def encode_value(data_type: str, value: t.Any, types: t.Dict) -> bytes:
    """Encode value."""
    if data_type == "string":
        return encode("bytes32", sha3(value))
    if data_type == "bytes":
        return encode("bytes32", sha3(scan_bin(value)))
    if types.get(data_type):
        return encode("bytes32", sha3(encode_data(data_type, value, types)))
    if data_type.endswith("]"):
        arrayType = data_type[: data_type.index("[")]
        return encode(
            "bytes32",
            sha3(
                b"".join(
                    [encode_data(arrayType, arrayValue, types) for arrayValue in value]
                )
            ),
        )
    return encode(data_type, value)


def encode_data(name: str, data: t.Dict[str, t.Dict[str, str]], types: t.Dict) -> bytes:
    """Encode data."""
    return create_schema_hash(name, types) + b"".join(
        [
            encode_value(schema_type["type"], data[schema_type["name"]], types)
            for schema_type in types[name]
        ]
    )


def create_struct_hash(
    name: str, data: t.Dict[str, t.Dict[str, str]], types: t.Dict
) -> bytes:
    """Create struct hash."""
    return sha3(encode_data(name, data, types))


def encode_typed_data(data: t.Dict[str, t.Any]) -> bytes:
    """Encode typed data."""
    types = t.cast(t.Dict, data.get("types"))
    primary_type = t.cast(str, data.get("primaryType"))
    domain = t.cast(t.Dict[str, t.Dict[str, str]], data.get("domain"))
    message = t.cast(t.Dict[str, t.Any], data.get("message"))
    domain_hash = create_struct_hash("EIP712Domain", domain, types)
    message_hash = create_struct_hash(primary_type, message, types)
    return sha3(bytes.fromhex("19") + bytes.fromhex("01") + domain_hash + message_hash)
