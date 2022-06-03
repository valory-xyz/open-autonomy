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

import functools
import logging
import re
from pathlib import Path
from typing import Any, Dict, Iterable, Set, Tuple, Union

import requests
import yaml
from google.protobuf.descriptor import FieldDescriptor

from packages.valory.connections.abci.protos.tendermint import abci  # type: ignore
from packages.valory.connections.abci.tendermint.abci import types_pb2  # type: ignore
from packages.valory.protocols import abci as abci_protocol


ENCODING = "utf-8"
VERSION = "v0.34.11"
LOCAL_TYPES_FILE = Path(abci.__path__[0]) / "types.proto"
URL = f"https://raw.githubusercontent.com/tendermint/tendermint/{VERSION}/proto/tendermint/abci/types.proto"

# regex patterns for parsing protobuf types
start_of_struct_pattern = re.compile(r"\s*(\w+)\s+(\w+) {.*")
types_proto_pattern = re.compile(r"\n\w+ \w+ \{(?:.|\n)*?(?:(?:}\n)+)")
field_pattern = re.compile(r"\s*(repeated)?\s*([a-zA-Z0-9_\.]+)?\s+(\w+)\s*= (\d+)")
abci_app_field_pattern = re.compile(r"\s*(\w+) ([a-zA-Z()]+) (\w+) ([a-zA-Z()]+);")

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


# utility functions
def translate_type(data_type: str) -> str:
    """Translate type"""
    if data_type in type_to_python:
        if type_to_python[data_type] is None:
            raise NotImplementedError(f"type_to_python: {data_type}")
        return f"pt:{type_to_python[data_type].__name__}"
    return f"ct:{data_type}"


def to_snake_case(name: str) -> str:
    """Convert CamelCase to snake_case"""
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def nested_dict_to_text(dict_obj, indent: int = 0, report: str = "") -> str:
    """Pretty Print nested dictionary with given indent level"""
    for key, value in dict_obj.items():
        if isinstance(value, dict):
            report += f"{' ' * indent}{key}: {{\n"
            report += nested_dict_to_text(value, indent + 4)
            report += f"{' ' * indent}}}\n"
        else:
            report += f"{' ' * indent}{key}: {value}\n"
    return report


@functools.lru_cache()
def parse_raw(s: str) -> Dict[Union[str, Tuple[str, str]], Any]:
    """Parse custom types from protocol readme.md and abci/types.proto"""

    open_bracket, closing_bracket, end_of_field = "{", "}", ";"
    container, stack, content = {}, [], ""  # type: ignore
    for line in re.sub("//.*", "", s).splitlines():

        # empty types: {}
        if open_bracket + closing_bracket in line:
            dtype, name = start_of_struct_pattern.match(line).groups()  # type: ignore
            container[(dtype, name)] = {}

        # dealing with nested structures: message or nested enum / oneof
        elif open_bracket in line:
            dtype, name = start_of_struct_pattern.match(line).groups()  # type: ignore
            stack.append((dtype, name))
            data = container
            for key in stack:
                data = data.setdefault(key, {})
                if key == (dtype, name):
                    break
            else:
                data[(dtype, name)] = {}
        elif closing_bracket in line:
            stack.pop()
        else:
            content += line

        # regular field (not message or nested enum / oneof)
        if end_of_field in line:

            # special case
            if stack and stack[-1][-1] == "ABCIApplication":
                fields = abci_app_field_pattern.match(line).groups()  # type: ignore
                protocol, request, _, response = fields
                container[stack[-1]][protocol, request] = response
                continue

            # base cases
            match = field_pattern.match(content)
            repeated, dtype, name, idx = match.groups()  # type: ignore
            data = container
            for key in stack:
                data = data[key]
            if not dtype and not repeated:  # == enum
                data[name] = idx
            else:
                key = name if not repeated else (repeated, name)  # type: ignore
                data[key] = (dtype, idx)  # type: ignore
            content = ""

    assert not stack  # sanity check
    return container


def get_tendermint_abci_types() -> Dict[Any, Any]:
    """Parse types from tendermint/abci/types.proto"""

    n_expected, structs = 47, []
    file_content = LOCAL_TYPES_FILE.read_text(encoding=ENCODING)
    raw_structs = types_proto_pattern.findall(file_content)
    assert len(raw_structs) == n_expected  # sanity check
    for s in raw_structs:
        structs.append(parse_raw(s))
        assert len(structs[-1]) == 1  # sanity check
    merged = {k: v for d in structs for k, v in d.items()}
    assert len(merged) == n_expected  # sanity check
    return merged


@functools.lru_cache()
def get_tendermint_message_types() -> Dict[str, Any]:
    """Get Tendermint message type definitions"""

    messages: Dict[str, Any] = dict()
    for msg, msg_desc in types_pb2.DESCRIPTOR.message_types_by_name.items():
        messages.setdefault(msg, {})

        # Request & Response
        for oneof in msg_desc.oneofs:
            for field in oneof.fields:
                item = [field.message_type.name, field.name, field.number]
                messages[msg].setdefault(oneof.name, []).append(item)
            messages[msg][oneof.name] = tuple(messages[msg][oneof.name])

        # ResponseOfferSnapshot & ResponseApplySnapshotChunk
        for enum_type in msg_desc.enum_types:
            enum = dict(zip(enum_type.values_by_name, enum_type.values_by_number))
            messages[msg][enum_type.name] = enum.items()

        # other fields
        for field in msg_desc.fields:
            messages[msg].setdefault(field.name, {})
            if field.message_type:
                item = [field.message_type.name, field.number]
            else:
                item = [type_mapping[field.type], field.number]
            if isinstance(field.default_value, list):
                item.append("repeated")
            messages[msg][field.name] = tuple(item)

    return messages


@functools.lru_cache()
def get_protocol_readme_spec() -> Tuple[Any, Any, Any]:
    """Test specification used to generate protocol matches ABCI spec"""

    protocol_readme = Path(abci_protocol.__path__[0]) / "README.md"  # type: ignore
    raw_chunks = open(protocol_readme).read().split("```")
    assert len(raw_chunks) == 3, "Expecting a single YAML code block"

    yaml_chunks = raw_chunks[1].strip("yaml").split("\n---")
    yaml_content = []
    for raw_doc in filter(None, yaml_chunks):
        try:
            yaml_content.append(yaml.safe_load(raw_doc))
        except yaml.YAMLError as e:
            raise e

    base, custom_types, dialogues = yaml_content
    assert base["name"] == "abci"  # sanity check
    return base, custom_types, dialogues


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
    base, *_ = get_protocol_readme_spec()
    message_types = get_tendermint_message_types()
    speech_acts = base["speech_acts"]
    request_oneof = message_types["Request"]["value"]
    for key, *_ in request_oneof:
        data = message_types[key].items()
        expected = {k: translate_type(v[0]) for k, v in data}
        defined = speech_acts[to_snake_case(key)]
        if expected != defined:
            differences[key] = get_unique(expected, defined)

    if differences:
        log_msg = "Defined speech act not matching"
        template = "message: {k}\n\texpected:\t{v[0]}\n\tdefined:\t{v[1]}"
        lines = (template.format(k=k, v=v) for k, v in differences.items())
        logging.error(f"{log_msg}\n" + "\n".join(lines))
    assert not bool(differences)


def test_defined_custom_types_match_abci_spec() -> None:
    """Test custom types abci spec"""

    def venn_keys(a: Iterable, b: Iterable) -> Tuple[Set[Any], Set[Any], Set[Any]]:
        set_a, set_b = set(a), set(b)
        return set_a - set_b, set_a & set_b, set_b - set_a

    # expected is Tendermint ABCI spec, defined is what we specified
    _, custom_types, _ = get_protocol_readme_spec()
    struct = get_tendermint_abci_types()
    defined_types = {k.split(":")[-1]: parse_raw(v) for k, v in custom_types.items()}
    expected_types = {k[-1]: v for k, v in struct.items()}

    missing, different, extra = (dict() for _ in range(3))
    for key, v_def in defined_types.items():
        if key not in expected_types:
            extra[key] = v_def
            continue

        v_exp = expected_types.get(key, {})
        miss, match, more = venn_keys(v_exp, v_def)
        diff = {k: (v_exp[k], v_def[k]) for k in match if v_exp[k] != v_def[k]}
        diff.update({k: (v_exp[k], "") for k in miss})
        diff.update({k: ("", v_def[k]) for k in more})
        if diff:
            different[key] = diff

    for key, v_exp in expected_types.items():
        if key not in defined_types:
            missing[key] = v_exp

    report, indent = "\n\n### Mismatch\n\n", " " * 4
    for k, v in different.items():
        report += f"{k}\n"
        for sub_k, (e, d) in v.items():
            sub_k = sub_k if isinstance(sub_k, str) else " ".join(sub_k)
            report += f"{indent}{sub_k}\n"
            report += f"{indent * 2}expected: {e}\n"
            report += f"{indent * 2}defined: {d}\n"

    report += "\n\n### Missing\n\n"
    report += nested_dict_to_text(missing)
    report += "\n\n### Extra\n\n"
    report += nested_dict_to_text(extra)
    if report:
        log_msg = "Custom types not matching ABCI spec"
        logging.error(f"{log_msg}\n{report}")

    # current assumptions:
    # - we MUST match what we implement
    # - missing structures ALLOWED, as we might not need or use them
    # - extra structures allowed (questionable)
    assert not bool(different)


def test_defined_dialogues_match_abci_spec() -> None:
    """Test defined dialogues match abci spec"""

    *_, dialogues = get_protocol_readme_spec()
    message_types = get_tendermint_message_types()

    # expected
    request_oneof = message_types["Request"]["value"]
    request_keys = {to_snake_case(key) for key, *_ in request_oneof}
    response_oneof = message_types["Response"]["value"]
    response_keys = {to_snake_case(key) for key, *_ in response_oneof}

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
