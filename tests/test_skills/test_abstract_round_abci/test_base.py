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

"""Test the base.py module of the skill."""
import datetime
import re
from abc import ABC
from copy import copy
from enum import Enum
from unittest import mock
from unittest.mock import MagicMock

import pytest
from aea_ledger_ethereum import EthereumCrypto
from hypothesis import given
from hypothesis.strategies import booleans, dictionaries, floats, one_of, text

from packages.valory.protocols.abci.custom_types import Timestamp
from packages.valory.skills.abstract_round_abci.base import (
    ABCIAppInternalError,
    AbstractRound,
    AddBlockError,
    BasePeriodState,
    BaseTxPayload,
    Block,
    BlockBuilder,
    Blockchain,
    ConsensusParams,
    Period,
    SignatureNotValidError,
    Transaction,
    TransactionTypeNotRecognizedError,
    _MetaPayload,
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


class ConcreteRound(AbstractRound):
    """Dummy instantiation of the AbstractRound class."""

    round_id = "concrete"

    def end_block(self):
        """End block."""

    def check_payload_a(self, *args, **kwargs) -> bool:
        """Check payloads of type 'payload_a'."""
        return True

    def payload_a(self, *args, **kwargs) -> None:
        """Process payloads of type 'payload_a'."""


class TestTransactions:
    """Test Transactions class."""

    def setup(self):
        """Set up the test."""
        self.old_value = copy(_MetaPayload.transaction_type_to_payload_cls)

    def test_encode_decode(self):
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

    def test_encode_decode_transaction(self):
        """Test encode/decode of a transaction."""
        sender = "sender"
        signature = "signature"
        payload = PayloadA(sender)
        expected = Transaction(payload, signature)
        actual = expected.decode(expected.encode())
        assert expected == actual

    def test_sign_verify_transaction(self):
        """Test sign/verify transaction."""
        crypto = EthereumCrypto()
        sender = crypto.address
        payload = PayloadA(sender)
        payload_bytes = payload.encode()
        signature = crypto.sign_message(payload_bytes)
        transaction = Transaction(payload, signature)
        transaction.verify(crypto.identifier)

    def teardown(self):
        """Tear down the test."""
        _MetaPayload.transaction_type_to_payload_cls = self.old_value


@mock.patch(
    "aea.crypto.ledger_apis.LedgerApis.recover_message", return_value={"wrong_sender"}
)
def test_verify_transaction_negative_case(*_mocks):
    """Test verify() of transaction, negative case."""
    transaction = Transaction(MagicMock(sender="right_sender", json={}), b"")
    with pytest.raises(SignatureNotValidError, match="signature not valid."):
        transaction.verify("")


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


class TestMetaPayloadUtilityMethods:
    """Test _MetaPayload private utility methods."""

    def setup(self):
        """Set up the test."""
        self.old_value = copy(_MetaPayload.transaction_type_to_payload_cls)

    def test_meta_payload_validate_tx_type(self):
        """
        Test _MetaPayload._validate_transaction_type utility method.

        First, it registers a class object with a transaction type name into the
        _MetaPayload map from transaction type name to classes.
        Then, it tries to validate a new insertion with the same transaction type name
        but different class object. This will raise an error.
        """
        tx_type_name = "transaction_type"
        tx_cls_1 = MagicMock()
        tx_cls_2 = MagicMock()
        _MetaPayload.transaction_type_to_payload_cls[tx_type_name] = tx_cls_1

        with pytest.raises(ValueError):
            _MetaPayload._validate_transaction_type(tx_type_name, tx_cls_2)

    def test_get_field_positive(self):
        """Test the utility class method "_get_field", positive case"""
        expected_value = 42
        result = _MetaPayload._get_field(
            MagicMock(field_name=expected_value), "field_name"
        )
        return result == expected_value

    def test_get_field_negative(self):
        """Test the utility class method "_get_field", negative case"""
        with pytest.raises(ValueError):
            _MetaPayload._get_field(object(), "field_name")

    def teardown(self):
        """Tear down the test."""
        _MetaPayload.transaction_type_to_payload_cls = self.old_value


def test_initialize_block():
    """Test instantiation of a Block instance."""
    block = Block(MagicMock(), [])
    assert block.transactions == tuple()


class TestBlockchain:
    """Test a blockchain object."""

    def setup(self):
        """Set up the test."""
        self.blockchain = Blockchain()

    def test_height(self):
        """Test the 'height' property getter."""
        assert self.blockchain.height == 0

    def test_len(self):
        """Test the 'length' property getter."""
        assert self.blockchain.length == 0

    def test_add_block_positive(self):
        """Test 'add_block', success."""
        block = Block(MagicMock(height=1), [])
        self.blockchain.add_block(block)
        assert self.blockchain.length == 1
        assert self.blockchain.height == 1

    def test_add_block_negative_wrong_height(self):
        """Test 'add_block', wrong height."""
        wrong_height = 42
        block = Block(MagicMock(height=wrong_height), [])
        with pytest.raises(
            AddBlockError,
            match=f"expected height {self.blockchain.height + 1}, got {wrong_height}",
        ):
            self.blockchain.add_block(block)

    def test_blocks(self):
        """Test 'blocks' property getter."""
        assert self.blockchain.blocks == tuple()


class TestBlockBuilder:
    """Test block builder."""

    def setup(self):
        """Set up the method."""
        self.block_builder = BlockBuilder()

    def test_get_header_positive(self):
        """Test header property getter, positive."""
        expected_header = MagicMock()
        self.block_builder._current_header = expected_header
        actual_header = self.block_builder.header
        assert expected_header == actual_header

    def test_get_header_negative(self):
        """Test header property getter, negative."""
        with pytest.raises(ValueError, match="header not set"):
            self.block_builder.header

    def test_set_header_positive(self):
        """Test header property setter, positive."""
        expected_header = MagicMock()
        self.block_builder.header = expected_header
        actual_header = self.block_builder.header
        assert expected_header == actual_header

    def test_set_header_negative(self):
        """Test header property getter, negative."""
        self.block_builder.header = MagicMock()
        with pytest.raises(ValueError, match="header already set"):
            self.block_builder.header = MagicMock()

    def test_transitions_getter(self):
        """Test 'transitions' property getter."""
        assert self.block_builder.transactions == tuple()

    def test_add_transitions(self):
        """Test 'add_transition'."""
        transaction = MagicMock()
        self.block_builder.add_transaction(transaction)
        assert self.block_builder.transactions == (transaction,)

    def test_get_block_negative_header_not_set_yet(self):
        """Test 'get_block', negative case (header not set yet)."""
        with pytest.raises(ValueError, match="header not set"):
            self.block_builder.get_block()

    def test_get_block_positive(self):
        """Test 'get_block', positive case."""
        self.block_builder.header = MagicMock()
        self.block_builder.get_block()


class TestConsensusParams:
    """Test the 'ConsensusParams' class."""

    def setup(self):
        """Set up the tests."""
        self.max_participants = 4
        self.consensus_params = ConsensusParams(self.max_participants)

    def test_max_participants_getter(self):
        """Test 'max_participants' property getter."""
        expected_max_participants = self.max_participants
        assert self.consensus_params.max_participants == expected_max_participants

    @pytest.mark.parametrize(
        "nb_participants,expected",
        [
            (1, 1),
            (2, 2),
            (3, 3),
            (4, 3),
            (5, 4),
            (6, 5),
            (7, 5),
            (8, 6),
            (9, 7),
            (10, 7),
        ],
    )
    def test_threshold_getter(self, nb_participants, expected):
        """Test threshold property getter."""
        params = ConsensusParams(nb_participants)
        assert params.consensus_threshold == expected

    def test_from_json(self):
        """Test 'from_json' method."""
        expected = ConsensusParams(self.max_participants)
        json_object = dict(
            max_participants=self.max_participants,
        )
        actual = ConsensusParams.from_json(json_object)
        assert expected == actual


class TestBasePeriodState:
    """Test 'BasePeriodState' class."""

    def setup(self):
        """Set up the tests."""
        self.participants = {"a", "b"}
        self.base_period_state = BasePeriodState(self.participants)

    def test_participants_getter_positive(self):
        """Test 'participants' property getter."""
        assert self.participants == self.base_period_state.participants

    def test_participants_getter_negative(self):
        """Test 'participants' property getter, negative case."""
        base_period_state = BasePeriodState()
        with pytest.raises(ValueError, match="'participants' field is None"):
            base_period_state.participants

    def test_update(self):
        """Test the 'update' method."""
        participants = {"a"}
        expected = BasePeriodState(participants=participants)
        actual = self.base_period_state.update(participants=participants)
        assert expected.participants == actual.participants

    def test_repr(self):
        """Test the '__repr__' magic method."""
        actual_repr = repr(self.base_period_state)
        expected_repr_regex = r"BasePeriodState\({(.*)}\)"
        assert re.match(expected_repr_regex, actual_repr) is not None


class TestAbstractRound:
    """Test the 'AbstractRound' class."""

    def setup(self):
        """Set up the tests."""
        self.known_payload_type = ConcreteRound.payload_a.__name__
        self.participants = {"a", "b"}
        self.base_period_state = BasePeriodState(participants=self.participants)
        self.params = ConsensusParams(
            max_participants=len(self.participants),
        )
        self.round = ConcreteRound(self.base_period_state, self.params)

    def test_period_state_getter(self):
        """Test 'period_state' property getter."""
        state = self.round.period_state
        assert state.participants == self.participants

    def test_check_transaction_unknown_payload(self):
        """Test 'check_transaction' method, with unknown payload type."""
        tx_type = "unknown_payload"
        tx_mock = MagicMock()
        tx_mock.payload.transaction_type.value = tx_type
        with pytest.raises(
            TransactionTypeNotRecognizedError,
            match=f"request '{tx_type}' not recognized",
        ):
            self.round.check_transaction(tx_mock)

    def test_check_transaction_known_payload(self):
        """Test 'check_transaction' method, with known payload type."""
        tx_mock = MagicMock()
        tx_mock.payload.transaction_type.value = self.known_payload_type
        assert self.round.check_transaction(tx_mock)

    def test_process_transaction_negative_unknown_payload(self):
        """Test 'process_transaction' method, with unknown payload type."""
        tx_type = "unknown_payload"
        tx_mock = MagicMock()
        tx_mock.payload.transaction_type.value = tx_type
        with pytest.raises(
            TransactionTypeNotRecognizedError,
            match=f"request '{tx_type}' not recognized",
        ):
            self.round.process_transaction(tx_mock)

    def test_process_transaction_negative_check_transaction_fails(self):
        """Test 'process_transaction' method, with 'check_transaction' failing."""
        tx_mock = MagicMock()
        tx_mock.payload.transaction_type.value = "payload_a"
        error_message = "transaction not valid"
        with mock.patch.object(
            self.round, "check_transaction", side_effect=ValueError(error_message)
        ):
            with pytest.raises(ValueError, match=error_message):
                self.round.process_transaction(tx_mock)

    def test_process_transaction_positive(self):
        """Test 'process_transaction' method, positive case."""
        tx_mock = MagicMock()
        tx_mock.payload.transaction_type.value = "payload_a"
        self.round.process_transaction(tx_mock)


class TestPeriod:
    """Test the Period class."""

    def setup(self):
        """Set up the test."""
        self.period = Period(starting_round_cls=ConcreteRound)
        self.period.setup(MagicMock(), MagicMock())

    def test_is_finished(self):
        """Test 'is_finished' property."""
        assert not self.period.is_finished
        self.period._current_round = None
        assert self.period.is_finished

    def test_last_round(self):
        """Test 'last_round' property."""
        assert self.period.last_round_id is None

    def test_last_timestamp_none(self):
        """
        Test 'last_timestamp' property.

        The property is None because there are no blocks.
        """
        assert self.period.last_timestamp is None

    def test_last_timestamp(self):
        """Test 'last_timestamp' property, positive case."""
        seconds = 1
        nanoseconds = 1000
        timestamp = Timestamp(seconds, nanoseconds)
        self.period._blockchain.add_block(Block(MagicMock(time=timestamp), []))

        expected_timestamp = datetime.datetime.fromtimestamp(
            seconds + nanoseconds / 10 ** 9
        )
        assert self.period.last_timestamp == expected_timestamp

    def test_check_is_finished_negative(self):
        """Test 'check_is_finished', negative case."""
        self.period._current_round = None
        with pytest.raises(
            ValueError, match="period is finished, cannot accept new transactions"
        ):
            self.period.check_is_finished()

    def test_current_round_positive(self):
        """Test 'current_round' property getter, positive case."""
        assert isinstance(self.period.current_round, ConcreteRound)

    def test_current_round_negative_current_round_not_set(self):
        """Test 'current_round' property getter, negative case (current round not set)."""
        self.period._current_round = None
        with pytest.raises(ValueError, match="current_round not set!"):
            self.period.current_round

    def test_current_round_id(self):
        """Test 'current_round_id' property getter"""
        assert self.period.current_round_id == ConcreteRound.round_id

    def test_latest_result(self):
        """Test 'latest_result' property getter."""
        assert self.period.latest_result is None

    def test_begin_block_negative_is_finished(self):
        """Test 'begin_block' method, negative case (period is finished)."""
        self.period._current_round = None
        with pytest.raises(
            ABCIAppInternalError,
            match="internal error: period is finished, cannot accept new blocks",
        ):
            self.period.begin_block(MagicMock())

    def test_begin_block_negative_wrong_phase(self):
        """Test 'begin_block' method, negative case (wrong phase)."""
        self.period._block_construction_phase = MagicMock()
        with pytest.raises(
            ABCIAppInternalError,
            match="internal error: cannot accept a 'begin_block' request.",
        ):
            self.period.begin_block(MagicMock())

    def test_begin_block_positive(self):
        """Test 'begin_block' method, positive case."""
        self.period.begin_block(MagicMock())

    def test_deliver_tx_negative_wrong_phase(self):
        """Test 'begin_block' method, negative (wrong phase)."""
        with pytest.raises(
            ABCIAppInternalError,
            match="internal error: cannot accept a 'deliver_tx' request",
        ):
            self.period.deliver_tx(MagicMock())

    def test_deliver_tx_positive_not_valid(self):
        """Test 'begin_block' method, positive (not valid)."""
        self.period.begin_block(MagicMock())
        with mock.patch.object(
            self.period.current_round, "check_transaction", return_value=True
        ):
            with mock.patch.object(self.period.current_round, "process_transaction"):
                self.period.deliver_tx(MagicMock())

    def test_end_block_negative_wrong_phase(self):
        """Test 'end_block' method, negative case (wrong phase)."""
        with pytest.raises(
            ABCIAppInternalError,
            match="internal error: cannot accept a 'end_block' request.",
        ):
            self.period.end_block()

    def test_end_block_positive(self):
        """Test 'end_block' method, positive case."""
        self.period.begin_block(MagicMock())
        self.period.end_block()

    def test_commit_negative_wrong_phase(self):
        """Test 'end_block' method, negative case (wrong phase)."""
        with pytest.raises(
            ABCIAppInternalError,
            match="internal error: cannot accept a 'commit' request.",
        ):
            self.period.commit()

    def test_commit_negative_exception(self):
        """Test 'end_block' method, negative case (raise exception)."""
        self.period.begin_block(MagicMock(height=1))
        self.period.end_block()
        with mock.patch.object(
            self.period._blockchain, "add_block", side_effect=AddBlockError
        ):
            with pytest.raises(AddBlockError):
                self.period.commit()

    def test_commit_positive_no_change_round(self):
        """Test 'end_block' method, positive (no change round)."""
        self.period.begin_block(MagicMock(height=1))
        self.period.end_block()
        self.period.commit()
        assert isinstance(self.period.current_round, ConcreteRound)

    def test_commit_positive_with_change_round(self):
        """Test 'end_block' method, positive (with change round)."""
        self.period.begin_block(MagicMock(height=1))
        self.period.end_block()
        round_result, next_round = MagicMock(), MagicMock()
        with mock.patch.object(
            self.period.current_round,
            "end_block",
            return_value=(round_result, next_round),
        ):
            self.period.commit()
        assert not isinstance(self.period.current_round, ConcreteRound)
        assert self.period.latest_result == round_result
