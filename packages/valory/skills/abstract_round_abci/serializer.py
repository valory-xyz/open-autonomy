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
"""
Serialize nested dictionaries to bytes using google.protobuf.Struct.

Prerequisites:
- All keys must be of type: str
- Values must be of type: bool, int, float, str, bytes, dict
- Strings must be unicode, as google.protobuf.Struct does not support bytes

The following encoding is required and performed,
and sentinel values are added for decoding:
- bytes to string
- integer to string
"""

import copy
from typing import Any, Dict, Tuple

from google.protobuf.struct_pb2 import Struct


ENCODING = "utf-8"


def to_bytes(data: Dict[str, Any]) -> bytes:
    """Serialize to bytes using protobuf. Adds extra data for type-casting."""

    pstruct = Struct()
    patched_data, patches = patch(copy.deepcopy(data))
    pstruct.update(  # pylint: disable=no-member
        {"data": patched_data, "patches": patches}
    )
    return pstruct.SerializeToString(deterministic=True)


def from_bytes(buffer: bytes) -> Dict[str, Any]:
    """Deserialize patched-up python dict from protobuf bytes."""

    pstruct = Struct()
    pstruct.ParseFromString(buffer)
    data = dict(pstruct)
    return unpatch(data["data"], data["patches"])


def patch(data: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Patch for protobuf serialization. In-place operation."""

    patches: Dict[str, Any] = {}
    for key, value in data.items():
        if isinstance(value, (bool, float, str, Struct)):
            pass
        elif isinstance(value, bytes):
            data[key], patches[key] = value.decode(ENCODING), "bytes"
        elif isinstance(value, int):
            data[key], patches[key] = str(value), "int"
        elif isinstance(value, dict):
            data[key], patches[key] = patch(value)
        else:
            raise NotImplementedError(f"Encoding of `{type(value)}` not supported")

    return data, patches


def unpatch(data: Dict[str, Any], patches: Dict[str, Any]) -> Dict[str, Any]:
    """Unpatch for protobuf deserialization. In-place operation."""

    for key, value in data.items():
        if isinstance(value, Struct):
            if value == Struct():
                data[key] = (
                    dict() if key in patches and patches[key] == "dict" else Struct()
                )
                continue
            data[key] = unpatch(dict(value), patches[key] if key in patches else {})
        elif key in patches:
            data[key] = int(value) if patches[key] == "int" else value.encode(ENCODING)
        elif isinstance(value, (bool, float, str, int)):
            continue
        else:  # pragma: nocover
            raise NotImplementedError(f"Encoding of `{type(value)}` not supported")

    return data


class DictProtobufStructSerializer:  # pylint: disable=too-few-public-methods
    """Class to keep backwards compatibility"""

    encode = to_bytes
    decode = from_bytes
