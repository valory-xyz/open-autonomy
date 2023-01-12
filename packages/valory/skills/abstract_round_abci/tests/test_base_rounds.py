# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2023 Valory AG
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

# pylint: skip-file

import re
from enum import Enum
from typing import FrozenSet, List, Optional, Tuple, cast

import pytest

from packages.valory.skills.abstract_round_abci.base import (
    ABCIAppInternalError,
    BaseSynchronizedData,
    BaseTxPayload,
    TransactionNotValidError,
)
from packages.valory.skills.abstract_round_abci.test_tools.rounds import (
    BaseOnlyKeeperSendsRoundTest,
    DummyCollectDifferentUntilAllRound,
    DummyCollectDifferentUntilThresholdRound,
    DummyCollectNonEmptyUntilThresholdRound,
    DummyCollectSameUntilAllRound,
    DummyCollectSameUntilThresholdRound,
    DummyCollectionRound,
    DummyEvent,
    DummyOnlyKeeperSendsRound,
    DummyTxPayload,
    DummyVotingRound,
    MAX_PARTICIPANTS,
    _BaseRoundTestClass,
    get_dummy_tx_payloads,
)


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
        round_id = DummyCollectionRound.auto_round_id()

        # collection round may set a flag to allow payments from inactive agents (rejoin)
        assert test_round._allow_rejoin_payloads is False  # default
        assert test_round.accepting_payloads_from == self.synchronized_data.participants
        test_round._allow_rejoin_payloads = True
        assert (
            test_round.accepting_payloads_from
            == self.synchronized_data.all_participants
        )

        first_payload, *_ = self.tx_payloads
        test_round.process_payload(first_payload)
        assert test_round.collection[first_payload.sender] == first_payload

        with pytest.raises(
            ABCIAppInternalError,
            match=f"internal error: sender agent_0 has already sent value for round: {round_id}",
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
            ABCIAppInternalError,
            match=re.escape(
                f"internal error: Expecting serialized data of chunk size 2, got: 0xZZZ in {round_id}"
            ),
        ):
            test_round._hash_length = 2
            test_round.process_payload(DummyTxPayload("agent_1", "0xZZZ"))
            test_round._hash_length = None

        with pytest.raises(
            TransactionNotValidError,
            match=f"sender agent_0 has already sent value for round: {round_id}",
        ):
            test_round.check_payload(first_payload)

        with pytest.raises(
            TransactionNotValidError,
            match=re.escape(
                "sender not in list of participants: ['agent_0', 'agent_1', 'agent_2', 'agent_3']"
            ),
        ):
            test_round.check_payload(DummyTxPayload("sender", "value"))

        with pytest.raises(
            TransactionNotValidError,
            match=re.escape(
                f"Expecting serialized data of chunk size 2, got: 0xZZZ in {round_id}"
            ),
        ):
            test_round.check_payload(DummyTxPayload("agent_1", "0xZZZ"))

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
        round_id = DummyCollectDifferentUntilAllRound.auto_round_id()

        first_payload, *payloads = self.tx_payloads
        test_round.process_payload(first_payload)
        assert not test_round.collection_threshold_reached

        with pytest.raises(
            ABCIAppInternalError,
            match=f"internal error: sender agent_0 has already sent value for round: {round_id}",
        ):
            test_round.process_payload(first_payload)

        with pytest.raises(
            TransactionNotValidError,
            match=f"sender agent_0 has already sent value for round: {round_id}",
        ):
            test_round.check_payload(first_payload)

        with pytest.raises(
            ABCIAppInternalError,
            match="internal error: `CollectDifferentUntilAllRound` encountered a value 'agent_0' that already exists.",
        ):
            object.__setattr__(first_payload, "sender", "other")
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
        round_id = DummyCollectSameUntilAllRound.auto_round_id()

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
            match="1 votes are not enough for `CollectSameUntilAllRound`",
        ):
            assert test_round.common_payload

        with pytest.raises(
            ABCIAppInternalError,
            match=f"internal error: sender agent_0 has already sent value for round: {round_id}",
        ):
            test_round.process_payload(first_payload)

        with pytest.raises(
            TransactionNotValidError,
            match=f"sender agent_0 has already sent value for round: {round_id}",
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
        assert test_round.common_payload
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
        test_round.collection_key = "dummy_collection_key"
        test_round.selection_key = "dummy_selection_key"
        assert test_round.end_block() is None

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

        test_round.done_event = DummyEvent.DONE
        return_value = cast(Tuple[BaseSynchronizedData, Enum], test_round.end_block())
        assert return_value[-1] == test_round.done_event

        test_round.none_event = DummyEvent.NONE
        test_round.collection.clear()
        payloads = get_dummy_tx_payloads(self.participants, value=None)
        for payload in payloads:  # must overwrite the value...
            object.__setattr__(payload, "value", None)
            test_round.process_payload(payload)
        assert test_round.most_voted_payload is None
        return_value = cast(Tuple[BaseSynchronizedData, Enum], test_round.end_block())
        assert return_value[-1] == test_round.none_event

        test_round.no_majority_event = DummyEvent.NO_MAJORITY
        test_round.collection.clear()
        for participant in self.participants:
            payload = DummyTxPayload(participant, value=participant)
            test_round.process_payload(payload)
        return_value = cast(Tuple[BaseSynchronizedData, Enum], test_round.end_block())
        assert return_value[-1] == test_round.no_majority_event

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
        assert test_round.has_keeper_sent_payload

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

        test_round.done_event = DummyEvent.DONE
        test_round.payload_key = "dummy_key"
        assert test_round.end_block()

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

    @pytest.mark.parametrize("vote", [True, False, None])
    def test_threshold(self, vote: Optional[bool]) -> None:
        """Runs threshold test."""

        test_round = self.setup_test_voting_round()
        test_round.collection_key = "dummy_collection_key"
        test_round.done_event = DummyEvent.DONE
        test_round.negative_event = DummyEvent.NEGATIVE
        test_round.none_event = DummyEvent.NONE

        expected_threshold = {
            True: lambda: test_round.positive_vote_threshold_reached,
            False: lambda: test_round.negative_vote_threshold_reached,
            None: lambda: test_round.none_vote_threshold_reached,
        }[vote]

        expected_event = {
            True: test_round.done_event,
            False: test_round.negative_event,
            None: test_round.none_event,
        }[vote]

        first_payload, *payloads = get_dummy_tx_payloads(self.participants, vote=vote)
        test_round.process_payload(first_payload)
        assert test_round.end_block() is None
        assert not expected_threshold()
        for payload in payloads:
            test_round.process_payload(payload)
        assert expected_threshold()
        return_value = cast(Tuple[BaseSynchronizedData, Enum], test_round.end_block())
        assert return_value[-1] == expected_event

    def test_end_round_no_majority(self) -> None:
        """Test end round"""

        test_round = self.setup_test_voting_round()
        test_round.no_majority_event = DummyEvent.NO_MAJORITY
        for i, participant in enumerate(self.participants):
            payload = DummyTxPayload(participant, value=participant, vote=bool(i % 2))
            test_round.process_payload(payload)
        return_value = cast(Tuple[BaseSynchronizedData, Enum], test_round.end_block())
        assert return_value[-1] == test_round.no_majority_event

    def test_invalid_vote_payload_count(self) -> None:
        """Testing agent vote count with invalid payload."""
        test_round = self.setup_test_voting_round()
        a, b, c, d = self.participants

        class InvalidPayload(BaseTxPayload):
            """InvalidPayload"""

        def get_dummy_tx_payloads_(
            participants: FrozenSet[str],
        ) -> List[BaseTxPayload]:
            """Returns a list of DummyTxPayload objects."""
            return [InvalidPayload(sender=agent) for agent in sorted(participants)]

        for agents in [(a, d), (c,), (b,)]:
            for payload in get_dummy_tx_payloads_(frozenset(agents)):
                test_round.process_payload(payload)

        with pytest.raises(ValueError):
            test_round.vote_count


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

    def test_end_round(self) -> None:
        """Test end round"""

        test_round = DummyCollectDifferentUntilThresholdRound(
            synchronized_data=self.synchronized_data,
            consensus_params=self.consensus_params,
        )
        test_round.collection_key = "dummy_collection_key"
        test_round.done_event = DummyEvent.DONE

        assert test_round.end_block() is None
        for participant in self.participants:
            payload = DummyTxPayload(participant, value=participant)
            test_round.process_payload(payload)
        return_value = cast(Tuple[BaseSynchronizedData, Enum], test_round.end_block())
        assert return_value[-1] == test_round.done_event


class TestCollectNonEmptyUntilThresholdRound(_BaseRoundTestClass):
    """Test `CollectNonEmptyUntilThresholdRound`."""

    def test_get_non_empty_values(self) -> None:
        """Test `_get_non_empty_values`."""
        test_round = DummyCollectNonEmptyUntilThresholdRound(
            synchronized_data=self.synchronized_data,
            consensus_params=self.consensus_params,
        )
        payloads = get_dummy_tx_payloads(self.participants)
        object.__setattr__(payloads[3], "value", None)
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
    @pytest.mark.parametrize("reach_block_confirmations", (True, False))
    def test_end_block_no_threshold_reached(
        self, is_majority_possible: bool, reach_block_confirmations: bool
    ) -> None:
        """Test `end_block` when no collection threshold is reached."""
        test_round = DummyCollectNonEmptyUntilThresholdRound(
            synchronized_data=self.synchronized_data,
            consensus_params=self.consensus_params,
        )
        test_round.block_confirmations = (
            test_round.required_block_confirmations + 1
            if reach_block_confirmations
            else 0
        )

        # TODO: fix below - type error indicates problem with this
        test_round.is_majority_possible = lambda *_: is_majority_possible  # type: ignore
        test_round.no_majority_event = DummyEvent.NO_MAJORITY

        res = test_round.end_block()

        if (
            test_round.block_confirmations > test_round.required_block_confirmations
            and not is_majority_possible
        ):
            assert res is not None
            assert res[0].db == self.synchronized_data.db
            assert res[1] == test_round.no_majority_event
        else:
            assert res is None

    @pytest.mark.parametrize(
        "is_value_none, expected_event",
        ((True, DummyEvent.NONE), (False, DummyEvent.DONE)),
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
        test_round.collection_key = "test"
        test_round.done_event = DummyEvent.DONE
        test_round.none_event = DummyEvent.NONE

        res = cast(Tuple[BaseSynchronizedData, Enum], test_round.end_block())
        assert res[0].db == self.synchronized_data.db
        assert res[1] == expected_event
