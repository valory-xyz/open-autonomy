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
from typing import Any, Dict

import requests
import yaml
from google.protobuf.descriptor import FieldDescriptor

from packages.valory.connections.abci.protos.tendermint import abci as tendermint_abci
from packages.valory.connections.abci.tendermint.abci.types_pb2 import DESCRIPTOR
from packages.valory.protocols import abci as abci_protocol


ENCODING = "utf-8"
VERSION = "v0.34.11"
local_file = Path(tendermint_abci.__path__[0]) / "types.proto"

type_mapping = {v: k[5:].lower() for k, v in vars(FieldDescriptor).items() if k.startswith("TYPE")}
type_to_python = dict(
    double=float,
    float=float,
    int64=int,
    uint64=int,
    int32=int,
    # fixed64=int,
    # fixed32=int,
    bool=bool,
    string=str,
    # group=,
    # message=,
    bytes=bytes,
    uint32=int,
    # enum=,
    # sfixed32=,
    # sfixed64=,
    # sint32=,
    # sint64=,
)


def translate_type(data_type: str):
    """Translate type"""
    if data_type in type_to_python:
        return f"pt:{type_to_python[data_type].__name__}"
    return f"ct:{data_type}"


def to_snake_case(name: str) -> str:
    """CamelCase to snake_case"""
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def get_tendermint_message_types() -> Dict[str, Any]:
    """Get Tendermint message type definitions"""

    messages = dict()
    for msg, msg_desc in DESCRIPTOR.message_types_by_name.items():
        messages.setdefault(msg, {})

        # Request & Response
        for oneof in msg_desc.oneofs:
            for field in oneof.fields:
                item = [field.message_type.name, field.name, field.number]
                messages[msg].setdefault(oneof.name, []).append(item)
            continue

        # ResponseOfferSnapshot & ResponseApplySnapshotChunk
        for enum_type in msg_desc.enum_types:
            enum = dict(zip(enum_type.values_by_name, enum_type.values_by_number))
            messages[msg][enum_type.name] = enum

        # other fields
        for field in msg_desc.fields:
            messages[msg].setdefault(field.name, {})
            if field.message_type:
                item = [field.message_type.name, field.number]
            else:
                item = [type_mapping[field.type], field.number]
            if field.default_value == []:
                item.append("repeated")
            messages[msg][field.name] = item

    return messages


@functools.lru_cache()
def get_protocol_readme_spec():
    """Test specification used to generate protocol matches ABCI spec"""

    protocol_readme = Path(abci_protocol.__path__[0]) / "README.md"
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


def test_local_file_matches_github():
    """Test local file containing ABCI spec matches Tendermint GitHub"""

    url = f"https://raw.githubusercontent.com/tendermint/tendermint/{VERSION}/proto/tendermint/abci/types.proto"
    response = requests.get(url)
    if response.status_code != 200:
        log_msg = "Failed to retrieve Tendermint abci types from Github: "
        raise requests.HTTPError(f"{log_msg}: {response.status_code} ({response.reason})")
    github_data = response.text
    local_data = local_file.read_text(encoding=ENCODING)
    assert github_data == local_data


def test_speech_act_matches_abci_spec():
    """Test speech act definitions"""

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
            differences[key] = (expected, defined)

    if differences:
        lines = (f"{k}\n{v[0]}\n{v[1]}" for k, v in differences.items())
        log_msg = "Defined speech act not matching"
        logging.error(f"{log_msg}\n" + "\n".join(lines))
    assert not bool(differences)


def test_defined_custom_types_match_abci_spec():
    """Test custom types abci spec"""

    differences = dict()
    _, custom_types, _ = get_protocol_readme_spec()
    message_types = get_tendermint_message_types()

    # these are not custom types
    request_keys = {key for key, *_ in message_types["Request"]["value"]}
    response_keys = {key for key, *_ in message_types["Response"]["value"]}
    filtered_keys = {"Request", "Response", *request_keys, *response_keys}

    for key, v in message_types.items():
        if key in filtered_keys:
            continue

        ckey = f"ct:{key}"
        if ckey in custom_types:
            message_types[key]
            custom_types[ckey]
        else:
            print(key)

    for key, v in custom_types.items():
        print(key)


def test_defined_dialogues_match_abci_spec():
    """Test defined dialogues match abci spec"""

    *_, dialogues = get_protocol_readme_spec()
    message_types = get_tendermint_message_types()

    # expected
    request_oneof = message_types['Request']["value"]
    request_keys = {to_snake_case(key) for key, *_ in request_oneof}
    response_oneof = message_types['Response']["value"]
    response_keys = {to_snake_case(key) for key, *_ in response_oneof}

    # defined
    initiation = dialogues['initiation']
    reply = dialogues['reply']
    termination = dialogues['termination']

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

