# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022-2023 Valory AG
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

"""Helper functions for checking compliance to ABCI spec"""

# pylint: skip-file

import builtins
import functools
import inspect
from enum import Enum
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, List, Tuple, Type, Union

import yaml
from aea.protocols.generator.common import (
    SPECIFICATION_COMPOSITIONAL_TYPES,
    _camel_case_to_snake_case,
    _get_sub_types_of_compositional_types,
    _to_camel_case,
)
from google.protobuf.descriptor import FieldDescriptor

from packages.valory.connections.abci.connection import PUBLIC_ID
from packages.valory.connections.abci.connection import (
    _TendermintProtocolDecoder as Decoder,
)
from packages.valory.connections.abci.connection import (
    _TendermintProtocolEncoder as Encoder,
)
from packages.valory.connections.abci.dialogues import AbciDialogues
from packages.valory.connections.abci.tendermint.abci.types_pb2 import (  # type: ignore
    DESCRIPTOR,
    Request,
    Response,
)
from packages.valory.protocols import abci as valory_abci_protocol
from packages.valory.protocols.abci import AbciMessage, custom_types


Node = Dict[str, Any]

camel_to_snake = _camel_case_to_snake_case
snake_to_camel = _to_camel_case


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

TENDERMINT_PRIMITIVES = tuple(type_mapping.values())
PYTHON_PRIMITIVES = (int, float, bool, str, bytes)

# simple value strategy
AEA_PRIMITIVES = {str: "sss", bytes: b"bbb", int: 123, float: 3.14, bool: True}
TENDER_PRIMITIVES = dict(
    int32=-32,
    uint32=32,
    int64=-64,
    uint64=64,
    bool=True,
    string="sss",
    bytes=b"bbb",
    nanos=999,
)
REPEATED_FIELD_SIZE = 3
USE_NON_ZERO_ENUM: bool = True


def is_enum(d_type: Any) -> bool:
    """Check if a type is an Enum (not instance!)."""
    return isinstance(d_type, type) and issubclass(d_type, Enum)


def my_repr(self: Any) -> str:
    """Custom __repr__ for Tendermint protobuf objects, which lack it."""
    return f"<{self.__module__}.{type(self).__name__} object at {hex(id(self))}>"


def is_typing_list(d_type: Any) -> bool:
    """Check if field is repeated."""
    return d_type.__class__.__module__ == "typing" and d_type.__origin__ is list


def replace_keys(node: Node, trans: Node) -> None:
    """Replace keys in-place"""
    for k, v in trans.items():
        if isinstance(v, dict):
            replace_keys(node[k], v)
        else:
            node[v] = node.pop(k)


def set_repr(cls: Type) -> Type:
    """Set custom __repr__"""
    cls.__repr__ = my_repr  # type: ignore
    return cls


def get_aea_classes(module: ModuleType) -> Dict[str, Type]:
    """Get AEA custom classes."""

    def is_locally_defined_class(item: Any) -> bool:
        return isinstance(item, type) and item.__module__ == module.__name__

    return {k: v for k, v in vars(module).items() if is_locally_defined_class(v)}


AEA_CUSTOM = get_aea_classes(custom_types)


@functools.lru_cache()
def get_protocol_readme_spec() -> Tuple[Any, Any, Any]:
    """Test specification used to generate protocol matches ABCI spec"""

    protocol_readme = Path(valory_abci_protocol.__file__).parent / "README.md"
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
def _create_aea_custom_type_tree(custom_type: Type) -> Tuple[Type, Node]:
    """Create custom type tree for AEA-native ABCI spec"""

    kwarg_types = {}
    parameters = inspect.signature(custom_type).parameters
    for name, parameter in parameters.items():
        d_type = parameter.annotation
        if d_type in PYTHON_PRIMITIVES:
            kwarg_types[name] = d_type
        elif is_enum(d_type):
            kwarg_types[name] = d_type
        elif is_typing_list(d_type):  # "repeated"
            assert len(d_type.__args__) == 1  # check assumption
            container, content = d_type.__origin__, d_type.__args__[0]
            if content in AEA_CUSTOM.values():
                content = _create_aea_custom_type_tree(content)
            kwarg_types[name] = container, content
        else:
            nested_type = AEA_CUSTOM.get(d_type, d_type)
            kwarg_types[name] = _create_aea_custom_type_tree(nested_type)

    return custom_type, kwarg_types


def _create_aea_type_tree(field: str) -> Any:
    """Create type tree for AEA-native ABCI spec"""

    if any(map(field.startswith, SPECIFICATION_COMPOSITIONAL_TYPES)):
        subfields = _get_sub_types_of_compositional_types(field)
        if field.startswith("pt:optional"):
            return _create_aea_type_tree(*subfields)
        elif field.startswith("pt:list"):  # repeated
            return list, _create_aea_type_tree(*subfields)
        raise NotImplementedError(f"field: {field}")

    if field.startswith("ct:"):
        custom_type = AEA_CUSTOM[field[3:]]
        return _create_aea_custom_type_tree(custom_type)

    primitive = getattr(builtins, field[3:])
    return primitive


def create_aea_abci_type_tree(
    speech_acts: Dict[str, Dict[str, str]]
) -> Dict[str, Node]:
    """Create AEA-native ABCI type tree from the defined speech acts"""

    def _get_message_types(fields: Dict[str, str]) -> Node:
        """Get message types for AEA-native ABCI spec"""
        return {k: _create_aea_type_tree(v) for k, v in fields.items()}

    return {k: _get_message_types(v) for k, v in speech_acts.items()}


# 2. Initialize AEA-native ABCI primitives
def _init_subtree(node: Node) -> Node:
    """Initialize subtree of type_tree non-custom objects"""

    def init_repeated(repeated_type: Any) -> Tuple[Any, ...]:
        """Repeated fields must be tuples for Tendermint protobuf"""

        if repeated_type in PYTHON_PRIMITIVES:
            data = AEA_PRIMITIVES[repeated_type]
            return tuple(data for _ in range(REPEATED_FIELD_SIZE))
        elif isinstance(repeated_type, tuple):
            cls, kws = repeated_type
            return tuple(_init_subtree(kws) for _ in range(REPEATED_FIELD_SIZE))
        raise NotImplementedError(f"Repeated in {name}: {repeated_type}")

    kwargs: Node = {}
    for name, d_type in node.items():
        if isinstance(d_type, tuple):
            container, content = d_type
            if container is list:
                kwargs[name] = init_repeated(content)
            else:
                kwargs[name] = _init_subtree(content)
        elif d_type in PYTHON_PRIMITIVES:
            kwargs[name] = AEA_PRIMITIVES[d_type]
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


def init_aea_abci_messages(type_tree: Node, init_tree: Node) -> Node:
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


class EncodingError(Exception):
    """EncodingError AEA- to Tendermint-native ABCI message"""


class DecodingError(Exception):
    """DecodingError Tendermint- to AEA-native ABCI message"""


# 4. Translate AEA-native to Tendermint-native
def encode(message: AbciMessage) -> Response:
    """Encode AEA-native ABCI protocol messages to Tendermint-native"""

    try:
        return Encoder.process(message)
    except Exception as e:
        raise EncodingError(f"ABCI message {message}: {e}")


def decode(request: Request) -> AbciMessage:
    """Decode Tendermint-native ABCI protocol messages to AEA-native"""

    dialogues = AbciDialogues(connection_id=PUBLIC_ID)
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


def _process_message_descriptor(m_descriptor: Any) -> Node:
    """Process fields of the message descriptor"""

    node: Node = {}
    for name, field in m_descriptor.fields_by_name.items():
        if field.message_type:
            cls = set_repr(field.message_type._concrete_class)
            node[name] = cls, _process_message_descriptor(cls.DESCRIPTOR)
        elif field.enum_type:
            names = field.enum_type.values_by_name
            numbers = field.enum_type.values_by_number
            node[name] = Enum(name, zip(names, numbers))
        else:
            node[name] = type_mapping[field.type]

        if field.label == field.LABEL_REPEATED:
            node[name] = list, node[name]

    return node


def get_tender_type_tree() -> Node:
    """Tendermint type tree"""

    descriptor = DESCRIPTOR
    tender_type_tree = {}
    for msg, msg_descr in descriptor.message_types_by_name.items():
        cls = set_repr(msg_descr._concrete_class)
        tender_type_tree[msg] = cls, _process_message_descriptor(msg_descr)
    return tender_type_tree


def _init_tender_tree(tender_node: Node) -> Node:
    """Initialize Tendermint classes"""

    def init_repeated(repeated_type: Any) -> List[Any]:
        if isinstance(repeated_type, str):
            return [
                TENDER_PRIMITIVES[repeated_type] for _ in range(REPEATED_FIELD_SIZE)
            ]
        cls, kwargs = repeated_type
        return [cls(**_init_tender_tree(kwargs)) for _ in range(REPEATED_FIELD_SIZE)]

    node = {}
    for field, d_type in tender_node.items():
        if isinstance(d_type, str):
            if field == "nanos":  # special
                node[field] = TENDER_PRIMITIVES[field]
            else:
                node[field] = TENDER_PRIMITIVES[d_type]
        elif is_enum(d_type):
            node[field] = list(d_type)[USE_NON_ZERO_ENUM].value
        elif isinstance(d_type, tuple):
            container, content = d_type
            if container is list:
                node[field] = init_repeated(content)
            else:
                node[field] = container(**_init_tender_tree(content))
        else:
            raise NotImplementedError(f"field {field}: {d_type}")

    return node


def _build_tendermint_messages(cls: Type, tree: Node) -> List[Union[Request, Response]]:
    """Build tendermint messages"""

    return [cls(**{k: v}) for k, v in _init_tender_tree(tree).items()]


def init_tendermint_messages(tender_type_tree: Node) -> List[Union[Request, Response]]:
    """Initialize tendermint ABCI messages"""

    request_cls, request_tree = tender_type_tree["Request"]

    # construct Tendermint-native messages
    messages = _build_tendermint_messages(request_cls, request_tree)

    return messages
