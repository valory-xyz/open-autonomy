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

"""Test tools for testing rounds."""

import re
from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from typing import (
    Any,
    Callable,
    FrozenSet,
    Generator,
    List,
    Mapping,
    Optional,
    Tuple,
    Type,
)
from unittest import mock

import pytest

from packages.valory.skills.abstract_round_abci.base import (
    ABCIAppInternalError,
    AbciAppDB,
    AbstractRound,
    BaseSynchronizedData,
    BaseTxPayload,
    CollectDifferentUntilAllRound,
    CollectDifferentUntilThresholdRound,
    CollectNonEmptyUntilThresholdRound,
    CollectSameUntilAllRound,
    CollectSameUntilThresholdRound,
    CollectionRound,
    ConsensusParams,
    OnlyKeeperSendsRound,
    TransactionNotValidError,
    VotingRound,
)


MAX_PARTICIPANTS: int = 4


def get_participants() -> FrozenSet[str]:
    """Participants"""
    return frozenset([f"agent_{i}" for i in range(MAX_PARTICIPANTS)])


class DummyEvent(Enum):
    """Dummy Event"""

    DONE = "done"
    ROUND_TIMEOUT = "round_timeout"
    NO_MAJORITY = "no_majority"
    RESET_TIMEOUT = "reset_timeout"
    NEGATIVE = "negative"
    NONE = "none"
    FAIL = "fail"


@dataclass(frozen=True)
class DummyTxPayload(BaseTxPayload):
    """Dummy Transaction Payload."""

    value: Optional[str] = None
    vote: Optional[bool] = None


class DummySynchronizedData(BaseSynchronizedData):
    """Dummy synchronized data for tests."""


def get_dummy_tx_payloads(
    participants: FrozenSet[str],
    value: Any = None,
    vote: Optional[bool] = False,
    is_value_none: bool = False,
) -> List[DummyTxPayload]:
    """Returns a list of DummyTxPayload objects."""
    return [
        DummyTxPayload(
            sender=agent,
            value=(value or agent) if not is_value_none else value,
            vote=vote,
        )
        for agent in sorted(participants)
    ]


class DummyRound(AbstractRound):
    """Dummy round."""

    payload_class = DummyTxPayload
    payload_attribute = "value"
    synchronized_data_class = BaseSynchronizedData

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Enum]]:
        """end_block method."""


class DummyCollectionRound(CollectionRound, DummyRound):
    """Dummy Class for CollectionRound"""


class DummyCollectDifferentUntilAllRound(CollectDifferentUntilAllRound, DummyRound):
    """Dummy Class for CollectDifferentUntilAllRound"""


class DummyCollectSameUntilAllRound(CollectSameUntilAllRound, DummyRound):
    """Dummy Class for CollectSameUntilThresholdRound"""


class DummyCollectDifferentUntilThresholdRound(
    CollectDifferentUntilThresholdRound, DummyRound
):
    """Dummy Class for CollectDifferentUntilThresholdRound"""


class DummyCollectSameUntilThresholdRound(CollectSameUntilThresholdRound, DummyRound):
    """Dummy Class for CollectSameUntilThresholdRound"""


class DummyOnlyKeeperSendsRound(OnlyKeeperSendsRound, DummyRound):
    """Dummy Class for OnlyKeeperSendsRound"""

    fail_event = "FAIL_EVENT"


class DummyVotingRound(VotingRound, DummyRound):
    """Dummy Class for VotingRound"""


class DummyCollectNonEmptyUntilThresholdRound(
    CollectNonEmptyUntilThresholdRound, DummyRound
):
    """Dummy Class for `CollectNonEmptyUntilThresholdRound`"""


class BaseRoundTestClass:  # pylint: disable=too-few-public-methods
    """Base test class."""

    synchronized_data: BaseSynchronizedData
    participants: FrozenSet[str]
    consensus_params: ConsensusParams

    _synchronized_data_class: Type[BaseSynchronizedData]
    _event_class: Any

    def setup(
        self,
    ) -> None:
        """Setup test class."""

        self.participants = get_participants()
        self.synchronized_data = self._synchronized_data_class(
            db=AbciAppDB(
                setup_data=dict(
                    participants=[self.participants],
                    all_participants=[self.participants],
                ),
            )
        )
        self.consensus_params = ConsensusParams(max_participants=MAX_PARTICIPANTS)

    def _test_no_majority_event(self, round_obj: AbstractRound) -> None:
        """Test the NO_MAJORITY event."""
        with mock.patch.object(round_obj, "is_majority_possible", return_value=False):
            result = round_obj.end_block()
            assert result is not None
            _, event = result
            assert event == self._event_class.NO_MAJORITY

    @staticmethod
    def _complete_run(
        test_runner: Generator, iter_count: int = MAX_PARTICIPANTS
    ) -> None:
        """
        This method represents logic to execute test logic defined in _test_round method.

        _test_round should follow these steps

        1. process first payload
        2. yield test_round
        3. test collection, end_block and thresholds
        4. process rest of the payloads
        5. yield test_round
        6. yield synchronized_data, event ( returned from end_block )
        7. test synchronized_data and event

        :param test_runner: test runner
        :param iter_count: iter_count
        """

        for _ in range(iter_count):
            next(test_runner)


class BaseCollectDifferentUntilAllRoundTest(  # pylint: disable=too-few-public-methods
    BaseRoundTestClass
):
    """Tests for rounds derived from CollectDifferentUntilAllRound."""

    def _test_round(
        self,
        test_round: CollectDifferentUntilAllRound,
        round_payloads: List[BaseTxPayload],
        synchronized_data_update_fn: Callable,
        synchronized_data_attr_checks: List[Callable],
        exit_event: Any,
    ) -> Generator:
        """Test round."""

        first_payload = round_payloads.pop(0)
        test_round.process_payload(first_payload)

        yield test_round
        assert test_round.collection[first_payload.sender] == first_payload
        assert not test_round.collection_threshold_reached
        assert test_round.end_block() is None

        for payload in round_payloads:
            test_round.process_payload(payload)
        yield test_round
        assert test_round.collection_threshold_reached

        actual_next_synchronized_data = synchronized_data_update_fn(
            deepcopy(self.synchronized_data), test_round
        )

        res = test_round.end_block()
        yield res
        if exit_event is None:
            assert res is exit_event
        else:
            assert res is not None
            synchronized_data, event = res
            for behaviour_attr_getter in synchronized_data_attr_checks:
                assert behaviour_attr_getter(
                    synchronized_data
                ) == behaviour_attr_getter(actual_next_synchronized_data)
            assert event == exit_event
        yield


class BaseCollectSameUntilAllRoundTest(
    BaseRoundTestClass
):  # pylint: disable=too-few-public-methods
    """Tests for rounds derived from CollectSameUntilAllRound."""

    def _test_round(  # pylint: disable=too-many-arguments,too-many-locals
        self,
        test_round: CollectSameUntilAllRound,
        round_payloads: Mapping[str, BaseTxPayload],
        synchronized_data_update_fn: Callable,
        synchronized_data_attr_checks: List[Callable],
        most_voted_payload: Any,
        exit_event: Any,
        finished: bool,
    ) -> Generator:
        """Test rounds derived from CollectionRound."""

        (_, first_payload), *payloads = round_payloads.items()

        test_round.process_payload(first_payload)
        yield test_round
        assert test_round.collection[first_payload.sender] == first_payload
        assert not test_round.collection_threshold_reached
        assert test_round.end_block() is None

        with pytest.raises(
            ABCIAppInternalError,
            match="internal error: 1 votes are not enough for `CollectSameUntilAllRound`. "
            f"Expected: `n_votes = max_participants = {MAX_PARTICIPANTS}`",
        ):
            _ = test_round.common_payload

        for _, payload in payloads:
            test_round.process_payload(payload)
        yield test_round
        if finished:
            assert test_round.collection_threshold_reached
        assert test_round.common_payload == most_voted_payload

        actual_next_synchronized_data = synchronized_data_update_fn(
            deepcopy(self.synchronized_data), test_round
        )
        res = test_round.end_block()
        yield res
        assert res is not None

        synchronized_data, event = res

        for behaviour_attr_getter in synchronized_data_attr_checks:
            assert behaviour_attr_getter(synchronized_data) == behaviour_attr_getter(
                actual_next_synchronized_data
            ), f"Mismatch in synchronized_data. Actual:\n{behaviour_attr_getter(synchronized_data)}\nExpected:\n{behaviour_attr_getter(actual_next_synchronized_data)}"
        assert event == exit_event
        yield


class BaseCollectSameUntilThresholdRoundTest(  # pylint: disable=too-few-public-methods
    BaseRoundTestClass
):
    """Tests for rounds derived from CollectSameUntilThresholdRound."""

    def _test_round(  # pylint: disable=too-many-arguments,too-many-locals
        self,
        test_round: CollectSameUntilThresholdRound,
        round_payloads: Mapping[str, BaseTxPayload],
        synchronized_data_update_fn: Callable,
        synchronized_data_attr_checks: List[Callable],
        most_voted_payload: Any,
        exit_event: Any,
    ) -> Generator:
        """Test rounds derived from CollectionRound."""

        (_, first_payload), *payloads = round_payloads.items()

        test_round.process_payload(first_payload)
        yield test_round
        assert test_round.collection[first_payload.sender] == first_payload
        assert not test_round.threshold_reached
        assert test_round.end_block() is None

        self._test_no_majority_event(test_round)
        with pytest.raises(ABCIAppInternalError, match="not enough votes"):
            _ = test_round.most_voted_payload

        for _, payload in payloads:
            test_round.process_payload(payload)
        yield test_round
        assert test_round.threshold_reached
        assert test_round.most_voted_payload == most_voted_payload

        actual_next_synchronized_data = synchronized_data_update_fn(
            deepcopy(self.synchronized_data), test_round
        )
        res = test_round.end_block()
        yield res
        assert res is not None

        synchronized_data, event = res

        for behaviour_attr_getter in synchronized_data_attr_checks:
            assert behaviour_attr_getter(synchronized_data) == behaviour_attr_getter(
                actual_next_synchronized_data
            ), f"Mismatch in synchronized_data. Actual:\n{behaviour_attr_getter(synchronized_data)}\nExpected:\n{behaviour_attr_getter(actual_next_synchronized_data)}"
        assert event == exit_event
        yield


class BaseOnlyKeeperSendsRoundTest(  # pylint: disable=too-few-public-methods
    BaseRoundTestClass
):
    """Tests for rounds derived from OnlyKeeperSendsRound."""

    def _test_round(
        self,
        test_round: OnlyKeeperSendsRound,
        keeper_payloads: BaseTxPayload,
        synchronized_data_update_fn: Callable,
        synchronized_data_attr_checks: List[Callable],
        exit_event: Any,
    ) -> Generator:
        """Test for rounds derived from OnlyKeeperSendsRound."""

        assert test_round.end_block() is None
        assert not test_round.has_keeper_sent_payload

        test_round.process_payload(keeper_payloads)
        yield test_round
        assert test_round.has_keeper_sent_payload

        yield test_round
        actual_next_synchronized_data = synchronized_data_update_fn(
            deepcopy(self.synchronized_data), test_round
        )
        res = test_round.end_block()
        yield res
        assert res is not None

        synchronized_data, event = res

        for behaviour_attr_getter in synchronized_data_attr_checks:
            assert behaviour_attr_getter(synchronized_data) == behaviour_attr_getter(
                actual_next_synchronized_data
            ), f"Mismatch in synchronized_data. Actual:\n{behaviour_attr_getter(synchronized_data)}\nExpected:\n{behaviour_attr_getter(actual_next_synchronized_data)}"
        assert event == exit_event
        yield


class BaseVotingRoundTest(BaseRoundTestClass):  # pylint: disable=too-few-public-methods
    """Tests for rounds derived from VotingRound."""

    def _test_round(  # pylint: disable=too-many-arguments,too-many-locals
        self,
        test_round: VotingRound,
        round_payloads: Mapping[str, BaseTxPayload],
        synchronized_data_update_fn: Callable,
        synchronized_data_attr_checks: List[Callable],
        exit_event: Any,
        threshold_check: Callable,
    ) -> Generator:
        """Test for rounds derived from VotingRound."""

        (_, first_payload), *payloads = round_payloads.items()

        test_round.process_payload(first_payload)
        yield test_round
        assert not threshold_check(test_round)  # negative_vote_threshold_reached
        assert test_round.end_block() is None
        self._test_no_majority_event(test_round)

        for _, payload in payloads:
            test_round.process_payload(payload)
        yield test_round
        assert threshold_check(test_round)

        actual_next_synchronized_data = synchronized_data_update_fn(
            deepcopy(self.synchronized_data), test_round
        )
        res = test_round.end_block()
        yield res
        assert res is not None

        synchronized_data, event = res

        for behaviour_attr_getter in synchronized_data_attr_checks:
            assert behaviour_attr_getter(synchronized_data) == behaviour_attr_getter(
                actual_next_synchronized_data
            ), f"Mismatch in synchronized_data. Actual:\n{behaviour_attr_getter(synchronized_data)}\nExpected:\n{behaviour_attr_getter(actual_next_synchronized_data)}"
        assert event == exit_event
        yield

    def _test_voting_round_positive(
        self,
        test_round: VotingRound,
        round_payloads: Mapping[str, BaseTxPayload],
        synchronized_data_update_fn: Callable,
        synchronized_data_attr_checks: List[Callable],
        exit_event: Any,
    ) -> Generator:
        """Test for rounds derived from VotingRound."""

        return self._test_round(
            test_round,
            round_payloads,
            synchronized_data_update_fn,
            synchronized_data_attr_checks,
            exit_event,
            threshold_check=lambda x: x.positive_vote_threshold_reached,
        )

    def _test_voting_round_negative(
        self,
        test_round: VotingRound,
        round_payloads: Mapping[str, BaseTxPayload],
        synchronized_data_update_fn: Callable,
        synchronized_data_attr_checks: List[Callable],
        exit_event: Any,
    ) -> Generator:
        """Test for rounds derived from VotingRound."""

        return self._test_round(
            test_round,
            round_payloads,
            synchronized_data_update_fn,
            synchronized_data_attr_checks,
            exit_event,
            threshold_check=lambda x: x.negative_vote_threshold_reached,
        )

    def _test_voting_round_none(
        self,
        test_round: VotingRound,
        round_payloads: Mapping[str, BaseTxPayload],
        synchronized_data_update_fn: Callable,
        synchronized_data_attr_checks: List[Callable],
        exit_event: Any,
    ) -> Generator:
        """Test for rounds derived from VotingRound."""

        return self._test_round(
            test_round,
            round_payloads,
            synchronized_data_update_fn,
            synchronized_data_attr_checks,
            exit_event,
            threshold_check=lambda x: x.none_vote_threshold_reached,
        )


class BaseCollectDifferentUntilThresholdRoundTest(  # pylint: disable=too-few-public-methods
    BaseRoundTestClass
):
    """Tests for rounds derived from CollectDifferentUntilThresholdRound."""

    def _test_round(
        self,
        test_round: CollectDifferentUntilThresholdRound,
        round_payloads: Mapping[str, BaseTxPayload],
        synchronized_data_update_fn: Callable,
        synchronized_data_attr_checks: List[Callable],
        exit_event: Any,
    ) -> Generator:
        """Test for rounds derived from CollectDifferentUntilThresholdRound."""

        (_, first_payload), *payloads = round_payloads.items()

        test_round.process_payload(first_payload)
        yield test_round
        assert not test_round.collection_threshold_reached
        assert test_round.end_block() is None

        for _, payload in payloads:
            test_round.process_payload(payload)
        yield test_round
        assert test_round.collection_threshold_reached

        actual_next_synchronized_data = synchronized_data_update_fn(
            deepcopy(self.synchronized_data), test_round
        )

        res = test_round.end_block()
        yield res
        assert res is not None

        synchronized_data, event = res

        for behaviour_attr_getter in synchronized_data_attr_checks:
            assert behaviour_attr_getter(synchronized_data) == behaviour_attr_getter(
                actual_next_synchronized_data
            ), f"Mismatch in synchronized_data. Actual:\n{behaviour_attr_getter(synchronized_data)}\nExpected:\n{behaviour_attr_getter(actual_next_synchronized_data)}"
        assert event == exit_event
        yield


class BaseCollectNonEmptyUntilThresholdRound(  # pylint: disable=too-few-public-methods
    BaseCollectDifferentUntilThresholdRoundTest
):
    """Tests for rounds derived from `CollectNonEmptyUntilThresholdRound`."""


class _BaseRoundTestClass(BaseRoundTestClass):  # pylint: disable=too-few-public-methods
    """Base test class."""

    synchronized_data: BaseSynchronizedData
    participants: FrozenSet[str]
    consensus_params: ConsensusParams
    tx_payloads: List[DummyTxPayload]

    _synchronized_data_class = DummySynchronizedData

    def setup(
        self,
    ) -> None:
        """Setup test class."""

        super().setup()
        self.tx_payloads = get_dummy_tx_payloads(self.participants)

    @staticmethod
    def _test_payload_with_wrong_round_count(
        test_round: AbstractRound, value: Optional[Any] = None
    ) -> None:
        """Test errors raised by payloads with wrong round count."""
        payload_with_wrong_round_count = DummyTxPayload("sender", value, False)
        object.__setattr__(payload_with_wrong_round_count, "round_count", 0)
        with pytest.raises(
            TransactionNotValidError,
            match=re.escape("Expected round count -1 and got 0."),
        ):
            test_round.check_payload(payload=payload_with_wrong_round_count)

        with pytest.raises(
            ABCIAppInternalError,
            match=re.escape("Expected round count -1 and got 0."),
        ):
            test_round.process_payload(payload=payload_with_wrong_round_count)
