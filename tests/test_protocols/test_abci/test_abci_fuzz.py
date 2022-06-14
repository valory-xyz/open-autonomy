

import copy
from pprint import pprint
from typing import Any, Dict, Tuple

from google.protobuf.descriptor import FieldDescriptor
from hypothesis import given, strategies

from packages.valory.connections.abci import tendermint

from tests.test_protocols.test_abci.helper import (
    PYTHON_PRIMITIVES,
    camel_to_snake,
    compare_trees,
    create_abci_type_tree,
    descriptor_parser,
    encode,
    get_full_mapping,
    get_protocol_readme_spec,
    get_tendermint_content,
    init_abci_messages,
    is_enum,
    replace_keys,
)


"""
Rules of the game

- Create a mapping from tendermint tree onto our type tree
  This is necessary because different types of integers are
  distinguished in protobuf: int32, uint32, int64, uint64.
   
1. Create a type_tree for the tendermint messages
2. Create a one-to-one mapping from Tendermint to AEA tree
   As long as the structure is maintained this an be used to
   initialize the AEA ABCIMessage instances.
3. Create hypothesis trees with (what should be) valid strategies
4. Run hypothesis trees with a single mutation
"""


KEY_MAPPING = dict(  # AEA to Tendermint, one-to-one
    request_set_option={"key": "option_key", "value": "option_value"},
    request_query={"data": "query_data"},
    request_load_snapshot_chunk={"chunk": "chunk_index"},
    request_apply_snapshot_chunk={"sender": "chunk_sender"},
    response_info={"data": "info_data"},
)


key_translation = {
    "type_": "type",
    "format_": "format",
    "hash_": "hash",
    "round_": "round",
    "evidence_params": "evidence",
    "validator_params": "validator",
    "version_params": "version",
    "evidence_type": "type",
}


Node = Dict[str, Any]


BIT32 = 1 << 31
BIT64 = BIT32 << 31

STRATEGY_MAP = dict(  # TODO: strategy to assert failure
    int32=strategies.integers(min_value=-BIT32, max_value=BIT32 - 1),
    uint32=strategies.integers(min_value=0, max_value=(BIT32 << 1) - 1),
    int64=strategies.integers(min_value=-BIT64, max_value=BIT64 - 1),
    uint64=strategies.integers(min_value=0, max_value=(BIT64 << 1) - 1),
    bool=strategies.booleans(),
    string=strategies.text(),
    bytes=strategies.binary(),
)

REPEATED_FIELD_SIZE = 3
USE_NON_ZERO_ENUM: bool = True

type_mapping = {
    v: k[5:].lower() for k, v in vars(FieldDescriptor).items() if k.startswith("TYPE_")
}

tendermint_mapping = get_full_mapping()


# Step 0: complete tendermint_type_tree
def unfold_nested(tree):
    """Build tendermint type tree (all strings)"""

    def init_repeated(content):
        if content in type_mapping.values():
            return list.__name__, content
        return list.__name__, (content, unfold_nested(tendermint_mapping[content]))

    fields = tree.get("fields", {})
    node = {}
    for name, field in fields.items():
        if field in type_mapping.values():
            node[name] = field
        elif isinstance(field, tuple):
            d_type, label = field
            if label == "repeated":
                node[name] = init_repeated(d_type)
            else:
                node[name] = d_type, label
        else:
            node[name] = field, unfold_nested(tendermint_mapping[field])

    return node


# Step 1: retrieve tendermint protobuf type for primitives
def translate(type_node, abci_node):
    """Translate ab_node into tt_node format"""

    for k, type_child in type_node.items():

        if is_enum(type_child):
            continue
        if k == "pub_key":
            type_child[-1]["data"] = "bytes"
            continue
        if k == "proof_ops" and "ops" in abci_node:
            translate(type_child[-1][-1], abci_node["ops"][-1][-1])
            continue

        tk = key_translation.get(k, k)
        abci_child = abci_node[tk]

        if isinstance(type_child, str) or type_child in PYTHON_PRIMITIVES:
            type_node[k] = abci_child
        elif isinstance(type_child, dict) and isinstance(abci_child, dict):
            translate(type_child, abci_child)

        elif isinstance(type_child, tuple) and isinstance(abci_child, tuple):
            cls, d_type = type_child
            name, nested = abci_child
            if d_type in PYTHON_PRIMITIVES or nested == "enum":
                type_node[k] = cls, nested
            elif isinstance(d_type, dict) and isinstance(nested, dict):
                translate(d_type, nested)
            elif isinstance(d_type, tuple):
                translate(d_type[-1], nested[-1])
            else:  # extra nested mapping
                repeated = list(d_type.values())
                assert len(repeated) == 1
                translate(repeated[0][-1][-1], nested[-1])
        else:
            raise NotImplementedError(f"{k}:\n{type_child}\n{abci_child}")

    return type_node


def create_abci_tree() -> Dict[str, Any]:
    """Create Tendermint ABCI types tree by unfolding fields"""

    abci_types = descriptor_parser(tendermint.abci.types_pb2.DESCRIPTOR)
    return {camel_to_snake(k): unfold_nested(v) for k, v in abci_types.items()}


def create_tender_type_tree(type_tree, abci_tree):
    """Create type tree with Tendermint primitives"""

    tender_type_tree = {}
    for k in type_tree:
        abci_node, type_node = abci_tree[k], type_tree[k]
        replace_keys(abci_node, KEY_MAPPING.get(k, {}))
        tender_type_tree[k] = translate(copy.deepcopy(type_node), abci_node)

    return tender_type_tree


def _init_subtree(node: Any) -> Node:
    """Initialize subtree of type_tree non-custom objects"""

    def init_repeated(repeated_type: Any) -> Tuple[Any, ...]:
        """Repeated fields must be tuples for Tendermint protobuf"""

        # TODO: repeated fields for hypothesis
        if isinstance(repeated_type, str) or repeated_type in PYTHON_PRIMITIVES:
            data = STRATEGY_MAP[repeated_type]
            repeated = tuple(data for _ in range(REPEATED_FIELD_SIZE))
        elif isinstance(repeated_type, tuple):
            cls, kws = repeated_type
            repeated = tuple(_init_subtree(kws) for _ in range(REPEATED_FIELD_SIZE))
        else:
            raise NotImplementedError(f"Repeated in {name}: {repeated_type}")

        return repeated

    if isinstance(node, str):
        return node

    kwargs: Node = {}
    for name, d_type in node.items():
        if isinstance(d_type, str) or d_type in PYTHON_PRIMITIVES:
            kwargs[name] = STRATEGY_MAP[d_type]
        elif is_enum(d_type):
            kwargs[name] = list(d_type)[USE_NON_ZERO_ENUM]
        elif isinstance(d_type, tuple):
            container, content = d_type
            if container is list:
                kwargs[name] = init_repeated(content)
            else:
                kwargs[name] = _init_subtree(content)
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


def create_hypotheses() -> Any:
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

    # 2. create abci tree from Tendermint type definitions
    abci_tree = create_abci_tree()

    # 3. map the primitive types from ABCI spec onto the type tree
    tender_type_tree = create_tender_type_tree(type_tree, abci_tree)

    # 4. initialize with hypothesis
    hypo_tree = init_type_tree_primitives(tender_type_tree)

    # # 5. collapse hypo_tree
    def collapse(node):  # TODO: tuples
        for k, v in node.items():
            if isinstance(v, dict):
                node[k] = strategies.fixed_dictionaries(collapse(v))
        return node

    return hypo_tree   # TO BE: strategies.fixed_dictionaries(collapse(hypo_tree))


h = hypothesis_tree = create_hypotheses()
pprint(hypothesis_tree)


h2 = {
    "response_echo": strategies.fixed_dictionaries(h["response_echo"]),
    "response_info": strategies.fixed_dictionaries(h["response_info"]),
}

@given(strategies.fixed_dictionaries(h))
def test_new(strategy):

    aea_protocol, *_ = get_protocol_readme_spec()
    speech_acts = aea_protocol["speech_acts"]
    type_tree = create_abci_type_tree(speech_acts)
    type_tree.pop("dummy")

    init_tree = {"response_echo": strategy['response_echo'], "response_info": strategy['response_info']}
    type_tree = {"response_echo": type_tree['response_echo'], "response_info": type_tree['response_info']}

    abci_messages = init_abci_messages(type_tree, init_tree)

    encoded = {k: encode(v) for k, v in abci_messages.items()}
    translated = {k: v for k, v in encoded.items() if v}
    untranslated = set(encoded).difference(translated)
    assert all(k.startswith("request") for k in untranslated)

    tender_tree = {k: get_tendermint_content(v) for k, v in translated.items()}

    tendermint_to_aea = dict(
        response_info={"data": "info_data"},
    )
    replace_keys(tender_tree, tendermint_to_aea)

    shared = set(type_tree).intersection(tender_tree)
    assert len(shared) == 2, shared  # expected number of matches

    for k in shared:
        init_node, tender_node = init_tree[k], tender_tree[k]
        compare_trees(init_node, tender_node)
        import logging
        logging.error(init_node)
        logging.error(tender_node)
