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

# pylint: skip-file

import logging
import time
from pathlib import Path
from typing import Any, Dict, Set

import requests
from aea.protocols.generator.common import (
    SPECIFICATION_COMPOSITIONAL_TYPES,
    _get_sub_types_of_compositional_types,
)

from packages.valory.connections import abci as tendermint_abci
from packages.valory.connections.abci.tests.helper import (
    camel_to_snake,
    compare_trees,
    create_aea_abci_type_tree,
    decode,
    encode,
    get_protocol_readme_spec,
    get_tender_type_tree,
    get_tendermint_content,
    init_aea_abci_messages,
    init_tendermint_messages,
    init_type_tree_primitives,
    replace_keys,
)


Node = Dict[str, Any]

# constants & utility functions
ENCODING = "utf-8"
VERSION = "v0.34.19"
REPO_PATH = Path(*tendermint_abci.__package__.split(".")).absolute()
PROTO_FILES = list((REPO_PATH / "protos" / "tendermint").glob("**/*.proto"))
URL_PREFIX = f"https://raw.githubusercontent.com/tendermint/tendermint/{VERSION}/proto/tendermint/"

# to ensure primitives are not initialized to empty default values
NON_DEFAULT_PRIMITIVES = {str: "sss", bytes: b"bbb", int: 123, float: 3.14, bool: True}
REPEATED_FIELD_SIZE = 3
USE_NON_ZERO_ENUM: bool = True


# tests
def test_local_types_file_matches_github(request_attempts: int = 3) -> None:
    """Test local file containing ABCI spec matches Tendermint GitHub"""

    different = []
    for file in PROTO_FILES:
        url = URL_PREFIX + "/".join(file.parts[-2:])
        response, i = requests.get(url), 0
        while response.status_code != 200 and i < request_attempts:
            time.sleep(0.1)
            response, i = requests.get(url), i + 1
        if response.status_code != 200:
            log_msg = "Failed to retrieve Tendermint proto types from Github"
            status_code, reason = response.status_code, response.reason
            raise requests.HTTPError(f"{log_msg}: {status_code} ({reason})")
        github_data = response.text
        local_data = file.read_text(encoding=ENCODING)
        if not github_data == local_data:
            different.append([file, url])

    if different:
        logging.error("\n".join(" =/= ".join(map(str, x)) for x in different))
    assert not bool(different)


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
    tender_type_tree = get_tender_type_tree()

    # expected
    request_oneof = tender_type_tree["Request"][-1]
    request_keys = {camel_to_snake(cls.__name__) for cls, _ in request_oneof.values()}
    response_oneof = tender_type_tree["Response"][-1]
    response_keys = {camel_to_snake(cls.__name__) for cls, _ in response_oneof.values()}

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
    type_tree = create_aea_abci_type_tree(speech_acts)
    type_tree.pop("dummy")  # TODO: known oddity on our side

    # 2. initialize primitives
    init_tree = init_type_tree_primitives(type_tree)

    # 3. create AEA-native ABCI protocol messages
    abci_messages = init_aea_abci_messages(type_tree, init_tree)

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


def test_tendermint_decoding() -> None:
    """Test Tendermint ABCI message decoding"""

    # 1. create tendermint type tree
    tender_type_tree = get_tender_type_tree()

    # 2. initialize messages
    messages = init_tendermint_messages(tender_type_tree)

    # 3. translate to AEA-native ABCI Messages
    decoded = list(map(decode, messages))
    assert len(decoded) == 15  # expected number of matches
