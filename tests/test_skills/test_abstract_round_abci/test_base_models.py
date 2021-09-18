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

"""Test the base_models.py module of the skill."""
from abc import ABC
from enum import Enum

from aea_ledger_ethereum import EthereumCrypto
from hypothesis import given
from hypothesis.strategies import booleans, dictionaries, floats, one_of, text

from packages.valory.skills.abstract_round_abci.base_models import (
    BaseTxPayload,
    Transaction,
)
from packages.valory.skills.abstract_round_abci.serializer import (
    DictProtobufStructSerializer,
)


class PayloadEnum(Enum):
    """Payload enumeration type."""

    A = "A"
    B = "B"
    C = "C"

    def __str__(self) -> str:
        """Get the string representation."""
        return self.value


class BasePayload(BaseTxPayload, ABC):
    """Base payload class for testing.."""


class PayloadA(BasePayload):
    """Payload class for payload type 'A'."""

    transaction_type = PayloadEnum.A


class PayloadB(BasePayload):
    """Payload class for payload type 'B'."""

    transaction_type = PayloadEnum.B


class PayloadC(BasePayload):
    """Payload class for payload type 'C'."""

    transaction_type = PayloadEnum.C


def test_encode_decode():
    """Test encoding and decoding of payloads."""
    sender = "sender"

    expected_payload = PayloadA(sender=sender)
    actual_payload = PayloadA.decode(expected_payload.encode())
    assert expected_payload == actual_payload

    expected_payload = PayloadB(sender=sender)
    actual_payload = PayloadB.decode(expected_payload.encode())
    assert expected_payload == actual_payload

    expected_payload = PayloadC(sender=sender)
    actual_payload = PayloadC.decode(expected_payload.encode())
    assert expected_payload == actual_payload


def test_encode_decode_transaction():
    """Test encode/decode of a transaction."""
    sender = "sender"
    signature = "signature"
    payload = PayloadA(sender)
    expected = Transaction(payload, signature)
    actual = expected.decode(expected.encode())
    assert expected == actual


def test_sign_verify_transaction():
    """Test sign/verify transaction."""
    crypto = EthereumCrypto()
    sender = crypto.address
    payload = PayloadA(sender)
    payload_bytes = payload.encode()
    signature = crypto.sign_message(payload_bytes)
    transaction = Transaction(payload, signature)
    transaction.verify(crypto.identifier)


@given(
    dictionaries(
        keys=text(),
        values=one_of(floats(allow_nan=False, allow_infinity=False), booleans()),
    )
)
def test_dict_serializer_is_deterministic(obj):
    """Test that 'DictProtobufStructSerializer' is deterministic."""
    obj_bytes = DictProtobufStructSerializer.encode(obj)
    for _ in range(100):
        assert obj_bytes == DictProtobufStructSerializer.encode(obj)
    assert obj == DictProtobufStructSerializer.decode(obj_bytes)
