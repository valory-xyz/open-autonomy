
# from tests.
from types import ModuleType
from typing import Dict, Any, Tuple
from hypothesis import strategies, given
from pathlib import Path
# from tests.test_protocols.test_abci.test_abci_spec import (
#     get_protocol_readme_spec,
#     create_abci_type_tree,
#     TENDERMINT_DEFS,
#     snake_to_camel,
#     PYTHON_PRIMITIVES,
#     NON_DEFAULT_PRIMITIVES,
#     REPEATED_FIELD_SIZE,
#     USE_NON_ZERO_ENUM,
#     is_enum,
# )
from pprint import pprint
from packages.valory.connections.abci import tendermint
# from packages.valory.connections.abci.tendermint.crypto import (  # type: ignore
#     keys_pb2,
#     proof_pb2,
# )
# from packages.valory.connections.abci.tendermint.types import (  # type: ignore
#     params_pb2,
#     types_pb2,
# )
from google.protobuf.descriptor import FieldDescriptor
import importlib.util
import sys


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


type_mapping = {
    v: k[5:].lower() for k, v in vars(FieldDescriptor).items() if k.startswith("TYPE_")
}


def _exec_module_import(path: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(path, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def descriptor_parser(descriptor) -> Dict[str, Any]:
    """Get Tendermint-native message type definitions"""

    messages: Dict[str, Any] = dict()
    for msg, msg_desc in descriptor.message_types_by_name.items():
        content = messages.setdefault(msg, {})

        # Request & Response
        for oneof in msg_desc.oneofs:
            fields = content.setdefault("oneofs", {}).setdefault(oneof.name, [])
            for field in oneof.fields:  # only PublicKey has no message_type
                name = field.message_type.name if field.message_type else oneof.containing_type.name
                fields.append((name, field.name))

        # ResponseOfferSnapshot & ResponseApplySnapshotChunk
        for enum_type in msg_desc.enum_types:
            enum = content.setdefault("enum_types", {})
            names, numbers = enum_type.values_by_name, enum_type.values_by_number
            enum[enum_type.name] = dict(zip(names, numbers))

        # other fields
        for field in msg_desc.fields:
            fields = content.setdefault("fields", {})
            d_type = type_mapping[field.type]
            repeated = field.label == field.LABEL_REPEATED

            if field.enum_type:
                assert not repeated  # assumed
                fields[field.name] = field.enum_type.name, d_type
                continue

            if field.message_type:
                d_type = field.message_type.name
            fields[field.name] = (d_type, "repeated") if repeated else d_type

    enum_types = {}
    for name, enum_type in descriptor.enum_types_by_name.items():
        enum = enum_types.setdefault("enum_types", {})
        names, numbers = enum_type.values_by_name, enum_type.values_by_number
        enum[enum_type.name] = dict(zip(names, numbers))
        messages.update(enum)

    # descriptor.extensions_by_name.items()
    # dependencies = {}
    # for dependency in descriptor.dependencies:
    #     key = '_'.join(Path(dependency.name).parts[-2:])[:-6]
    #     messages[key] = descriptor_parser(dependency)
    #     print(messages[key])

    return messages  # {"messages": messages, "enum_types": enum_types}


class TendermintModule:
    """"""

    __module = tendermint
    __MODULE_PATH = Path(*tendermint.__package__.split('.')).absolute()
    __python_files = tuple(__MODULE_PATH.rglob("*/*.py"))
    __slots__ = ["_".join(f.parts[-2:])[:-3] for f in __python_files]

    def __init__(self):
        for name, file in zip(self.__slots__, self.__python_files):
            setattr(self, name, _exec_module_import(str(file)))

    @property
    def description(self):
        return dict(zip(self.__slots__, (descriptor_parser(s.DESCRIPTOR) for s in self)))

    def __iter__(self):
        for slot in self.__slots__:
            yield getattr(self, slot)

    @property
    def abci_type_tree(self):
        return self.description.get('abci_types_pb2')


def get_name(x):
    # return x
    if isinstance(x, str):
        return x
    if isinstance(x, type):
        return x.__name__
    print(x)
    1/0


def _create_custom_type_tree(custom_type: Type) -> Tuple[Type, Node]:
    """Create custom type tree for AEA-native ABCI spec"""

    kwarg_types = {}
    parameters = inspect.signature(custom_type).parameters
    for name, parameter in parameters.items():
        d_type = parameter.annotation
        if d_type in PYTHON_PRIMITIVES:
            kwarg_types[name] = get_name(d_type)
        elif is_enum(d_type):
            kwarg_types[name] = get_name(d_type)
        elif is_repeated(d_type):
            assert len(d_type.__args__) == 1  # check assumption
            container, content = get_name(d_type.__origin__), d_type.__args__[0]
            if content in AEA_CUSTOM.values():
                kwarg_types[name] = container, _create_custom_type_tree(content)
            else:
                kwarg_types[name] = container, get_name(content)
        elif d_type in AEA_CUSTOM or d_type in AEA_CUSTOM.values():
            nested_type = AEA_CUSTOM.get(d_type, d_type)
            kwarg_types[name] = _create_custom_type_tree(nested_type)
        else:
            raise NotImplementedError(f"{name}: {d_type}")

    return get_name(custom_type), kwarg_types


def _create_type_tree(field: str) -> Any:
    """Create type tree for AEA-native ABCI spec"""

    if any(map(field.startswith, SPECIFICATION_COMPOSITIONAL_TYPES)):
        subfields = _get_sub_types_of_compositional_types(field)
        if field.startswith("pt:optional"):
            return _create_type_tree(*subfields)
        elif field.startswith("pt:list"):  # repeated
            return get_name(list), _create_type_tree(*subfields)
        else:
            raise NotImplementedError(f"field: {field}")

    if field.startswith("ct:"):
        custom_type = AEA_CUSTOM[field[3:]]
        return _create_custom_type_tree(custom_type)

    primitive = getattr(builtins, field[3:])
    return get_name(primitive)


def create_abci_type_tree(speech_acts: Dict[str, Dict[str, str]]) -> Dict[str, Node]:
    """Create AEA-native ABCI type tree from the defined speech acts"""

    def _get_message_types(fields: Dict[str, str]) -> Node:
        """Get message types for AEA-native ABCI spec"""
        return {k: _create_type_tree(v) for k, v in fields.items()}

    return {k: _get_message_types(v) for k, v in speech_acts.items()}


tm = TendermintModule()
# one conflicting key with an additional field
from google.protobuf import timestamp_pb2
from google.protobuf import duration_pb2
# from google.protobuf import

full = {k: v for m in tm.description.values() for k, v in m.items()}
TENDERMINT_TIME_STAMP = {"Timestamp": timestamp_pb2.Timestamp}
time_stamp = descriptor_parser(timestamp_pb2.DESCRIPTOR)
duration = descriptor_parser(duration_pb2.DESCRIPTOR)
full.update(time_stamp)
full.update(duration)
abci_tree = tm.abci_type_tree


def build_full(tree):

    fields = tree.get("fields", {})
    node = {}
    for name, field in fields.items():
        if field in type_mapping.values():
            node[name] = field
        elif isinstance(field, tuple):
            d_type, label = field
            if label == "repeated":
                if d_type in type_mapping.values():
                    node[name] = list.__name__, d_type
                else:
                    # print(list.__name__, (d_type, full[d_type], build_full(full[d_type])))
                    node[name] = list.__name__, (d_type, build_full(full[d_type]))
            else:
                node[name] = d_type, label
        else:
            # print(name)
            node[name] = field, build_full(full[field])

    return node


param_keys_trans = {k: f"{k}_params" for k in ["evidence", "validator", "version"]}
tendermint_to_aea = dict(
    # response_info={"data": "info_data"},
    response_query={"proof_ops": {"ops": "proof_ops"}},
    response_init_chain={"consensus_params": param_keys_trans},
    response_end_block={"consensus_param_updates": param_keys_trans},
)

KEY_MAPPING = dict(  # AEA to Tendermint, one-to-one
    request_set_option={"key": "option_key", "value": "option_value"},
    request_query={"data": "query_data"},
    request_load_snapshot_chunk={"chunk": "chunk_index"},
    request_apply_snapshot_chunk={"sender": "chunk_sender"},
    response_info={"data": "info_data"},
    # request_init_chain={"consensus_params": param_keys_trans},
    # response_query={"proof_ops": {"ops": "proof_ops"}},
    # response_query={"proof_ops": {"ProofOps"}},
    # response_init_chain={"consensus_params": param_keys_trans},
    # response_end_block={"consensus_param_updates": param_keys_trans},
)
# tendermint_to_aea = dict(
#     response_info={"data": "info_data"},
#
#     response_init_chain={"consensus_params": param_keys_trans},
#     response_end_block={"consensus_param_updates": param_keys_trans},
# )
# replace_keys(tender_tree, tendermint_to_aea)


type_tree = create_abci_type_tree(speech_acts)
type_tree.pop("dummy")

abci_tree = {camel_to_snake(k): v for k, v in abci_tree.items()}


key_translation = {
    "type_": "type",
    "format_": "format",
    "hash_": "hash",
    "round_": "round",
    "evidence_params": "evidence",
    "validator_params": "validator",
    "version_params": "version",
    # "info_data": "data",
}




def translate(tt_node, ab_node):
    """Translate ab_node into tt_node format"""

    kwargs = {}
    for k, tt_child in tt_node.items():

        if k == "pub_key":
            continue

        tk = key_translation.get(k, k)
        # ab_child = ab_node[tk]

        try:
            ab_child = ab_node[tk]
        except:
            print(tk)
            pprint(tt_child)
            pprint(ab_node)
            1/0

        if k == "validators":
            ab_child = (snake_to_camel("validator_updates"), {"validator_updates": ab_node[tk]})

        # if k == "time":
        #     ab_child = (snake_to_camel("timestamp"), ab_node[tk])

        if isinstance(tt_child, str) or tt_child in PYTHON_PRIMITIVES:
            kwargs[k] = ab_child
        elif isinstance(tt_child, tuple):
            # pprint(tt_child)
            # pprint(ab_child)
            tt_container, tt_content = tt_child
            ab_container, ab_content = ab_child

            # if tt_container in ["validators"]:  # or .values()
            # ab_node["snapshots"] = ("SnapShots", {"snapshots": ab_node["snapshots"]})
            if isinstance(tt_content, dict):
                kwargs[k] = tt_container, translate(tt_content, ab_content)
            elif isinstance(tt_content, tuple):  # nested repeated type
                cls, tt_kws = tt_content
                _, ab_kws = ab_content
                kwargs[k] = tt_container, (cls, translate(tt_kws, ab_kws))
            elif isinstance(tt_content, str) or tt_content in PYTHON_PRIMITIVES:
                kwargs[k] = tt_container, ab_content
            else:
                # assert tt_container == "list"
                # print(k)
                # print(tt_container, tt_content)
                # print(ab_container, ab_content)
                raise NotImplementedError(f"tt: {tt_node}\nab: {ab_node}")
        else:
            raise NotImplementedError(f"tt: {tt_node}\nab: {ab_node}")
    return kwargs



def replace_types(d):

    # for k in kkk:  # keys :(
    #     if k in d:
    #         d[kkk[k]] = d.pop(k)

    for k, v in d.items():
        if isinstance(v, dict):
            replace_types(v)
        elif isinstance(v, tuple):
            container, content = v
            if content == "enum":
                continue
            elif isinstance(content, dict):
                replace_types(content)
            else:
                if isinstance(content, tuple):
                    custom_type, kwargs = content
                    replace_types(kwargs)
                else:
                    d[k] = container, type_to_python[content].__name__
        elif isinstance(v, str) and v in type_to_python:
            d[k] = type_to_python[v].__name__
        else:
            raise NotImplementedError()


# def tr(v):
#     if isinstance(v, str) and v in type_to_python:
#         return type_to_python[v].__name__
#     return v


def replace_keys(node, trans) -> None:
    """Replace keys in-place"""
    for k, v in trans.items():
        if isinstance(v, dict):
            replace_keys(node[k], v)
        else:
            node[v] = node.pop(k)


# def get_diff(a, b):
#     for k in a:
#
#     return


# replace_keys(tender_tree, tendermint_to_aea)
for k in type_tree:
    # k = "response_end_block"  # "response_list_snapshots"
    # k = "response_init_chain"
    if k in abci_tree:

        # k = "response_apply_snapshot_chunk"

        ab_node = build_full(abci_tree[k])
        tt_node = type_tree[k]
        replace_types(ab_node)

        replace_keys(ab_node, KEY_MAPPING.get(k, {}))
        if k in KEY_MAPPING:
            ab_node = {KEY_MAPPING[k].get(kk, kk): v for kk, v in ab_node.items()}

        # ab_node = {kk: tr(v) for kk, v in ab_node.items()}


        if ab_node != tt_node:
            x = translate(tt_node, ab_node)
            print(k)
            if x == tt_node:
                print('successful translation')
                continue

            # pprint(ab_node)
            # pprint(tt_node)
            # pprint(x)
            # 1 / 0

            # for k2 in list(ab_node):
            #     if ab_node[k2] == tt_node.get(k2):
            #         ab_node.pop(k2)
            #         tt_node.pop(k2)
            print(k)
            pprint(ab_node)
            pprint(tt_node)
            # 1/0
    # 1/0
        # else:
        #     pprint(ab_node)
        #     pprint(tt_node)
        #     print(k)
        # for

1/0
def descriptor_parser(descriptor) -> Dict[str, Any]:
    """Get Tendermint-native message type definitions"""

    messages: Dict[str, Any] = dict()
    for msg, msg_desc in descriptor.message_types_by_name.items():
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
                item.append(tuple)
            fields[field.name] = tuple(item)


    # enum_types = {}
    # for name, enum_type in descriptor.enum_types_by_name.items():
    #     enum = enum_types.setdefault("enum_types", {})
    #     names, numbers = enum_type.values_by_name, enum_type.values_by_number
    #     enum[enum_type.name] = dict(zip(names, numbers))
    #
    # descriptor.extensions_by_name.items()
    # descriptor.dependencies

    return messages




#
#
#
# def get_tendermint_defs():
#     """"""
#
#     ABCI_TYPES = descriptor_parser(tendermint.abci.types_pb2.DESCRIPTOR)
#     PROOF = descriptor_parser(tendermint.crypto.proof_pb2.DESCRIPTOR)
#     PARAMS = descriptor_parser(tendermint.types.params_pb2.DESCRIPTOR)
#     TYPES_TYPES = descriptor_parser(tendermint.types.types_pb2.DESCRIPTOR)
#     VALIDATOR = descriptor_parser(tendermint.types.validator_pb2.DESCRIPTOR)
#     VERSION = descriptor_parser(tendermint.version.types_pb2.DESCRIPTOR)
#
#     PARAMS.pop("BlockParams")  # one additional field: 'time_iota_ms': ('int64', 3)
#
#     merged = {}
#     containers = [ABCI_TYPES, PROOF, PARAMS, TYPES_TYPES]
#     for (key, value) in (pair for d in containers for pair in d.items()):
#         if key in merged:
#             assert merged[key] == value, key
#         merged[key] = value
#     return merged
#
#
# TENDERMINT_DEFS = get_tendermint_defs()
#
# Node: Dict[str, Any]


# PRIMITIVE_STRATEGIES = {
#     # int: lambda mi = 0, ma=(1 << 63) - 1: strategies.integers(mi, ma),  # closure scoping!!
#     int: strategies.integers,
#     # bool=strategies.booleans,
#     str: strategies.text,
#     bytes: strategies.binary,
# }


# Step 0: complete tendermint_type_tree
# Step 1: retrieve tendermint protobuf type
# Step 2: select strategy based on this

#
# def _init_subtree(node: Node, ttree) -> Node:
#     """Initialize subtree of type_tree non-custom objects"""
#
#     def init_repeated(repeated_type: Any) -> Tuple[Any, ...]:
#         """Repeated fields must be tuples for Tendermint protobuf"""
#
#         if repeated_type in PYTHON_PRIMITIVES:
#             # print(name, d_type)
#             data = NON_DEFAULT_PRIMITIVES[repeated_type]
#             repeated = tuple(data for _ in range(REPEATED_FIELD_SIZE))
#         elif isinstance(repeated_type, tuple):
#             cls, kws = repeated_type
#             return
#             repeated = tuple(_init_subtree(kws) for _ in range(REPEATED_FIELD_SIZE))
#         else:
#             raise NotImplementedError(f"Repeated in {name}: {repeated_type}")
#
#         return repeated
#
#     kwargs: Node = {}
#     for name, d_type in node.items():
#         # print(name, d_type)
#         if isinstance(d_type, tuple):
#             container, content = d_type
#             if container is list:
#                 kwargs[name] = init_repeated(content)
#             else:
#                 try:
#                     k = snake_to_camel(name)
#                     node = ttree[k] if k in ttree else TENDERMINT_DEFS[k]
#                     kwargs[name] = _init_subtree(content, node)
#                 except Exception as e:
#                     print(f"{name}: {e}")
#         elif d_type in PYTHON_PRIMITIVES:
#             # print(name)
#             kwargs[name] = NON_DEFAULT_PRIMITIVES[d_type]
#         elif is_enum(d_type):
#             kwargs[name] = list(d_type)[USE_NON_ZERO_ENUM]
#         else:
#             raise NotImplementedError(f"{name}: {d_type}")
#
#     return kwargs
#
#
# def init_hypo_tree(type_tree: Node) -> Node:
#     """
#     Initialize the primitive types and size of repeated fields.
#
#     These are the only initialization parameters that can vary;
#     after this the initialization of custom types is what remains
#
#     This structure allows:
#     - Comparison of structure and these values with Tendermint translation
#     - Visual inspection of fields to be sets, also on custom objects
#     - Randomized testing strategies using e.g. hypothesis
#
#     :param type_tree: mapping from message / field name to type.
#     :return: mapping from message / field name to initialized primitive.
#     """
#     for k, node in type_tree.items():
#         # print(k)
#         _init_subtree(node, TENDERMINT_DEFS[snake_to_camel(k)])
#
#     return {k: _init_subtree(node, TENDERMINT_DEFS[snake_to_camel(k)]) for k, node in type_tree.items()}


# def create_hypo_tree():
#
#     aea_protocol, *_ = get_protocol_readme_spec()
#     speech_acts = aea_protocol["speech_acts"]
#     type_tree = create_abci_type_tree(speech_acts)
#     type_tree.pop("dummy")
#
#     # for k, type_node in type_tree.items():
#     hypo_tree = init_hypo_tree(type_tree)


        # x = TENDERMINT_DEFS[snake_to_camel(k)]
        # print(k)
        # print(x)
        # print(type_tree[k])
        # print()


# create_hypo_tree()

# # def __init_subtree(node: Node) -> Node:
# #     """Initialize subtree of type_tree non-custom objects"""
# #
# #     def init_repeated(repeated_type: Any) -> Tuple[Any, ...]:
# #         """Repeated fields must be tuples for Tendermint protobuf"""
# #
# #         if repeated_type in PYTHON_PRIMITIVES:
# #             data = NON_DEFAULT_PRIMITIVES[repeated_type]
# #             repeated = tuple(data for _ in range(REPEATED_FIELD_SIZE))
# #         elif isinstance(repeated_type, tuple):
# #             cls, kws = repeated_type
# #             repeated = tuple(_init_subtree(kws) for _ in range(REPEATED_FIELD_SIZE))
# #         else:
# #             raise NotImplementedError(f"Repeated in {name}: {repeated_type}")
# #
# #         return repeated
# #
# #     kwargs: Node = {}
# #     for name, d_type in node.items():
# #         if isinstance(d_type, tuple):
# #             container, content = d_type
# #             if container is list:
# #                 kwargs[name] = init_repeated(content)
# #             else:
# #                 kwargs[name] = _init_subtree(content)
# #         elif d_type in PYTHON_PRIMITIVES:
# #             # print(d_type)
# #             if d_type in PRIMITIVE_STRATEGIES:
# #                 # print(name)
# #                 kwargs[name] = PRIMITIVE_STRATEGIES[d_type]()
# #             else:
# #                 kwargs[name] = NON_DEFAULT_PRIMITIVES[d_type]
# #         elif is_enum(d_type):
# #             kwargs[name] = strategies.sampled_from(d_type)
# #         else:
# #             raise NotImplementedError(f"{name}: {d_type}")
# #
# #     return kwargs
#
#
# def init_type_tree_hypothesis(type_tree: Node) -> Node:
#     """
#     Initialize the primitive types and size of repeated fields.
#
#     These are the only initialization parameters that can vary;
#     after this the initialization of custom types is what remains
#
#     This structure allows:
#     - Comparison of structure and these values with Tendermint translation
#     - Visual inspection of fields to be sets, also on custom objects
#     - Randomized testing strategies using e.g. hypothesis
#
#     :param type_tree: mapping from message / field name to type.
#     :return: mapping from message / field name to initialized primitive.
#     """
#     return {k: __init_subtree(node) for k, node in type_tree.items()}
#
#
# def create_hypo_tree():
#     """"""
#     aea_protocol, *_ = get_protocol_readme_spec()
#     speech_acts = aea_protocol["speech_acts"]
#     type_tree = create_abci_type_tree(speech_acts)
#     type_tree.pop("dummy")
#     hypo_tree = init_type_tree_hypothesis(type_tree)
#     return hypo_tree
#
#
# # h = create_hypo_tree()
# h2 = {
#     "response_echo": strategies.fixed_dictionaries(h["response_echo"]),
#     "response_info": strategies.fixed_dictionaries(h["response_info"]),
# }
#
#
# @given(strategies.fixed_dictionaries(h2))
# def test_new(strat):
#
#     aea_protocol, *_ = get_protocol_readme_spec()
#     speech_acts = aea_protocol["speech_acts"]
#     type_tree = create_abci_type_tree(speech_acts)
#     type_tree.pop("dummy")
#
#     # init_tree = {"response_echo": strat['response_echo'], "response_info": strat['response_info']}
#     init_tree = {"response_echo": init_tree['response_echo'], "response_info": init_tree['response_info']}
#     #
#     type_tree = {"response_echo": type_tree['response_echo'], "response_info": type_tree['response_info']}
#     abci_messages = init_abci_messages(type_tree, init_tree)
#
#     encoded = {k: encode(v) for k, v in abci_messages.items()}
#     translated = {k: v for k, v in encoded.items() if v}
#     untranslated = set(encoded).difference(translated)
#     assert all(k.startswith("request") for k in untranslated)
#
#     # 5. create Tendermint message content tree
#     tender_tree = {k: get_tendermint_content(v) for k, v in translated.items()}
#
#     param_keys_trans = {k: f"{k}_params" for k in ["evidence", "validator", "version"]}
#     tendermint_to_aea = dict(
#         response_info={"data": "info_data"},
#         # response_query={"proof_ops": {"ops": "proof_ops"}},
#         # response_init_chain={"consensus_params": param_keys_trans},
#         # response_end_block={"consensus_param_updates": param_keys_trans},
#     )
#     replace_keys(tender_tree, tendermint_to_aea)
#
#     shared = set(type_tree).intersection(tender_tree)
#     assert len(shared) == 2, shared  # expected number of matches
#
#     for k in shared:
#         init_node, tender_node = init_tree[k], tender_tree[k]
#         compare_trees(init_node, tender_node)
#         logging.error(init_node)
#         logging.error(tender_node)



# h = strategies.text()
# d = {"message": h}
#
#
# @given(strategies.fixed_dictionaries(d))
# def test_new(strat):
#
#     aea_protocol, *_ = get_protocol_readme_spec()
#     speech_acts = aea_protocol["speech_acts"]
#     type_tree = create_abci_type_tree(speech_acts)
#     type_tree.pop("dummy")
#
#     init_tree = {"response_echo": strat}
#     type_tree = {"response_echo": type_tree['response_echo']}
#     abci_messages = init_abci_messages(type_tree, init_tree)
#
#     encoded = {k: encode(v) for k, v in abci_messages.items()}
#     translated = {k: v for k, v in encoded.items() if v}
#     untranslated = set(encoded).difference(translated)
#     assert all(k.startswith("request") for k in untranslated)
#
#     # 5. create Tendermint message content tree
#     tender_tree = {k: get_tendermint_content(v) for k, v in translated.items()}
#
#     shared = set(type_tree).intersection(tender_tree)
#     assert len(shared) == 1  # expected number of matches
#     for k in shared:
#         init_node, tender_node = init_tree[k], tender_tree[k]
#         compare_trees(init_node, tender_node)


