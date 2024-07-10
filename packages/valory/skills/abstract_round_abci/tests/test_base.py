# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2024 Valory AG
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

import dataclasses
import datetime
import json
import logging
import re
import shutil
from abc import ABC
from calendar import timegm
from collections import deque
from contextlib import suppress
from copy import copy, deepcopy
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from time import sleep
from typing import (
    Any,
    Callable,
    Deque,
    Dict,
    FrozenSet,
    Generator,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    cast,
)
from unittest import mock
from unittest.mock import MagicMock

import pytest
from _pytest.logging import LogCaptureFixture
from aea.exceptions import AEAEnforceError
from aea_ledger_ethereum import EthereumCrypto
from hypothesis import HealthCheck, given, settings
from hypothesis.strategies import (
    DrawFn,
    binary,
    booleans,
    builds,
    composite,
    data,
    datetimes,
    dictionaries,
    floats,
    integers,
    just,
    lists,
    none,
    one_of,
    sampled_from,
    text,
)

import packages.valory.skills.abstract_round_abci.base as abci_base
from packages.valory.connections.abci.connection import MAX_READ_IN_BYTES
from packages.valory.protocols.abci.custom_types import (
    Evidence,
    EvidenceType,
    Evidences,
    LastCommitInfo,
    Timestamp,
    Validator,
    VoteInfo,
)
from packages.valory.skills.abstract_round_abci.base import (
    ABCIAppException,
    ABCIAppInternalError,
    AbciApp,
    AbciAppDB,
    AbciAppTransitionFunction,
    AbstractRound,
    AbstractRoundInternalError,
    AddBlockError,
    AppState,
    AvailabilityWindow,
    BaseSynchronizedData,
    BaseTxPayload,
    Block,
    BlockBuilder,
    Blockchain,
    CollectionRound,
    EventType,
    LateArrivingTransaction,
    OffenceStatus,
    OffenseStatusDecoder,
    OffenseStatusEncoder,
    OffenseType,
    RoundSequence,
    SignatureNotValidError,
    SlashingNotConfiguredError,
    Timeouts,
    Transaction,
    TransactionTypeNotRecognizedError,
    _MetaAbciApp,
    _MetaAbstractRound,
    _MetaPayload,
    get_name,
    light_offences,
    serious_offences,
)
from packages.valory.skills.abstract_round_abci.test_tools.abci_app import (
    AbciAppTest,
    ConcreteBackgroundRound,
    ConcreteBackgroundSlashingRound,
    ConcreteEvents,
    ConcreteRoundA,
    ConcreteRoundB,
    ConcreteRoundC,
    ConcreteSlashingRoundA,
    ConcreteTerminationRoundA,
    ConcreteTerminationRoundB,
    ConcreteTerminationRoundC,
    SlashingAppTest,
    TerminationAppTest,
)
from packages.valory.skills.abstract_round_abci.test_tools.rounds import (
    BaseRoundTestClass,
    get_participants,
)
from packages.valory.skills.abstract_round_abci.tests.conftest import profile_name


# pylint: skip-file


settings.load_profile(profile_name)


PACKAGE_DIR = Path(__file__).parent.parent


DUMMY_CONCRETE_BACKGROUND_PAYLOAD = ConcreteBackgroundRound.payload_class(
    sender="sender"
)


@pytest.fixture(scope="session", autouse=True)
def hypothesis_cleanup() -> Generator:
    """Fixture to remove hypothesis directory after tests."""
    yield
    hypothesis_dir = PACKAGE_DIR / ".hypothesis"
    if hypothesis_dir.exists():
        with suppress(OSError, PermissionError):
            shutil.rmtree(hypothesis_dir)


class BasePayload(BaseTxPayload, ABC):
    """Base payload class for testing."""


@dataclass(frozen=True)
class PayloadA(BasePayload):
    """Payload class for payload type 'A'."""


@dataclass(frozen=True)
class PayloadB(BasePayload):
    """Payload class for payload type 'B'."""


@dataclass(frozen=True)
class PayloadC(BasePayload):
    """Payload class for payload type 'C'."""


@dataclass(frozen=True)
class PayloadD(BasePayload):
    """Payload class for payload type 'D'."""


@dataclass(frozen=True)
class DummyPayload(BasePayload):
    """Dummy payload class."""

    dummy_attribute: int


@dataclass(frozen=True)
class TooBigPayload(BaseTxPayload):
    """Base payload class for testing."""

    dummy_field: str = "0" * 10**7


class ObjectImitator:
    """For custom __eq__ implementation testing"""

    def __init__(self, other: Any):
        """Copying references to class attr, and instance attr"""

        for attr, value in vars(other.__class__).items():
            if not attr.startswith("__") and not attr.endswith("__"):
                setattr(self.__class__, attr, value)

        self.__dict__ = other.__dict__


def test_base_tx_payload() -> None:
    """Test BaseTxPayload."""

    payload = PayloadA(sender="sender")
    object.__setattr__(payload, "round_count", 9)
    new_payload = payload.with_new_id()

    assert not payload == new_payload
    payload_data, new_payload_data = payload.json, new_payload.json
    assert not payload_data.pop("id_") == new_payload_data.pop("id_")
    assert payload_data == new_payload_data
    with pytest.raises(dataclasses.FrozenInstanceError):
        payload.round_count = 1  # type: ignore
    object.__setattr__(payload, "round_count", 1)
    assert payload.round_count == 1
    assert type(hash(payload)) == int


def test_meta_round_abstract_round_when_instance_not_subclass_of_abstract_round() -> (
    None
):
    """Test instantiation of meta class when instance not a subclass of abstract round."""

    class MyAbstractRound(metaclass=_MetaAbstractRound):
        pass


def test_abstract_round_instantiation_without_attributes_raises_error() -> None:
    """Test that definition of concrete subclass of AbstractRound without attributes raises error."""
    with pytest.raises(AbstractRoundInternalError):

        class MyRoundBehaviour(AbstractRound):
            pass

    with pytest.raises(AbstractRoundInternalError):

        class MyRoundBehaviourB(AbstractRound):
            synchronized_data_class = MagicMock()


class TestTransactions:
    """Test Transactions class."""

    def setup(self) -> None:
        """Set up the test."""
        self.old_value = copy(_MetaPayload.registry)

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

    def test_encode_too_big_payload(self) -> None:
        """Test encode of a too big payload."""
        sender = "sender"
        payload = TooBigPayload(sender)
        with pytest.raises(
            ValueError,
            match=f"{type(payload)} must be smaller than {MAX_READ_IN_BYTES} bytes",
        ):
            payload.encode()

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
        _MetaPayload.registry = self.old_value


@mock.patch(
    "aea.crypto.ledger_apis.LedgerApis.recover_message", return_value={"wrong_sender"}
)
def test_verify_transaction_negative_case(*_mocks: Any) -> None:
    """Test verify() of transaction, negative case."""
    transaction = Transaction(MagicMock(sender="right_sender", json={}), "")
    with pytest.raises(
        SignatureNotValidError, match="Signature not valid on transaction: .*"
    ):
        transaction.verify("")


@dataclass(frozen=True)
class SomeClass(BaseTxPayload):
    """Test class."""

    content: Dict


@given(
    dictionaries(
        keys=text(),
        values=one_of(floats(allow_nan=False, allow_infinity=False), booleans()),
    )
)
def test_payload_serializer_is_deterministic(obj: Any) -> None:
    """Test that 'DictProtobufStructSerializer' is deterministic."""
    obj_ = SomeClass(sender="", content=obj)
    obj_bytes = obj_.encode()
    assert obj_ == BaseTxPayload.decode(obj_bytes)


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

    def test_add_block_before_initial_height(self) -> None:
        """Test 'add_block', too old height."""
        height_offset = 42
        blockchain = Blockchain(height_offset=height_offset)
        block = Block(MagicMock(height=height_offset - 1), [])
        blockchain.add_block(block)

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


class TestAbciAppDB:
    """Test 'AbciAppDB' class."""

    def setup(self) -> None:
        """Set up the tests."""
        self.participants = ("a", "b")
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
    @pytest.mark.parametrize(
        "cross_period_persisted_keys, expected_cross_period_persisted_keys",
        ((None, set()), (set(), set()), ({"test"}, {"test"})),
    )
    def test_init(
        self,
        data: Dict,
        setup_data: Optional[Dict],
        cross_period_persisted_keys: Optional[Set[str]],
        expected_cross_period_persisted_keys: Set[str],
    ) -> None:
        """Test constructor."""
        # keys are a set, but we cast them to a frozenset, so we can still update them and also make `mypy`
        # think that the type is correct, to simulate a user incorrectly passing a different type and check if the
        # attribute can be altered
        cast_keys = cast(Optional[FrozenSet[str]], cross_period_persisted_keys)
        # update with the default keys
        expected_cross_period_persisted_keys.update(AbciAppDB.default_cross_period_keys)

        if setup_data is None:
            # the parametrization of `setup_data` set to `None` is in order to check if the exception is raised
            # when we incorrectly set the data in the configuration file with a type that is not allowed
            with pytest.raises(
                ValueError,
                match=re.escape(
                    f"AbciAppDB data must be `Dict[str, List[Any]]`, found `{type(data)}` instead"
                ),
            ):
                AbciAppDB(
                    data,
                )
            return

        # use copies because otherwise the arguments will be modified and the next test runs will be polluted
        data_copy = deepcopy(data)
        cross_period_persisted_keys_copy = cast_keys.copy() if cast_keys else cast_keys
        db = AbciAppDB(data_copy, cross_period_persisted_keys_copy)
        assert db._data == {0: setup_data}
        assert db.setup_data == setup_data
        assert db.cross_period_persisted_keys == expected_cross_period_persisted_keys

        def data_assertion() -> None:
            """Assert that the data are fine."""
            assert db._data == {0: setup_data} and db.setup_data == setup_data, (
                "The database's `setup_data` have been altered indirectly, "
                "by updating an item passed via the `__init__`!"
            )

        new_value_attempt = "new_value_attempt"
        data_copy.update({"dummy_key": [new_value_attempt]})
        data_assertion()

        data_copy["participants"].append(new_value_attempt)
        data_assertion()

        if cross_period_persisted_keys_copy:
            # cast back to set
            cast(Set[str], cross_period_persisted_keys_copy).add(new_value_attempt)
            assert (
                db.cross_period_persisted_keys == expected_cross_period_persisted_keys
            ), (
                "The database's `cross_period_persisted_keys` have been altered indirectly, "
                "by updating an item passed via the `__init__`!"
            )

    class EnumTest(Enum):
        """A test Enum class"""

        test = 10

    @pytest.mark.parametrize(
        "data_in, expected_output",
        (
            (0, 0),
            ([], []),
            ({"test": 2}, {"test": 2}),
            (EnumTest.test, 10),
            (b"test", b"test".hex()),
            ({3, 4}, "[3, 4]"),
            (object(), None),
        ),
    )
    def test_normalize(self, data_in: Any, expected_output: Any) -> None:
        """Test `normalize`."""
        if expected_output is None:
            with pytest.raises(ValueError):
                self.db.normalize(data_in)
            return
        assert self.db.normalize(data_in) == expected_output

    @pytest.mark.parametrize("data", {0: [{"test": 2}]})
    def test_reset_index(self, data: Dict) -> None:
        """Test `reset_index`."""
        assert self.db.reset_index == 0
        self.db.sync(self.db.serialize())
        assert self.db.reset_index == 0

    def test_round_count_setter(self) -> None:
        """Tests the round count setter."""
        expected_value = 1

        # assume the round count is 0 in the begging
        self.db._round_count = 0

        # update to one via the setter
        self.db.round_count = expected_value

        assert self.db.round_count == expected_value

    def test_try_alter_init_data(self) -> None:
        """Test trying to alter the init data."""
        data_key = "test"
        data_value = [data_key]
        expected_data = {data_key: data_value}
        passed_data = {data_key: data_value.copy()}
        db = AbciAppDB(passed_data)
        assert db.setup_data == expected_data

        mutability_error_message = (
            "The database's `setup_data` have been altered indirectly, "
            "by updating an item retrieved via the `setup_data` property!"
        )

        db.setup_data.update({data_key: ["altered"]})
        assert db.setup_data == expected_data, mutability_error_message

        db.setup_data[data_key].append("altered")
        assert db.setup_data == expected_data, mutability_error_message

    def test_cross_period_persisted_keys(self) -> None:
        """Test `cross_period_persisted_keys` property"""
        setup_data: Dict[str, List] = {}
        cross_period_persisted_keys = frozenset({"test"})
        db = AbciAppDB(setup_data, cross_period_persisted_keys.copy())

        assert isinstance(db.cross_period_persisted_keys, frozenset), (
            "The database's `cross_period_persisted_keys` can be altered indirectly. "
            "The `cross_period_persisted_keys` was expected to be a `frozenset`!"
        )

    def test_get(self) -> None:
        """Test getters."""
        assert self.db.get("participants", default="default") == self.participants
        assert self.db.get("inexistent", default="default") == "default"
        assert self.db.get_latest_from_reset_index(0) == {
            "participants": self.participants
        }
        assert self.db.get_latest() == {"participants": self.participants}

        mutable_key = "mutable"
        mutable_value = ["test"]
        self.db.update(**{mutable_key: mutable_value.copy()})
        mutable_getters = set()
        for getter, kwargs in (
            ("get", {"key": mutable_key}),
            ("get_strict", {"key": mutable_key}),
            ("get_latest_from_reset_index", {"reset_index": 0}),
            ("get_latest", {}),
        ):
            retrieved = getattr(self.db, getter)(**kwargs)
            if getter.startswith("get_latest"):
                retrieved = retrieved[mutable_key]
            retrieved.append("new_value_attempt")

            if self.db.get(mutable_key) != mutable_value:
                mutable_getters.add(getter)

        assert not mutable_getters, (
            "The database has been altered indirectly, "
            f"by updating the item(s) retrieved via the `{mutable_getters}` method(s)!"
        )

    def test_increment_round_count(self) -> None:
        """Test increment_round_count."""
        assert self.db.round_count == -1
        self.db.increment_round_count()
        assert self.db.round_count == 0

    @mock.patch.object(
        abci_base,
        "is_json_serializable",
        return_value=False,
    )
    def test_validate(self, _: mock._patch) -> None:
        """Test `validate` method."""
        data = "does not matter"

        with pytest.raises(
            ABCIAppInternalError,
            match=re.escape(
                "internal error: `AbciAppDB` data must be json-serializable. Please convert non-serializable data in "
                f"`{data}`. You may use `AbciAppDB.validate(your_data)` to validate your data for the `AbciAppDB`."
            ),
        ):
            AbciAppDB.validate(data)

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

        mutable_key = "mutable"
        mutable_value = ["test"]
        update_data = {mutable_key: mutable_value.copy()}
        db.update(**update_data)

        update_data[mutable_key].append("new_value_attempt")
        assert (
            db.get(mutable_key) == mutable_value
        ), "The database has been altered indirectly, by updating the item passed via the `update` method!"

    @pytest.mark.parametrize(
        "replacement_value, expected_replacement",
        (
            (132, 132),
            ("test", "test"),
            (set("132"), ("1", "2", "3")),
            ({"132"}, ("132",)),
            (frozenset("231"), ("1", "2", "3")),
            (frozenset({"231"}), ("231",)),
            (("1", "3", "2"), ("1", "3", "2")),
            (["1", "5", "3"], ["1", "5", "3"]),
        ),
    )
    @pytest.mark.parametrize(
        "setup_data, cross_period_persisted_keys",
        (
            (dict(), frozenset()),
            ({"test": [["test"]]}, frozenset()),
            ({"test": [["test"]]}, frozenset({"test"})),
            ({"test": ["test"]}, frozenset({"test"})),
        ),
    )
    def test_create(
        self,
        replacement_value: Any,
        expected_replacement: Any,
        setup_data: Dict,
        cross_period_persisted_keys: FrozenSet[str],
    ) -> None:
        """Test `create` db."""
        db = AbciAppDB(setup_data)
        db._cross_period_persisted_keys = cross_period_persisted_keys
        db.create()
        assert db._data == {
            0: setup_data,
            1: setup_data if cross_period_persisted_keys else {},
        }, "`create` did not produce the expected result!"

        mutable_key = "mutable"
        mutable_value = ["test"]
        existing_key = "test"
        create_data = {
            mutable_key: mutable_value.copy(),
            existing_key: replacement_value,
        }
        db.create(**create_data)

        assert db._data == {
            0: setup_data,
            1: setup_data if cross_period_persisted_keys else {},
            2: db.data_to_lists(
                {
                    mutable_key: mutable_value.copy(),
                    existing_key: expected_replacement,
                }
            ),
        }, "`create` did not produce the expected result!"

        create_data[mutable_key].append("new_value_attempt")
        assert (
            db.get(mutable_key) == mutable_value
        ), "The database has been altered indirectly, by updating the item passed via the `create` method!"

    def test_create_key_not_in_db(self) -> None:
        """Test the `create` method when a given or a cross-period key does not exist in the db."""
        existing_key = "existing_key"
        non_existing_key = "non_existing_key"

        db = AbciAppDB({existing_key: ["test_value"]})
        db._cross_period_persisted_keys = frozenset({non_existing_key})
        with pytest.raises(
            ABCIAppInternalError,
            match=f"Cross period persisted key `{non_existing_key}` "
            "was not found in the db but was required for the next period.",
        ):
            db.create()

        db._cross_period_persisted_keys = frozenset({existing_key})
        db.create(**{non_existing_key: "test_value"})

    @pytest.mark.parametrize(
        "existing_data, cleanup_history_depth, cleanup_history_depth_current, expected",
        (
            (
                {1: {"test": ["test", ["dummy_value1", "dummy_value2"]]}},
                0,
                None,
                {1: {"test": ["test", ["dummy_value1", "dummy_value2"]]}},
            ),
            (
                {
                    1: {"test": ["test", ["dummy_value1", "dummy_value2"]]},
                    2: {"test": [0]},
                },
                0,
                None,
                {2: {"test": [0]}},
            ),
            (
                {
                    1: {"test": ["test", ["dummy_value1", "dummy_value2"]]},
                    2: {"test": [0, 1, 2]},
                },
                0,
                0,
                {2: {"test": [0, 1, 2]}},
            ),
            (
                {
                    1: {"test": ["test", ["dummy_value1", "dummy_value2"]]},
                    2: {"test": [0, 1, 2]},
                },
                0,
                1,
                {2: {"test": [2]}},
            ),
            (
                {
                    1: {"test": ["test", ["dummy_value1", "dummy_value2"]]},
                    2: {"test": list(range(5))},
                    3: {"test": list(range(5, 10))},
                    4: {"test": list(range(10, 15))},
                    5: {"test": list(range(15, 20))},
                },
                3,
                0,
                {
                    3: {"test": list(range(5, 10))},
                    4: {"test": list(range(10, 15))},
                    5: {"test": list(range(15, 20))},
                },
            ),
            (
                {
                    1: {"test": ["test", ["dummy_value1", "dummy_value2"]]},
                    2: {"test": list(range(5))},
                    3: {"test": list(range(5, 10))},
                    4: {"test": list(range(10, 15))},
                    5: {"test": list(range(15, 20))},
                },
                5,
                3,
                {
                    1: {"test": ["test", ["dummy_value1", "dummy_value2"]]},
                    2: {"test": list(range(5))},
                    3: {"test": list(range(5, 10))},
                    4: {"test": list(range(10, 15))},
                    5: {"test": list(range(15 + 2, 20))},
                },
            ),
            (
                {
                    1: {"test": ["test", ["dummy_value1", "dummy_value2"]]},
                    2: {"test": list(range(5))},
                    3: {"test": list(range(5, 10))},
                    4: {"test": list(range(10, 15))},
                    5: {"test": list(range(15, 20))},
                },
                2,
                3,
                {
                    4: {"test": list(range(10, 15))},
                    5: {"test": list(range(15 + 2, 20))},
                },
            ),
            (
                {
                    1: {"test": ["test", ["dummy_value1", "dummy_value2"]]},
                    2: {"test": list(range(5))},
                    3: {"test": list(range(5, 10))},
                    4: {"test": list(range(10, 15))},
                    5: {"test": list(range(15, 20))},
                },
                0,
                1,
                {
                    5: {"test": [19]},
                },
            ),
        ),
    )
    def test_cleanup(
        self,
        existing_data: Dict[int, Dict[str, List[Any]]],
        cleanup_history_depth: int,
        cleanup_history_depth_current: Optional[int],
        expected: Dict[int, Dict[str, List[Any]]],
    ) -> None:
        """Test cleanup db."""
        db = AbciAppDB({})
        db._cross_period_persisted_keys = frozenset()
        for _, _data in existing_data.items():
            db._create_from_keys(**_data)

        db.cleanup(cleanup_history_depth, cleanup_history_depth_current)
        assert db._data == expected

    def test_serialize(self) -> None:
        """Test `serialize` method."""
        assert (
            self.db.serialize()
            == '{"db_data": {"0": {"participants": [["a", "b"]]}}, "slashing_config": ""}'
        )

    @pytest.mark.parametrize(
        "_data",
        ({"db_data": {0: {"test": [0]}}, "slashing_config": "serialized_config"},),
    )
    def test_sync(self, _data: Dict[str, Dict[int, Dict[str, List[Any]]]]) -> None:
        """Test `sync` method."""
        try:
            serialized_data = json.dumps(_data)
        except TypeError as exc:
            raise AssertionError(
                "Incorrectly parametrized test. Data must be json serializable."
            ) from exc

        self.db.sync(serialized_data)
        assert self.db._data == _data["db_data"]
        assert self.db.slashing_config == _data["slashing_config"]

    @pytest.mark.parametrize(
        "serialized_data, match",
        (
            (b"", "Could not decode data using "),
            (
                json.dumps({"both_mandatory_keys_missing": {}}),
                "internal error: Mandatory keys `db_data`, `slashing_config` are missing from the deserialized data: "
                "{'both_mandatory_keys_missing': {}}\nThe following serialized data were given: "
                '{"both_mandatory_keys_missing": {}}',
            ),
            (
                json.dumps({"db_data": {}}),
                "internal error: Mandatory keys `db_data`, `slashing_config` are missing from the deserialized data: "
                "{'db_data': {}}\nThe following serialized data were given: {\"db_data\": {}}",
            ),
            (
                json.dumps({"slashing_config": {}}),
                "internal error: Mandatory keys `db_data`, `slashing_config` are missing from the deserialized data: "
                "{'slashing_config': {}}\nThe following serialized data were given: {\"slashing_config\": {}}",
            ),
            (
                json.dumps(
                    {"db_data": {"invalid_index": {}}, "slashing_config": "anything"}
                ),
                "An invalid index was found while trying to sync the db using data: ",
            ),
            (
                json.dumps({"db_data": "invalid", "slashing_config": "anything"}),
                "Could not decode db data with an invalid format: ",
            ),
        ),
    )
    def test_sync_incorrect_data(self, serialized_data: Any, match: str) -> None:
        """Test `sync` method with incorrect data."""
        with pytest.raises(
            ABCIAppInternalError,
            match=match,
        ):
            self.db.sync(serialized_data)

    def test_hash(self) -> None:
        """Test `hash` method."""
        expected_hash = (
            b"\xd0^\xb0\x85\xf1\xf5\xd2\xe8\xe8\x85\xda\x1a\x99k"
            b"\x1c\xde\xfa1\x8a\x87\xcc\xd7q?\xdf\xbbofz\xfb\x7fI"
        )
        assert self.db.hash() == expected_hash


class TestBaseSynchronizedData:
    """Test 'BaseSynchronizedData' class."""

    def setup(self) -> None:
        """Set up the tests."""
        self.participants = ("a", "b")
        self.base_synchronized_data = BaseSynchronizedData(
            db=AbciAppDB(setup_data=dict(participants=[self.participants]))
        )

    @given(text())
    def test_slashing_config(self, slashing_config: str) -> None:
        """Test the `slashing_config` property."""
        self.base_synchronized_data.slashing_config = slashing_config
        assert (
            self.base_synchronized_data.slashing_config
            == self.base_synchronized_data.db.slashing_config
            == slashing_config
        )

    def test_participants_getter_positive(self) -> None:
        """Test 'participants' property getter."""
        assert frozenset(self.participants) == self.base_synchronized_data.participants

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
        participants = ("a",)
        expected = BaseSynchronizedData(
            db=AbciAppDB(setup_data=dict(participants=[participants]))
        )
        actual = self.base_synchronized_data.update(participants=participants)
        assert expected.participants == actual.participants
        assert actual.db._data == {0: {"participants": [("a", "b"), ("a",)]}}

    def test_create(self) -> None:
        """Test the 'create' method."""
        self.base_synchronized_data.db._cross_period_persisted_keys = frozenset(
            {"participants"}
        )
        assert self.base_synchronized_data.db._data == {
            0: {"participants": [("a", "b")]}
        }
        actual = self.base_synchronized_data.create()
        assert actual.db._data == {
            0: {"participants": [("a", "b")]},
            1: {"participants": [("a", "b")]},
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
            db=AbciAppDB(setup_data=dict(participants=[tuple()]))
        )
        with pytest.raises(ValueError, match="List participants cannot be empty."):
            _ = base_synchronized_data.participants

    def test_all_participants_list_is_empty(
        self,
    ) -> None:
        """Tets when participants list is set to zero."""
        base_synchronized_data = BaseSynchronizedData(
            db=AbciAppDB(setup_data=dict(all_participants=[tuple()]))
        )
        with pytest.raises(ValueError, match="List participants cannot be empty."):
            _ = base_synchronized_data.all_participants

    @pytest.mark.parametrize(
        "n_participants, given_threshold, expected_threshold",
        (
            (1, None, 1),
            (5, None, 4),
            (10, None, 7),
            (345, None, 231),
            (246236, None, 164158),
            (1, 1, 1),
            (5, 5, 5),
            (10, 7, 7),
            (10, 8, 8),
            (10, 9, 9),
            (10, 10, 10),
            (345, 300, 300),
            (246236, 194158, 194158),
        ),
    )
    def test_consensus_threshold(
        self, n_participants: int, given_threshold: int, expected_threshold: int
    ) -> None:
        """Test the `consensus_threshold` property."""
        base_synchronized_data = BaseSynchronizedData(
            db=AbciAppDB(
                setup_data=dict(
                    all_participants=[tuple(range(n_participants))],
                    consensus_threshold=[given_threshold],
                )
            )
        )

        assert base_synchronized_data.consensus_threshold == expected_threshold

    @pytest.mark.parametrize(
        "n_participants, given_threshold",
        (
            (1, 2),
            (5, 2),
            (10, 4),
            (10, 11),
            (10, 18),
            (345, 200),
            (246236, 164157),
            (246236, 246237),
        ),
    )
    def test_consensus_threshold_incorrect(
        self,
        n_participants: int,
        given_threshold: int,
    ) -> None:
        """Test the `consensus_threshold` property when an incorrect threshold value has been inserted to the db."""
        base_synchronized_data = BaseSynchronizedData(
            db=AbciAppDB(
                setup_data=dict(
                    all_participants=[tuple(range(n_participants))],
                    consensus_threshold=[given_threshold],
                )
            )
        )

        with pytest.raises(ValueError, match="Consensus threshold "):
            _ = base_synchronized_data.consensus_threshold

    def test_properties(self) -> None:
        """Test several properties"""
        participants = ["b", "a"]
        randomness_str = (
            "3439d92d58e47d342131d446a3abe264396dd264717897af30525c98408c834f"
        )
        randomness_value = 0.20400769574270503
        most_voted_keeper_address = "most_voted_keeper_address"
        blacklisted_keepers = "blacklisted_keepers"
        participant_to_selection = participant_to_randomness = participant_to_votes = {
            "sender": DummyPayload(sender="sender", dummy_attribute=0)
        }
        safe_contract_address = "0x0"

        base_synchronized_data = BaseSynchronizedData(
            db=AbciAppDB(
                setup_data=AbciAppDB.data_to_lists(
                    dict(
                        participants=participants,
                        all_participants=participants,
                        most_voted_randomness=randomness_str,
                        most_voted_keeper_address=most_voted_keeper_address,
                        blacklisted_keepers=blacklisted_keepers,
                        participant_to_selection=CollectionRound.serialize_collection(
                            participant_to_selection
                        ),
                        participant_to_randomness=CollectionRound.serialize_collection(
                            participant_to_randomness
                        ),
                        participant_to_votes=CollectionRound.serialize_collection(
                            participant_to_votes
                        ),
                        safe_contract_address=safe_contract_address,
                    )
                )
            )
        )
        assert self.base_synchronized_data.period_count == 0
        assert base_synchronized_data.all_participants == frozenset(participants)
        assert base_synchronized_data.sorted_participants == ["a", "b"]
        assert base_synchronized_data.max_participants == len(participants)
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
        assert base_synchronized_data.safe_contract_address == safe_contract_address


class DummyConcreteRound(AbstractRound):
    """A dummy concrete round's implementation."""

    payload_class: Optional[Type[BaseTxPayload]] = None
    synchronized_data_class = MagicMock()
    payload_attribute = MagicMock()

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, EventType]]:
        """A dummy `end_block` implementation."""

    def check_payload(self, payload: BaseTxPayload) -> None:
        """A dummy `check_payload` implementation."""

    def process_payload(self, payload: BaseTxPayload) -> None:
        """A dummy `process_payload` implementation."""


class TestAbstractRound:
    """Test the 'AbstractRound' class."""

    def setup(self) -> None:
        """Set up the tests."""
        self.known_payload_type = ConcreteRoundA.payload_class
        self.participants = ("a", "b")
        self.base_synchronized_data = BaseSynchronizedData(
            db=AbciAppDB(
                setup_data=dict(
                    all_participants=[self.participants],
                    participants=[self.participants],
                    consensus_threshold=[2],
                )
            )
        )
        self.round = ConcreteRoundA(self.base_synchronized_data, MagicMock())

    def test_auto_round_id(self) -> None:
        """Test that the 'auto_round_id()' method works as expected."""

        assert DummyConcreteRound.auto_round_id() == "dummy_concrete_round"

    def test_must_not_set_round_id(self) -> None:
        """Test that the 'round_id' must be set in concrete classes."""

        # no exception as round id is auto-assigned
        my_concrete_round = DummyConcreteRound(MagicMock(), MagicMock())
        assert my_concrete_round.round_id == "dummy_concrete_round"

    def test_must_set_payload_class_type(self) -> None:
        """Test that the 'payload_class' must be set in concrete classes."""

        with pytest.raises(
            AbstractRoundInternalError, match="'payload_class' not set on .*"
        ):

            class MyConcreteRound(AbstractRound):
                synchronized_data_class = MagicMock()
                payload_attribute = MagicMock()
                # here payload_class is missing

    def test_check_payload_type_with_previous_round_transaction(self) -> None:
        """Test check 'check_payload_type'."""

        class MyConcreteRound(DummyConcreteRound):
            """A concrete round with the payload class defined."""

            payload_class = BaseTxPayload

        with pytest.raises(LateArrivingTransaction):
            MyConcreteRound(MagicMock(), MagicMock(), BaseTxPayload).check_payload_type(
                MagicMock(payload=BaseTxPayload("dummy"))
            )

    def test_check_payload_type(self) -> None:
        """Test check 'check_payload_type'."""

        with pytest.raises(
            TransactionTypeNotRecognizedError,
            match="current round does not allow transactions",
        ):
            DummyConcreteRound(MagicMock(), MagicMock()).check_payload_type(MagicMock())

    def test_synchronized_data_getter(self) -> None:
        """Test 'synchronized_data' property getter."""
        state = self.round.synchronized_data
        assert state.participants == frozenset(self.participants)

    def test_check_transaction_unknown_payload(self) -> None:
        """Test 'check_transaction' method, with unknown payload type."""
        tx_type = "unknown_payload"
        tx_mock = MagicMock()
        tx_mock.payload_class = tx_type
        with pytest.raises(
            TransactionTypeNotRecognizedError,
            match="request '.*' not recognized",
        ):
            self.round.check_transaction(tx_mock)

    def test_check_transaction_known_payload(self) -> None:
        """Test 'check_transaction' method, with known payload type."""
        tx_mock = MagicMock()
        tx_mock.payload = self.known_payload_type(sender="dummy")
        self.round.check_transaction(tx_mock)

    def test_process_transaction_negative_unknown_payload(self) -> None:
        """Test 'process_transaction' method, with unknown payload type."""
        tx_mock = MagicMock()
        tx_mock.payload = object
        with pytest.raises(
            TransactionTypeNotRecognizedError,
            match="request '.*' not recognized",
        ):
            self.round.process_transaction(tx_mock)

    def test_process_transaction_negative_check_transaction_fails(self) -> None:
        """Test 'process_transaction' method, with 'check_transaction' failing."""
        tx_mock = MagicMock()
        tx_mock.payload = object
        error_message = "transaction not valid"
        with mock.patch.object(
            self.round, "check_payload_type", side_effect=ValueError(error_message)
        ):
            with pytest.raises(ValueError, match=error_message):
                self.round.process_transaction(tx_mock)

    def test_process_transaction_positive(self) -> None:
        """Test 'process_transaction' method, positive case."""
        tx_mock = MagicMock()
        tx_mock.payload = BaseTxPayload(sender="dummy")
        self.round.process_transaction(tx_mock)

    def test_check_majority_possible_raises_error_when_nb_participants_is_0(
        self,
    ) -> None:
        """Check that 'check_majority_possible' raises error when nb_participants=0."""
        with pytest.raises(
            ABCIAppInternalError,
            match="nb_participants not consistent with votes_by_participants",
        ):
            DummyConcreteRound(
                self.base_synchronized_data, MagicMock()
            ).check_majority_possible({}, 0)

    def test_check_majority_possible_passes_when_vote_set_is_empty(self) -> None:
        """Check that 'check_majority_possible' passes when the set of votes is empty."""
        DummyConcreteRound(
            self.base_synchronized_data, MagicMock()
        ).check_majority_possible({}, 1)

    def test_check_majority_possible_passes_when_vote_set_nonempty_and_check_passes(
        self,
    ) -> None:
        """
        Check that 'check_majority_possible' passes when set of votes is non-empty.

        The check passes because:
        - the threshold is 2
        - the other voter can vote for the same item of the first voter
        """
        DummyConcreteRound(
            self.base_synchronized_data, MagicMock()
        ).check_majority_possible({"alice": DummyPayload("alice", True)}, 2)

    def test_check_majority_possible_passes_when_payload_attributes_majority_match(
        self,
    ) -> None:
        """
        Test 'check_majority_possible' when set of votes is non-empty and the majority of the attribute values match.

        The check passes because:
        - the threshold is 3 (participants are 4)
        - 3 voters have the same attribute value in their payload
        """
        DummyConcreteRound(
            self.base_synchronized_data, MagicMock()
        ).check_majority_possible(
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
            DummyConcreteRound(
                self.base_synchronized_data, MagicMock()
            ).check_majority_possible(
                {
                    "alice": DummyPayload("alice", False),
                    "bob": DummyPayload("bob", True),
                },
                2,
            )

    def test_is_majority_possible_positive_case(self) -> None:
        """Test 'is_majority_possible', positive case."""
        assert DummyConcreteRound(
            self.base_synchronized_data, MagicMock()
        ).is_majority_possible({"alice": DummyPayload("alice", False)}, 2)

    def test_is_majority_possible_negative_case(self) -> None:
        """Test 'is_majority_possible', negative case."""
        assert not DummyConcreteRound(
            self.base_synchronized_data, MagicMock()
        ).is_majority_possible(
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
            DummyConcreteRound(
                self.base_synchronized_data,
                MagicMock(),
            ).check_majority_possible_with_new_voter(
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
            DummyConcreteRound(
                self.base_synchronized_data,
                MagicMock(),
            ).check_majority_possible_with_new_voter(
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
        DummyConcreteRound(
            self.base_synchronized_data,
            MagicMock(),
        ).check_majority_possible_with_new_voter(
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


STUB_TERMINATION_CONFIG = abci_base.BackgroundAppConfig(
    round_cls=ConcreteBackgroundRound,
    start_event=ConcreteEvents.TERMINATE,
    abci_app=TerminationAppTest,
)

STUB_SLASH_CONFIG = abci_base.BackgroundAppConfig(
    round_cls=ConcreteBackgroundSlashingRound,
    start_event=ConcreteEvents.SLASH_START,
    end_event=ConcreteEvents.SLASH_END,
    abci_app=SlashingAppTest,
)


class TestAbciApp:
    """Test the 'AbciApp' class."""

    def setup(self) -> None:
        """Set up the test."""
        self.abci_app = AbciAppTest(MagicMock(), MagicMock(), MagicMock())
        self.abci_app.add_background_app(STUB_TERMINATION_CONFIG)

    def teardown(self) -> None:
        """Teardown the test."""
        self.abci_app.background_apps.clear()

    @pytest.mark.parametrize("flag", (True, False))
    def test_is_abstract(self, flag: bool) -> None:
        """Test `is_abstract` property."""

        class CopyOfAbciApp(AbciAppTest):
            """Copy to avoid side effects due to state change"""

        CopyOfAbciApp._is_abstract = flag
        assert CopyOfAbciApp.is_abstract() is flag

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

    @pytest.mark.parametrize(
        "db_key, sync_classes, default, property_found",
        (
            ("", set(), "default", False),
            ("non_existing_key", {BaseSynchronizedData}, True, False),
            ("participants", {BaseSynchronizedData}, {}, False),
            ("is_keeper_set", {BaseSynchronizedData}, True, True),
        ),
    )
    def test_get_synced_value(
        self,
        db_key: str,
        sync_classes: Set[Type[BaseSynchronizedData]],
        default: Any,
        property_found: bool,
    ) -> None:
        """Test the `_get_synced_value` method."""
        res = self.abci_app._get_synced_value(db_key, sync_classes, default)
        if property_found:
            assert res == getattr(self.abci_app.synchronized_data, db_key)
            return
        assert res == self.abci_app.synchronized_data.db.get(db_key, default)

    def test_process_event(self) -> None:
        """Test the 'process_event' method, positive case, with timeout events."""
        self.abci_app.add_background_app(STUB_SLASH_CONFIG)
        self.abci_app.setup()
        self.abci_app._last_timestamp = MagicMock()
        assert self.abci_app._transition_backup.transition_function is None
        assert isinstance(self.abci_app.current_round, ConcreteRoundA)
        self.abci_app.process_event(ConcreteEvents.B)
        assert isinstance(self.abci_app.current_round, ConcreteRoundB)
        self.abci_app.process_event(ConcreteEvents.TIMEOUT)
        assert isinstance(self.abci_app.current_round, ConcreteRoundA)
        self.abci_app.process_event(ConcreteEvents.TERMINATE)
        assert isinstance(self.abci_app.current_round, ConcreteTerminationRoundA)
        expected_backup = deepcopy(self.abci_app.transition_function)
        assert (
            self.abci_app._transition_backup.transition_function
            == AbciAppTest.transition_function
        )
        self.abci_app.process_event(ConcreteEvents.SLASH_START)
        assert isinstance(self.abci_app.current_round, ConcreteSlashingRoundA)
        assert (
            self.abci_app._transition_backup.transition_function
            == expected_backup
            == TerminationAppTest.transition_function
        )
        assert self.abci_app.transition_function == SlashingAppTest.transition_function
        self.abci_app.process_event(ConcreteEvents.SLASH_END)
        # should return back to the round that was running before the slashing started
        assert isinstance(self.abci_app.current_round, ConcreteTerminationRoundA)
        assert self.abci_app.transition_function == expected_backup
        assert self.abci_app._transition_backup.transition_function is None
        assert self.abci_app._transition_backup.round is None

    def test_process_event_negative_case(self) -> None:
        """Test the 'process_event' method, negative case."""
        with mock.patch.object(self.abci_app.logger, "warning") as mock_warning:
            self.abci_app.process_event(ConcreteEvents.A)
            mock_warning.assert_called_with(
                "Cannot process event 'a' as current state is not set"
            )

    def test_update_time(self) -> None:
        """Test the 'update_time' method."""
        # schedule round_a
        current_time = datetime.datetime.now()
        self.abci_app.setup()
        self.abci_app._last_timestamp = current_time

        # move to round_b that schedules timeout events
        self.abci_app.process_event(ConcreteEvents.B)
        assert self.abci_app.current_round_id == "concrete_round_b"

        # simulate most recent timestamp beyond earliest deadline
        # after pop, len(timeouts) == 0, because round_a does not schedule new timeout events
        current_time = current_time + datetime.timedelta(0, AbciAppTest.TIMEOUT)
        self.abci_app.update_time(current_time)

        # now we are back to round_a
        assert self.abci_app.current_round_id == "concrete_round_a"

        # move to round_c that schedules timeout events to itself
        self.abci_app.process_event(ConcreteEvents.C)
        assert self.abci_app.current_round_id == "concrete_round_c"

        # simulate most recent timestamp beyond earliest deadline
        # after pop, len(timeouts) == 0, because round_c schedules timeout events
        current_time = current_time + datetime.timedelta(0, AbciAppTest.TIMEOUT)
        self.abci_app.update_time(current_time)

        assert self.abci_app.current_round_id == "concrete_round_c"

        # further update changes nothing
        height = self.abci_app.current_round_height
        self.abci_app.update_time(current_time)
        assert height == self.abci_app.current_round_height

    def test_get_all_events(self) -> None:
        """Test the all events getter."""
        assert {
            ConcreteEvents.A,
            ConcreteEvents.B,
            ConcreteEvents.C,
            ConcreteEvents.TIMEOUT,
        } == self.abci_app.get_all_events()

    @pytest.mark.parametrize("include_background_rounds", (True, False))
    def test_get_all_rounds_classes(
        self,
        include_background_rounds: bool,
    ) -> None:
        """Test the get all rounds getter."""
        expected_rounds = {ConcreteRoundA, ConcreteRoundB, ConcreteRoundC}

        if include_background_rounds:
            expected_rounds.update(
                {
                    ConcreteBackgroundRound,
                    ConcreteTerminationRoundA,
                    ConcreteTerminationRoundB,
                    ConcreteTerminationRoundC,
                }
            )

        actual_rounds = self.abci_app.get_all_round_classes(
            {ConcreteBackgroundRound}, include_background_rounds
        )

        assert actual_rounds == expected_rounds

    def test_get_all_rounds_classes_bg_ever_running(
        self,
    ) -> None:
        """Test the get all rounds when the background round is of an ever running type."""
        # we clear the pre-existing bg apps and add an ever running
        self.abci_app.background_apps.clear()
        self.abci_app.add_background_app(
            abci_base.BackgroundAppConfig(ConcreteBackgroundRound)
        )
        include_background_rounds = True
        expected_rounds = {
            ConcreteRoundA,
            ConcreteRoundB,
            ConcreteRoundC,
        }
        assert expected_rounds == self.abci_app.get_all_round_classes(
            {ConcreteBackgroundRound}, include_background_rounds
        )

    def test_add_background_app(self) -> None:
        """Tests the add method for the background apps."""
        # remove the terminating bg round added in `setup()` and the pending offences bg app added in the metaclass
        self.abci_app.background_apps.clear()

        class EmptyAbciApp(AbciAppTest):
            """An AbciApp without background apps' attributes set."""

            cross_period_persisted_keys = frozenset({"1", "2"})

        class BackgroundAbciApp(AbciAppTest):
            """A mock background AbciApp."""

            cross_period_persisted_keys = frozenset({"2", "3"})

        assert len(EmptyAbciApp.background_apps) == 0
        assert EmptyAbciApp.cross_period_persisted_keys == {"1", "2"}
        # add the background app
        bg_app_config = abci_base.BackgroundAppConfig(
            round_cls=ConcreteBackgroundRound,
            start_event=ConcreteEvents.TERMINATE,
            abci_app=BackgroundAbciApp,
        )
        EmptyAbciApp.add_background_app(bg_app_config)
        assert len(EmptyAbciApp.background_apps) == 1
        assert EmptyAbciApp.cross_period_persisted_keys == {"1", "2", "3"}

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
        dummy_round = ConcreteRoundA(dummy_synchronized_data, MagicMock())

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

    @mock.patch.object(ConcreteBackgroundRound, "check_transaction")
    @pytest.mark.parametrize(
        "transaction",
        [mock.MagicMock(payload=DUMMY_CONCRETE_BACKGROUND_PAYLOAD)],
    )
    def test_check_transaction_for_termination_round(
        self,
        check_transaction_mock: mock.Mock,
        transaction: Transaction,
    ) -> None:
        """Tests process_transaction when it's a transaction meant for the termination app."""
        self.abci_app.setup()
        self.abci_app.check_transaction(transaction)
        check_transaction_mock.assert_called_with(transaction)

    @mock.patch.object(ConcreteBackgroundRound, "process_transaction")
    @pytest.mark.parametrize(
        "transaction",
        [mock.MagicMock(payload=DUMMY_CONCRETE_BACKGROUND_PAYLOAD)],
    )
    def test_process_transaction_for_termination_round(
        self,
        process_transaction_mock: mock.Mock,
        transaction: Transaction,
    ) -> None:
        """Tests process_transaction when it's a transaction meant for the termination app."""
        self.abci_app.setup()
        self.abci_app.process_transaction(transaction)
        process_transaction_mock.assert_called_with(transaction)


class TestOffenceTypeFns:
    """Test `OffenceType`-related functions."""

    @staticmethod
    def test_light_offences() -> None:
        """Test `light_offences` function."""
        assert list(light_offences()) == [
            OffenseType.VALIDATOR_DOWNTIME,
            OffenseType.INVALID_PAYLOAD,
            OffenseType.BLACKLISTED,
            OffenseType.SUSPECTED,
        ]

    @staticmethod
    def test_serious_offences() -> None:
        """Test `serious_offences` function."""
        assert list(serious_offences()) == [
            OffenseType.UNKNOWN,
            OffenseType.DOUBLE_SIGNING,
            OffenseType.LIGHT_CLIENT_ATTACK,
        ]


@composite
def availability_window_data(draw: DrawFn) -> Dict[str, int]:
    """A strategy for building valid availability window data."""
    max_length = draw(integers(min_value=1, max_value=12_000))
    array = draw(integers(min_value=0, max_value=(2**max_length) - 1))
    num_positive = draw(integers(min_value=0, max_value=1_000_000))
    num_negative = draw(integers(min_value=0, max_value=1_000_000))

    return {
        "max_length": max_length,
        "array": array,
        "num_positive": num_positive,
        "num_negative": num_negative,
    }


class TestAvailabilityWindow:
    """Test `AvailabilityWindow`."""

    @staticmethod
    @given(integers(min_value=1, max_value=100))
    def test_not_equal(max_length: int) -> None:
        """Test the `add` method."""
        availability_window_1 = AvailabilityWindow(max_length)
        availability_window_2 = AvailabilityWindow(max_length)
        assert availability_window_1 == availability_window_2
        availability_window_2.add(False)
        assert availability_window_1 != availability_window_2
        # test with a different type
        assert availability_window_1 != MagicMock()

    @staticmethod
    @given(integers(min_value=0, max_value=100), data())
    def test_add(max_length: int, hypothesis_data: Any) -> None:
        """Test the `add` method."""
        if max_length < 1:
            with pytest.raises(
                ValueError,
                match=f"An `AvailabilityWindow` with a `max_length` {max_length} < 1 is not valid.",
            ):
                AvailabilityWindow(max_length)
            return

        availability_window = AvailabilityWindow(max_length)

        expected_positives = expected_negatives = 0
        for i in range(max_length):
            value = hypothesis_data.draw(booleans())
            availability_window.add(value)
            items_in = i + 1
            assert len(availability_window._window) == items_in
            assert availability_window._window[-1] is value
            expected_positives += 1 if value else 0
            assert availability_window._num_positive == expected_positives
            expected_negatives = items_in - expected_positives
            assert availability_window._num_negative == expected_negatives

        # max length is reached and window starts cycling
        assert len(availability_window._window) == max_length
        for _ in range(10):
            value = hypothesis_data.draw(booleans())
            expected_popped_value = (
                None if max_length == 0 else availability_window._window[0]
            )
            availability_window.add(value)
            assert len(availability_window._window) == max_length
            if expected_popped_value is not None:
                expected_positives -= bool(expected_popped_value)
                expected_negatives -= bool(not expected_popped_value)
            expected_positives += bool(value)
            expected_negatives += bool(not value)
            assert availability_window._num_positive == expected_positives
            assert availability_window._num_negative == expected_negatives

    @staticmethod
    @given(
        max_length=integers(min_value=1, max_value=30_000),
        num_positive=integers(min_value=0),
        num_negative=integers(min_value=0),
    )
    @pytest.mark.parametrize(
        "window, expected_serialization",
        (
            (deque(()), 0),
            (deque((False, False, False)), 0),
            (deque((True, False, True)), 5),
            (deque((True for _ in range(3))), 7),
            (
                deque((True for _ in range(1000))),
                int(
                    "10715086071862673209484250490600018105614048117055336074437503883703510511249361224931983788156958"
                    "58127594672917553146825187145285692314043598457757469857480393456777482423098542107460506237114187"
                    "79541821530464749835819412673987675591655439460770629145711964776865421676604298316526243868372056"
                    "68069375"
                ),
            ),
        ),
    )
    def test_to_dict(
        max_length: int,
        num_positive: int,
        num_negative: int,
        window: Deque,
        expected_serialization: int,
    ) -> None:
        """Test `to_dict` method."""
        availability_window = AvailabilityWindow(max_length)
        availability_window._num_positive = num_positive
        availability_window._num_negative = num_negative
        availability_window._window = window
        assert availability_window.to_dict() == {
            "max_length": max_length,
            "array": expected_serialization,
            "num_positive": num_positive,
            "num_negative": num_negative,
        }

    @staticmethod
    @pytest.mark.parametrize(
        "data_, key, validator, expected_error",
        (
            ({"a": 1, "b": 2, "c": 3}, "a", lambda x: x > 0, None),
            (
                {"a": 1, "b": 2, "c": 3},
                "d",
                lambda x: x > 0,
                r"Missing required key: d\.",
            ),
            (
                {"a": "1", "b": 2, "c": 3},
                "a",
                lambda x: x > 0,
                r"a must be of type int\.",
            ),
            (
                {"a": -1, "b": 2, "c": 3},
                "a",
                lambda x: x > 0,
                r"a has invalid value -1\.",
            ),
        ),
    )
    def test_validate_key(
        data_: dict, key: str, validator: Callable, expected_error: Optional[str]
    ) -> None:
        """Test the `_validate_key` method."""
        if expected_error:
            with pytest.raises(ValueError, match=expected_error):
                AvailabilityWindow._validate_key(data_, key, validator)
        else:
            AvailabilityWindow._validate_key(data_, key, validator)

    @staticmethod
    @pytest.mark.parametrize(
        "data_, error_regex",
        (
            ("not a dict", r"Expected dict, got"),
            (
                {"max_length": -1, "array": 42, "num_positive": 10, "num_negative": 0},
                r"max_length",
            ),
            (
                {"max_length": 2, "array": 4, "num_positive": 10, "num_negative": 0},
                r"array",
            ),
            (
                {"max_length": 8, "array": 42, "num_positive": -1, "num_negative": 0},
                r"num_positive",
            ),
            (
                {"max_length": 8, "array": 42, "num_positive": 10, "num_negative": -1},
                r"num_negative",
            ),
        ),
    )
    def test_validate_negative(data_: dict, error_regex: str) -> None:
        """Negative tests for the `_validate` method."""
        with pytest.raises((TypeError, ValueError), match=error_regex):
            AvailabilityWindow._validate(data_)

    @staticmethod
    @given(availability_window_data())
    def test_validate_positive(data_: Dict[str, int]) -> None:
        """Positive tests for the `_validate` method."""
        AvailabilityWindow._validate(data_)

    @staticmethod
    @given(availability_window_data())
    def test_from_dict(data_: Dict[str, int]) -> None:
        """Test `from_dict` method."""
        availability_window = AvailabilityWindow.from_dict(data_)

        # convert the serialized array to a binary string
        binary_number = bin(data_["array"])[2:]
        # convert each character in the binary string to a flag
        flags = [bool(int(digit)) for digit in binary_number]
        expected_window = deque(flags, maxlen=data_["max_length"])

        assert availability_window._max_length == data_["max_length"]
        assert availability_window._window == expected_window
        assert availability_window._num_positive == data_["num_positive"]
        assert availability_window._num_negative == data_["num_negative"]

    @staticmethod
    @given(availability_window_data())
    def test_to_dict_and_back(data_: Dict[str, int]) -> None:
        """Test that the `from_dict` produces an object that generates the input data again when calling `to_dict`."""
        availability_window = AvailabilityWindow.from_dict(data_)
        assert availability_window.to_dict() == data_


class TestOffenceStatus:
    """Test the `OffenceStatus` dataclass."""

    @staticmethod
    @pytest.mark.parametrize("custom_amount", (0, 5))
    @pytest.mark.parametrize("light_unit_amount, serious_unit_amount", ((1, 2),))
    @pytest.mark.parametrize(
        "validator_downtime, invalid_payload, blacklisted, suspected, "
        "num_unknown_offenses, num_double_signed, num_light_client_attack, expected",
        (
            (False, False, False, False, 0, 0, 0, 0),
            (True, False, False, False, 0, 0, 0, 1),
            (False, True, False, False, 0, 0, 0, 1),
            (False, False, True, False, 0, 0, 0, 1),
            (False, False, False, True, 0, 0, 0, 1),
            (False, False, False, False, 1, 0, 0, 2),
            (False, False, False, False, 0, 1, 0, 2),
            (False, False, False, False, 0, 0, 1, 2),
            (False, False, False, False, 0, 2, 1, 6),
            (False, True, False, True, 5, 2, 1, 18),
            (True, True, True, True, 5, 2, 1, 20),
        ),
    )
    def test_slash_amount(
        custom_amount: int,
        light_unit_amount: int,
        serious_unit_amount: int,
        validator_downtime: bool,
        invalid_payload: bool,
        blacklisted: bool,
        suspected: bool,
        num_unknown_offenses: int,
        num_double_signed: int,
        num_light_client_attack: int,
        expected: int,
    ) -> None:
        """Test the `slash_amount` method."""
        status = OffenceStatus()

        if validator_downtime:
            for _ in range(abci_base.NUMBER_OF_BLOCKS_TRACKED):
                status.validator_downtime.add(True)

        for _ in range(abci_base.NUMBER_OF_ROUNDS_TRACKED):
            if invalid_payload:
                status.invalid_payload.add(True)
            if blacklisted:
                status.blacklisted.add(True)
            if suspected:
                status.suspected.add(True)

        status.num_unknown_offenses = num_unknown_offenses
        status.num_double_signed = num_double_signed
        status.num_light_client_attack = num_light_client_attack
        status.custom_offences_amount = custom_amount

        actual = status.slash_amount(light_unit_amount, serious_unit_amount)
        assert actual == expected + status.custom_offences_amount


@composite
def offence_tracking(draw: DrawFn) -> Tuple[Evidences, LastCommitInfo]:
    """A strategy for building offences reported by Tendermint."""
    n_validators = draw(integers(min_value=1, max_value=10))

    validators = [
        draw(
            builds(
                Validator,
                address=just(bytes(i)),
                power=integers(min_value=0),
            )
        )
        for i in range(n_validators)
    ]

    evidences = builds(
        Evidences,
        byzantine_validators=lists(
            builds(
                Evidence,
                evidence_type=sampled_from(EvidenceType),
                validator=sampled_from(validators),
                height=integers(min_value=0),
                time=builds(
                    Timestamp,
                    seconds=integers(min_value=0),
                    nanos=integers(min_value=0, max_value=999_999_999),
                ),
                total_voting_power=integers(min_value=0),
            ),
            min_size=n_validators,
            max_size=n_validators,
            unique_by=lambda v: v.validator.address,
        ),
    )

    last_commit_info = builds(
        LastCommitInfo,
        round_=integers(min_value=0),
        votes=lists(
            builds(
                VoteInfo,
                validator=sampled_from(validators),
                signed_last_block=booleans(),
            ),
            min_size=n_validators,
            max_size=n_validators,
            unique_by=lambda v: v.validator.address,
        ),
    )

    ev_example, commit_example = draw(evidences), draw(last_commit_info)

    # this assertion proves that all the validators are unique
    unique_commit_addresses = set(
        v.validator.address.decode() for v in commit_example.votes
    )
    assert len(unique_commit_addresses) == n_validators

    # this assertion proves that the same validators are used for evidences and votes
    assert unique_commit_addresses == set(
        e.validator.address.decode() for e in ev_example.byzantine_validators
    )

    return ev_example, commit_example


@composite
def offence_status(draw: DrawFn) -> OffenceStatus:
    """Build an offence status instance."""
    validator_downtime = just(
        AvailabilityWindow.from_dict(draw(availability_window_data()))
    )
    invalid_payload = just(
        AvailabilityWindow.from_dict(draw(availability_window_data()))
    )
    blacklisted = just(AvailabilityWindow.from_dict(draw(availability_window_data())))
    suspected = just(AvailabilityWindow.from_dict(draw(availability_window_data())))

    status = builds(
        OffenceStatus,
        validator_downtime=validator_downtime,
        invalid_payload=invalid_payload,
        blacklisted=blacklisted,
        suspected=suspected,
        num_unknown_offenses=integers(min_value=0),
        num_double_signed=integers(min_value=0),
        num_light_client_attack=integers(min_value=0),
    )

    return draw(status)


class TestOffenseStatusEncoderDecoder:
    """Test the `OffenseStatusEncoder` and the `OffenseStatusDecoder`."""

    @staticmethod
    @given(dictionaries(keys=text(), values=offence_status(), min_size=1))
    def test_encode_decode_offense_status(offense_status: str) -> None:
        """Test encoding an offense status mapping and then decoding it by using the custom encoder/decoder."""
        encoded = json.dumps(offense_status, cls=OffenseStatusEncoder)
        decoded = json.loads(encoded, cls=OffenseStatusDecoder)

        assert decoded == offense_status

    def test_encode_unknown(self) -> None:
        """Test the encoder with an unknown input."""

        class Unknown:
            """A dummy class that the encoder is not aware of."""

            unknown = "?"

        with pytest.raises(
            TypeError, match="Object of type Unknown is not JSON serializable"
        ):
            json.dumps(Unknown(), cls=OffenseStatusEncoder)


class TestRoundSequence:
    """Test the RoundSequence class."""

    def setup(self) -> None:
        """Set up the test."""
        self.round_sequence = RoundSequence(
            context=MagicMock(), abci_app_cls=AbciAppTest
        )
        self.round_sequence.setup(MagicMock(), logging.getLogger())
        self.round_sequence.tm_height = 1

    @pytest.mark.parametrize(
        "property_name, set_twice_exc, config_exc",
        (
            (
                "validator_to_agent",
                "The mapping of the validators' addresses to their agent addresses can only be set once. "
                "Attempted to set with {new_content_attempt} but it has content already: {value}.",
                "The mapping of the validators' addresses to their agent addresses has not been set.",
            ),
        ),
    )
    @given(data())
    def test_slashing_properties(
        self, property_name: str, set_twice_exc: str, config_exc: str, _data: Any
    ) -> None:
        """Test `validator_to_agent` getter and setter."""
        if property_name == "validator_to_agent":
            data_generator = dictionaries(text(), text())
        else:
            data_generator = dictionaries(text(), just(OffenceStatus()))

        value = _data.draw(data_generator)
        round_sequence = RoundSequence(context=MagicMock(), abci_app_cls=AbciAppTest)

        if value:
            setattr(round_sequence, property_name, value)
            assert getattr(round_sequence, property_name) == value
            new_content_attempt = _data.draw(data_generator)
            with pytest.raises(
                ValueError,
                match=re.escape(
                    set_twice_exc.format(
                        new_content_attempt=new_content_attempt, value=value
                    )
                ),
            ):
                setattr(round_sequence, property_name, new_content_attempt)
            return

        with pytest.raises(SlashingNotConfiguredError, match=config_exc):
            getattr(round_sequence, property_name)

    @mock.patch("json.loads", return_value="json_serializable")
    @pytest.mark.parametrize("slashing_config", (None, "", "test"))
    def test_sync_db_and_slashing(
        self, mock_loads: mock.MagicMock, slashing_config: str
    ) -> None:
        """Test the `sync_db_and_slashing` method."""
        self.round_sequence.latest_synchronized_data.slashing_config = slashing_config
        serialized_db_state = "dummy_db_state"
        self.round_sequence.sync_db_and_slashing(serialized_db_state)

        # Check that `sync()` was called with the correct arguments
        mock_sync = cast(
            mock.Mock, self.round_sequence.abci_app.synchronized_data.db.sync
        )
        mock_sync.assert_called_once_with(serialized_db_state)

        if slashing_config:
            mock_loads.assert_called_once_with(
                slashing_config, cls=OffenseStatusDecoder
            )
        else:
            mock_loads.assert_not_called()

    @mock.patch("json.dumps")
    @pytest.mark.parametrize("slashing_enabled", (True, False))
    def test_store_offence_status(
        self, mock_dumps: mock.MagicMock, slashing_enabled: bool
    ) -> None:
        """Test the `store_offence_status` method."""
        # Set up mock objects and return values
        self.round_sequence._offence_status = {"not_encoded": OffenceStatus()}
        mock_encoded_status = "encoded_status"
        mock_dumps.return_value = mock_encoded_status

        self.round_sequence._slashing_enabled = slashing_enabled

        # Call the method to be tested
        self.round_sequence.store_offence_status()

        if slashing_enabled:
            # Check that `json.dumps()` was called with the correct arguments, only if slashing is enabled
            mock_dumps.assert_called_once_with(
                self.round_sequence.offence_status,
                cls=OffenseStatusEncoder,
                sort_keys=True,
            )
            assert (
                self.round_sequence.abci_app.synchronized_data.db.slashing_config
                == mock_encoded_status
            )
            return

        # otherwise check that it was not called
        mock_dumps.assert_not_called()

    @given(
        validator=builds(Validator, address=binary(), power=integers()),
        agent_address=text(),
    )
    def test_get_agent_address(self, validator: Validator, agent_address: str) -> None:
        """Test `get_agent_address` method."""
        round_sequence = RoundSequence(context=MagicMock(), abci_app_cls=AbciAppTest)
        round_sequence.validator_to_agent = {
            validator.address.hex().upper(): agent_address
        }
        assert round_sequence.get_agent_address(validator) == agent_address

        unknown = deepcopy(validator)
        unknown.address += b"unknown"
        with pytest.raises(
            ValueError,
            match=re.escape(
                f"Requested agent address for an unknown validator address {unknown.address.hex().upper()}. "
                f"Available validators are: {round_sequence.validator_to_agent.keys()}"
            ),
        ):
            round_sequence.get_agent_address(unknown)

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
            seconds + nanoseconds / 10**9
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
        assert self.round_sequence.current_round_id == ConcreteRoundA.auto_round_id()

    def test_latest_result(self) -> None:
        """Test 'latest_result' property getter."""
        assert self.round_sequence.latest_synchronized_data

    @pytest.mark.parametrize("committed", (True, False))
    def test_last_round_transition_timestamp(self, committed: bool) -> None:
        """Test 'last_round_transition_timestamp' method."""
        if committed:
            self.round_sequence.begin_block(
                MagicMock(height=1), MagicMock(), MagicMock()
            )
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
            self.round_sequence.begin_block(
                MagicMock(height=1), MagicMock(), MagicMock()
            )
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

    def test_block_before_blockchain_is_init(self, caplog: LogCaptureFixture) -> None:
        """Test block received before blockchain initialized."""

        self.round_sequence.begin_block(MagicMock(height=1), MagicMock(), MagicMock())
        self.round_sequence.end_block()
        blockchain = self.round_sequence.blockchain
        blockchain._is_init = False
        self.round_sequence.blockchain = blockchain
        with caplog.at_level(logging.INFO):
            self.round_sequence.commit()
        expected = "Received block with height 1 before the blockchain was initialized."
        assert expected in caplog.text

    @pytest.mark.parametrize("last_round_transition_root_hash", (b"", b"test"))
    def test_last_round_transition_root_hash(
        self,
        last_round_transition_root_hash: bytes,
    ) -> None:
        """Test 'last_round_transition_root_hash' method."""
        self.round_sequence._last_round_transition_root_hash = (
            last_round_transition_root_hash
        )

        if last_round_transition_root_hash == b"":
            with mock.patch.object(
                RoundSequence,
                "root_hash",
                new_callable=mock.PropertyMock,
                return_value="test",
            ):
                assert self.round_sequence.last_round_transition_root_hash == "test"
        else:
            assert (
                self.round_sequence.last_round_transition_root_hash
                == last_round_transition_root_hash
            )

    @pytest.mark.parametrize("tm_height", (None, 1, 5))
    def test_last_round_transition_tm_height(self, tm_height: Optional[int]) -> None:
        """Test 'last_round_transition_tm_height' method."""
        if tm_height is None:
            with pytest.raises(
                ValueError,
                match="Trying to access Tendermint's last round transition height before any `end_block` calls.",
            ):
                _ = self.round_sequence.last_round_transition_tm_height
        else:
            self.round_sequence.tm_height = tm_height
            self.round_sequence.begin_block(
                MagicMock(height=1), MagicMock(), MagicMock()
            )
            self.round_sequence.end_block()
            self.round_sequence.commit()
            assert self.round_sequence.last_round_transition_tm_height == tm_height

    @given(one_of(none(), integers()))
    def test_tm_height(self, tm_height: int) -> None:
        """Test `tm_height` getter and setter."""

        self.round_sequence.tm_height = tm_height

        if tm_height is None:
            with pytest.raises(
                ValueError,
                match="Trying to access Tendermint's current height before any `end_block` calls.",
            ):
                _ = self.round_sequence.tm_height
        else:
            assert (
                self.round_sequence.tm_height
                == self.round_sequence._tm_height
                == tm_height
            )

    @given(one_of(none(), datetimes()))
    def test_block_stall_deadline_expired(
        self, block_stall_deadline: datetime.datetime
    ) -> None:
        """Test 'block_stall_deadline_expired' method."""

        self.round_sequence._block_stall_deadline = block_stall_deadline
        actual = self.round_sequence.block_stall_deadline_expired

        if block_stall_deadline is None:
            assert actual is False
        else:
            expected = datetime.datetime.now() > block_stall_deadline
            assert actual is expected

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

    @given(offence_tracking())
    @settings(suppress_health_check=[HealthCheck.too_slow])
    def test_track_tm_offences(
        self, offences: Tuple[Evidences, LastCommitInfo]
    ) -> None:
        """Test `_track_tm_offences` method."""
        evidences, last_commit_info = offences
        dummy_addr_template = "agent_{i}"
        round_sequence = RoundSequence(context=MagicMock(), abci_app_cls=AbciAppTest)
        synchronized_data_mock = MagicMock()
        round_sequence.setup(synchronized_data_mock, MagicMock())
        round_sequence.enable_slashing()

        expected_offence_status = {
            dummy_addr_template.format(i=i): OffenceStatus()
            for i in range(len(last_commit_info.votes))
        }
        for i, vote_info in enumerate(last_commit_info.votes):
            agent_address = dummy_addr_template.format(i=i)
            # initialize dummy round sequence's offence status and validator to agent address mapping
            round_sequence._offence_status[agent_address] = OffenceStatus()
            validator_address = vote_info.validator.address.hex()
            round_sequence._validator_to_agent[validator_address] = agent_address
            # set expected result
            expected_was_down = not vote_info.signed_last_block
            expected_offence_status[agent_address].validator_downtime.add(
                expected_was_down
            )

        for byzantine_validator in evidences.byzantine_validators:
            agent_address = round_sequence._validator_to_agent[
                byzantine_validator.validator.address.hex()
            ]
            evidence_type = byzantine_validator.evidence_type
            expected_offence_status[agent_address].num_unknown_offenses += bool(
                evidence_type == EvidenceType.UNKNOWN
            )
            expected_offence_status[agent_address].num_double_signed += bool(
                evidence_type == EvidenceType.DUPLICATE_VOTE
            )
            expected_offence_status[agent_address].num_light_client_attack += bool(
                evidence_type == EvidenceType.LIGHT_CLIENT_ATTACK
            )

        round_sequence._track_tm_offences(evidences, last_commit_info)
        assert round_sequence._offence_status == expected_offence_status

    @mock.patch.object(abci_base, "ADDRESS_LENGTH", len("agent_i"))
    def test_track_app_offences(self) -> None:
        """Test `_track_app_offences` method."""
        dummy_addr_template = "agent_{i}"
        stub_offending_keepers = [dummy_addr_template.format(i=i) for i in range(2)]
        self.round_sequence.enable_slashing()
        self.round_sequence._offence_status = {
            dummy_addr_template.format(i=i): OffenceStatus() for i in range(4)
        }
        expected_offence_status = deepcopy(self.round_sequence._offence_status)

        for i in (dummy_addr_template.format(i=i) for i in range(4)):
            offended = i in stub_offending_keepers
            expected_offence_status[i].blacklisted.add(offended)
            expected_offence_status[i].suspected.add(offended)

        with mock.patch.object(
            self.round_sequence.latest_synchronized_data.db,
            "get",
            return_value="".join(stub_offending_keepers),
        ):
            self.round_sequence._track_app_offences()
        assert self.round_sequence._offence_status == expected_offence_status

    @given(builds(SlashingNotConfiguredError, text()))
    def test_handle_slashing_not_configured(
        self, exc: SlashingNotConfiguredError
    ) -> None:
        """Test `_handle_slashing_not_configured` method."""
        logging.disable(logging.CRITICAL)

        round_sequence = RoundSequence(context=MagicMock(), abci_app_cls=AbciAppTest)
        round_sequence.setup(MagicMock(), MagicMock())

        assert not round_sequence._slashing_enabled
        assert round_sequence.latest_synchronized_data.nb_participants == 0
        round_sequence._handle_slashing_not_configured(exc)
        assert not round_sequence._slashing_enabled

        with mock.patch.object(
            round_sequence.latest_synchronized_data.db,
            "get",
            return_value=[i for i in range(4)],
        ):
            assert round_sequence.latest_synchronized_data.nb_participants == 4
            round_sequence._handle_slashing_not_configured(exc)
            assert not round_sequence._slashing_enabled

        logging.disable(logging.NOTSET)

    @pytest.mark.parametrize("_track_offences_raises", (True, False))
    def test_try_track_offences(self, _track_offences_raises: bool) -> None:
        """Test `_try_track_offences` method."""
        evidences, last_commit_info = MagicMock(), MagicMock()
        self.round_sequence.enable_slashing()
        with mock.patch.object(
            self.round_sequence,
            "_track_app_offences",
        ), mock.patch.object(
            self.round_sequence,
            "_track_tm_offences",
            side_effect=SlashingNotConfiguredError if _track_offences_raises else None,
        ) as _track_offences_mock, mock.patch.object(
            self.round_sequence, "_handle_slashing_not_configured"
        ) as _handle_slashing_not_configured_mock:
            self.round_sequence._try_track_offences(evidences, last_commit_info)
            if _track_offences_raises:
                _handle_slashing_not_configured_mock.assert_called_once()
            else:
                _track_offences_mock.assert_called_once_with(
                    evidences, last_commit_info
                )

    def test_begin_block_negative_is_finished(self) -> None:
        """Test 'begin_block' method, negative case (round sequence is finished)."""
        self.round_sequence.abci_app._current_round = None
        with pytest.raises(
            ABCIAppInternalError,
            match="internal error: round sequence is finished, cannot accept new blocks",
        ):
            self.round_sequence.begin_block(MagicMock(), MagicMock(), MagicMock())

    def test_begin_block_negative_wrong_phase(self) -> None:
        """Test 'begin_block' method, negative case (wrong phase)."""
        self.round_sequence._block_construction_phase = MagicMock()
        with pytest.raises(
            ABCIAppInternalError,
            match="internal error: cannot accept a 'begin_block' request.",
        ):
            self.round_sequence.begin_block(MagicMock(), MagicMock(), MagicMock())

    def test_begin_block_positive(self) -> None:
        """Test 'begin_block' method, positive case."""
        self.round_sequence.begin_block(MagicMock(), MagicMock(), MagicMock())

    def test_deliver_tx_negative_wrong_phase(self) -> None:
        """Test 'begin_block' method, negative (wrong phase)."""
        with pytest.raises(
            ABCIAppInternalError,
            match="internal error: cannot accept a 'deliver_tx' request",
        ):
            self.round_sequence.deliver_tx(MagicMock())

    def test_deliver_tx_positive_not_valid(self) -> None:
        """Test 'begin_block' method, positive (not valid)."""
        self.round_sequence.begin_block(MagicMock(), MagicMock(), MagicMock())
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
        self.round_sequence.begin_block(MagicMock(), MagicMock(), MagicMock())
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
        self.round_sequence.begin_block(MagicMock(height=1), MagicMock(), MagicMock())
        self.round_sequence.end_block()
        with mock.patch.object(
            self.round_sequence._blockchain, "add_block", side_effect=AddBlockError
        ):
            with pytest.raises(AddBlockError):
                self.round_sequence.commit()

    def test_commit_positive_no_change_round(self) -> None:
        """Test 'end_block' method, positive (no change round)."""
        self.round_sequence.begin_block(MagicMock(height=1), MagicMock(), MagicMock())
        self.round_sequence.end_block()
        with mock.patch.object(
            self.round_sequence.current_round,
            "end_block",
            return_value=None,
        ):
            assert isinstance(self.round_sequence.current_round, ConcreteRoundA)

    def test_commit_positive_with_change_round(self) -> None:
        """Test 'end_block' method, positive (with change round)."""
        self.round_sequence.begin_block(MagicMock(height=1), MagicMock(), MagicMock())
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

    def last_round_values_updated(self, any_: bool = True) -> bool:
        """Check if the values for the last round-related attributes have been updated."""
        seq = self.round_sequence

        current_last_pairs = (
            (
                seq._blockchain.last_block.timestamp,
                seq._last_round_transition_timestamp,
            ),
            (seq._blockchain.height, seq._last_round_transition_height),
            (seq.root_hash, seq._last_round_transition_root_hash),
            (seq.tm_height, seq._last_round_transition_tm_height),
        )

        if any_:
            return any(current == last for current, last in current_last_pairs)

        return all(current == last for current, last in current_last_pairs)

    @mock.patch.object(AbciApp, "process_event")
    @mock.patch.object(RoundSequence, "serialized_offence_status")
    @pytest.mark.parametrize("end_block_res", (None, (MagicMock(), MagicMock())))
    @pytest.mark.parametrize(
        "slashing_enabled, offence_status_",
        (
            (
                False,
                False,
            ),
            (
                False,
                True,
            ),
            (
                False,
                False,
            ),
            (
                True,
                True,
            ),
        ),
    )
    def test_update_round(
        self,
        serialized_offence_status_mock: mock.Mock,
        process_event_mock: mock.Mock,
        end_block_res: Optional[Tuple[BaseSynchronizedData, Any]],
        slashing_enabled: bool,
        offence_status_: dict,
    ) -> None:
        """Test '_update_round' method."""
        self.round_sequence.begin_block(MagicMock(height=1), MagicMock(), MagicMock())
        block = self.round_sequence._block_builder.get_block()
        self.round_sequence._blockchain.add_block(block)
        self.round_sequence._slashing_enabled = slashing_enabled
        self.round_sequence._offence_status = offence_status_

        with mock.patch.object(
            self.round_sequence.current_round, "end_block", return_value=end_block_res
        ):
            self.round_sequence._update_round()

        if end_block_res is None:
            assert not self.last_round_values_updated()
            process_event_mock.assert_not_called()
            return

        assert self.last_round_values_updated(any_=False)
        process_event_mock.assert_called_with(
            end_block_res[-1], result=end_block_res[0]
        )

        if slashing_enabled:
            serialized_offence_status_mock.assert_called_once()
        else:
            serialized_offence_status_mock.assert_not_called()

    @mock.patch.object(AbciApp, "process_event")
    @pytest.mark.parametrize(
        "termination_round_result, current_round_result",
        [
            (None, None),
            (None, (MagicMock(), MagicMock())),
            ((MagicMock(), MagicMock()), None),
            ((MagicMock(), MagicMock()), (MagicMock(), MagicMock())),
        ],
    )
    def test_update_round_when_termination_returns(
        self,
        process_event_mock: mock.Mock,
        termination_round_result: Optional[Tuple[BaseSynchronizedData, Any]],
        current_round_result: Optional[Tuple[BaseSynchronizedData, Any]],
    ) -> None:
        """Test '_update_round' method."""
        self.round_sequence.begin_block(MagicMock(height=1), MagicMock(), MagicMock())
        block = self.round_sequence._block_builder.get_block()
        self.round_sequence._blockchain.add_block(block)
        self.round_sequence.abci_app.add_background_app(STUB_TERMINATION_CONFIG)
        self.round_sequence.abci_app.setup()

        with mock.patch.object(
            self.round_sequence.current_round,
            "end_block",
            return_value=current_round_result,
        ), mock.patch.object(
            ConcreteBackgroundRound,
            "end_block",
            return_value=termination_round_result,
        ):
            self.round_sequence._update_round()

        if termination_round_result is None and current_round_result is None:
            assert (
                self.round_sequence._last_round_transition_timestamp
                != self.round_sequence._blockchain.last_block.timestamp
            )
            assert (
                self.round_sequence._last_round_transition_height
                != self.round_sequence._blockchain.height
            )
            assert (
                self.round_sequence._last_round_transition_root_hash
                != self.round_sequence.root_hash
            )
            assert (
                self.round_sequence._last_round_transition_tm_height
                != self.round_sequence.tm_height
            )
            process_event_mock.assert_not_called()
        elif termination_round_result is None and current_round_result is not None:
            assert (
                self.round_sequence._last_round_transition_timestamp
                == self.round_sequence._blockchain.last_block.timestamp
            )
            assert (
                self.round_sequence._last_round_transition_height
                == self.round_sequence._blockchain.height
            )
            assert (
                self.round_sequence._last_round_transition_root_hash
                == self.round_sequence.root_hash
            )
            assert (
                self.round_sequence._last_round_transition_tm_height
                == self.round_sequence.tm_height
            )
            process_event_mock.assert_called_with(
                current_round_result[-1],
                result=current_round_result[0],
            )
        elif termination_round_result is not None:
            assert (
                self.round_sequence._last_round_transition_timestamp
                == self.round_sequence._blockchain.last_block.timestamp
            )
            assert (
                self.round_sequence._last_round_transition_height
                == self.round_sequence._blockchain.height
            )
            assert (
                self.round_sequence._last_round_transition_root_hash
                == self.round_sequence.root_hash
            )
            assert (
                self.round_sequence._last_round_transition_tm_height
                == self.round_sequence.tm_height
            )
            process_event_mock.assert_called_with(
                termination_round_result[-1],
                result=termination_round_result[0],
            )

        self.round_sequence.abci_app.background_apps.clear()

    @pytest.mark.parametrize("restart_from_round", (ConcreteRoundA, MagicMock()))
    @pytest.mark.parametrize("serialized_db_state", (None, "serialized state"))
    @given(integers())
    def test_reset_state(
        self,
        restart_from_round: AbstractRound,
        serialized_db_state: str,
        round_count: int,
    ) -> None:
        """Tests reset_state"""
        with mock.patch.object(
            self.round_sequence,
            "_reset_to_default_params",
        ) as mock_reset, mock.patch.object(
            self.round_sequence, "sync_db_and_slashing"
        ) as mock_sync_db_and_slashing:
            transition_fn = self.round_sequence.abci_app.transition_function
            round_id = restart_from_round.auto_round_id()
            if restart_from_round in transition_fn:
                self.round_sequence.reset_state(
                    round_id, round_count, serialized_db_state
                )
                mock_reset.assert_called()

                if serialized_db_state is None:
                    mock_sync_db_and_slashing.assert_not_called()

                else:
                    mock_sync_db_and_slashing.assert_called_once_with(
                        serialized_db_state
                    )
                    assert (
                        self.round_sequence._last_round_transition_root_hash
                        == self.round_sequence.root_hash
                    )

            else:
                round_ids = {cls.auto_round_id() for cls in transition_fn}
                with pytest.raises(
                    ABCIAppInternalError,
                    match=re.escape(
                        "internal error: Cannot reset state. The Tendermint recovery parameters are incorrect. "
                        "Did you update the `restart_from_round` with an incorrect round id? "
                        f"Found {round_id}, but the app's transition function has the following round ids: "
                        f"{round_ids}.",
                    ),
                ):
                    self.round_sequence.reset_state(
                        restart_from_round.auto_round_id(),
                        round_count,
                        serialized_db_state,
                    )

    def test_reset_to_default_params(self) -> None:
        """Tests _reset_to_default_params."""
        # we set some values to the parameters, to make sure that they are not "empty"
        self.round_sequence._last_round_transition_timestamp = MagicMock()
        self.round_sequence._last_round_transition_height = MagicMock()
        self.round_sequence._last_round_transition_root_hash = MagicMock()
        self.round_sequence._last_round_transition_tm_height = MagicMock()
        self.round_sequence._tm_height = MagicMock()
        self._pending_offences = MagicMock()
        self._slashing_enabled = MagicMock()

        # we reset them
        self.round_sequence._reset_to_default_params()

        # we check whether they have been reset
        assert self.round_sequence._last_round_transition_timestamp is None
        assert self.round_sequence._last_round_transition_height == 0
        assert self.round_sequence._last_round_transition_root_hash == b""
        assert self.round_sequence._last_round_transition_tm_height is None
        assert self.round_sequence._tm_height is None
        assert self.round_sequence.pending_offences == set()
        assert not self.round_sequence._slashing_enabled

    def test_add_pending_offence(self) -> None:
        """Tests add_pending_offence."""
        assert self.round_sequence.pending_offences == set()
        mock_offence = MagicMock()
        self.round_sequence.add_pending_offence(mock_offence)
        assert self.round_sequence.pending_offences == {mock_offence}


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

    class FinalRound(AbstractRound, ABC):
        """A round class for testing."""

        payload_class = MagicMock()
        synchronized_data_class = MagicMock()
        payload_attribute = MagicMock()
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


def test_synchronized_data_type_on_abci_app_init(caplog: LogCaptureFixture) -> None:
    """Test synchronized data access"""

    # NOTE: the synchronized data of a particular AbciApp is only
    #  updated at the end of a round. However, we want to make sure
    #  that the instance during the first round of any AbciApp is
    #  in fact and instance of the locally defined SynchronizedData

    sentinel = object()

    class SynchronizedData(BaseSynchronizedData):
        """SynchronizedData"""

        @property
        def dummy_attr(self) -> object:
            return sentinel

    # this is how it's setup in SharedState.setup, using BaseSynchronizedData
    synchronized_data = BaseSynchronizedData(db=AbciAppDB(setup_data={}))

    with mock.patch.object(AbciAppTest, "initial_round_cls") as m:
        m.synchronized_data_class = SynchronizedData
        abci_app = AbciAppTest(synchronized_data, logging.getLogger(), MagicMock())
        abci_app.setup()
        assert isinstance(abci_app.synchronized_data, SynchronizedData)
        assert abci_app.synchronized_data.dummy_attr == sentinel


def test_get_name() -> None:
    """Test the get_name method."""

    class SomeObject:
        @property
        def some_property(self) -> Any:
            """Some getter."""
            return object()

    assert get_name(SomeObject.some_property) == "some_property"
    with pytest.raises(ValueError, match="1 is not a property"):
        get_name(1)


@pytest.mark.parametrize(
    "sender, accused_agent_address, offense_round, offense_type_value, last_transition_timestamp, time_to_live, custom_amount",
    (
        (
            "sender",
            "test_address",
            90,
            3,
            10,
            2,
            10,
        ),
    ),
)
def test_pending_offences_payload(
    sender: str,
    accused_agent_address: str,
    offense_round: int,
    offense_type_value: int,
    last_transition_timestamp: int,
    time_to_live: int,
    custom_amount: int,
) -> None:
    """Test `PendingOffencesPayload`"""

    payload = abci_base.PendingOffencesPayload(
        sender,
        accused_agent_address,
        offense_round,
        offense_type_value,
        last_transition_timestamp,
        time_to_live,
        custom_amount,
    )

    assert payload.id_
    assert payload.round_count == abci_base.ROUND_COUNT_DEFAULT
    assert payload.sender == sender
    assert payload.accused_agent_address == accused_agent_address
    assert payload.offense_round == offense_round
    assert payload.offense_type_value == offense_type_value
    assert payload.last_transition_timestamp == last_transition_timestamp
    assert payload.time_to_live == time_to_live
    assert payload.custom_amount == custom_amount
    assert payload.data == {
        "accused_agent_address": accused_agent_address,
        "offense_round": offense_round,
        "offense_type_value": offense_type_value,
        "last_transition_timestamp": last_transition_timestamp,
        "time_to_live": time_to_live,
        "custom_amount": custom_amount,
    }


class TestPendingOffencesRound(BaseRoundTestClass):
    """Tests for `PendingOffencesRound`."""

    _synchronized_data_class = BaseSynchronizedData

    @given(
        accused_agent_address=sampled_from(list(get_participants())),
        offense_round=integers(min_value=0),
        offense_type_value=sampled_from(
            [value.value for value in OffenseType.__members__.values()]
        ),
        last_transition_timestamp=floats(
            min_value=timegm(datetime.datetime(1971, 1, 1).utctimetuple()),
            max_value=timegm(datetime.datetime(8000, 1, 1).utctimetuple()) - 2000,
        ),
        time_to_live=floats(min_value=1, max_value=2000),
        custom_amount=integers(min_value=0),
    )
    def test_run(
        self,
        accused_agent_address: str,
        offense_round: int,
        offense_type_value: int,
        last_transition_timestamp: float,
        time_to_live: float,
        custom_amount: int,
    ) -> None:
        """Run tests."""

        test_round = abci_base.PendingOffencesRound(
            synchronized_data=self.synchronized_data,
            context=MagicMock(),
        )
        # initialize the offence status
        status_initialization = dict.fromkeys(self.participants, OffenceStatus())
        test_round.context.state.round_sequence.offence_status = status_initialization

        # create the actual and expected value
        actual = test_round.context.state.round_sequence.offence_status
        expected_invalid = offense_type_value == OffenseType.INVALID_PAYLOAD.value
        expected_custom_amount = offense_type_value == OffenseType.CUSTOM.value
        expected = deepcopy(status_initialization)

        first_payload, *payloads = [
            abci_base.PendingOffencesPayload(
                sender,
                accused_agent_address,
                offense_round,
                offense_type_value,
                last_transition_timestamp,
                time_to_live,
                custom_amount,
            )
            for sender in self.participants
        ]

        test_round.process_payload(first_payload)
        assert test_round.collection == {first_payload.sender: first_payload}
        test_round.end_block()
        assert actual == expected

        for payload in payloads:
            test_round.process_payload(payload)
            test_round.end_block()

        expected[accused_agent_address].invalid_payload.add(expected_invalid)
        if expected_custom_amount:
            expected[accused_agent_address].custom_offences_amount += custom_amount

        assert actual == expected
