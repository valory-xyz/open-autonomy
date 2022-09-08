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

"""Test the rounds of the skill."""

# pylint: skip-file

import logging  # noqa: F401
from types import MappingProxyType
from typing import Dict, FrozenSet, cast
from unittest import mock

from packages.valory.skills.abstract_round_abci.base import (
    AbciAppDB,
    AbstractRound,
    ConsensusParams,
    MAX_INT_256,
)
from packages.valory.skills.hello_world_abci.payloads import (
    PrintMessagePayload,
    RegistrationPayload,
    ResetPayload,
    SelectKeeperPayload,
)
from packages.valory.skills.hello_world_abci.rounds import (
    Event,
    PrintMessageRound,
    RegistrationRound,
    ResetAndPauseRound,
    SelectKeeperRound,
    SynchronizedData,
)


MAX_PARTICIPANTS: int = 4


def get_participants() -> FrozenSet[str]:
    """Participants"""
    return frozenset([f"agent_{i}" for i in range(MAX_PARTICIPANTS)])


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

    synchronized_data: SynchronizedData
    consensus_params: ConsensusParams
    participants: FrozenSet[str]

    @classmethod
    def setup(
        cls,
    ) -> None:
        """Setup the test class."""

        cls.participants = get_participants()
        cls.synchronized_data = SynchronizedData(
            AbciAppDB(
                setup_data=dict(
                    participants=[cls.participants], all_participants=[cls.participants]
                ),
            )
        )
        cls.consensus_params = ConsensusParams(max_participants=MAX_PARTICIPANTS)

    def _test_no_majority_event(self, round_obj: AbstractRound) -> None:
        """Test the NO_MAJORITY event."""
        with mock.patch.object(round_obj, "is_majority_possible", return_value=False):
            result = round_obj.end_block()
            assert result is not None
            synchronized_data, event = result
            assert event == Event.NO_MAJORITY


class TestRegistrationRound(BaseRoundTestClass):
    """Tests for RegistrationRound."""

    def test_run(
        self,
    ) -> None:
        """Run tests."""

        test_round = RegistrationRound(
            synchronized_data=self.synchronized_data,
            consensus_params=self.consensus_params,
        )

        first_payload, *payloads = [
            RegistrationPayload(sender=participant) for participant in self.participants
        ]

        test_round.process_payload(first_payload)
        assert test_round.collection == {first_payload.sender: first_payload}
        assert test_round.end_block() is None

        for payload in payloads:
            test_round.process_payload(payload)

        actual_next_behaviour = SynchronizedData(
            AbciAppDB(setup_data=dict(participants=[test_round.collection]))
        )

        res = test_round.end_block()
        assert res is not None
        synchronized_data, event = res
        assert (
            cast(SynchronizedData, synchronized_data).participants
            == cast(SynchronizedData, actual_next_behaviour).participants
        )
        assert event == Event.DONE


class TestSelectKeeperRound(BaseRoundTestClass):
    """Tests for SelectKeeperRound."""

    def test_run(
        self,
    ) -> None:
        """Run tests."""

        test_round = SelectKeeperRound(
            synchronized_data=self.synchronized_data,
            consensus_params=self.consensus_params,
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

        actual_next_behaviour = self.synchronized_data.update(
            participant_to_selection=MappingProxyType(test_round.collection),
            most_voted_keeper_address=test_round.most_voted_payload,
        )

        res = test_round.end_block()
        assert res is not None
        synchronized_data, event = res
        assert all(
            [
                key
                in cast(SynchronizedData, synchronized_data).participant_to_selection
                for key in cast(
                    SynchronizedData, actual_next_behaviour
                ).participant_to_selection
            ]
        )
        assert event == Event.DONE


class TestPrintMessageRound(BaseRoundTestClass):
    """Tests for PrintMessageRound."""

    def test_run(
        self,
    ) -> None:
        """Run tests."""

        test_round = PrintMessageRound(
            synchronized_data=self.synchronized_data,
            consensus_params=self.consensus_params,
        )

        first_payload, *payloads = [
            PrintMessagePayload(sender=participant, message=f"{participant}_message")
            for participant in self.participants
        ]

        test_round.process_payload(first_payload)
        assert test_round.collection == {first_payload.sender: first_payload}
        assert test_round.end_block() is None

        for payload in payloads:
            test_round.process_payload(payload)

        actual_next_behaviour = SynchronizedData(
            AbciAppDB(setup_data=dict(participants=[test_round.collection]))
        )

        res = test_round.end_block()
        assert res is not None
        synchronized_data, event = res
        assert (
            cast(SynchronizedData, synchronized_data).participants
            == cast(SynchronizedData, actual_next_behaviour).participants
        )
        assert event == Event.DONE


class TestResetAndPauseRound(BaseRoundTestClass):
    """Tests for ResetAndPauseRound."""

    def test_run(
        self,
    ) -> None:
        """Run tests."""
        test_round = ResetAndPauseRound(
            synchronized_data=self.synchronized_data,
            consensus_params=self.consensus_params,
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

        actual_next_behaviour = self.synchronized_data.create(
            participants=[self.synchronized_data.participants],
            all_participants=[self.synchronized_data.all_participants],
        )

        res = test_round.end_block()
        assert res is not None
        synchronized_data, event = res

        assert (
            cast(SynchronizedData, synchronized_data).period_count
            == cast(SynchronizedData, actual_next_behaviour).period_count
        )

        assert event == Event.DONE


def test_synchronized_data() -> None:  # pylint:too-many-locals
    """Test SynchronizedData."""

    participants = get_participants()
    setup_params = {}  # type: ignore
    most_voted_randomness = "0xabcd"
    participant_to_selection = {
        participant: SelectKeeperPayload(sender=participant, keeper="keeper")
        for participant in participants
    }
    most_voted_keeper_address = "keeper"

    synchronized_data = SynchronizedData(
        AbciAppDB(
            setup_data=AbciAppDB.data_to_lists(
                dict(
                    participants=participants,
                    setup_params=setup_params,
                    most_voted_randomness=most_voted_randomness,
                    participant_to_selection=participant_to_selection,
                    most_voted_keeper_address=most_voted_keeper_address,
                )
            ),
        )
    )

    assert synchronized_data.participants == participants
    assert synchronized_data.period_count == 0
    assert synchronized_data.most_voted_randomness == most_voted_randomness
    assert synchronized_data.participant_to_selection == participant_to_selection
    assert synchronized_data.most_voted_keeper_address == most_voted_keeper_address
    assert synchronized_data.sorted_participants == sorted(participants)
    actual_keeper_randomness = int(most_voted_randomness, base=16) / MAX_INT_256
    assert (
        abs(synchronized_data.keeper_randomness - actual_keeper_randomness) < 1e-10
    )  # avoid equality comparisons between floats
