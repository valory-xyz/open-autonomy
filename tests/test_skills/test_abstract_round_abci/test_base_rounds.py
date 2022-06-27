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

"""Test the base round classes."""

import re
from copy import deepcopy
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
    cast,
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
    ROUND_COUNT_DEFAULT,
    TransactionNotValidError,
    VotingRound,
)


MAX_PARTICIPANTS: int = 4


def get_participants() -> FrozenSet[str]:
    """Participants"""
    return frozenset([f"agent_{i}" for i in range(MAX_PARTICIPANTS)])


class DummyTxPayload(BaseTxPayload):
    """Dummy Transaction Payload."""

    transaction_type = "DummyPayload"
    _value: Optional[str]
    _vote: Optional[bool]

    def __init__(
        self,
        sender: str,
        value: Any,
        vote: Optional[bool] = False,
        round_count: int = ROUND_COUNT_DEFAULT,
    ) -> None:
        """Initialize a dummy transaction payload."""

        super().__init__(sender, None)
        self._value = value
        self._vote = vote
        self._round_count = round_count

    @property
    def value(self) -> Any:
        """Get the tx value."""
        return self._value

    @property
    def vote(self) -> Optional[bool]:
        """Get the vote value."""
        return self._vote


class DummySynchronizedSata(BaseSynchronizedData):
    """Dummy synchronized data for tests."""

    @property
    def most_voted_keeper_address(
        self,
    ) -> str:
        """Returns value for _most_voted_keeper_address."""
        return self.db.get_strict("most_voted_keeper_address")


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

    round_id = "round_id"
    allowed_tx_type = DummyTxPayload.transaction_type
    payload_attribute = "value"

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


class BaseRoundTestClass:
    """Base test class."""

    synchronized_data: BaseSynchronizedData
    participants: FrozenSet[str]
    consensus_params: ConsensusParams

    _synchronized_data_class: Type[BaseSynchronizedData]
    _event_class: Any

    @classmethod
    def setup(
        cls,
    ) -> None:
        """Setup test class."""

        cls.participants = get_participants()
        cls.synchronized_data = cls._synchronized_data_class(
            db=AbciAppDB(
                setup_data=dict(
                    participants=[cls.participants], all_participants=[cls.participants]
                ),
            )
        )  # type: ignore
        cls.consensus_params = ConsensusParams(max_participants=MAX_PARTICIPANTS)

    def _test_no_majority_event(self, round_obj: AbstractRound) -> None:
        """Test the NO_MAJORITY event."""
        with mock.patch.object(round_obj, "is_majority_possible", return_value=False):
            result = round_obj.end_block()
            assert result is not None
            _, event = result
            assert event == self._event_class.NO_MAJORITY

    def _complete_run(self, test_runner: Generator, iter_count: int = 4) -> None:
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


class BaseCollectDifferentUntilAllRoundTest(BaseRoundTestClass):
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

        actual_next_synchronized_data = cast(
            self._synchronized_data_class,  # type: ignore
            synchronized_data_update_fn(deepcopy(self.synchronized_data), test_round),  # type: ignore
        )

        res = test_round.end_block()
        yield res
        if exit_event is None:
            assert res is exit_event
        else:
            assert res is not None
            synchronized_data, event = res
            synchronized_data = cast(self._synchronized_data_class, synchronized_data)  # type: ignore
            for behaviour_attr_getter in synchronized_data_attr_checks:
                assert behaviour_attr_getter(
                    synchronized_data
                ) == behaviour_attr_getter(actual_next_synchronized_data)
            assert event == exit_event
        yield


class BaseCollectSameUntilAllRoundTest(BaseRoundTestClass):
    """Tests for rounds derived from CollectSameUntilAllRound."""

    def _test_round(
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
            "Expected: `n_votes = max_participants = 4`",
        ):
            _ = test_round.common_payload

        for _, payload in payloads:
            test_round.process_payload(payload)
        yield test_round
        if finished:
            assert test_round.collection_threshold_reached
        assert test_round.common_payload == most_voted_payload

        actual_next_synchronized_data = cast(
            self._synchronized_data_class,  # type: ignore
            synchronized_data_update_fn(deepcopy(self.synchronized_data), test_round),  # type: ignore
        )
        res = test_round.end_block()
        yield res
        assert res is not None

        synchronized_data, event = res
        synchronized_data = cast(self._synchronized_data_class, synchronized_data)  # type: ignore

        for behaviour_attr_getter in synchronized_data_attr_checks:
            assert behaviour_attr_getter(synchronized_data) == behaviour_attr_getter(
                actual_next_synchronized_data
            )
        assert event == exit_event
        yield


class BaseCollectSameUntilThresholdRoundTest(BaseRoundTestClass):
    """Tests for rounds derived from CollectSameUntilThresholdRound."""

    def _test_round(
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

        actual_next_synchronized_data = cast(
            self._synchronized_data_class,  # type: ignore
            synchronized_data_update_fn(deepcopy(self.synchronized_data), test_round),  # type: ignore
        )
        res = test_round.end_block()
        yield res
        assert res is not None

        synchronized_data, event = res
        synchronized_data = cast(self._synchronized_data_class, synchronized_data)  # type: ignore

        for behaviour_attr_getter in synchronized_data_attr_checks:
            assert behaviour_attr_getter(synchronized_data) == behaviour_attr_getter(
                actual_next_synchronized_data
            )
        assert event == exit_event
        yield


class BaseOnlyKeeperSendsRoundTest(BaseRoundTestClass):
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
        actual_next_synchronized_data = cast(
            self._synchronized_data_class,  # type: ignore
            synchronized_data_update_fn(deepcopy(self.synchronized_data), test_round),  # type: ignore
        )
        res = test_round.end_block()
        yield res
        assert res is not None

        synchronized_data, event = res
        synchronized_data = cast(self._synchronized_data_class, synchronized_data)  # type: ignore
        for behaviour_attr_getter in synchronized_data_attr_checks:
            assert behaviour_attr_getter(synchronized_data) == behaviour_attr_getter(
                actual_next_synchronized_data
            )
        assert event == exit_event
        yield


class BaseVotingRoundTest(BaseRoundTestClass):
    """Tests for rounds derived from VotingRound."""

    def _test_round(
        self,
        test_round: VotingRound,
        round_payloads: Mapping[str, BaseTxPayload],
        synchronized_data_update_fn: Callable,
        synchronized_data_attr_checks: List[Callable],
        exit_event: Any,
        threshold_check: Callable,
    ) -> Generator:
        """Test for rounds derived from VotingRound."""

        (sender, first_payload), *payloads = round_payloads.items()

        test_round.process_payload(first_payload)
        yield test_round
        assert not threshold_check(test_round)  # negative_vote_threshold_reached
        assert test_round.end_block() is None
        self._test_no_majority_event(test_round)

        for _, payload in payloads:
            test_round.process_payload(payload)
        yield test_round
        assert threshold_check(test_round)

        actual_next_synchronized_data = cast(
            self._synchronized_data_class,  # type: ignore
            synchronized_data_update_fn(deepcopy(self.synchronized_data), test_round),  # type: ignore
        )
        res = test_round.end_block()
        yield res
        assert res is not None

        synchronized_data, event = res
        synchronized_data = cast(self._synchronized_data_class, synchronized_data)  # type: ignore
        for behaviour_attr_getter in synchronized_data_attr_checks:
            assert behaviour_attr_getter(synchronized_data) == behaviour_attr_getter(
                actual_next_synchronized_data
            )
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


class BaseCollectDifferentUntilThresholdRoundTest(BaseRoundTestClass):
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

        actual_next_synchronized_data = cast(
            self._synchronized_data_class,  # type: ignore
            synchronized_data_update_fn(deepcopy(self.synchronized_data), test_round),  # type: ignore
        )
        res = test_round.end_block()
        yield res
        assert res is not None

        synchronized_data, event = res
        synchronized_data = cast(self._synchronized_data_class, synchronized_data)  # type: ignore

        for behaviour_attr_getter in synchronized_data_attr_checks:
            assert behaviour_attr_getter(synchronized_data) == behaviour_attr_getter(
                actual_next_synchronized_data
            )
        assert event == exit_event
        yield


class BaseCollectNonEmptyUntilThresholdRound(
    BaseCollectDifferentUntilThresholdRoundTest
):
    """Tests for rounds derived from `CollectNonEmptyUntilThresholdRound`."""


class _BaseRoundTestClass(BaseRoundTestClass):
    """Base test class."""

    synchronized_data: BaseSynchronizedData
    participants: FrozenSet[str]
    consensus_params: ConsensusParams
    tx_payloads: List[DummyTxPayload]

    _synchronized_data_class = DummySynchronizedSata

    @classmethod
    def setup(
        cls,
    ) -> None:
        """Setup test class."""

        super().setup()
        cls.tx_payloads = get_dummy_tx_payloads(cls.participants)

    def _test_payload_with_wrong_round_count(
        self, test_round: AbstractRound, value: Optional[Any] = None
    ) -> None:
        """Test errors raised by pyaloads with wrong round count."""
        payload_with_wrong_round_count = DummyTxPayload("sender", value, False, 0)
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


class TestCollectionRound(_BaseRoundTestClass):
    """Test class for CollectionRound."""

    def test_run(
        self,
    ) -> None:
        """Run tests."""

        test_round = DummyCollectionRound(
            synchronized_data=self.synchronized_data,
            consensus_params=self.consensus_params,
        )

        # collection round may set a flag to allow payments from inactive agents (rejoin)
        assert test_round._allow_rejoin_payloads is False  # default
        assert test_round.accepting_payloads_from is self.synchronized_data.participants
        test_round._allow_rejoin_payloads = True
        assert (
            test_round.accepting_payloads_from
            is self.synchronized_data.all_participants
        )

        first_payload, *_ = self.tx_payloads
        test_round.process_payload(first_payload)
        assert test_round.collection[first_payload.sender] == first_payload

        with pytest.raises(
            ABCIAppInternalError,
            match="internal error: sender agent_0 has already sent value for round: round_id",
        ):
            test_round.process_payload(first_payload)

        with pytest.raises(
            ABCIAppInternalError,
            match=re.escape(
                "internal error: sender not in list of participants: ['agent_0', 'agent_1', 'agent_2', 'agent_3']"
            ),
        ):
            test_round.process_payload(DummyTxPayload("sender", "value"))

        with pytest.raises(
            TransactionNotValidError,
            match="sender agent_0 has already sent value for round: round_id",
        ):
            test_round.check_payload(first_payload)

        with pytest.raises(
            TransactionNotValidError,
            match=re.escape(
                "sender not in list of participants: ['agent_0', 'agent_1', 'agent_2', 'agent_3']"
            ),
        ):
            test_round.check_payload(DummyTxPayload("sender", "value"))

        self._test_payload_with_wrong_round_count(test_round)


class TestCollectDifferentUntilAllRound(_BaseRoundTestClass):
    """Test class for CollectDifferentUntilAllRound."""

    def test_run(
        self,
    ) -> None:
        """Run Tests."""

        test_round = DummyCollectDifferentUntilAllRound(
            synchronized_data=self.synchronized_data,
            consensus_params=self.consensus_params,
        )

        first_payload, *payloads = self.tx_payloads
        test_round.process_payload(first_payload)
        assert not test_round.collection_threshold_reached

        with pytest.raises(
            ABCIAppInternalError,
            match="internal error: sender agent_0 has already sent value for round: round_id",
        ):
            test_round.process_payload(first_payload)

        with pytest.raises(
            TransactionNotValidError,
            match="sender agent_0 has already sent value for round: round_id",
        ):
            test_round.check_payload(first_payload)

        with pytest.raises(
            ABCIAppInternalError,
            match="internal error: `CollectDifferentUntilAllRound` encountered a value 'agent_0' that already exists.",
        ):
            first_payload.sender = "other"
            test_round.process_payload(first_payload)

        with pytest.raises(
            TransactionNotValidError,
            match="`CollectDifferentUntilAllRound` encountered a value 'agent_0' that already exists.",
        ):
            test_round.check_payload(first_payload)

        for payload in payloads:
            assert not test_round.collection_threshold_reached
            test_round.process_payload(payload)

        assert test_round.collection_threshold_reached
        self._test_payload_with_wrong_round_count(test_round)


class TestCollectSameUntilAllRound(_BaseRoundTestClass):
    """Test class for CollectSameUntilAllRound."""

    def test_run(
        self,
    ) -> None:
        """Run Tests."""

        test_round = DummyCollectSameUntilAllRound(
            synchronized_data=self.synchronized_data,
            consensus_params=self.consensus_params,
        )

        first_payload, *payloads = [
            DummyTxPayload(
                sender=agent,
                value="test",
            )
            for agent in sorted(self.participants)
        ]
        test_round.process_payload(first_payload)
        assert not test_round.collection_threshold_reached

        with pytest.raises(
            ABCIAppInternalError,
            match="internal error: sender agent_0 has already sent value for round: round_id",
        ):
            test_round.process_payload(first_payload)

        with pytest.raises(
            TransactionNotValidError,
            match="sender agent_0 has already sent value for round: round_id",
        ):
            test_round.check_payload(first_payload)

        with pytest.raises(
            ABCIAppInternalError,
            match="internal error: `CollectSameUntilAllRound` encountered a value 'other' "
            "which is not the same as the already existing one: 'test",
        ):
            bad_payload = DummyTxPayload(
                sender="other",
                value="other",
            )
            test_round.process_payload(bad_payload)

        with pytest.raises(
            TransactionNotValidError,
            match="`CollectSameUntilAllRound` encountered a value 'other' "
            "which is not the same as the already existing one: 'test",
        ):
            test_round.check_payload(bad_payload)

        for payload in payloads:
            assert not test_round.collection_threshold_reached
            test_round.process_payload(payload)

        assert test_round.collection_threshold_reached
        self._test_payload_with_wrong_round_count(test_round, "test")


class TestCollectSameUntilThresholdRound(_BaseRoundTestClass):
    """Test CollectSameUntilThresholdRound."""

    def test_run(
        self,
    ) -> None:
        """Run tests."""

        test_round = DummyCollectSameUntilThresholdRound(
            synchronized_data=self.synchronized_data,
            consensus_params=self.consensus_params,
        )

        first_payload, *payloads = get_dummy_tx_payloads(
            self.participants, value="vote"
        )
        test_round.process_payload(first_payload)

        assert not test_round.threshold_reached
        with pytest.raises(ABCIAppInternalError, match="not enough votes"):
            _ = test_round.most_voted_payload

        for payload in payloads:
            test_round.process_payload(payload)

        assert test_round.threshold_reached
        assert test_round.most_voted_payload == "vote"

        self._test_payload_with_wrong_round_count(test_round)

    def test_run_with_none(
        self,
    ) -> None:
        """Run tests."""

        test_round = DummyCollectSameUntilThresholdRound(
            synchronized_data=self.synchronized_data,
            consensus_params=self.consensus_params,
        )

        first_payload, *payloads = get_dummy_tx_payloads(
            self.participants,
            value=None,
            is_value_none=True,
        )
        test_round.process_payload(first_payload)

        assert not test_round.threshold_reached
        with pytest.raises(ABCIAppInternalError, match="not enough votes"):
            _ = test_round.most_voted_payload

        for payload in payloads:
            test_round.process_payload(payload)

        assert test_round.threshold_reached
        assert test_round.most_voted_payload is None


class TestOnlyKeeperSendsRound(_BaseRoundTestClass, BaseOnlyKeeperSendsRoundTest):
    """Test OnlyKeeperSendsRound."""

    def test_run(
        self,
    ) -> None:
        """Run tests."""

        test_round = DummyOnlyKeeperSendsRound(
            synchronized_data=self.synchronized_data.update(
                most_voted_keeper_address="agent_0"
            ),
            consensus_params=self.consensus_params,
        )

        assert not test_round.has_keeper_sent_payload
        first_payload, *_ = self.tx_payloads
        test_round.process_payload(first_payload)

        with pytest.raises(
            ABCIAppInternalError,
            match="internal error: keeper already set the payload.",
        ):
            test_round.process_payload(first_payload)

        with pytest.raises(
            ABCIAppInternalError,
            match=re.escape(
                "internal error: sender not in list of participants: ['agent_0', 'agent_1', 'agent_2', 'agent_3']"
            ),
        ):
            test_round.process_payload(DummyTxPayload(sender="sender", value="sender"))

        with pytest.raises(
            ABCIAppInternalError, match="internal error: agent_1 not elected as keeper."
        ):
            test_round.process_payload(DummyTxPayload(sender="agent_1", value="sender"))

        with pytest.raises(
            TransactionNotValidError, match="keeper payload value already set."
        ):
            test_round.check_payload(first_payload)

        with pytest.raises(
            TransactionNotValidError,
            match=re.escape(
                "sender not in list of participants: ['agent_0', 'agent_1', 'agent_2', 'agent_3']"
            ),
        ):
            test_round.check_payload(DummyTxPayload(sender="sender", value="sender"))

        with pytest.raises(
            TransactionNotValidError, match="agent_1 not elected as keeper."
        ):
            test_round.check_payload(DummyTxPayload(sender="agent_1", value="sender"))

        self._test_payload_with_wrong_round_count(test_round)

    def test_keeper_payload_is_none(
        self,
    ) -> None:
        """Test keeper payload valur set to none."""

        keeper = "agent_0"
        self._complete_run(
            self._test_round(
                test_round=DummyOnlyKeeperSendsRound(
                    synchronized_data=self.synchronized_data.update(
                        most_voted_keeper_address=keeper,
                    ),
                    consensus_params=self.consensus_params,
                ),
                keeper_payloads=DummyTxPayload(keeper, None),
                synchronized_data_update_fn=lambda _synchronized_data, _test_round: _synchronized_data,
                synchronized_data_attr_checks=[],
                exit_event="FAIL_EVENT",
            )
        )


class TestVotingRound(_BaseRoundTestClass):
    """Test VotingRound."""

    def setup_test_voting_round(self) -> DummyVotingRound:
        """Setup test voting round"""
        return DummyVotingRound(
            synchronized_data=self.synchronized_data,
            consensus_params=self.consensus_params,
        )

    def test_vote_count(self) -> None:
        """Testing agent vote count"""
        test_round = self.setup_test_voting_round()
        a, b, c, d = self.participants
        for agents, vote in [((a, d), True), ((c,), False), ((b,), None)]:
            for payload in get_dummy_tx_payloads(frozenset(agents), vote=vote):
                test_round.process_payload(payload)
        assert dict(test_round.vote_count) == {True: 2, False: 1, None: 1}

        self._test_payload_with_wrong_round_count(test_round)

    def test_negative_threshold(
        self,
    ) -> None:
        """Runs test."""

        test_round = self.setup_test_voting_round()
        first_payload, *payloads = get_dummy_tx_payloads(self.participants, vote=False)
        test_round.process_payload(first_payload)

        assert not test_round.negative_vote_threshold_reached
        for payload in payloads:
            test_round.process_payload(payload)

        assert test_round.negative_vote_threshold_reached

    def test_positive_threshold(
        self,
    ) -> None:
        """Runs test."""

        test_round = self.setup_test_voting_round()
        first_payload, *payloads = get_dummy_tx_payloads(self.participants, vote=True)
        test_round.process_payload(first_payload)

        assert not test_round.positive_vote_threshold_reached
        for payload in payloads:
            test_round.process_payload(payload)

        assert test_round.positive_vote_threshold_reached


class TestCollectDifferentUntilThresholdRound(_BaseRoundTestClass):
    """Test CollectDifferentUntilThresholdRound."""

    @pytest.mark.parametrize(
        "required_confirmations", (MAX_PARTICIPANTS, MAX_PARTICIPANTS + 1)
    )
    def test_run(
        self,
        required_confirmations: int,
    ) -> None:
        """Run tests."""

        test_round = DummyCollectDifferentUntilThresholdRound(
            synchronized_data=self.synchronized_data,
            consensus_params=self.consensus_params,
        )
        test_round.block_confirmations = 0
        test_round.required_block_confirmations = required_confirmations
        test_round.selection_key = "selection_key"
        test_round.collection_key = "collection_key"
        test_round.done_event = 0
        test_round.no_majority_event = 1
        assert (
            test_round.consensus_threshold <= required_confirmations
        ), "Incorrect test parametrization: required confirmations cannot be set with a smalled value than the consensus threshold"

        first_payload, *payloads = get_dummy_tx_payloads(self.participants, vote=False)
        test_round.process_payload(first_payload)

        assert not test_round.collection_threshold_reached
        for payload in payloads:
            test_round.process_payload(payload)
            res = test_round.end_block()
            if test_round.block_confirmations <= required_confirmations:
                assert res is None
            else:
                assert res is not None
                assert res[1] == test_round.done_event
        assert test_round.collection_threshold_reached
        self._test_payload_with_wrong_round_count(test_round)


class TestCollectNonEmptyUntilThresholdRound(_BaseRoundTestClass):
    """Test `CollectNonEmptyUntilThresholdRound`."""

    def test_get_non_empty_values(self) -> None:
        """Test `_get_non_empty_values`."""
        test_round = DummyCollectNonEmptyUntilThresholdRound(
            synchronized_data=self.synchronized_data,
            consensus_params=self.consensus_params,
        )
        payloads = get_dummy_tx_payloads(self.participants)
        payloads[3]._value = None
        for payload in payloads:
            test_round.process_payload(payload)

        non_empty_values = test_round._get_non_empty_values()
        assert non_empty_values == [f"agent_{i}" for i in range(3)]

        self._test_payload_with_wrong_round_count(test_round)

    def test_process_payload(self) -> None:
        """Test `process_payload`."""
        test_round = DummyCollectNonEmptyUntilThresholdRound(
            synchronized_data=self.synchronized_data,
            consensus_params=self.consensus_params,
        )

        first_payload, *payloads = get_dummy_tx_payloads(self.participants)
        test_round.process_payload(first_payload)

        assert not test_round.collection_threshold_reached
        for payload in payloads:
            test_round.process_payload(payload)

        assert test_round.collection_threshold_reached

    @pytest.mark.parametrize("is_majority_possible", (True, False))
    def test_end_block_no_threshold_reached(self, is_majority_possible: bool) -> None:
        """Test `end_block` when no collection threshold is reached."""
        test_round = DummyCollectNonEmptyUntilThresholdRound(
            synchronized_data=self.synchronized_data,
            consensus_params=self.consensus_params,
        )

        test_round.is_majority_possible = lambda *_: is_majority_possible  # type: ignore
        test_round.no_majority_event = "no_majority"

        res = cast(Tuple[BaseSynchronizedData, Enum], test_round.end_block())

        if test_round.block_confirmations > test_round.required_block_confirmations:
            assert res[0].db == self.synchronized_data.db
            assert res[1] == test_round.no_majority_event
        else:
            assert res is None

    @pytest.mark.parametrize(
        "is_value_none, expected_event", ((True, "none"), (False, "done"))
    )
    def test_end_block(self, is_value_none: bool, expected_event: str) -> None:
        """Test `end_block` when collection threshold is reached."""
        test_round = DummyCollectNonEmptyUntilThresholdRound(
            synchronized_data=self.synchronized_data,
            consensus_params=self.consensus_params,
        )

        payloads = get_dummy_tx_payloads(self.participants, is_value_none=is_value_none)
        for payload in payloads:
            test_round.process_payload(payload)

        test_round.collection = {f"test_{i}": payloads[i] for i in range(len(payloads))}
        test_round.selection_key = "test"
        test_round.collection_key = "test"
        test_round.done_event = "done"
        test_round.none_event = "none"

        res = cast(Tuple[BaseSynchronizedData, Enum], test_round.end_block())
        assert res[0].db == self.synchronized_data.db
        assert res[1] == expected_event
