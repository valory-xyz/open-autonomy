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


"""Test the `rounds` test tool module of the skill."""

import re
from enum import Enum
from typing import Any, FrozenSet, Generator, List, Optional, Tuple, Type, cast
from unittest.mock import MagicMock

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from packages.valory.skills.abstract_round_abci.base import (
    AbciAppDB,
    BaseSynchronizedData,
)
from packages.valory.skills.abstract_round_abci.test_tools.rounds import (
    BaseCollectDifferentUntilAllRoundTest,
    BaseCollectDifferentUntilThresholdRoundTest,
    BaseCollectSameUntilAllRoundTest,
    BaseCollectSameUntilThresholdRoundTest,
    BaseOnlyKeeperSendsRoundTest,
    BaseRoundTestClass,
    BaseVotingRoundTest,
    DummyCollectDifferentUntilAllRound,
    DummyCollectDifferentUntilThresholdRound,
    DummyCollectSameUntilAllRound,
    DummyCollectSameUntilThresholdRound,
    DummyEvent,
    DummyOnlyKeeperSendsRound,
    DummySynchronizedData,
    DummyTxPayload,
    DummyVotingRound,
    MAX_PARTICIPANTS,
    get_dummy_tx_payloads,
    get_participants,
)
from packages.valory.skills.abstract_round_abci.tests.conftest import profile_name
from packages.valory.skills.abstract_round_abci.tests.test_common import last_iteration


settings.load_profile(profile_name)

# this is how many times we need to iterate before reaching the last iteration for a base test.
BASE_TEST_GEN_ITERATIONS = 4


def test_get_participants() -> None:
    """Test `get_participants`."""
    participants = get_participants()
    assert isinstance(participants, frozenset)
    assert all(isinstance(p, str) for p in participants)
    assert len(participants) == MAX_PARTICIPANTS


class DummyTxPayloadMatcher:
    """A `DummyTxPayload` matcher for assertion comparisons."""

    expected: DummyTxPayload

    def __init__(self, expected: DummyTxPayload) -> None:
        """Initialize the matcher."""
        self.expected = expected

    def __repr__(self) -> str:
        """Needs to be implemented for better assertion messages."""
        return (
            "DummyTxPayload("
            f"id={repr(self.expected.id_)}, "
            f"round_count={repr(self.expected.round_count)}, "
            f"sender={repr(self.expected.sender)}, "
            f"value={repr(self.expected.value)}, "
            f"vote={repr(self.expected.vote)}"
            ")"
        )

    def __eq__(self, other: Any) -> bool:
        """The method that will be used for the assertion comparisons."""
        return (
            self.expected.round_count == other.round_count
            and self.expected.sender == other.sender
            and self.expected.value == other.value
            and self.expected.vote == other.vote
        )


@given(
    st.frozensets(st.text(max_size=200), max_size=100),
    st.text(max_size=500),
    st.one_of(st.none(), st.booleans()),
    st.booleans(),
)
def test_get_dummy_tx_payloads(
    participants: FrozenSet[str],
    value: str,
    vote: Optional[bool],
    is_value_none: bool,
) -> None:
    """Test `get_dummy_tx_payloads`."""
    expected = [
        DummyTxPayloadMatcher(
            DummyTxPayload(
                sender=agent,
                value=(value or agent) if not is_value_none else value,
                vote=vote,
            )
        )
        for agent in sorted(participants)
    ]

    actual = get_dummy_tx_payloads(participants, value, vote, is_value_none)

    assert len(actual) == len(expected) == len(participants)
    assert actual == expected


class TestDummyTxPayload:  # pylint: disable=too-few-public-methods
    """Test class for `DummyTxPayload`"""

    @staticmethod
    @given(st.text(max_size=200), st.text(max_size=500), st.booleans())
    def test_properties(
        sender: str,
        value: str,
        vote: bool,
    ) -> None:
        """Test all the properties."""
        dummy_tx_payload = DummyTxPayload(sender, value, vote)
        assert dummy_tx_payload.value == value
        assert dummy_tx_payload.vote == vote
        assert dummy_tx_payload.data == {"value": value, "vote": vote}


class TestDummySynchronizedData:  # pylint: disable=too-few-public-methods
    """Test class for `DummySynchronizedData`."""

    @staticmethod
    @given(st.lists(st.text(max_size=200), max_size=100))
    def test_most_voted_keeper_address(
        most_voted_keeper_address_data: List[str],
    ) -> None:
        """Test `most_voted_keeper_address`."""
        most_voted_keeper_address_key = "most_voted_keeper_address"

        dummy_synchronized_data = DummySynchronizedData(
            db=AbciAppDB(
                setup_data={
                    most_voted_keeper_address_key: most_voted_keeper_address_data
                }
            )
        )

        if len(most_voted_keeper_address_data) == 0:
            with pytest.raises(
                ValueError,
                match=re.escape(
                    f"'{most_voted_keeper_address_key}' "
                    "field is not set for this period [0] and no default value was provided.",
                ),
            ):
                _ = dummy_synchronized_data.most_voted_keeper_address
            return

        assert (
            dummy_synchronized_data.most_voted_keeper_address
            == most_voted_keeper_address_data[-1]
        )


class TestBaseRoundTestClass:
    """Test `BaseRoundTestClass`."""

    @staticmethod
    def test_test_no_majority_event() -> None:
        """Test `_test_no_majority_event`."""
        base_round_test = BaseRoundTestClass()
        base_round_test._event_class = DummyEvent  # pylint: disable=protected-access

        base_round_test._test_no_majority_event(  # pylint: disable=protected-access
            MagicMock(
                end_block=lambda: (
                    MagicMock(),
                    DummyEvent.NO_MAJORITY,
                )
            )
        )

    @staticmethod
    @given(st.integers(min_value=0, max_value=100), st.integers(min_value=1))
    def test_complete_run(iter_count: int, shift: int) -> None:
        """Test `_complete_run`."""

        def dummy_gen() -> Generator[MagicMock, None, None]:
            """A dummy generator."""
            return (MagicMock() for _ in range(iter_count))

        # test with the same number as the generator's contents
        gen = dummy_gen()
        BaseRoundTestClass._complete_run(  # pylint: disable=protected-access
            gen, iter_count
        )

        # assert that the generator has been fully consumed
        with pytest.raises(StopIteration):
            next(gen)

        # test with a larger count than a generator's
        with pytest.raises(StopIteration):
            BaseRoundTestClass._complete_run(  # pylint: disable=protected-access
                dummy_gen(), iter_count + shift
            )


class BaseTestBase:
    """Base class for the Base tests."""

    gen: Generator
    base_round_test: BaseRoundTestClass
    base_round_test_cls: Type[BaseRoundTestClass]
    test_method_name = "_test_round"

    def setup(self) -> None:
        """Setup that is run before each test."""
        self.base_round_test = self.base_round_test_cls()
        self.base_round_test._synchronized_data_class = (  # pylint: disable=protected-access
            DummySynchronizedData
        )
        self.base_round_test.setup()
        self.base_round_test._event_class = (  # pylint: disable=protected-access
            DummyEvent
        )

    def create_test_gen(self, **kwargs: Any) -> None:
        """Create the base test generator."""
        test_method = getattr(self.base_round_test, self.test_method_name)
        self.gen = test_method(**kwargs)

    def exhaust_base_test_gen(self) -> None:
        """Exhaust the base test generator."""
        for _ in range(BASE_TEST_GEN_ITERATIONS):
            next(self.gen)
        last_iteration(self.gen)

    def run_test(self, **kwargs: Any) -> None:
        """Run a test for a base test."""
        self.create_test_gen(**kwargs)
        self.exhaust_base_test_gen()


class DummyCollectDifferentUntilAllRoundWithEndBlock(
    DummyCollectDifferentUntilAllRound
):
    """A `DummyCollectDifferentUntilAllRound` with `end_block` implemented."""

    def __init__(self, dummy_exit_event: DummyEvent, *args: Any, **kwargs: Any):
        """Initialize the dummy class."""
        super().__init__(*args, **kwargs)
        self.dummy_exit_event = dummy_exit_event

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Enum]]:
        """A dummy `end_block` implementation."""
        if self.collection_threshold_reached and self.dummy_exit_event is not None:
            return (
                cast(
                    DummySynchronizedData,
                    self.synchronized_data.update(
                        most_voted_keeper_address=list(self.collection.keys())
                    ),
                ),
                self.dummy_exit_event,
            )
        return None


class TestBaseCollectDifferentUntilAllRoundTest(BaseTestBase):
    """Test `BaseCollectDifferentUntilAllRoundTest`."""

    base_round_test: BaseCollectDifferentUntilAllRoundTest
    base_round_test_cls = BaseCollectDifferentUntilAllRoundTest

    @given(
        st.one_of(st.none(), st.sampled_from(DummyEvent)),
    )
    def test_test_round(self, exit_event: DummyEvent) -> None:
        """Test `_test_round`."""
        test_round = DummyCollectDifferentUntilAllRoundWithEndBlock(
            exit_event,
            self.base_round_test.synchronized_data,
            context=MagicMock(),
        )
        round_payloads = [
            DummyTxPayload(f"agent_{i}", str(i)) for i in range(MAX_PARTICIPANTS)
        ]
        synchronized_data_attr_checks = [
            lambda _synchronized_data: _synchronized_data.most_voted_keeper_address
        ]

        self.run_test(
            test_round=test_round,
            round_payloads=round_payloads,
            synchronized_data_update_fn=lambda synchronized_data, _: synchronized_data.update(
                most_voted_keeper_address=[
                    f"agent_{i}" for i in range(MAX_PARTICIPANTS)
                ]
            ),
            synchronized_data_attr_checks=synchronized_data_attr_checks,
            exit_event=exit_event,
        )


class DummyCollectSameUntilAllRoundWithEndBlock(DummyCollectSameUntilAllRound):
    """A `DummyCollectSameUntilAllRound` with `end_block` implemented."""

    def __init__(self, dummy_exit_event: DummyEvent, *args: Any, **kwargs: Any):
        """Initialize the dummy class."""
        super().__init__(*args, **kwargs)
        self.dummy_exit_event = dummy_exit_event

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Enum]]:
        """A dummy `end_block` implementation."""
        if self.collection_threshold_reached:
            return (
                cast(
                    DummySynchronizedData,
                    self.synchronized_data.update(
                        most_voted_keeper_address=self.common_payload
                    ),
                ),
                self.dummy_exit_event,
            )
        return None


class TestBaseCollectSameUntilAllRoundTest(BaseTestBase):
    """Test `BaseCollectSameUntilAllRoundTest`."""

    base_round_test: BaseCollectSameUntilAllRoundTest
    base_round_test_cls: Type[
        BaseCollectSameUntilAllRoundTest
    ] = BaseCollectSameUntilAllRoundTest

    @given(
        st.sampled_from(DummyEvent),
        st.text(max_size=500),
        st.booleans(),
    )
    def test_test_round(
        self, exit_event: DummyEvent, common_value: str, finished: bool
    ) -> None:
        """Test `_test_round`."""
        test_round = DummyCollectSameUntilAllRoundWithEndBlock(
            exit_event,
            self.base_round_test.synchronized_data,
            context=MagicMock(),
        )
        round_payloads = {
            f"test{i}": DummyTxPayload(f"agent_{i}", common_value)
            for i in range(MAX_PARTICIPANTS)
        }
        synchronized_data_attr_checks = [
            lambda _synchronized_data: _synchronized_data.most_voted_keeper_address
        ]

        self.run_test(
            test_round=test_round,
            round_payloads=round_payloads,
            synchronized_data_update_fn=lambda synchronized_data, _: synchronized_data.update(
                most_voted_keeper_address=common_value
            ),
            synchronized_data_attr_checks=synchronized_data_attr_checks,
            most_voted_payload=common_value,
            exit_event=exit_event,
            finished=finished,
        )


class DummyCollectSameUntilThresholdRoundWithEndBlock(
    DummyCollectSameUntilThresholdRound
):
    """A `DummyCollectSameUntilThresholdRound` with `end_block` overriden."""

    def __init__(self, dummy_exit_event: DummyEvent, *args: Any, **kwargs: Any):
        """Initialize the dummy class."""
        super().__init__(*args, **kwargs)
        self.dummy_exit_event = dummy_exit_event

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Enum]]:
        """A dummy `end_block` override."""
        if self.threshold_reached:
            return (
                cast(
                    DummySynchronizedData,
                    self.synchronized_data.update(
                        most_voted_keeper_address=self.most_voted_payload
                    ),
                ),
                self.dummy_exit_event,
            )
        if not self.is_majority_possible(
            self.collection, self.synchronized_data.nb_participants
        ):
            return self.synchronized_data, DummyEvent.NO_MAJORITY
        return None


class TestBaseCollectSameUntilThresholdRoundTest(BaseTestBase):
    """Test `BaseCollectSameUntilThresholdRoundTest`."""

    base_round_test: BaseCollectSameUntilThresholdRoundTest
    base_round_test_cls: Type[
        BaseCollectSameUntilThresholdRoundTest
    ] = BaseCollectSameUntilThresholdRoundTest

    @given(
        st.sampled_from(DummyEvent),
        st.text(max_size=500),
    )
    def test_test_round(self, exit_event: DummyEvent, most_voted_payload: str) -> None:
        """Test `_test_round`."""
        test_round = DummyCollectSameUntilThresholdRoundWithEndBlock(
            exit_event,
            self.base_round_test.synchronized_data,
            context=MagicMock(),
        )
        round_payloads = {
            f"test{i}": DummyTxPayload(f"agent_{i}", most_voted_payload)
            for i in range(MAX_PARTICIPANTS)
        }
        synchronized_data_attr_checks = [
            lambda _synchronized_data: _synchronized_data.most_voted_keeper_address
        ]

        self.run_test(
            test_round=test_round,
            round_payloads=round_payloads,
            synchronized_data_update_fn=lambda synchronized_data, _: synchronized_data.update(
                most_voted_keeper_address=most_voted_payload
            ),
            synchronized_data_attr_checks=synchronized_data_attr_checks,
            most_voted_payload=most_voted_payload,
            exit_event=exit_event,
        )


class DummyOnlyKeeperSendsRoundTest(DummyOnlyKeeperSendsRound):
    """A `DummyOnlyKeeperSendsRound` with `end_block` implemented."""

    def __init__(self, dummy_exit_event: DummyEvent, *args: Any, **kwargs: Any):
        """Initialize the dummy class."""
        super().__init__(*args, **kwargs)
        self.dummy_exit_event = dummy_exit_event

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Enum]]:
        """A dummy `end_block` implementation."""
        if self.keeper_payload is not None and any(
            [val is not None for val in self.keeper_payload.values]
        ):
            return (
                cast(
                    DummySynchronizedData,
                    self.synchronized_data.update(
                        blacklisted_keepers=self.keeper_payload.values[0]
                    ),
                ),
                self.dummy_exit_event,
            )
        return None


class TestBaseOnlyKeeperSendsRoundTest(BaseTestBase):
    """Test `BaseOnlyKeeperSendsRoundTest`."""

    base_round_test: BaseOnlyKeeperSendsRoundTest
    base_round_test_cls: Type[
        BaseOnlyKeeperSendsRoundTest
    ] = BaseOnlyKeeperSendsRoundTest
    most_voted_keeper_address: str = "agent_0"

    def setup(self) -> None:
        """Setup that is run before each test."""
        super().setup()
        self.base_round_test.synchronized_data.update(
            most_voted_keeper_address=self.most_voted_keeper_address
        )

    @given(
        st.sampled_from(DummyEvent),
        st.text(),
    )
    def test_test_round(self, exit_event: DummyEvent, keeper_value: str) -> None:
        """Test `_test_round`."""
        test_round = DummyOnlyKeeperSendsRoundTest(
            exit_event,
            self.base_round_test.synchronized_data,
            context=MagicMock(),
        )
        keeper_payload = DummyTxPayload(self.most_voted_keeper_address, keeper_value)
        synchronized_data_attr_checks = [
            lambda _synchronized_data: _synchronized_data.blacklisted_keepers
        ]

        self.run_test(
            test_round=test_round,
            keeper_payloads=keeper_payload,
            synchronized_data_update_fn=lambda synchronized_data, _: synchronized_data.update(
                blacklisted_keepers=keeper_value
            ),
            synchronized_data_attr_checks=synchronized_data_attr_checks,
            exit_event=exit_event,
        )


class DummyBaseVotingRoundTestWithEndBlock(DummyVotingRound):
    """A `DummyVotingRound` with `end_block` overriden."""

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Enum]]:
        """A dummy `end_block` override."""
        if self.positive_vote_threshold_reached:
            synchronized_data = cast(
                DummySynchronizedData,
                self.synchronized_data.update(
                    is_keeper_set=bool(self.collection),
                ),
            )
            return synchronized_data, DummyEvent.DONE
        if self.negative_vote_threshold_reached:
            return self.synchronized_data, DummyEvent.NEGATIVE
        if self.none_vote_threshold_reached:
            return self.synchronized_data, DummyEvent.NONE
        if not self.is_majority_possible(
            self.collection, self.synchronized_data.nb_participants
        ):
            return self.synchronized_data, DummyEvent.NO_MAJORITY
        return None


class TestBaseVotingRoundTest(BaseTestBase):
    """Test `BaseVotingRoundTest`."""

    base_round_test: BaseVotingRoundTest
    base_round_test_cls: Type[BaseVotingRoundTest] = BaseVotingRoundTest

    @given(
        st.one_of(st.none(), st.booleans()),
    )
    def test_test_round(self, is_keeper_set: Optional[bool]) -> None:
        """Test `_test_round`."""
        if is_keeper_set is None:
            exit_event = DummyEvent.NONE
            self.test_method_name = "_test_voting_round_none"
        elif is_keeper_set:
            exit_event = DummyEvent.DONE
            self.test_method_name = "_test_voting_round_positive"
        else:
            exit_event = DummyEvent.NEGATIVE
            self.test_method_name = "_test_voting_round_negative"

        test_round = DummyBaseVotingRoundTestWithEndBlock(
            self.base_round_test.synchronized_data,
            context=MagicMock(),
        )
        round_payloads = {
            f"test{i}": DummyTxPayload(f"agent_{i}", value="", vote=is_keeper_set)
            for i in range(MAX_PARTICIPANTS)
        }
        synchronized_data_attr_checks = [
            lambda _synchronized_data: _synchronized_data.is_keeper_set
        ]

        self.run_test(
            test_round=test_round,
            round_payloads=round_payloads,
            synchronized_data_update_fn=lambda synchronized_data, _: synchronized_data.update(
                is_keeper_set=is_keeper_set
            ),
            synchronized_data_attr_checks=synchronized_data_attr_checks,
            exit_event=exit_event,
        )


class DummyCollectDifferentUntilThresholdRoundWithEndBlock(
    DummyCollectDifferentUntilThresholdRound
):
    """A `DummyCollectDifferentUntilThresholdRound` with `end_block` implemented."""

    def __init__(self, dummy_exit_event: DummyEvent, *args: Any, **kwargs: Any):
        """Initialize the dummy class."""
        super().__init__(*args, **kwargs)
        self.dummy_exit_event = dummy_exit_event

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Enum]]:
        """A dummy `end_block` implementation."""
        if self.collection_threshold_reached and self.dummy_exit_event is not None:
            return (
                cast(
                    DummySynchronizedData,
                    self.synchronized_data.update(
                        most_voted_keeper_address=list(self.collection.keys())
                    ),
                ),
                self.dummy_exit_event,
            )
        return None


class TestBaseCollectDifferentUntilThresholdRoundTest(BaseTestBase):
    """Test `BaseCollectDifferentUntilThresholdRoundTest`."""

    base_round_test: BaseCollectDifferentUntilThresholdRoundTest
    base_round_test_cls: Type[
        BaseCollectDifferentUntilThresholdRoundTest
    ] = BaseCollectDifferentUntilThresholdRoundTest

    @given(st.sampled_from(DummyEvent))
    def test_test_round(self, exit_event: DummyEvent) -> None:
        """Test `_test_round`."""
        test_round = DummyCollectDifferentUntilThresholdRoundWithEndBlock(
            exit_event,
            self.base_round_test.synchronized_data,
            context=MagicMock(),
        )
        round_payloads = {
            f"test{i}": DummyTxPayload(f"agent_{i}", str(i))
            for i in range(MAX_PARTICIPANTS)
        }
        synchronized_data_attr_checks = [
            lambda _synchronized_data: _synchronized_data.most_voted_keeper_address
        ]

        self.run_test(
            test_round=test_round,
            round_payloads=round_payloads,
            synchronized_data_update_fn=lambda synchronized_data, _: synchronized_data.update(
                most_voted_keeper_address=[
                    f"agent_{i}" for i in range(MAX_PARTICIPANTS)
                ]
            ),
            synchronized_data_attr_checks=synchronized_data_attr_checks,
            exit_event=exit_event,
        )
