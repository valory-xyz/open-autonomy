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
import logging  # noqa: F401
from types import MappingProxyType
from typing import Dict, FrozenSet, cast
from unittest import mock

from packages.valory.skills.abstract_round_abci.base import (
    AbstractRound,
    ConsensusParams,
)
from packages.valory.skills.simple_abci.payloads import (
    RandomnessPayload,
    RegistrationPayload,
    ResetPayload,
    SelectKeeperPayload,
)
from packages.valory.skills.simple_abci.rounds import (
    Event,
    PeriodState,
    RandomnessStartupRound,
    RegistrationRound,
    ResetAndPauseRound,
    SelectKeeperAStartupRound,
    rotate_list,
)


MAX_PARTICIPANTS: int = 4
RANDOMNESS: str = "d1c29dce46f979f9748210d24bce4eae8be91272f5ca1a6aea2832d3dd676f51"


def get_participants() -> FrozenSet[str]:
    """Participants"""
    return frozenset([f"agent_{i}" for i in range(MAX_PARTICIPANTS)])


def get_participant_to_randomness(
    participants: FrozenSet[str], round_id: int
) -> Dict[str, RandomnessPayload]:
    """participant_to_randomness"""
    return {
        participant: RandomnessPayload(
            sender=participant,
            round_id=round_id,
            randomness=RANDOMNESS,
        )
        for participant in participants
    }


def get_participant_to_selection(
    participants: FrozenSet[str],
) -> Dict[str, SelectKeeperPayload]:
    """participant_to_selection"""
    return {
        participant: SelectKeeperPayload(sender=participant, keeper="keeper")
        for participant in participants
    }


def get_participant_to_period_count(
    participants: FrozenSet[str], period_count: int
) -> Dict[str, ResetPayload]:
    """participant_to_selection"""
    return {
        participant: ResetPayload(sender=participant, period_count=period_count)
        for participant in participants
    }


class BaseRoundTestClass:
    """Base test class for Rounds."""

    period_state: PeriodState
    consensus_params: ConsensusParams
    participants: FrozenSet[str]

    @classmethod
    def setup(
        cls,
    ) -> None:
        """Setup the test class."""

        cls.participants = get_participants()
        cls.period_state = PeriodState(participants=cls.participants)
        cls.consensus_params = ConsensusParams(max_participants=MAX_PARTICIPANTS)

    def _test_no_majority_event(self, round_obj: AbstractRound) -> None:
        """Test the NO_MAJORITY event."""
        with mock.patch.object(round_obj, "is_majority_possible", return_value=False):
            result = round_obj.end_block()
            assert result is not None
            state, event = result
            assert event == Event.NO_MAJORITY


class TestRegistrationRound(BaseRoundTestClass):
    """Tests for RegistrationRound."""

    def test_run(
        self,
    ) -> None:
        """Run tests."""

        test_round = RegistrationRound(
            state=self.period_state, consensus_params=self.consensus_params
        )

        first_payload, *payloads = [
            RegistrationPayload(sender=participant) for participant in self.participants
        ]

        test_round.process_payload(first_payload)
        assert test_round.collection == {first_payload.sender}
        assert test_round.end_block() is None

        for payload in payloads:
            test_round.process_payload(payload)

        actual_next_state = PeriodState(participants=test_round.collection)

        res = test_round.end_block()
        assert res is not None
        state, event = res
        assert (
            cast(PeriodState, state).participants
            == cast(PeriodState, actual_next_state).participants
        )
        assert event == Event.DONE


class TestRandomnessStartupRound(BaseRoundTestClass):
    """Tests for RandomnessStartupRound."""

    def test_run(
        self,
    ) -> None:
        """Run tests."""

        test_round = RandomnessStartupRound(
            state=self.period_state, consensus_params=self.consensus_params
        )
        first_payload, *payloads = [
            RandomnessPayload(sender=participant, randomness=RANDOMNESS, round_id=0)
            for participant in self.participants
        ]

        test_round.process_payload(first_payload)
        assert test_round.collection[first_payload.sender] == first_payload
        assert test_round.end_block() is None

        self._test_no_majority_event(test_round)

        for payload in payloads:
            test_round.process_payload(payload)

        actual_next_state = self.period_state.update(
            participant_to_randomness=MappingProxyType(test_round.collection),
            most_voted_randomness=test_round.most_voted_payload,
        )

        res = test_round.end_block()
        assert res is not None
        state, event = res
        assert all(
            [
                key in cast(PeriodState, state).participant_to_randomness
                for key in cast(
                    PeriodState, actual_next_state
                ).participant_to_randomness
            ]
        )
        assert event == Event.DONE


class TestSelectKeeperAStartupRound(BaseRoundTestClass):
    """Tests for SelectKeeperAStartupRound."""

    def test_run(
        self,
    ) -> None:
        """Run tests."""

        test_round = SelectKeeperAStartupRound(
            state=self.period_state, consensus_params=self.consensus_params
        )

        first_payload, *payloads = [
            SelectKeeperPayload(sender=participant, keeper="keeper")
            for participant in self.participants
        ]

        test_round.process_payload(first_payload)
        assert test_round.collection[first_payload.sender] == first_payload
        assert test_round.end_block() is None

        self._test_no_majority_event(test_round)

        for payload in payloads:
            test_round.process_payload(payload)

        actual_next_state = self.period_state.update(
            participant_to_selection=MappingProxyType(test_round.collection),
            most_voted_keeper_address=test_round.most_voted_payload,
        )

        res = test_round.end_block()
        assert res is not None
        state, event = res
        assert all(
            [
                key in cast(PeriodState, state).participant_to_selection
                for key in cast(PeriodState, actual_next_state).participant_to_selection
            ]
        )
        assert event == Event.DONE


class TestResetAndPauseRound(BaseRoundTestClass):
    """Tests for ResetAndPauseRound."""

    def test_run(
        self,
    ) -> None:
        """Run tests."""

        test_round = ResetAndPauseRound(
            state=self.period_state, consensus_params=self.consensus_params
        )

        first_payload, *payloads = [
            ResetPayload(sender=participant, period_count=1)
            for participant in self.participants
        ]

        test_round.process_payload(first_payload)
        assert test_round.collection[first_payload.sender] == first_payload
        assert test_round.end_block() is None

        self._test_no_majority_event(test_round)

        for payload in payloads:
            test_round.process_payload(payload)

        actual_next_state = self.period_state.update(
            period_count=test_round.most_voted_payload,
            participant_to_randomness=None,
            most_voted_randomness=None,
            participant_to_selection=None,
            most_voted_keeper_address=None,
        )

        res = test_round.end_block()
        assert res is not None
        state, event = res

        assert (
            cast(PeriodState, state).period_count
            == cast(PeriodState, actual_next_state).period_count
        )

        assert event == Event.DONE


def test_rotate_list_method() -> None:
    """Test `rotate_list` method."""

    ex_list = [1, 2, 3, 4, 5]
    assert rotate_list(ex_list, 2) == [3, 4, 5, 1, 2]


def test_period_state() -> None:  # pylint:too-many-locals
    """Test PeriodState."""

    participants = get_participants()
    period_count = 10
    period_setup_params = {}  # type: ignore
    participant_to_randomness = {
        participant: RandomnessPayload(
            sender=participant, randomness=RANDOMNESS, round_id=0
        )
        for participant in participants
    }
    most_voted_randomness = "0xabcd"
    participant_to_selection = {
        participant: SelectKeeperPayload(sender=participant, keeper="keeper")
        for participant in participants
    }
    most_voted_keeper_address = "keeper"

    period_state = PeriodState(
        participants=participants,
        period_count=period_count,
        period_setup_params=period_setup_params,
        participant_to_randomness=participant_to_randomness,
        most_voted_randomness=most_voted_randomness,
        participant_to_selection=participant_to_selection,
        most_voted_keeper_address=most_voted_keeper_address,
    )

    assert period_state.participants == participants
    assert period_state.period_count == period_count
    assert period_state.period_setup_params == period_setup_params
    assert period_state.participant_to_randomness == participant_to_randomness
    assert period_state.most_voted_randomness == most_voted_randomness
    assert period_state.participant_to_selection == participant_to_selection
    assert period_state.most_voted_keeper_address == most_voted_keeper_address
    assert period_state.sorted_participants == sorted(participants)
    assert period_state.keeper_randomness == cast(
        float, (int(most_voted_randomness, base=16) // 10 ** 0 % 10) / 10
    )
