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
from enum import Enum
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, Set, Tuple, Type, Union
from unittest import mock

import requests
import yaml
from aea.protocols.generator.common import (
    SPECIFICATION_COMPOSITIONAL_TYPES,
    _camel_case_to_snake_case,
    _get_sub_types_of_compositional_types,
    _to_camel_case,
)
from google.protobuf import timestamp_pb2
from google.protobuf.descriptor import FieldDescriptor

from packages.valory import protocols
from packages.valory.connections import abci as tendermint_abci
from packages.valory.connections.abci import tendermint
from packages.valory.connections.abci.connection import (
    _TendermintProtocolDecoder as Decoder,
)
from packages.valory.connections.abci.connection import (
    _TendermintProtocolEncoder as Encoder,
)
from packages.valory.connections.abci.tendermint.abci.types_pb2 import (  # type: ignore
    Request,
    Response,
)
from packages.valory.connections.abci.tendermint.crypto import (  # type: ignore
    keys_pb2,
    proof_pb2,
)
from packages.valory.connections.abci.tendermint.types import (  # type: ignore
    params_pb2,
    types_pb2,
)
from packages.valory.protocols import abci as valory_abci_protocol
from packages.valory.protocols.abci import AbciMessage
from packages.valory.skills.abstract_round_abci.dialogues import AbciDialogues


Node = Dict[str, Any]

# constants & utility functions
ENCODING = "utf-8"
VERSION = "v0.34.11"
REPO_PATH = Path(*tendermint_abci.__package__.split(".")).absolute()
LOCAL_TYPES_FILE = REPO_PATH / "protos" / "tendermint" / "abci" / "types.proto"
URL = f"https://raw.githubusercontent.com/tendermint/tendermint/{VERSION}/proto/tendermint/abci/types.proto"
DESCRIPTOR = tendermint.abci.types_pb2.DESCRIPTOR

# to ensure primitives are not initialized to empty default values
NON_DEFAULT_PRIMITIVES = {str: "sss", bytes: b"bbb", int: 123, float: 3.14, bool: True}
REPEATED_FIELD_SIZE = 3
USE_NON_ZERO_ENUM: bool = True


class EncodingError(Exception):
    """EncodingError AEA- to Tendermint-native ABCI message"""


class DecodingError(Exception):
    """DecodingError Tendermint- to AEA-native ABCI message"""


def is_enum(d_type: Any) -> bool:
    """Check if a type is an Enum."""
    return isinstance(d_type, type) and issubclass(d_type, Enum)


def my_repr(self: Any) -> str:
    """Custom __repr__ for Tendermint protobuf objects, which lack it."""
    return f"<{self.__module__}.{type(self).__name__} object at {hex(id(self))}>"


def is_repeated(d_type: Any) -> bool:
    """Check if field is repeated."""
    return d_type.__class__.__module__ == "typing" and d_type.__origin__ is list


def replace_keys(node: Node, trans: Node) -> None:
    """Replace keys in-place"""
    for k, v in trans.items():
        if isinstance(v, dict):
            replace_keys(node[k], v)
        else:
            node[v] = node.pop(k)


def get_aea_classes(module: ModuleType) -> Dict[str, Type]:
    """Get AEA custom classes."""

    def is_locally_defined_class(item: Any) -> bool:
        return isinstance(item, type) and item.__module__ == module.__name__

    return {k: v for k, v in vars(module).items() if is_locally_defined_class(v)}


def get_tendermint_classes(module: ModuleType) -> Dict[str, Type]:
    """Get Tendermint classes and set __repr__"""

    def set_repr(cls: Type) -> Type:
        cls.__repr__ = my_repr  # type: ignore
        return cls

    return {k: set_repr(v) for k, v in vars(module).items() if isinstance(v, type)}


def get_tendermint_message_types() -> Dict[str, Any]:
    """Get Tendermint-native message type definitions"""

    messages: Dict[str, Any] = dict()
    for msg, msg_desc in DESCRIPTOR.message_types_by_name.items():
        content = messages.setdefault(msg, {})

        # Request & Response
        for oneof in msg_desc.oneofs:
            fields = content.setdefault("oneofs", {}).setdefault(oneof.name, [])
            for field in oneof.fields:
                fields.append((field.message_type.name, field.name, field.number))

        # ResponseOfferSnapshot & ResponseApplySnapshotChunk
        for enum_type in msg_desc.enum_types:
            enum = content.setdefault("enum_types", {})
            names, numbers = enum_type.values_by_name, enum_type.values_by_number
            enum[enum_type.name] = dict(zip(names, numbers))

        # other fields
        for field in msg_desc.fields:
            fields = content.setdefault("fields", {})
            if field.message_type:
                name = field.message_type.name
            else:
                name = type_mapping[field.type]
            item = [name, field.number]
            if isinstance(field.default_value, list):
                item.append("repeated")
            fields[field.name] = tuple(item)

    return messages


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


PYTHON_PRIMITIVES = (int, float, bool, str, bytes)
AEA_CUSTOM = get_aea_classes(protocols.abci.custom_types)
TENDERMINT_DEFS = get_tendermint_message_types()

TENDERMINT_ABCI_TYPES = get_tendermint_classes(tendermint.abci.types_pb2)
TENDERMINT_PARAMS = get_tendermint_classes(params_pb2)
TENDERMINT_KEYS = get_tendermint_classes(keys_pb2)
TENDERMINT_PROOF = get_tendermint_classes(proof_pb2)
TENDERMINT_TYPES_TYPES = get_tendermint_classes(types_pb2)
TENDERMINT_TIME_STAMP = timestamp_pb2.Timestamp


def get_aea_type(data_type: str) -> str:
    """Translate type to AEA-native ABCI format"""
    if data_type in type_to_python:
        if type_to_python[data_type] is None:
            raise NotImplementedError(f"type_to_python: {data_type}")
        return f"pt:{type_to_python[data_type].__name__}"
    return f"ct:{data_type}"


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


# 1. Create type tree for the AEA-native ABCI protocol
def _create_custom_type_tree(custom_type: Type) -> Tuple[Type, Node]:
    """Create custom type tree for AEA-native ABCI spec"""

    kwarg_types = {}
    parameters = inspect.signature(custom_type).parameters
    for name, parameter in parameters.items():
        d_type = parameter.annotation
        if d_type in PYTHON_PRIMITIVES:
            kwarg_types[name] = d_type
        elif is_enum(d_type):
            kwarg_types[name] = d_type
        elif is_repeated(d_type):
            assert len(d_type.__args__) == 1  # check assumption
            container, content = d_type.__origin__, d_type.__args__[0]
            if content in AEA_CUSTOM.values():
                content = _create_custom_type_tree(content)
            kwarg_types[name] = container, content
        else:
            nested_type = AEA_CUSTOM.get(d_type, d_type)
            kwarg_types[name] = _create_custom_type_tree(nested_type)

    return custom_type, kwarg_types


def _create_type_tree(field: str) -> Any:
    """Create type tree for AEA-native ABCI spec"""

    if any(map(field.startswith, SPECIFICATION_COMPOSITIONAL_TYPES)):
        subfields = _get_sub_types_of_compositional_types(field)
        if field.startswith("pt:optional"):
            return _create_type_tree(*subfields)
        elif field.startswith("pt:list"):  # repeated
            return list, _create_type_tree(*subfields)
        else:
            raise NotImplementedError(f"field: {field}")

    if field.startswith("ct:"):
        custom_type = AEA_CUSTOM[field[3:]]
        return _create_custom_type_tree(custom_type)

    primitive = getattr(builtins, field[3:])
    return primitive


def create_abci_type_tree(speech_acts: Dict[str, Dict[str, str]]) -> Dict[str, Node]:
    """Create AEA-native ABCI type tree from the defined speech acts"""

    def _get_message_types(fields: Dict[str, str]) -> Node:
        """Get message types for AEA-native ABCI spec"""
        return {k: _create_type_tree(v) for k, v in fields.items()}

    return {k: _get_message_types(v) for k, v in speech_acts.items()}


# 2. Initialize AEA-native ABCI primitives
def _init_subtree(node: Node) -> Node:
    """Initialize subtree of type_tree non-custom objects"""

    def init_repeated(repeated_type: Any) -> Tuple[Any, ...]:
        """Repeated fields must be tuples for Tendermint protobuf"""

        if repeated_type in PYTHON_PRIMITIVES:
            data = NON_DEFAULT_PRIMITIVES[repeated_type]
            repeated = tuple(data for _ in range(REPEATED_FIELD_SIZE))
        elif isinstance(repeated_type, tuple):
            cls, kws = repeated_type
            repeated = tuple(_init_subtree(kws) for _ in range(REPEATED_FIELD_SIZE))
        else:
            raise NotImplementedError(f"Repeated in {name}: {repeated_type}")

        return repeated

    kwargs: Node = {}
    for name, d_type in node.items():
        if isinstance(d_type, tuple):
            container, content = d_type
            if container is list:
                kwargs[name] = init_repeated(content)
            else:
                kwargs[name] = _init_subtree(content)
        elif d_type in PYTHON_PRIMITIVES:
            kwargs[name] = NON_DEFAULT_PRIMITIVES[d_type]
        elif is_enum(d_type):
            kwargs[name] = list(d_type)[USE_NON_ZERO_ENUM]
        else:
            raise NotImplementedError(f"{name}: {d_type}")

    return kwargs


def init_type_tree_primitives(type_tree: Node) -> Node:
    """
    Initialize the primitive types and size of repeated fields.

    These are the only initialization parameters that can vary;
    after this the initialization of custom types is what remains

    This structure allows:
    - Comparison of structure and these values with Tendermint translation
    - Visual inspection of fields to be sets, also on custom objects
    - Randomized testing strategies using e.g. hypothesis

    :param type_tree: mapping from message / field name to type.
    :return: mapping from message / field name to initialized primitive.
    """
    return {k: _init_subtree(node) for k, node in type_tree.items()}


# 3. Initialize AEA-native ABCI protocol messages
def _complete_init(type_node: Node, init_node: Node) -> Node:
    """Initialize custom classes and containers"""

    def init_repeated(repeated_type: Any) -> Tuple[Any, ...]:
        if not isinstance(content, tuple):
            return init_node[key]  # already initialized primitives
        custom_type, kwargs = repeated_type
        return tuple(custom_type(**_complete_init(kwargs, c)) for c in init_node[key])

    node: Node = {}
    for key, d_type in type_node.items():
        if d_type in PYTHON_PRIMITIVES:
            node[key] = init_node[key]
        elif isinstance(d_type, tuple):
            container, content = d_type
            if container is list:
                node[key] = init_repeated(content)
            else:
                node[key] = container(**_complete_init(content, init_node[key]))
        elif is_enum(d_type):
            node[key] = init_node[key]
        else:
            raise NotImplementedError(f"{key}: {d_type}")

    return node


def init_abci_messages(type_tree: Node, init_tree: Node) -> Node:
    """
    Create ABCI messages for AEA-native ABCI spec

    We iterate the type_tree and init_tree to finalize the
    initialization of custom objects contained in it, and
    create an instance of all ABCI messages.

    :param type_tree: mapping from message / field name to type.
    :param init_tree: mapping from message / field name to initialized primitive.
    :return: mapping from message name to ABCI Message instance
    """

    messages = dict.fromkeys(type_tree)
    for key in type_tree:
        performative = getattr(AbciMessage.Performative, key.upper())
        kwargs = _complete_init(type_tree[key], init_tree[key])
        messages[key] = AbciMessage(performative, **kwargs)

    return messages


# 4. Translate AEA-native to Tendermint-native
def encode(message: AbciMessage) -> Response:
    """Encode AEA-native ABCI protocol messages to Tendermint-native"""

    try:
        return Encoder.process(message)
    except Exception as e:
        raise EncodingError(f"ABCI message {message}: {e}")


def decode(request: Request) -> AbciMessage:
    """Decode Tendermint-native ABCI protocol messages to AEA-native"""

    dialogues = AbciDialogues(name="", skill_context=mock.MagicMock())
    try:
        message, dialogue = Decoder().process(request, dialogues, "dummy")  # type: ignore
        return message
    except Exception as e:
        raise DecodingError(f"Request {request}: {e}")


# 5. Build content tree from Tendermint-native ABCI messages
def _get_message_content(message: Any) -> Node:
    """Verify Tendermint-native ABCI message"""

    # NOTE: PublicKey objects are an Enum in AEA-native protocol
    #       but are retrieved as mapping from Tendermint side

    assert message.IsInitialized()
    assert not message.UnknownFields()
    assert not message.FindInitializationErrors()

    # NOTE: ListFields does not retrieve what is empty!
    fields = dict(message.DESCRIPTOR.fields_by_name)
    enum_types = dict(message.DESCRIPTOR.enum_types_by_name)
    oneofs = dict(message.DESCRIPTOR.oneofs_by_name)

    kwargs: Node = {}
    for name, descr in fields.items():
        attr = getattr(message, name)

        if descr.enum_type:
            enum_type = enum_types.pop(snake_to_camel(name))
            kwargs[name] = (enum_type.values[attr].name, attr)
        elif isinstance(attr, PYTHON_PRIMITIVES):
            kwargs[name] = attr
        elif descr.label == descr.LABEL_REPEATED:
            assert isinstance(descr.default_value, list)  # attr
            assert len(set(map(type, attr))) <= 1, "Expecting single type"
            if not attr or isinstance(attr[0], PYTHON_PRIMITIVES):
                kwargs[name] = list(attr)
            else:
                kwargs[name] = [_get_message_content(c) for c in attr]
        elif descr.message_type:
            kwargs[name] = _get_message_content(attr)
        else:
            raise NotImplementedError(f"name: {name} {attr}")

    # in the case of oneofs, we assert they were retrieved from fields (PublicKey)
    expected = {f.name for oneof in oneofs.values() for f in oneof.fields}
    assert all(k in kwargs for k in expected), f"oneofs in {message}"
    assert not enum_types, f"assumed max 1 enum per message: {message}"

    return kwargs


def get_tendermint_content(envelope: Union[Request, Response]) -> Node:
    """
    Get Tendermint-native ABCI message content.

    For all Request / Response instances obtained after encoding,
    we retrieve the information present in the message they contain.

    :param envelope: a Tendermint Request / Response object.
    :return: mapping structure from message / field name to leaf values
    """

    assert isinstance(envelope, (Request, Response))
    assert envelope.IsInitialized()
    assert not envelope.UnknownFields()
    assert not envelope.FindInitializationErrors()
    assert len(envelope.ListFields()) == 1
    descr, message = envelope.ListFields()[0]
    return _get_message_content(message)


# compare AEA- and Tendermint-native ABCI protocol input and output
def compare_trees(init_node: Node, tender_node: Node) -> None:
    """Compare Initialization and Tendermint tree nodes"""

    # NOTE: PublicKey objects are an Enum in AEA-native protocol
    #       but are retrieved as mapping from Tendermint side

    if init_node == tender_node:
        return

    for k, init_child in init_node.items():

        # translate key to tendermint key
        tk = {"type_": "type", "format_": "format", "hash_": "hash"}.get(k, k)
        tender_child = tender_node[tk]

        if k == "pub_key":
            init_child = {init_child["key_type"].name: init_child["data"]}

        if init_child == tender_child:
            continue
        elif isinstance(init_child, dict) and isinstance(tender_child, dict):
            compare_trees(init_child, tender_child)

        elif isinstance(tender_child, list):

            # we use a nested mapping to represent a custom class,
            # tendermint doesn't use this for storing repeated fields
            if isinstance(init_child, dict):
                repeated = list(init_child.values())
                assert len(repeated) == 1
                init_child = repeated[0]

            assert len(init_child) == len(tender_child)
            for a, b in zip(init_child, tender_child):
                compare_trees(a, b)

        else:
            assert len(init_child) == 1, "expecting enum"
            enum = set(init_child.values()).pop()
            assert (enum.name, enum.value) == tender_node[tk]


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


def test_all_custom_types_used() -> None:
    """
    Test if all custom types are used in speech acts.

    By asserting their usage in the speech acts we can delegate
    the verification of their implementation and translation to
    another test that addresses this (test_aea_to_tendermint).
    """

    aea_protocol, custom_types, _ = get_protocol_readme_spec()
    speech_acts = aea_protocol["speech_acts"]
    defined_types = {v for vals in speech_acts.values() for v in vals.values()}

    custom_in_speech: Set[str] = set()
    for d_type in defined_types:
        if any(map(d_type.startswith, SPECIFICATION_COMPOSITIONAL_TYPES)):
            subfields = _get_sub_types_of_compositional_types(d_type)
            custom_in_speech.update(s[3:] for s in subfields if s.startswith("ct:"))
        elif d_type.startswith("ct:"):
            custom_in_speech.add(d_type[3:])

    assert custom_in_speech == {s[3:] for s in custom_types}


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
    """
    Test translation from AEA-native to Tendermint-native ABCI protocol.

    "repeated" fields are returned as list in python,
    but must be passed as tuples to Tendermint protobuf.
    """

    aea_protocol, *_ = get_protocol_readme_spec()
    speech_acts = aea_protocol["speech_acts"]

    # 1. create type tree from speech acts
    type_tree = create_abci_type_tree(speech_acts)
    type_tree.pop("dummy")  # TODO: known oddity on our side

    # 2. initialize primitives
    init_tree = init_type_tree_primitives(type_tree)

    # 3. create AEA-native ABCI protocol messages
    abci_messages = init_abci_messages(type_tree, init_tree)

    # 4. encode to Tendermint-native ABCI protocol
    #    NOTE: request not implemented in encoder
    encoded = {k: encode(v) for k, v in abci_messages.items()}
    translated = {k: v for k, v in encoded.items() if v}
    untranslated = set(encoded).difference(translated)
    assert all(k.startswith("request") for k in untranslated)

    # 5. create Tendermint message content tree
    tender_tree = {k: get_tendermint_content(v) for k, v in translated.items()}

    # 6. translate expected differences in attribute / field naming
    #    these are known difference introduced by translating between protocols
    param_keys_trans = {k: f"{k}_params" for k in ["evidence", "validator", "version"]}
    tendermint_to_aea = dict(
        response_info={"data": "info_data"},
        response_query={"proof_ops": {"ops": "proof_ops"}},
        response_init_chain={"consensus_params": param_keys_trans},
        response_end_block={"consensus_param_updates": param_keys_trans},
    )
    replace_keys(tender_tree, tendermint_to_aea)

    # 7. compare AEA-native message initialization with the information
    #    retrieved from the Tendermint Response after translation
    shared = set(type_tree).intersection(tender_tree)
    assert len(shared) == 16  # expected number of matches
    for k in shared:
        init_node, tender_node = init_tree[k], tender_tree[k]
        compare_trees(init_node, tender_node)
