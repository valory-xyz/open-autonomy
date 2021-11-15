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

"""Test the base round classes."""

import re
from typing import AbstractSet, Any, Dict, List, Optional

import pytest

from packages.valory.skills.abstract_round_abci.base import (
    ABCIAppInternalError,
    AbstractRound,
    BasePeriodState,
    BaseTxPayload,
    CollectDifferentUntilAllRound,
    CollectDifferentUntilThresholdRound,
    CollectSameUntilThresholdRound,
    CollectionRound,
    ConsensusParams,
    OnlyKeeperSendsRound,
    TransactionNotValidError,
    VotingRound,
)

from tests.test_skills.test_price_estimation_abci.test_rounds import (
    MAX_PARTICIPANTS,
    get_participants,
)


class DummyTxPayload(BaseTxPayload):
    """Dummy Transaction Payload."""

    transaction_type = "DummyPayload"
    _value: str
    _vote: bool

    def __init__(
        self, sender: str, value: str, vote: bool = False
    ) -> None:
        """Initialize a dummy transaction payload."""

        super().__init__(sender, None)
        self._value = value
        self._vote = vote

    @property
    def value(self) -> str:
        """Get the tx value."""
        return self._value

    @property
    def vote(self) -> bool:
        """Get the vote value."""
        return self._vote


class DummyPeriodState(BasePeriodState):
    """Dummy Period state for tests."""

    def __init__(self,
                 participants: Optional[AbstractSet[str]] = None,
                 period_count: Optional[int] = None,
                 period_setup_params: Optional[Dict] = None,
                 most_voted_keeper_address: Optional[str] = None
                 ) -> None:
        """Initialize DummyPeriodState."""

        super().__init__(
            participants=participants,
            period_count=period_count,
            period_setup_params=period_setup_params,
        )
        self._most_voted_keeper_address = most_voted_keeper_address

    @property
    def most_voted_keeper_address(self,) -> Optional[str]:
        """Returns value for _most_voted_keeper_address."""
        return self._most_voted_keeper_address


def get_dummy_tx_payloads(participants: List[str], value: Any = None, vote: bool = False) -> List[DummyTxPayload]:
    """Returns a list of DummyTxPayload objects."""
    return [DummyTxPayload(sender=agent, value=(value or agent), vote=vote) for agent in participants]


class BaseTestClass:
    """Base test class."""

    period_state: BasePeriodState
    participants: List[str]
    consensus_params: ConsensusParams
    tx_payloads: List[DummyTxPayload]

    def setup(self,) -> None:
        """Setup test class."""

        self.participants = sorted(get_participants())
        self.tx_payloads = get_dummy_tx_payloads(self.participants)

        self.period_state = DummyPeriodState(
            participants=self.participants)  # type: ignore
        self.consensus_params = ConsensusParams(max_participants=MAX_PARTICIPANTS)


class DummyRound(AbstractRound):
    """Dummy round."""

    round_id = "round_id"
    allowed_tx_type = DummyTxPayload.transaction_type
    payload_attribute = "value"

    def end_block(self) -> None:
        """end_block method."""


class DummyCollectionRound(CollectionRound, DummyRound):
    """Dummy Class for CollectionRound"""


class DummyCollectDifferentUntilAllRound(CollectDifferentUntilAllRound, DummyRound):
    """Dummy Class for CollectDifferentUntilAllRound"""


class DummyCollectDifferentUntilThresholdRound(CollectDifferentUntilThresholdRound, DummyRound):
    """Dummy Class for CollectDifferentUntilThresholdRound"""


class DummyCollectSameUntilThresholdRound(CollectSameUntilThresholdRound, DummyRound):
    """Dummy Class for CollectSameUntilThresholdRound"""


class DummyOnlyKeeperSendsRound(OnlyKeeperSendsRound, DummyRound):
    """Dummy Class for OnlyKeeperSendsRound"""


class DummyVotingRound(VotingRound, DummyRound):
    """Dummy Class for VotingRound"""


class TestCollectionRound(BaseTestClass):
    """Test class for CollectionRound."""

    def test_run(self,) -> None:
        """Run tests."""

        test_round = DummyCollectionRound(
            state=self.period_state,
            consensus_params=self.consensus_params
        )

        first_payload, *_ = self.tx_payloads
        test_round.process_payload(first_payload)
        assert test_round.collection[first_payload.sender] == first_payload

        with pytest.raises(
            ABCIAppInternalError,
            match="internal error: sender agent_0 has already sent value for round: round_id"
        ):
            test_round.process_payload(first_payload)

        with pytest.raises(
            ABCIAppInternalError,
            match=re.escape(
                "internal error: sender not in list of participants: ['agent_0', 'agent_1', 'agent_2', 'agent_3']")
        ):
            test_round.process_payload(DummyTxPayload("sender", "value"))

        with pytest.raises(
            TransactionNotValidError,
            match="sender agent_0 has already sent value for round: round_id"
        ):
            test_round.check_payload(first_payload)

        with pytest.raises(
            TransactionNotValidError,
            match=re.escape(
                "sender not in list of participants: ['agent_0', 'agent_1', 'agent_2', 'agent_3']")
        ):
            test_round.check_payload(DummyTxPayload("sender", "value"))


class TestCollectDifferentUntilAllRound(BaseTestClass):
    """Test class for CollectDifferentUntilAllRound."""

    def test_run(self,) -> None:
        """Run Tests."""

        test_round = DummyCollectDifferentUntilAllRound(
            state=self.period_state,
            consensus_params=self.consensus_params
        )

        first_payload, *payloads = self.tx_payloads
        test_round.process_payload(first_payload)
        assert test_round.collection == {first_payload.value, }
        assert not test_round.collection_threshold_reached

        with pytest.raises(
            ABCIAppInternalError,
            match="internal error: payload attribute value with value agent_0 has already been added for round: round_id"
        ):
            test_round.process_payload(first_payload)

        with pytest.raises(
            TransactionNotValidError,
            match="payload attribute value with value agent_0 has already been added for round: round_id"
        ):
            test_round.check_payload(first_payload)

        for payload in payloads:
            test_round.process_payload(payload)


class TestCollectSameUntilThresholdRound(BaseTestClass):
    """Test CollectSameUntilThresholdRound."""

    def test_run(self,) -> None:
        """Run tests."""

        test_round = DummyCollectSameUntilThresholdRound(
            state=self.period_state,
            consensus_params=self.consensus_params
        )

        first_payload, * \
            payloads = get_dummy_tx_payloads(self.participants, value="vote")
        test_round.process_payload(first_payload)

        assert not test_round.threshold_reached
        with pytest.raises(ABCIAppInternalError, match="not enough votes"):
            _ = test_round.most_voted_payload

        for payload in payloads:
            test_round.process_payload(payload)

        assert test_round.threshold_reached
        assert test_round.most_voted_payload == "vote"


class TestOnlyKeeperSendsRound(BaseTestClass):
    """Test OnlyKeeperSendsRound."""

    def test_run(self,) -> None:
        """Run tests."""

        test_round = DummyOnlyKeeperSendsRound(
            state=self.period_state.update(
                most_voted_keeper_address="agent_0"
            ),
            consensus_params=self.consensus_params
        )

        assert not test_round.has_keeper_sent_payload
        first_payload, *_ = self.tx_payloads
        test_round.process_payload(first_payload)

        with pytest.raises(
            ABCIAppInternalError,
            match="internal error: keeper already set the payload."
        ):
            test_round.process_payload(first_payload)

        with pytest.raises(
            ABCIAppInternalError,
            match=re.escape(
                "internal error: sender not in list of participants: ['agent_0', 'agent_1', 'agent_2', 'agent_3']")
        ):
            test_round.process_payload(DummyTxPayload(sender="sender", value="sender"))

        with pytest.raises(
            ABCIAppInternalError,
            match="internal error: agent_1 not elected as keeper."
        ):
            test_round.process_payload(DummyTxPayload(sender="agent_1", value="sender"))

        with pytest.raises(
            TransactionNotValidError,
            match="keeper payload value already set."
        ):
            test_round.check_payload(first_payload)

        with pytest.raises(
            TransactionNotValidError,
            match=re.escape(
                "sender not in list of participants: ['agent_0', 'agent_1', 'agent_2', 'agent_3']")
        ):
            test_round.check_payload(DummyTxPayload(sender="sender", value="sender"))

        with pytest.raises(
            TransactionNotValidError,
            match="agent_1 not elected as keeper."
        ):
            test_round.check_payload(DummyTxPayload(sender="agent_1", value="sender"))


class TestVotingRound(BaseTestClass):
    """Test VotingRound."""

    def test_negative_threshold(self,) -> None:
        """Runs test."""

        test_round = DummyVotingRound(
            state=self.period_state,
            consensus_params=self.consensus_params
        )

        first_payload, *payloads = get_dummy_tx_payloads(self.participants, vote=False)
        test_round.process_payload(first_payload)

        assert not test_round.negative_vote_threshold_reached
        for payload in payloads:
            test_round.process_payload(payload)

        assert test_round.negative_vote_threshold_reached

    def test_positive_threshold(self,) -> None:
        """Runs test."""

        test_round = DummyVotingRound(
            state=self.period_state,
            consensus_params=self.consensus_params
        )

        first_payload, *payloads = get_dummy_tx_payloads(self.participants, vote=True)
        test_round.process_payload(first_payload)

        assert not test_round.positive_vote_threshold_reached
        for payload in payloads:
            test_round.process_payload(payload)

        assert test_round.positive_vote_threshold_reached


class TestCollectDifferentUntilThresholdRound(BaseTestClass):
    """Test CollectDifferentUntilThresholdRound."""

    def test_run(self,) -> None:
        """Run tests."""

        test_round = DummyCollectDifferentUntilThresholdRound(
            state=self.period_state,
            consensus_params=self.consensus_params
        )

        first_payload, *payloads = get_dummy_tx_payloads(self.participants, vote=False)
        test_round.process_payload(first_payload)

        assert not test_round.collection_threshold_reached
        for payload in payloads:
            test_round.process_payload(payload)

        assert test_round.collection_threshold_reached
