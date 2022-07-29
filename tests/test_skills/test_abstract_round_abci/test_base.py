# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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
from time import sleep
from typing import Any, Dict, Optional, Set, Tuple, Type
from unittest import mock
from unittest.mock import MagicMock

import hypothesis
import pytest
from aea.exceptions import AEAEnforceError
from aea_ledger_ethereum import EthereumCrypto
from hypothesis import given
from hypothesis.strategies import booleans, dictionaries, floats, one_of, text

from packages.valory.connections.abci.connection import MAX_READ_IN_BYTES
from packages.valory.skills.abstract_round_abci.base import (
    ABCIAppException,
    ABCIAppInternalError,
    AbciApp,
    AbciAppDB,
    AbciAppTransitionFunction,
    AbstractRound,
    AddBlockError,
    AppState,
    BaseSynchronizedData,
    BaseTxPayload,
    Block,
    BlockBuilder,
    Blockchain,
    ConsensusParams,
    EventType,
    LateArrivingTransaction,
    RoundSequence,
    SignatureNotValidError,
    Timeouts,
    Transaction,
    TransactionTypeNotRecognizedError,
    _MetaAbciApp,
    _MetaPayload,
)
from packages.valory.skills.abstract_round_abci.base import _logger as default_logger
from packages.valory.skills.abstract_round_abci.serializer import (
    DictProtobufStructSerializer,
)


class PayloadEnum(Enum):
    """Payload enumeration type."""

    A = "A"
    B = "B"
    C = "C"
    DUMMY = "DUMMY"

    def __str__(self) -> str:
        """Get the string representation."""
        return self.value


class PayloadEnumB(Enum):
    """Payload enumeration type."""

    A = "AA"

    def __str__(self) -> str:
        """Get the string representation."""
        return self.value


class BasePayload(BaseTxPayload, ABC):
    """Base payload class for testing."""


class PayloadA(BasePayload):
    """Payload class for payload type 'A'."""

    transaction_type = PayloadEnum.A


class PayloadB(BasePayload):
    """Payload class for payload type 'B'."""

    transaction_type = PayloadEnum.B


class PayloadC(BasePayload):
    """Payload class for payload type 'C'."""

    transaction_type = PayloadEnum.C


class PayloadD(BasePayload):
    """Payload class for payload type 'D'."""

    transaction_type = PayloadEnumB.A


class DummyPayload(BasePayload):
    """Dummy payload class."""

    transaction_type = PayloadEnum.DUMMY

    def __init__(self, sender: str, dummy_attribute: int, **kwargs: Any) -> None:
        """Initialize a dummy payload.

        :param sender: the sender address
        :param dummy_attribute: a dummy attribute
        :param kwargs: the keyword arguments
        """
        super().__init__(sender, **kwargs)
        self._dummy_attribute = dummy_attribute

    @property
    def dummy_attribute(self) -> int:
        """Get the dummy_attribute."""
        return self._dummy_attribute

    @property
    def data(self) -> Dict:
        """Get the data."""
        return dict(dummy_attribute=self.dummy_attribute)


class TooBigPayload(BaseTxPayload, ABC):
    """Base payload class for testing."""

    transaction_type = PayloadEnum.A

    @property
    def data(self) -> Dict:
        """Get the data"""
        return dict(dummy_field="0" * 10 ** 7)


class ConcreteRoundA(AbstractRound):
    """Dummy instantiation of the AbstractRound class."""

    round_id = "concrete_a"
    allowed_tx_type = "payload_a"

    def end_block(self) -> Tuple[MagicMock, MagicMock]:
        """End block."""
        return MagicMock(), MagicMock()

    def check_payload(self, payload: BaseTxPayload) -> None:
        """Check payloads of type 'payload_a'."""

    def process_payload(self, payload: BaseTxPayload) -> None:
        """Process payloads of type 'payload_a'."""


class ObjectImitator:
    """For custom __eq__ implementation testing"""

    def __init__(self, other: Any):
        """Copying references to class attr, and instance attr"""

        for attr, value in vars(other.__class__).items():
            if not attr.startswith("__") and not attr.endswith("__"):
                setattr(self.__class__, attr, value)

        self.__dict__ = other.__dict__


class ConcreteRoundB(AbstractRound):
    """Dummy instantiation of the AbstractRound class."""

    round_id = "concrete_b"
    allowed_tx_type = "payload_b"

    def end_block(self) -> None:
        """End block."""

    def check_payload(self, payload: BaseTxPayload) -> None:
        """Check payloads of type 'payload_b'."""

    def process_payload(self, payload: BaseTxPayload) -> None:
        """Process payloads of type 'payload_b'."""


class ConcreteRoundC(AbstractRound):
    """Dummy instantiation of the AbstractRound class."""

    round_id = "concrete_c"
    allowed_tx_type = "payload_c"

    def end_block(self) -> None:
        """End block."""

    def check_payload(self, payload: BaseTxPayload) -> None:
        """Check payloads of type 'payload_c'."""

    def process_payload(self, payload: BaseTxPayload) -> None:
        """Process payloads of type 'payload_c'."""


class AbciAppTest(AbciApp[str]):
    """A dummy AbciApp for testing purposes."""

    TIMEOUT: float = 1.0

    initial_round_cls: Type[AbstractRound] = ConcreteRoundA
    transition_function: Dict[Type[AbstractRound], Dict[str, Type[AbstractRound]]] = {
        ConcreteRoundA: {"a": ConcreteRoundA, "b": ConcreteRoundB, "c": ConcreteRoundC},
        ConcreteRoundB: {"b": ConcreteRoundB, "timeout": ConcreteRoundA},
        ConcreteRoundC: {"c": ConcreteRoundA, "timeout": ConcreteRoundC},
    }
    event_to_timeout: Dict[str, float] = {
        "timeout": TIMEOUT,
    }


def test_base_tx_payload() -> None:
    """Test BaseTxPayload."""

    payload = BasePayload(sender="sender")
    new_payload = payload.with_new_id()

    assert payload.sender == new_payload.sender
    assert payload.id_ != new_payload.id_
    payload.round_count = 1
    assert payload.round_count == 1
    assert type(hash(payload)) == int


class TestTransactions:
    """Test Transactions class."""

    def setup(self) -> None:
        """Set up the test."""
        self.old_value = copy(_MetaPayload.transaction_type_to_payload_cls)

    def test_encode_decode(self) -> None:
        """Test encoding and decoding of payloads."""
        sender = "sender"

        expected_payload = PayloadA(sender=sender)
        actual_payload = PayloadA.decode(expected_payload.encode())
        assert expected_payload == actual_payload

        expected_payload_ = PayloadB(sender=sender)
        actual_payload_ = PayloadB.decode(expected_payload_.encode())
        assert expected_payload_ == actual_payload_

        expected_payload__ = PayloadC(sender=sender)
        actual_payload__ = PayloadC.decode(expected_payload__.encode())
        assert expected_payload__ == actual_payload__

        expected_payload___ = PayloadD(sender=sender)
        actual_payload___ = PayloadD.decode(expected_payload___.encode())
        assert expected_payload___ == actual_payload___

    def test_encode_decode_transaction(self) -> None:
        """Test encode/decode of a transaction."""
        sender = "sender"
        signature = "signature"
        payload = PayloadA(sender)
        expected = Transaction(payload, signature)
        actual = expected.decode(expected.encode())
        assert expected == actual

    def test_encode_too_big_transaction(self) -> None:
        """Test encode of a too big transaction."""
        sender = "sender"
        signature = "signature"
        payload = TooBigPayload(sender)
        tx = Transaction(payload, signature)
        with pytest.raises(
            ValueError,
            match=f"Transaction must be smaller than {MAX_READ_IN_BYTES} bytes",
        ):
            tx.encode()

    def test_sign_verify_transaction(self) -> None:
        """Test sign/verify transaction."""
        crypto = EthereumCrypto()
        sender = crypto.address
        payload = PayloadA(sender)
        payload_bytes = payload.encode()
        signature = crypto.sign_message(payload_bytes)
        transaction = Transaction(payload, signature)
        transaction.verify(crypto.identifier)

    def test_payload_not_equal_lookalike(self) -> None:
        """Test payload __eq__ reflection via NotImplemented"""
        payload = PayloadA(sender="sender")
        lookalike = ObjectImitator(payload)
        assert not payload == lookalike

    def test_transaction_not_equal_lookalike(self) -> None:
        """Test transaction __eq__ reflection via NotImplemented"""
        payload = PayloadA(sender="sender")
        transaction = Transaction(payload, signature="signature")
        lookalike = ObjectImitator(transaction)
        assert not transaction == lookalike

    def teardown(self) -> None:
        """Tear down the test."""
        _MetaPayload.transaction_type_to_payload_cls = self.old_value


@mock.patch(
    "aea.crypto.ledger_apis.LedgerApis.recover_message", return_value={"wrong_sender"}
)
def test_verify_transaction_negative_case(*_mocks: Any) -> None:
    """Test verify() of transaction, negative case."""
    transaction = Transaction(MagicMock(sender="right_sender", json={}), "")
    with pytest.raises(SignatureNotValidError, match="signature not valid."):
        transaction.verify("")


@hypothesis.settings(deadline=2000)
@given(
    dictionaries(
        keys=text(),
        values=one_of(floats(allow_nan=False, allow_infinity=False), booleans()),
    )
)
def test_dict_serializer_is_deterministic(obj: Any) -> None:
    """Test that 'DictProtobufStructSerializer' is deterministic."""
    obj_bytes = DictProtobufStructSerializer.encode(obj)
    for _ in range(100):
        assert obj_bytes == DictProtobufStructSerializer.encode(obj)
        assert obj == DictProtobufStructSerializer.decode(obj_bytes)


class TestMetaPayloadUtilityMethods:
    """Test _MetaPayload private utility methods."""

    def setup(self) -> None:
        """Set up the test."""
        self.old_value = copy(_MetaPayload.transaction_type_to_payload_cls)

    def test_meta_payload_validate_tx_type(self) -> None:
        """
        Test _MetaPayload._validate_transaction_type utility method.

        First, it registers a class object with a transaction type name into the
        _MetaPayload map from transaction type name to classes.
        Then, it tries to validate a new insertion with the same transaction type name
        but different class object. This will raise an error.
        """
        tx_type_name = "transaction_type"
        tx_cls_1 = MagicMock(__name__="name_1")
        tx_cls_2 = MagicMock(__name__="name_2")
        _MetaPayload.transaction_type_to_payload_cls[tx_type_name] = tx_cls_1

        with pytest.raises(ValueError):
            _MetaPayload._validate_transaction_type(tx_type_name, tx_cls_2)

    def test_get_field_positive(self) -> None:
        """Test the utility class method "_get_field", positive case"""
        expected_value = 42
        result = _MetaPayload._get_field(
            MagicMock(field_name=expected_value), "field_name"
        )
        return result == expected_value

    def test_get_field_negative(self) -> None:
        """Test the utility class method "_get_field", negative case"""
        with pytest.raises(ValueError):
            _MetaPayload._get_field(MagicMock, "field_name")

    def teardown(self) -> None:
        """Tear down the test."""
        _MetaPayload.transaction_type_to_payload_cls = self.old_value


def test_initialize_block() -> None:
    """Test instantiation of a Block instance."""
    block = Block(MagicMock(), [])
    assert block.transactions == tuple()


class TestBlockchain:
    """Test a blockchain object."""

    def setup(self) -> None:
        """Set up the test."""
        self.blockchain = Blockchain()

    def test_height(self) -> None:
        """Test the 'height' property getter."""
        assert self.blockchain.height == 0

    def test_len(self) -> None:
        """Test the 'length' property getter."""
        assert self.blockchain.length == 0

    def test_add_block_positive(self) -> None:
        """Test 'add_block', success."""
        block = Block(MagicMock(height=1), [])
        self.blockchain.add_block(block)
        assert self.blockchain.length == 1
        assert self.blockchain.height == 1

    def test_add_block_negative_wrong_height(self) -> None:
        """Test 'add_block', wrong height."""
        wrong_height = 42
        block = Block(MagicMock(height=wrong_height), [])
        with pytest.raises(
            AddBlockError,
            match=f"expected height {self.blockchain.height + 1}, got {wrong_height}",
        ):
            self.blockchain.add_block(block)

    def test_blocks(self) -> None:
        """Test 'blocks' property getter."""
        assert self.blockchain.blocks == tuple()


class TestBlockBuilder:
    """Test block builder."""

    def setup(self) -> None:
        """Set up the method."""
        self.block_builder = BlockBuilder()

    def test_get_header_positive(self) -> None:
        """Test header property getter, positive."""
        expected_header = MagicMock()
        self.block_builder._current_header = expected_header
        actual_header = self.block_builder.header
        assert expected_header == actual_header

    def test_get_header_negative(self) -> None:
        """Test header property getter, negative."""
        with pytest.raises(ValueError, match="header not set"):
            self.block_builder.header

    def test_set_header_positive(self) -> None:
        """Test header property setter, positive."""
        expected_header = MagicMock()
        self.block_builder.header = expected_header
        actual_header = self.block_builder.header
        assert expected_header == actual_header

    def test_set_header_negative(self) -> None:
        """Test header property getter, negative."""
        self.block_builder.header = MagicMock()
        with pytest.raises(ValueError, match="header already set"):
            self.block_builder.header = MagicMock()

    def test_transitions_getter(self) -> None:
        """Test 'transitions' property getter."""
        assert self.block_builder.transactions == tuple()

    def test_add_transitions(self) -> None:
        """Test 'add_transition'."""
        transaction = MagicMock()
        self.block_builder.add_transaction(transaction)
        assert self.block_builder.transactions == (transaction,)

    def test_get_block_negative_header_not_set_yet(self) -> None:
        """Test 'get_block', negative case (header not set yet)."""
        with pytest.raises(ValueError, match="header not set"):
            self.block_builder.get_block()

    def test_get_block_positive(self) -> None:
        """Test 'get_block', positive case."""
        self.block_builder.header = MagicMock()
        self.block_builder.get_block()


class TestConsensusParams:
    """Test the 'ConsensusParams' class."""

    def setup(self) -> None:
        """Set up the tests."""
        self.max_participants = 4
        self.consensus_params = ConsensusParams(self.max_participants)

    def test_max_participants_getter(self) -> None:
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
    def test_threshold_getter(self, nb_participants: int, expected: int) -> None:
        """Test threshold property getter."""
        params = ConsensusParams(nb_participants)
        assert params.consensus_threshold == expected

    def test_consensus_params_not_equal_lookalike(self) -> None:
        """Test consensus param __eq__ reflection via NotImplemented"""
        lookalike = ObjectImitator(self.consensus_params)
        assert not self.consensus_params == lookalike

    def test_from_json(self) -> None:
        """Test 'from_json' method."""
        expected = ConsensusParams(self.max_participants)
        json_object = dict(
            max_participants=self.max_participants,
        )
        actual = ConsensusParams.from_json(json_object)
        assert expected == actual


class TestAbciAppDB:
    """Test 'AbciAppDB' class."""

    def setup(self) -> None:
        """Set up the tests."""
        self.participants = {"a", "b"}
        self.db = AbciAppDB(
            setup_data=dict(participants=[self.participants]),
        )

    @pytest.mark.parametrize(
        "data, setup_data",
        (
            ({"participants": ["a", "b"]}, {"participants": ["a", "b"]}),
            ({"participants": []}, {}),
            ({"participants": None}, None),
            ("participants", None),
            (1, None),
            (object(), None),
            (["participants"], None),
            ({"participants": [], "other": [1, 2]}, {"other": [1, 2]}),
        ),
    )
    def test_init(self, data: Dict, setup_data: Optional[Dict]) -> None:
        """Test constructor."""
        if setup_data is None:
            # the parametrization of `setup_data` set to `None` is in order to check if the exception is raised
            # when we incorrectly set the data in the configuration file with a type that is not allowed
            with pytest.raises(
                ValueError,
                match=re.escape(
                    f"AbciAppDB data must be `Dict[str, List[Any]]`, found `{type(data)}` instead"
                ),
            ):
                AbciAppDB(setup_data=data)
        else:
            db = AbciAppDB(setup_data=data)
            assert db._data == {0: setup_data}
            assert db.setup_data == setup_data
            assert db.cross_period_persisted_keys == []

    def test_try_alter_init_data(self) -> None:
        """Test trying to alter the init data."""
        setup_data = {"test": ["test"]}
        db = AbciAppDB(setup_data)
        assert db.setup_data == {"test": ["test"]}
        db.setup_data.update({"test": ["altered"]})
        assert db.setup_data == {"test": ["test"]}

    def test_get(self) -> None:
        """Test getters."""
        assert self.db.get("participants", default="default") == self.participants
        assert self.db.get("inexistent", default="default") == "default"
        assert self.db.get_latest_from_reset_index(0) == {
            "participants": self.participants
        }
        assert self.db.get_latest() == {"participants": self.participants}

    def test_increment_round_count(self) -> None:
        """Test increment_round_count."""
        assert self.db.round_count == -1
        self.db.increment_round_count()
        assert self.db.round_count == 0

    @pytest.mark.parametrize(
        "setup_data, update_data, expected_data",
        (
            (dict(), {"dummy_key": "dummy_value"}, {0: {"dummy_key": ["dummy_value"]}}),
            (
                dict(),
                {"dummy_key": ["dummy_value1", "dummy_value2"]},
                {0: {"dummy_key": [["dummy_value1", "dummy_value2"]]}},
            ),
            (
                {"test": ["test"]},
                {"dummy_key": "dummy_value"},
                {0: {"dummy_key": ["dummy_value"], "test": ["test"]}},
            ),
            (
                {"test": ["test"]},
                {"test": "dummy_value"},
                {0: {"test": ["test", "dummy_value"]}},
            ),
            (
                {"test": [["test"]]},
                {"test": ["dummy_value1", "dummy_value2"]},
                {0: {"test": [["test"], ["dummy_value1", "dummy_value2"]]}},
            ),
            (
                {"test": ["test"]},
                {"test": ["dummy_value1", "dummy_value2"]},
                {0: {"test": ["test", ["dummy_value1", "dummy_value2"]]}},
            ),
        ),
    )
    def test_update(
        self, setup_data: Dict, update_data: Dict, expected_data: Dict[int, Dict]
    ) -> None:
        """Test update db."""
        db = AbciAppDB(setup_data)
        db.update(**update_data)
        assert db._data == expected_data


class TestBaseSynchronizedData:
    """Test 'BaseSynchronizedData' class."""

    def setup(self) -> None:
        """Set up the tests."""
        self.participants = {"a", "b"}
        self.base_synchronized_data = BaseSynchronizedData(
            db=AbciAppDB(setup_data=dict(participants=[self.participants]))
        )

    def test_participants_getter_positive(self) -> None:
        """Test 'participants' property getter."""
        assert self.participants == self.base_synchronized_data.participants

    def test_nb_participants_getter(self) -> None:
        """Test 'participants' property getter."""
        assert len(self.participants) == self.base_synchronized_data.nb_participants

    def test_participants_getter_negative(self) -> None:
        """Test 'participants' property getter, negative case."""
        base_synchronized_data = BaseSynchronizedData(db=AbciAppDB(setup_data={}))
        # with pytest.raises(ValueError, match="Value of key=participants is None"):
        with pytest.raises(
            ValueError,
            match=re.escape(
                "'participants' field is not set for this period [0] and no default value was provided."
            ),
        ):
            base_synchronized_data.participants

    def test_update(self) -> None:
        """Test the 'update' method."""
        participants = {"a"}
        expected = BaseSynchronizedData(
            db=AbciAppDB(setup_data=dict(participants=[participants]))
        )
        actual = self.base_synchronized_data.update(participants=participants)
        assert expected.participants == actual.participants
        assert actual.db._data == {0: {"participants": [{"a", "b"}, {"a"}]}}

    def test_create(self) -> None:
        """Test the 'create' method."""
        participants = {"a"}
        actual = self.base_synchronized_data.create(participants=[participants])
        assert actual.db._data == {
            0: {"participants": [{"a", "b"}]},
            1: {"participants": [{"a"}]},
        }

    def test_repr(self) -> None:
        """Test the '__repr__' magic method."""
        actual_repr = repr(self.base_synchronized_data)
        expected_repr_regex = r"BaseSynchronizedData\(db=AbciAppDB\({(.*)}\)\)"
        assert re.match(expected_repr_regex, actual_repr) is not None

    def test_participants_list_is_empty(
        self,
    ) -> None:
        """Tets when participants list is set to zero."""
        base_synchronized_data = BaseSynchronizedData(
            db=AbciAppDB(setup_data=dict(participants=[{}]))
        )
        with pytest.raises(ValueError, match="List participants cannot be empty."):
            _ = base_synchronized_data.participants

    def test_all_participants_list_is_empty(
        self,
    ) -> None:
        """Tets when participants list is set to zero."""
        base_synchronized_data = BaseSynchronizedData(
            db=AbciAppDB(setup_data=dict(all_participants=[{}]))
        )
        with pytest.raises(ValueError, match="List participants cannot be empty."):
            _ = base_synchronized_data.all_participants

    def test_properties(self) -> None:
        """Test several properties"""
        participants = {"b", "a"}
        randomness_str = (
            "3439d92d58e47d342131d446a3abe264396dd264717897af30525c98408c834f"
        )
        randomness_value = 0.20400769574270503
        most_voted_keeper_address = "most_voted_keeper_address"
        blacklisted_keepers = "blacklisted_keepers"
        participant_to_selection = "participant_to_selection"
        participant_to_randomness = "participant_to_randomness"
        participant_to_votes = "participant_to_votes"

        base_synchronized_data = BaseSynchronizedData(
            db=AbciAppDB(
                setup_data=AbciAppDB.data_to_lists(
                    dict(
                        participants=participants,
                        all_participants=participants,
                        most_voted_randomness=randomness_str,
                        most_voted_keeper_address=most_voted_keeper_address,
                        blacklisted_keepers=blacklisted_keepers,
                        participant_to_selection=participant_to_selection,
                        participant_to_randomness=participant_to_randomness,
                        participant_to_votes=participant_to_votes,
                    )
                )
            )
        )
        assert self.base_synchronized_data.period_count == 0
        assert base_synchronized_data.all_participants == participants
        assert base_synchronized_data.sorted_participants == ["a", "b"]
        assert abs(base_synchronized_data.keeper_randomness - randomness_value) < 1e-10
        assert base_synchronized_data.most_voted_randomness == randomness_str
        assert (
            base_synchronized_data.most_voted_keeper_address
            == most_voted_keeper_address
        )
        assert base_synchronized_data.is_keeper_set
        assert base_synchronized_data.blacklisted_keepers == {blacklisted_keepers}
        assert (
            base_synchronized_data.participant_to_selection == participant_to_selection
        )
        assert (
            base_synchronized_data.participant_to_randomness
            == participant_to_randomness
        )
        assert base_synchronized_data.participant_to_votes == participant_to_votes


class TestAbstractRound:
    """Test the 'AbstractRound' class."""

    def setup(self) -> None:
        """Set up the tests."""
        self.known_payload_type = ConcreteRoundA.allowed_tx_type
        self.participants = {"a", "b"}
        self.base_synchronized_data = BaseSynchronizedData(
            db=AbciAppDB(setup_data=dict(participants=[self.participants]))
        )
        self.params = ConsensusParams(
            max_participants=len(self.participants),
        )
        self.round = ConcreteRoundA(self.base_synchronized_data, self.params)

    def test_must_set_round_id(self) -> None:
        """Test that the 'round_id' must be set in concrete classes."""

        class MyConcreteRound(AbstractRound):
            # here round_id is missing
            # ...
            allowed_tx_type = MagicMock()

            def end_block(self) -> Optional[Tuple[BaseSynchronizedData, EventType]]:
                pass

            def check_payload(self, payload: BaseTxPayload) -> None:
                pass

            def process_payload(self, payload: BaseTxPayload) -> None:
                pass

        with pytest.raises(ABCIAppInternalError, match="'round_id' field not set"):
            MyConcreteRound(MagicMock(), MagicMock())

    def test_must_set_allowed_tx_type(self) -> None:
        """Test that the 'allowed_tx_type' must be set in concrete classes."""

        class MyConcreteRound(AbstractRound):
            round_id = ""
            # here allowed_tx_type is missing
            # ...

            def end_block(self) -> Optional[Tuple[BaseSynchronizedData, EventType]]:
                pass

            def check_payload(self, payload: BaseTxPayload) -> None:
                pass

            def process_payload(self, payload: BaseTxPayload) -> None:
                pass

        with pytest.raises(
            ABCIAppInternalError, match="'allowed_tx_type' field not set"
        ):
            MyConcreteRound(MagicMock(), MagicMock())

    def test_check_allowed_tx_type_with_previous_round_transaction(self) -> None:
        """Test check 'allowed_tx_type'."""

        class MyConcreteRound(AbstractRound):
            round_id = ""
            allowed_tx_type = "allowed_tx_type"

            def end_block(self) -> Optional[Tuple[BaseSynchronizedData, EventType]]:
                pass

            def check_payload(self, payload: BaseTxPayload) -> None:
                pass

            def process_payload(self, payload: BaseTxPayload) -> None:
                pass

        with pytest.raises(LateArrivingTransaction), mock.patch.object(
            default_logger, "debug"
        ) as mock_logger:
            MyConcreteRound(
                MagicMock(), MagicMock(), "previous_transaction"
            ).check_allowed_tx_type(
                MagicMock(payload=MagicMock(transaction_type="previous_transaction"))
            )
            mock_logger.assert_called()

    def test_check_allowed_tx_type(self) -> None:
        """Test check 'allowed_tx_type'."""

        class MyConcreteRound(AbstractRound):
            round_id = ""
            allowed_tx_type = None

            def end_block(self) -> Optional[Tuple[BaseSynchronizedData, EventType]]:
                pass

            def check_payload(self, payload: BaseTxPayload) -> None:
                pass

            def process_payload(self, payload: BaseTxPayload) -> None:
                pass

        with pytest.raises(
            TransactionTypeNotRecognizedError,
            match="current round does not allow transactions",
        ):
            MyConcreteRound(MagicMock(), MagicMock()).check_allowed_tx_type(MagicMock())

    def test_synchronized_data_getter(self) -> None:
        """Test 'synchronized_data' property getter."""
        state = self.round.synchronized_data
        assert state.participants == self.participants

    def test_check_transaction_unknown_payload(self) -> None:
        """Test 'check_transaction' method, with unknown payload type."""
        tx_type = "unknown_payload"
        tx_mock = MagicMock()
        tx_mock.payload.transaction_type = tx_type
        with pytest.raises(
            TransactionTypeNotRecognizedError,
            match=f"request '{tx_type}' not recognized",
        ):
            self.round.check_transaction(tx_mock)

    def test_check_transaction_known_payload(self) -> None:
        """Test 'check_transaction' method, with known payload type."""
        tx_mock = MagicMock()
        tx_mock.payload.transaction_type = self.known_payload_type
        self.round.check_transaction(tx_mock)

    def test_process_transaction_negative_unknown_payload(self) -> None:
        """Test 'process_transaction' method, with unknown payload type."""
        tx_type = "unknown_payload"
        tx_mock = MagicMock()
        tx_mock.payload.transaction_type = tx_type
        with pytest.raises(
            TransactionTypeNotRecognizedError,
            match=f"request '{tx_type}' not recognized",
        ):
            self.round.process_transaction(tx_mock)

    def test_process_transaction_negative_check_transaction_fails(self) -> None:
        """Test 'process_transaction' method, with 'check_transaction' failing."""
        tx_mock = MagicMock()
        tx_mock.payload.transaction_type = "payload_a"
        error_message = "transaction not valid"
        with mock.patch.object(
            self.round, "check_allowed_tx_type", side_effect=ValueError(error_message)
        ):
            with pytest.raises(ValueError, match=error_message):
                self.round.process_transaction(tx_mock)

    def test_process_transaction_positive(self) -> None:
        """Test 'process_transaction' method, positive case."""
        tx_mock = MagicMock()
        tx_mock.payload.transaction_type = "payload_a"
        self.round.process_transaction(tx_mock)

    def test_check_majority_possible_raises_error_when_nb_participants_is_0(
        self,
    ) -> None:
        """Check that 'check_majority_possible' raises error when nb_participants=0."""
        with pytest.raises(
            ABCIAppInternalError,
            match="nb_participants not consistent with votes_by_participants",
        ):
            AbstractRound.check_majority_possible({}, 0)

    def test_check_majority_possible_passes_when_vote_set_is_empty(self) -> None:
        """Check that 'check_majority_possible' passes when the set of votes is empty."""
        AbstractRound.check_majority_possible({}, 1)

    def test_check_majority_possible_passes_when_vote_set_nonempty_and_check_passes(
        self,
    ) -> None:
        """
        Check that 'check_majority_possible' passes when set of votes is non-empty.

        The check passes because:
        - the threshold is 2
        - the other voter can vote for the same item of the first voter
        """
        AbstractRound.check_majority_possible({"alice": DummyPayload("alice", True)}, 2)

    def test_check_majority_possible_passes_when_payload_attributes_majority_match(
        self,
    ) -> None:
        """
        Test 'check_majority_possible' when set of votes is non-empty and the majority of the attribute values match.

        The check passes because:
        - the threshold is 3 (participants are 4)
        - 3 voters have the same attribute value in their payload
        """
        AbstractRound.check_majority_possible(
            {
                "voter_1": DummyPayload("voter_1", 0),
                "voter_2": DummyPayload("voter_2", 0),
                "voter_3": DummyPayload("voter_3", 0),
            },
            4,
        )

    def test_check_majority_possible_passes_when_vote_set_nonempty_and_check_doesnt_pass(
        self,
    ) -> None:
        """
        Check that 'check_majority_possible' doesn't pass when set of votes is non-empty.

        the check does not pass because:
        - the threshold is 2
        - both voters have already voted for different items
        """
        with pytest.raises(
            ABCIAppException,
            match="cannot reach quorum=2, number of remaining votes=0, number of most voted item's votes=1",
        ):
            AbstractRound.check_majority_possible(
                {
                    "alice": DummyPayload("alice", False),
                    "bob": DummyPayload("bob", True),
                },
                2,
            )

    def test_is_majority_possible_positive_case(self) -> None:
        """Test 'is_majority_possible', positive case."""
        assert AbstractRound.is_majority_possible(
            {"alice": DummyPayload("alice", False)}, 2
        )

    def test_is_majority_possible_negative_case(self) -> None:
        """Test 'is_majority_possible', negative case."""
        assert not AbstractRound.is_majority_possible(
            {
                "alice": DummyPayload("alice", False),
                "bob": DummyPayload("bob", True),
            },
            2,
        )

    def test_check_majority_possible_raises_error_when_new_voter_already_voted(
        self,
    ) -> None:
        """Test 'check_majority_possible_with_new_vote' raises when new voter already voted."""
        with pytest.raises(ABCIAppInternalError, match="voter has already voted"):
            AbstractRound.check_majority_possible_with_new_voter(
                {"alice": DummyPayload("alice", False)},
                "alice",
                DummyPayload("alice", True),
                2,
            )

    def test_check_majority_possible_raises_error_when_nb_participants_inconsistent(
        self,
    ) -> None:
        """Test 'check_majority_possible_with_new_vote' raises when 'nb_participants' inconsistent with other args."""
        with pytest.raises(
            ABCIAppInternalError,
            match="nb_participants not consistent with votes_by_participants",
        ):
            AbstractRound.check_majority_possible_with_new_voter(
                {"alice": DummyPayload("alice", True)},
                "bob",
                DummyPayload("bob", True),
                1,
            )

    def test_check_majority_possible_when_check_passes(
        self,
    ) -> None:
        """
        Test 'check_majority_possible_with_new_vote' when the check passes.

        The test passes because:
        - the number of participants is 2, and so the threshold is 2
        - the new voter votes for the same item already voted by voter 1.
        """
        AbstractRound.check_majority_possible_with_new_voter(
            {"alice": DummyPayload("alice", True)}, "bob", DummyPayload("bob", True), 2
        )


class TestTimeouts:
    """Test the 'Timeouts' class."""

    def setup(self) -> None:
        """Set up the test."""
        self.timeouts: Timeouts = Timeouts()

    def test_size(self) -> None:
        """Test the 'size' property."""
        assert self.timeouts.size == 0
        self.timeouts._heap.append(MagicMock())
        assert self.timeouts.size == 1

    def test_add_timeout(self) -> None:
        """Test the 'add_timeout' method."""
        # the first time, entry_count = 0
        entry_count = self.timeouts.add_timeout(datetime.datetime.now(), MagicMock())
        assert entry_count == 0

        # the second time, entry_count is incremented
        entry_count = self.timeouts.add_timeout(datetime.datetime.now(), MagicMock())
        assert entry_count == 1

    def test_cancel_timeout(self) -> None:
        """Test the 'cancel_timeout' method."""
        entry_count = self.timeouts.add_timeout(datetime.datetime.now(), MagicMock())
        assert self.timeouts.size == 1

        self.timeouts.cancel_timeout(entry_count)

        # cancelling timeouts does not remove them from the heap
        assert self.timeouts.size == 1

    def test_pop_earliest_cancelled_timeouts(self) -> None:
        """Test the 'pop_earliest_cancelled_timeouts' method."""
        entry_count_1 = self.timeouts.add_timeout(datetime.datetime.now(), MagicMock())
        entry_count_2 = self.timeouts.add_timeout(datetime.datetime.now(), MagicMock())
        self.timeouts.cancel_timeout(entry_count_1)
        self.timeouts.cancel_timeout(entry_count_2)
        self.timeouts.pop_earliest_cancelled_timeouts()
        assert self.timeouts.size == 0

    def test_get_earliest_timeout_a(self) -> None:
        """Test the 'get_earliest_timeout' method."""
        deadline_1 = datetime.datetime.now()
        event_1 = MagicMock()

        sleep(0.5)

        deadline_2 = datetime.datetime.now()
        event_2 = MagicMock()
        assert deadline_1 < deadline_2

        self.timeouts.add_timeout(deadline_2, event_2)
        self.timeouts.add_timeout(deadline_1, event_1)

        assert self.timeouts.size == 2
        # test that we get the event with the earliest deadline
        timeout, event = self.timeouts.get_earliest_timeout()
        assert timeout == deadline_1
        assert event == event_1

        # test that get_earliest_timeout does not remove elements
        assert self.timeouts.size == 2

        popped_timeout, popped_event = self.timeouts.pop_timeout()
        assert popped_timeout == timeout
        assert popped_event == event

    def test_get_earliest_timeout_b(self) -> None:
        """Test the 'get_earliest_timeout' method."""

        deadline_1 = datetime.datetime.now()
        event_1 = MagicMock()

        sleep(0.5)

        deadline_2 = datetime.datetime.now()
        event_2 = MagicMock()
        assert deadline_1 < deadline_2

        self.timeouts.add_timeout(deadline_1, event_1)
        self.timeouts.add_timeout(deadline_2, event_2)

        assert self.timeouts.size == 2
        # test that we get the event with the earliest deadline
        timeout, event = self.timeouts.get_earliest_timeout()
        assert timeout == deadline_1
        assert event == event_1

        # test that get_earliest_timeout does not remove elements
        assert self.timeouts.size == 2

    def test_pop_timeout(self) -> None:
        """Test the 'pop_timeout' method."""
        deadline_1 = datetime.datetime.now()
        event_1 = MagicMock()

        sleep(0.5)

        deadline_2 = datetime.datetime.now()
        event_2 = MagicMock()
        assert deadline_1 < deadline_2

        self.timeouts.add_timeout(deadline_2, event_2)
        self.timeouts.add_timeout(deadline_1, event_1)

        assert self.timeouts.size == 2
        # test that we get the event with the earliest deadline
        timeout, event = self.timeouts.pop_timeout()
        assert timeout == deadline_1
        assert event == event_1

        # test that pop_timeout removes elements
        assert self.timeouts.size == 1


class TestAbciApp:
    """Test the 'AbciApp' class."""

    def setup(self) -> None:
        """Set up the test."""
        self.abci_app = AbciAppTest(MagicMock(), MagicMock(), MagicMock())

    def test_initial_round_cls_not_set(self) -> None:
        """Test when 'initial_round_cls' is not set."""

        with pytest.raises(
            ABCIAppInternalError, match="'initial_round_cls' field not set"
        ):

            class MyAbciApp(AbciApp):
                # here 'initial_round_cls' should be defined.
                # ...
                transition_function: AbciAppTransitionFunction = {}

    def test_transition_function_not_set(self) -> None:
        """Test when 'transition_function' is not set."""
        with pytest.raises(
            ABCIAppInternalError, match="'transition_function' field not set"
        ):

            class MyAbciApp(AbciApp):
                initial_round_cls = ConcreteRoundA
                # here 'transition_function' should be defined.
                # ...

    def test_last_timestamp_negative(self) -> None:
        """Test the 'last_timestamp' property, negative case."""
        with pytest.raises(ABCIAppInternalError, match="last timestamp is None"):
            self.abci_app.last_timestamp

    def test_last_timestamp_positive(self) -> None:
        """Test the 'last_timestamp' property, positive case."""
        expected = MagicMock()
        self.abci_app._last_timestamp = expected
        assert expected == self.abci_app.last_timestamp

    def test_process_event(self) -> None:
        """Test the 'process_event' method, positive case, with timeout events."""
        self.abci_app.setup()
        self.abci_app._last_timestamp = MagicMock()
        assert isinstance(self.abci_app.current_round, ConcreteRoundA)
        self.abci_app.process_event("b")
        assert isinstance(self.abci_app.current_round, ConcreteRoundB)
        self.abci_app.process_event("timeout")
        assert isinstance(self.abci_app.current_round, ConcreteRoundA)

    def test_process_event_negative_case(self) -> None:
        """Test the 'process_event' method, negative case."""
        with mock.patch.object(self.abci_app.logger, "info") as mock_info:
            self.abci_app.process_event("a")
            mock_info.assert_called_with(
                "cannot process event 'a' as current state is not set"
            )

    def test_update_time(self) -> None:
        """Test the 'update_time' method."""
        # schedule round_a
        current_time = datetime.datetime.now()
        self.abci_app.setup()
        self.abci_app._last_timestamp = current_time

        # move to round_b that schedules timeout events
        self.abci_app.process_event("b")
        assert self.abci_app.current_round_id == "concrete_b"

        # simulate most recent timestamp beyond earliest deadline
        # after pop, len(timeouts) == 0, because round_a does not schedule new timeout events
        current_time = current_time + datetime.timedelta(0, AbciAppTest.TIMEOUT)
        self.abci_app.update_time(current_time)

        # now we are back to round_a
        assert self.abci_app.current_round_id == "concrete_a"

        # move to round_c that schedules timeout events to itself
        self.abci_app.process_event("c")
        assert self.abci_app.current_round_id == "concrete_c"

        # simulate most recent timestamp beyond earliest deadline
        # after pop, len(timeouts) == 0, because round_c schedules timeout events
        current_time = current_time + datetime.timedelta(0, AbciAppTest.TIMEOUT)
        self.abci_app.update_time(current_time)

        assert self.abci_app.current_round_id == "concrete_c"

        # further update changes nothing
        height = self.abci_app.current_round_height
        self.abci_app.update_time(current_time)
        assert height == self.abci_app.current_round_height

    def test_get_all_events(self) -> None:
        """Test the all events getter."""
        assert {"a", "b", "c", "timeout"} == self.abci_app.get_all_events()

    def test_cleanup(self) -> None:
        """Test the cleanup method."""
        self.abci_app.setup()

        # Dummy parameters, synchronized data and round
        cleanup_history_depth = 1
        start_history_depth = 5
        max_participants = 4
        dummy_synchronized_data = BaseSynchronizedData(
            db=AbciAppDB(setup_data=dict(participants=[max_participants]))
        )
        dummy_consensus_params = ConsensusParams(max_participants)
        dummy_round = ConcreteRoundA(dummy_synchronized_data, dummy_consensus_params)

        # Add dummy data
        self.abci_app._previous_rounds = [dummy_round] * start_history_depth
        self.abci_app._round_results = [dummy_synchronized_data] * start_history_depth
        self.abci_app.synchronized_data.db._data = {
            i: {"dummy_key": ["dummy_value"]} for i in range(start_history_depth)
        }

        round_height = self.abci_app.current_round_height
        # Verify that cleanup reduces the data amount
        assert len(self.abci_app._previous_rounds) == start_history_depth
        assert len(self.abci_app._round_results) == start_history_depth
        assert len(self.abci_app.synchronized_data.db._data) == start_history_depth
        assert list(self.abci_app.synchronized_data.db._data.keys()) == list(
            range(start_history_depth)
        )
        previous_reset_index = self.abci_app.synchronized_data.db.reset_index

        self.abci_app.cleanup(cleanup_history_depth)

        assert len(self.abci_app._previous_rounds) == cleanup_history_depth
        assert len(self.abci_app._round_results) == cleanup_history_depth
        assert len(self.abci_app.synchronized_data.db._data) == cleanup_history_depth
        assert list(self.abci_app.synchronized_data.db._data.keys()) == list(
            range(start_history_depth - cleanup_history_depth, start_history_depth)
        )
        # reset_index must not change after a cleanup
        assert self.abci_app.synchronized_data.db.reset_index == previous_reset_index

        # Verify round height stays unaffected
        assert self.abci_app.current_round_height == round_height

        # Add more values to the history
        reset_index = self.abci_app.synchronized_data.db.reset_index
        cleanup_history_depth_current = 3
        for _ in range(10):
            self.abci_app.synchronized_data.db.update(dummy_key="dummy_value")

        # Check that the history cleanup keeps the desired history length
        self.abci_app.cleanup_current_histories(cleanup_history_depth_current)
        history_len = len(
            self.abci_app.synchronized_data.db._data[reset_index]["dummy_key"]
        )
        assert history_len == cleanup_history_depth_current


class TestRoundSequence:
    """Test the RoundSequence class."""

    def setup(self) -> None:
        """Set up the test."""
        self.round_sequence = RoundSequence(abci_app_cls=AbciAppTest)
        self.round_sequence.setup(MagicMock(), MagicMock(), MagicMock())
        self.round_sequence.tm_height = 1

    @pytest.mark.parametrize("offset", tuple(range(5)))
    @pytest.mark.parametrize("n_blocks", (0, 1, 10))
    def test_height(self, n_blocks: int, offset: int) -> None:
        """Test 'height' property."""
        self.round_sequence._blockchain._blocks = [MagicMock() for _ in range(n_blocks)]
        self.round_sequence._blockchain._height_offset = offset
        assert self.round_sequence._blockchain.length == n_blocks
        assert self.round_sequence.height == n_blocks + offset

    def test_is_finished(self) -> None:
        """Test 'is_finished' property."""
        assert not self.round_sequence.is_finished
        self.round_sequence.abci_app._current_round = None
        assert self.round_sequence.is_finished

    def test_last_round(self) -> None:
        """Test 'last_round' property."""
        assert self.round_sequence.last_round_id is None

    def test_last_timestamp_none(self) -> None:
        """
        Test 'last_timestamp' property.

        The property is None because there are no blocks.
        """
        with pytest.raises(ABCIAppInternalError, match="last timestamp is None"):
            self.round_sequence.last_timestamp

    def test_last_timestamp(self) -> None:
        """Test 'last_timestamp' property, positive case."""
        seconds = 1
        nanoseconds = 1000
        expected_timestamp = datetime.datetime.fromtimestamp(
            seconds + nanoseconds / 10 ** 9
        )
        self.round_sequence._blockchain.add_block(
            Block(MagicMock(height=1, timestamp=expected_timestamp), [])
        )
        assert self.round_sequence.last_timestamp == expected_timestamp

    def test_abci_app_negative(self) -> None:
        """Test 'abci_app' property, negative case."""
        self.round_sequence._abci_app = None
        with pytest.raises(ABCIAppInternalError, match="AbciApp not set"):
            self.round_sequence.abci_app

    def test_check_is_finished_negative(self) -> None:
        """Test 'check_is_finished', negative case."""
        self.round_sequence.abci_app._current_round = None
        with pytest.raises(
            ValueError,
            match="round sequence is finished, cannot accept new transactions",
        ):
            self.round_sequence.check_is_finished()

    def test_current_round_positive(self) -> None:
        """Test 'current_round' property getter, positive case."""
        assert isinstance(self.round_sequence.current_round, ConcreteRoundA)

    def test_current_round_negative_current_round_not_set(self) -> None:
        """Test 'current_round' property getter, negative case (current round not set)."""
        self.round_sequence.abci_app._current_round = None
        with pytest.raises(ValueError, match="current_round not set!"):
            self.round_sequence.current_round

    def test_current_round_id(self) -> None:
        """Test 'current_round_id' property getter"""
        assert self.round_sequence.current_round_id == ConcreteRoundA.round_id

    def test_latest_result(self) -> None:
        """Test 'latest_result' property getter."""
        assert self.round_sequence.latest_synchronized_data

    @pytest.mark.parametrize("committed", (True, False))
    def test_last_round_transition_timestamp(self, committed: bool) -> None:
        """Test 'last_round_transition_timestamp' method."""
        if committed:
            self.round_sequence.begin_block(MagicMock(height=1))
            self.round_sequence.end_block()
            self.round_sequence.commit()
            assert (
                self.round_sequence.last_round_transition_timestamp
                == self.round_sequence._blockchain.last_block.timestamp
            )
        else:
            assert self.round_sequence._blockchain.height == 0
            with pytest.raises(
                ValueError,
                match="Trying to access `last_round_transition_timestamp` while no transition has been completed yet.",
            ):
                _ = self.round_sequence.last_round_transition_timestamp

    @pytest.mark.parametrize("committed", (True, False))
    def test_last_round_transition_height(self, committed: bool) -> None:
        """Test 'last_round_transition_height' method."""
        if committed:
            self.round_sequence.begin_block(MagicMock(height=1))
            self.round_sequence.end_block()
            self.round_sequence.commit()
            assert (
                self.round_sequence.last_round_transition_height
                == self.round_sequence._blockchain.height
                == 1
            )
        else:
            assert self.round_sequence._blockchain.height == 0
            with pytest.raises(
                ValueError,
                match="Trying to access `last_round_transition_height` while no transition has been completed yet.",
            ):
                _ = self.round_sequence.last_round_transition_height

    @pytest.mark.parametrize("round_count, reset_index", ((0, 0), (4, 2), (8, 1)))
    def test_last_round_transition_root_hash(
        self, round_count: int, reset_index: int
    ) -> None:
        """Test 'last_round_transition_height' method."""
        self.round_sequence.abci_app.synchronized_data.db.round_count = round_count  # type: ignore
        self.round_sequence.abci_app._reset_index = reset_index
        assert (
            self.round_sequence.last_round_transition_root_hash
            == f"root:{round_count}reset:{reset_index}".encode("utf-8")
        )

    @pytest.mark.parametrize("tm_height", (None, 1, 5))
    def test_last_round_transition_tm_height(self, tm_height: Optional[int]) -> None:
        """Test 'last_round_transition_height' method."""
        if tm_height is None:
            with pytest.raises(
                ValueError,
                match="Trying to access Tendermint's last round transition height before any `end_block` calls.",
            ):
                _ = self.round_sequence.last_round_transition_tm_height
        else:
            self.round_sequence.tm_height = tm_height
            self.round_sequence.begin_block(MagicMock(height=1))
            self.round_sequence.end_block()
            self.round_sequence.commit()
            assert self.round_sequence.last_round_transition_tm_height == tm_height

    @pytest.mark.parametrize("begin_height", tuple(range(0, 50, 10)))
    @pytest.mark.parametrize("initial_height", tuple(range(0, 11, 5)))
    def test_init_chain(self, begin_height: int, initial_height: int) -> None:
        """Test 'init_chain' method."""
        for i in range(begin_height):
            self.round_sequence._blockchain.add_block(
                MagicMock(header=MagicMock(height=i + 1))
            )
        assert self.round_sequence._blockchain.height == begin_height
        self.round_sequence.init_chain(initial_height)
        assert self.round_sequence._blockchain.height == initial_height - 1

    def test_begin_block_negative_is_finished(self) -> None:
        """Test 'begin_block' method, negative case (round sequence is finished)."""
        self.round_sequence.abci_app._current_round = None
        with pytest.raises(
            ABCIAppInternalError,
            match="internal error: round sequence is finished, cannot accept new blocks",
        ):
            self.round_sequence.begin_block(MagicMock())

    def test_begin_block_negative_wrong_phase(self) -> None:
        """Test 'begin_block' method, negative case (wrong phase)."""
        self.round_sequence._block_construction_phase = MagicMock()
        with pytest.raises(
            ABCIAppInternalError,
            match="internal error: cannot accept a 'begin_block' request.",
        ):
            self.round_sequence.begin_block(MagicMock())

    def test_begin_block_positive(self) -> None:
        """Test 'begin_block' method, positive case."""
        self.round_sequence.begin_block(MagicMock())

    def test_deliver_tx_negative_wrong_phase(self) -> None:
        """Test 'begin_block' method, negative (wrong phase)."""
        with pytest.raises(
            ABCIAppInternalError,
            match="internal error: cannot accept a 'deliver_tx' request",
        ):
            self.round_sequence.deliver_tx(MagicMock())

    def test_deliver_tx_positive_not_valid(self) -> None:
        """Test 'begin_block' method, positive (not valid)."""
        self.round_sequence.begin_block(MagicMock())
        with mock.patch.object(
            self.round_sequence.current_round, "check_transaction", return_value=True
        ):
            with mock.patch.object(
                self.round_sequence.current_round, "process_transaction"
            ):
                self.round_sequence.deliver_tx(MagicMock())

    def test_end_block_negative_wrong_phase(self) -> None:
        """Test 'end_block' method, negative case (wrong phase)."""
        with pytest.raises(
            ABCIAppInternalError,
            match="internal error: cannot accept a 'end_block' request.",
        ):
            self.round_sequence.end_block()

    def test_end_block_positive(self) -> None:
        """Test 'end_block' method, positive case."""
        self.round_sequence.begin_block(MagicMock())
        self.round_sequence.end_block()

    def test_commit_negative_wrong_phase(self) -> None:
        """Test 'end_block' method, negative case (wrong phase)."""
        with pytest.raises(
            ABCIAppInternalError,
            match="internal error: cannot accept a 'commit' request.",
        ):
            self.round_sequence.commit()

    def test_commit_negative_exception(self) -> None:
        """Test 'end_block' method, negative case (raise exception)."""
        self.round_sequence.begin_block(MagicMock(height=1))
        self.round_sequence.end_block()
        with mock.patch.object(
            self.round_sequence._blockchain, "add_block", side_effect=AddBlockError
        ):
            with pytest.raises(AddBlockError):
                self.round_sequence.commit()

    def test_commit_positive_no_change_round(self) -> None:
        """Test 'end_block' method, positive (no change round)."""
        self.round_sequence.begin_block(MagicMock(height=1))
        self.round_sequence.end_block()
        with mock.patch.object(
            self.round_sequence.current_round,
            "end_block",
            return_value=None,
        ):
            assert isinstance(self.round_sequence.current_round, ConcreteRoundA)

    def test_commit_positive_with_change_round(self) -> None:
        """Test 'end_block' method, positive (with change round)."""
        self.round_sequence.begin_block(MagicMock(height=1))
        self.round_sequence.end_block()
        round_result, next_round = MagicMock(), MagicMock()
        with mock.patch.object(
            self.round_sequence.current_round,
            "end_block",
            return_value=(round_result, next_round),
        ):
            self.round_sequence.commit()
        assert not isinstance(
            self.round_sequence.abci_app._current_round, ConcreteRoundA
        )
        assert self.round_sequence.latest_synchronized_data == round_result

    @pytest.mark.parametrize("is_replay", (True, False))
    def test_reset_blockchain(self, is_replay: bool) -> None:
        """Test `reset_blockchain` method."""
        self.round_sequence.reset_blockchain(is_replay)
        if is_replay:
            assert (
                self.round_sequence._block_construction_phase
                == RoundSequence._BlockConstructionState.WAITING_FOR_BEGIN_BLOCK
            )
        assert self.round_sequence._blockchain.height == 0


def test_meta_abci_app_when_instance_not_subclass_of_abstract_round() -> None:
    """
    Test instantiation of meta-class when instance not a subclass of AbciApp.

    Since the class is not a subclass of AbciApp, the checks performed by
    the meta-class should not apply.
    """

    class MyAbciApp(metaclass=_MetaAbciApp):
        pass


def test_meta_abci_app_when_final_round_not_subclass_of_degenerate_round() -> None:
    """Test instantiation of meta-class when a final round is not a subclass of DegenerateRound."""

    class FinalRound(AbstractRound):
        """A round class for testing."""

        def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Enum]]:
            pass

        def check_payload(self, payload: BaseTxPayload) -> None:
            pass

        def process_payload(self, payload: BaseTxPayload) -> None:
            pass

        round_id = "final_round"

    with pytest.raises(
        AEAEnforceError,
        match="non-final state.*must have at least one non-timeout transition",
    ):

        class MyAbciApp(AbciApp, metaclass=_MetaAbciApp):
            initial_round_cls: Type[AbstractRound] = ConcreteRoundA
            transition_function: Dict[
                Type[AbstractRound], Dict[str, Type[AbstractRound]]
            ] = {
                ConcreteRoundA: {"event": FinalRound, "timeout": ConcreteRoundA},
                FinalRound: {},
            }
            event_to_timeout = {"timeout": 1.0}
            final_states: Set[AppState] = set()
