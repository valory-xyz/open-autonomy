# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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

"""Tests to ensure implementation is on par with ABCI spec"""
import builtins
import functools
import inspect
import logging
import typing
from enum import Enum
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, Iterable, Set, Tuple, Union, Type
from unittest import mock

import requests
import yaml
from google.protobuf.descriptor import FieldDescriptor
from google.protobuf import timestamp_pb2

from packages.valory.connections.abci.tendermint.types import params_pb2
from packages.valory.connections.abci.tendermint.types import types_pb2
from packages.valory.connections.abci.tendermint.crypto import keys_pb2
from packages.valory.connections.abci.tendermint.crypto import proof_pb2

from aea.protocols.generator.common import (
    SPECIFICATION_COMPOSITIONAL_TYPES,
    _get_sub_types_of_compositional_types,
    _to_camel_case,
    _camel_case_to_snake_case,
)

from packages.valory.skills.abstract_round_abci.dialogues import AbciDialogues
from packages.valory.connections.abci.protos.tendermint import abci as protos_abci
from packages.valory.connections.abci import tendermint
from packages.valory.connections.abci.tendermint.abci.types_pb2 import (
    Request,
    Response,
)
from packages.valory.protocols.abci import AbciMessage
from packages.valory import protocols
from packages.valory.connections.abci.connection import (
    _TendermintProtocolDecoder as Decoder,
    _TendermintProtocolEncoder as Encoder,
)

from packages.valory.protocols import abci as valory_abci_protocol


# constants & utility functions

ENCODING = "utf-8"
VERSION = "v0.34.11"
LOCAL_TYPES_FILE = Path(protos_abci.__path__[0]) / "types.proto"
URL = f"https://raw.githubusercontent.com/tendermint/tendermint/{VERSION}/proto/tendermint/abci/types.proto"
CLASS_ATTRS = ("oneofs", "enum_types", "fields")
DESCRIPTOR = tendermint.abci.types_pb2.DESCRIPTOR


def is_enum(dtype: Any) -> bool:
    return isinstance(dtype, type) and issubclass(dtype, Enum)


def my_repr(self) -> str:
    """Custom __repr__ for Tendermint protobuf objects, which lack it"""
    return f"<{self.__module__}.{type(self).__name__} object at {hex(id(self))}>"


def is_repeated(d_type: typing.Any) -> bool:
    return d_type.__class__.__module__ == "typing" and d_type.__origin__ is list


def get_aea_custom(module: ModuleType) -> Dict[str, Type]:
    """Test coverage"""

    def is_locally_defined_class(item: Any) -> bool:
        return isinstance(item, type) and item.__module__ == module.__name__

    return {k: v for k, v in vars(module).items() if is_locally_defined_class(v)}


def get_tendermint_classes(module: ModuleType) -> Dict[str, Type]:
    """Get Tendermint classes and set __repr__"""

    def set_repr(cls: Type) -> Type:
        cls.__repr__ = my_repr
        return cls

    return {k: set_repr(v) for k, v in vars(module).items() if isinstance(v, type)}


def get_tendermint_message_types() -> Dict[str, Any]:
    """Get Tendermint-native message type definitions"""

    messages: Dict[str, Any] = dict()
    for msg, msg_desc in DESCRIPTOR.message_types_by_name.items():
        content = messages.setdefault(msg, {})

        # Request & Response
        for oneof in msg_desc.oneofs:
            oneofs = content.setdefault("oneofs", {})
            fields = [(field.message_type.name, field.name, field.number) for field in oneof.fields]
            oneofs[oneof.name] = fields

        # ResponseOfferSnapshot & ResponseApplySnapshotChunk
        for enum_type in msg_desc.enum_types:
            enum = content.setdefault("enum_types", {})
            names, numbers = enum_type.values_by_name, enum_type.values_by_number
            enum[enum_type.name] = dict(zip(names, numbers))

        # other fields
        for field in msg_desc.fields:
            fields = content.setdefault("fields", {})
            name = field.message_type.name if field.message_type else type_mapping[field.type]
            item = [name, field.number]
            if isinstance(field.default_value, list):
                item.append("repeated")
            fields[field.name] = tuple(item)

    return messages


PYTHON_PRIMITIVES = (int, float, bool, str, bytes)
AEA_CUSTOM = get_aea_custom(protocols.abci.custom_types)
TENDERMINT_DEFS = get_tendermint_message_types()

TENDERMINT_ABCI_TYPES = get_tendermint_classes(tendermint.abci.types_pb2)
TENDERMINT_PARAMS = get_tendermint_classes(params_pb2)
TENDERMINT_KEYS = get_tendermint_classes(keys_pb2)
TENDERMINT_PROOF = get_tendermint_classes(proof_pb2)
TENDERMINT_TYPES_TYPES = get_tendermint_classes(types_pb2)
TENDERMINT_TIME_STAMP = timestamp_pb2.Timestamp

type_mapping = {
    v: k[5:].lower() for k, v in vars(FieldDescriptor).items() if k.startswith("TYPE_")
}

type_to_python = dict.fromkeys(type_mapping.values())
type_to_python.update(
    dict(
        double=float,
        float=float,
        int64=int,
        uint64=int,
        int32=int,
        bool=bool,
        string=str,
        bytes=bytes,
        uint32=int,
    )
)


camel_to_snake = _camel_case_to_snake_case
snake_to_camel = _to_camel_case


def get_aea_type(data_type: str) -> str:
    """Translate type to AEA-native ABCI format"""
    if data_type in type_to_python:
        if type_to_python[data_type] is None:
            raise NotImplementedError(f"type_to_python: {data_type}")
        return f"pt:{type_to_python[data_type].__name__}"
    return f"ct:{data_type}"


def venn_keys(a: Iterable, b: Iterable) -> Tuple[Set[Any], Set[Any], Set[Any]]:
    """split into: unique_to_a, common, unique_to_b"""
    set_a, set_b = set(a), set(b)
    return set_a - set_b, set_a & set_b, set_b - set_a


def nested_dict_to_text(dict_obj: Dict[str, Any], indent: int = 0) -> str:
    """Pretty Print nested dictionary with given indent level"""
    report: str = ""
    for key, value in dict_obj.items():
        if isinstance(value, dict):
            report += f"{' ' * indent}{key}: {{\n"
            report += nested_dict_to_text(value, indent + 4)
            report += f"{' ' * indent}}}\n"
        else:
            report += f"{' ' * indent}{key}: {value}\n"
    return report


@functools.lru_cache()
def get_protocol_readme_spec() -> Tuple[Any, Any, Any]:
    """Test specification used to generate protocol matches ABCI spec"""

    protocol_readme = Path(valory_abci_protocol.__path__[0]) / "README.md"  # type: ignore
    raw_chunks = open(protocol_readme).read().split("```")
    assert len(raw_chunks) == 3, "Expecting a single YAML code block"

    yaml_chunks = raw_chunks[1].strip("yaml").split("\n---")
    yaml_content = []
    for raw_doc in filter(None, yaml_chunks):
        try:
            yaml_content.append(yaml.safe_load(raw_doc))
        except yaml.YAMLError as e:
            raise e

    protocol, custom, dialogues = yaml_content
    assert protocol["name"] == "abci"  # sanity check
    return protocol, custom, dialogues


# 1. Create tree type for the AEA-native ABCI protocol
def _create_custom_type_tree(custom_type) -> Tuple[Type, Dict[str, Any]]:
    """Create custom type branch for AEA-native ABCI spec"""

    kwarg_types = {}
    parameters = inspect.signature(custom_type).parameters
    for name, parameter in parameters.items():
        d_type = parameter.annotation
        if d_type in PYTHON_PRIMITIVES:
            kwarg_types[name] = d_type
        elif is_enum(d_type):
            kwarg_types[name] = d_type
        elif is_repeated(d_type):
            container, content = d_type.__origin__, d_type.__args__[0]
            if content in AEA_CUSTOM.values():
                content = _create_custom_type_tree(content)
            kwarg_types[name] = container, content
        else:
            nested_type = AEA_CUSTOM.get(d_type, d_type)
            kwarg_types[name] = _create_custom_type_tree(nested_type)

    return custom_type, kwarg_types


def _create_type_tree(field: str) -> Any:
    """Create type branch for AEA-native ABCI spec"""

    if any(map(field.startswith, SPECIFICATION_COMPOSITIONAL_TYPES)):
        subfields = _get_sub_types_of_compositional_types(field)
        if field.startswith("pt:optional"):
            return _create_type_tree(subfields[0])
        elif field.startswith("pt:list"):  # repeated
            return list, _create_type_tree(*subfields)
        else:
            raise NotImplementedError(f"field: {field}")

    if field.startswith("ct:"):
        custom_type = AEA_CUSTOM[field[3:]]
        return _create_custom_type_tree(custom_type)

    primitive = getattr(builtins, field[3:])
    return primitive


def _get_message_types(name: str, fields: Dict[str, Any]) -> Tuple:
    """Create message types for AEA-native ABCI spec"""
    performative = getattr(AbciMessage.Performative, name.upper())
    kwargs = {k: _create_type_tree(v) for k, v in fields.items()}
    return performative, kwargs


def create_abci_type_tree(speech_acts: Dict[str, Any]) -> Dict[str, Any]:
    """Create ABCI type tree for AEA-native ABCI spec"""
    return {k: _get_message_types(k, v) for k, v in speech_acts.items()}


# 2. Initialize AEA-native ABCI protocol messages
def _init_subtree(node: Dict[str, Any]) -> Dict[str, Any]:
    """Initialize subtree of type_tree"""

    def init_repeated(repeated_type: Any) -> Tuple[Any]:
        if repeated_type in PYTHON_PRIMITIVES:
            repeated = tuple(repeated_type() for _ in range(1))
        elif isinstance(repeated_type, tuple):
            cls, cls_kwargs = repeated_type
            repeated = tuple(cls(**_init_subtree(cls_kwargs)) for _ in range(1))
        else:
            raise NotImplementedError(f"Repeated in {name}: {repeated_type}")
        return repeated

    kwargs = {}
    for name, d_type in node.items():
        if isinstance(d_type, tuple):
            container, content = d_type
            if container is list:
                kwargs[name] = init_repeated(content)
            else:
                kwargs[name] = container(**_init_subtree(content))
        elif d_type in PYTHON_PRIMITIVES:
            kwargs[name] = d_type()
        elif is_enum(d_type):
            kwargs[name] = list(d_type)[0]
        else:
            raise NotImplementedError(f"{name}: {d_type}")

    return kwargs


def init_abci_messages(type_tree):
    """Initialize ABCI messages"""
    return {k: AbciMessage(p, **_init_subtree(root)) for k, (p, root) in type_tree.items()}


# 3. Translate AEA-native to Tendermint-native
def encode(abci_messages: Dict[str, AbciMessage]):
    """Encode AEA-native protocol messages to Tendermint-native"""

    tendermint_messages = dict.fromkeys(abci_messages)
    for key, message in abci_messages.items():
        try:
            tendermint_messages[key] = Encoder.process(message)
        except Exception as e:
            print(key, message)
            print(e)
    return tendermint_messages


# 4. Check Tendermint-native ABCI messages
def _verify(subtype) -> True:
    """Verify Tendermint-native ABCI message"""

    name = subtype.__class__.__name__
    cls_attrs = (TENDERMINT_DEFS[name].get(x, {}) for x in CLASS_ATTRS)
    oneofs, enum_types, fields = cls_attrs
    for field, (d_type, idx, *repeated) in fields.items():
        data = getattr(subtype, field)
        if d_type == "enum":
            enum_type = enum_types[snake_to_camel(field)]
            assert data in enum_type.values()
        elif d_type in type_to_python:
            x = type_to_python[d_type]()
            x = [x] if repeated else x
            assert data == x
        elif d_type in TENDERMINT_ABCI_TYPES:
            _verify(TENDERMINT_ABCI_TYPES[d_type])
        else:
            raise NotImplementedError(f"{name}: {d_type}")
    return True


def verify_tendermint_message(message: Union[Request, Response]):
    """Verify Tendermint-native ABCI message"""

    assert message.IsInitialized()
    assert not message.UnknownFields()
    assert not message.FindInitializationErrors()
    descr, subtype = message.ListFields()[0]
    try:
        return _verify(subtype)
    except Exception:
        return False


# tests
def test_local_types_file_matches_github() -> None:
    """Test local file containing ABCI spec matches Tendermint GitHub"""

    response = requests.get(URL)
    if response.status_code != 200:
        log_msg = "Failed to retrieve Tendermint abci types from Github: "
        status_code, reason = response.status_code, response.reason
        raise requests.HTTPError(f"{log_msg}: {status_code} ({reason})")
    github_data = response.text
    local_data = LOCAL_TYPES_FILE.read_text(encoding=ENCODING)
    assert github_data == local_data


def test_speech_act_matches_abci_spec() -> None:
    """Test speech act definitions"""

    def get_unique(a: Dict[str, str], b: Dict[str, str]) -> Tuple[Dict[str, str]]:
        set_a, set_b = set(a.items()), set(b.items())
        return dict(set_a - set_b), dict(set_b - set_a)  # type: ignore

    differences = dict()
    aea_protocol, *_ = get_protocol_readme_spec()
    message_types = get_tendermint_message_types()
    speech_acts = aea_protocol["speech_acts"]

    request_oneof = message_types["Request"]['oneofs']["value"]
    for key, *_ in request_oneof:
        data = message_types[key].items()
        expected = {k: get_aea_type(v[0]) for k, v in data}
        defined = speech_acts[camel_to_snake(key)]
        if expected != defined:
            differences[key] = get_unique(expected, defined)

    if differences:
        log_msg = "Defined speech act not matching"
        template = "message: {k}\n\texpected:\t{v[0]}\n\tdefined:\t{v[1]}"
        lines = (template.format(k=k, v=v) for k, v in differences.items())
        logging.error(f"{log_msg}\n" + "\n".join(lines))
    assert not bool(differences)


def test_defined_dialogues_match_abci_spec() -> None:
    """
    Test defined dialogues match ABCI spec.

    It verifies solely that request response pairs match:
      - AEA requests match Tendermint requests
      - AEA responses match Tendermint responses
      - That all requests have a matching response
      - That all request, response and the exception are covered
    """

    *_, dialogues = get_protocol_readme_spec()
    message_types = get_tendermint_message_types()

    # expected
    request_oneof = message_types["Request"]["oneofs"]["value"]
    request_keys = {camel_to_snake(key) for key, *_ in request_oneof}
    response_oneof = message_types["Response"]["oneofs"]["value"]
    response_keys = {camel_to_snake(key) for key, *_ in response_oneof}

    # defined
    initiation = dialogues["initiation"]
    reply = dialogues["reply"]
    termination = dialogues["termination"]

    # initiation
    assert not request_keys.difference(initiation)
    assert set(initiation).difference(request_keys) == {"dummy"}

    # reply
    missing_response, alt = set(), "response_exception"
    for key in request_keys:
        if not set(reply[key]) == {key.replace("request", "response"), alt}:
            missing_response.add(key)
    assert not missing_response
    assert not any(reply[key] for key in response_keys)

    # termination
    assert not response_keys.difference(termination)
    assert set(termination).difference(response_keys) == {"dummy"}


def test_aea_to_tendermint() -> None:
    """Test translation from AEA-native to Tendermint-native ABCI protocol"""

    aea_protocol, *_ = get_protocol_readme_spec()
    speech_acts = aea_protocol["speech_acts"]
    # 1. create type tree
    type_tree = create_abci_type_tree(speech_acts)
    type_tree.pop("dummy")  # TODO: known oddity on our side
    # 2. create AEA-native ABCI protocol
    abci_messages = init_abci_messages(type_tree)
    # 3. encode to Tendermint-native ABCI protocol
    encoded = encode(abci_messages)
    # 4. verify content
    for key, message in encoded.items():
        if not message:  # request not implemented in encoder
            continue
        verify_tendermint_message(message)
