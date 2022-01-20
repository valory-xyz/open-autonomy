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
"""This module contains Serializers that can be used for custom types."""

import copy
from typing import Any, Dict

from google.protobuf.struct_pb2 import Struct


class DictProtobufStructSerializer:
    """Serialize python dictionaries

    Serialize python dictionaries of type DictType = Dict[str, ValueType]
    recursively conserving their dynamic type, using google.protobuf.Struct

    ValueType = PrimitiveType | DictType | List[ValueType]
    PrimitiveType = bool | int | float | str | bytes

    The following encoding is required and performed,
    and sentinel values are added for decoding:
     - bytes to string
     - integer to float
    """

    NEED_PATCH = "_need_patch"  # sentinel value
    ENCODING = "utf-8"

    @classmethod
    def encode(cls, data: Dict[str, Any]) -> bytes:
        """
        Serialize compatible dictionary to bytes.

        Copies entire dictionary in the process.

        :param data: the dictionary to serialize
        :return: serialized bytes string
        """
        if not isinstance(data, dict):
            raise TypeError(f"Only encode dict (not {type(data)})")  # pragma: nocover
        patched_dict = copy.deepcopy(data)
        cls._patch_dict(patched_dict)
        pstruct = Struct()
        pstruct.update(patched_dict)  # pylint: disable=no-member
        return pstruct.SerializeToString(deterministic=True)

    @classmethod
    def decode(cls, buffer: bytes) -> Dict[str, Any]:
        """Deserialize a compatible dictionary"""
        pstruct = Struct()
        pstruct.ParseFromString(buffer)
        dictionary = dict(pstruct)
        cls._patch_dict_restore(dictionary)
        return dictionary

    @classmethod
    def _patch_dict(cls, data: Dict[str, Any]) -> None:
        # Struct stores int as float under numeric_value type
        needs_patching: Dict[str, bool] = {}
        for key, value in data.items():
            if isinstance(value, (bool, float, str, Struct)):
                # what use case possibly requires Struct to be accepted here?
                continue  # these cases protobuf can deal with

            if isinstance(value, dict):
                cls._patch_dict(value)  # pylint: disable=protected-access
            elif isinstance(value, bytes):
                data[key] = value.decode(cls.ENCODING)
                needs_patching[key] = True
            elif isinstance(value, int):
                data[key] = float(value)
                needs_patching[key] = True
            else:  # pragma: nocover
                raise TypeError(f"Encoding of {type(data)} not supported")

        if len(needs_patching) > 0:
            data[cls.NEED_PATCH] = needs_patching

    @classmethod
    def _patch_dict_restore(cls, data: Dict[str, Any]) -> None:
        # protobuf Struct doesn't recursively convert Struct to dict
        needs_patching = dict(data.pop(cls.NEED_PATCH, Struct()))
        for key, value in data.items():
            if isinstance(value, Struct):
                # why should we not convert an empty Struct?
                data[key] = dict(value) if value != Struct() else value
                cls._patch_dict_restore(dict(value))
            elif isinstance(value, str) and needs_patching.pop(key, False):
                data[key] = value.encode(cls.ENCODING)
            elif isinstance(value, float) and needs_patching.pop(key, False):
                data[key] = int(value)
            elif isinstance(value, (bool, float, str, int)):
                continue  # values that don't need patching
            else:  # pragma: nocover
                raise TypeError(f"Encoding of {type(value)} not supported")
