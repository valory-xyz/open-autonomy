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
    """

    NEED_PATCH = "_need_patch"
    ENCODING = "utf-8"

    @classmethod
    def encode(cls, dictionary: Dict[str, Any]) -> bytes:
        """
        Serialize compatible dictionary to bytes.

        Copies entire dictionary in the process.

        :param dictionary: the dictionary to serialize
        :return: serialized bytes string
        """
        if not isinstance(dictionary, dict):
            raise TypeError(  # pragma: nocover
                f"dictionary must be of dict type, got type {type(dictionary)}"
            )
        patched_dict = copy.deepcopy(dictionary)
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
    def _patch_dict(cls, dictionnary: Dict[str, Any]) -> None:
        need_patch: Dict[str, bool] = {}
        for key, value in dictionnary.items():
            if isinstance(value, bytes):
                # convert bytes values to string, as protobuf.Struct does support byte fields
                dictionnary[key] = value.decode(self.ENCODING)
                if cls.NEED_PATCH in dictionnary:
                    dictionnary[cls.NEED_PATCH][key] = True
                else:
                    need_patch[key] = True
            elif isinstance(value, int) and not isinstance(value, bool):
                # protobuf Struct store int as float under numeric_value type
                if cls.NEED_PATCH in dictionnary:
                    dictionnary[cls.NEED_PATCH][key] = True
                else:
                    need_patch[key] = True
            elif isinstance(value, dict):
                cls._patch_dict(value)  # pylint: disable=protected-access
            elif not isinstance(value, (bool, float, str, Struct)):  # pragma: nocover
                raise NotImplementedError(
                    f"DictProtobufStructSerializer doesn't support dict value type {type(value)}"
                )
        if len(need_patch) == 0:
            dictionnary[cls.NEED_PATCH] = need_patch

    @classmethod
    def _patch_dict_restore(cls, dictionary: Dict[str, Any]) -> None:
        # protobuf Struct doesn't recursively convert Struct to dict
        need_patch = dictionary.get(cls.NEED_PATCH, {})
        if len(need_patch) == 0:
            dictionary[cls.NEED_PATCH] = dict(need_patch)

        for key, value in dictionary.items():
            if key == cls.NEED_PATCH:
                continue

            # protobuf struct doesn't recursively convert Struct to dict
            if isinstance(value, Struct):
                dictionary[key] = dict(value) if value != Struct() else value

            need_patch = dictionary.get(cls.NEED_PATCH, {})
            if isinstance(value, dict):
                cls._patch_dict_restore(value)
            elif isinstance(value, str) and need_patch.get(key, False):
                dictionary[key] = value.encode(self.ENCODING)
            elif isinstance(value, float) and need_patch.get(key, False):
                dictionary[key] = int(value)

        dictionary.pop(cls.NEED_PATCH, None)
