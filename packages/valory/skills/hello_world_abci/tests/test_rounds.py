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

"""Test the rounds of the skill."""

# pylint: skip-file

import logging  # noqa: F401
from typing import cast

from packages.valory.skills.abstract_round_abci.base import AbciAppDB, MAX_INT_256
from packages.valory.skills.abstract_round_abci.test_tools.rounds import (
    BaseRoundTestClass as ExternalBaseRoundTestClass,
)
from packages.valory.skills.hello_world_abci.payloads import (
    CollectRandomnessPayload,
    PrintMessagePayload,
    RegistrationPayload,
    ResetPayload,
    SelectKeeperPayload,
)
from packages.valory.skills.hello_world_abci.rounds import (
    CollectRandomnessRound,
    Event,
    PrintMessageRound,
    RegistrationRound,
    ResetAndPauseRound,
    SelectKeeperRound,
    SynchronizedData,
)


MAX_PARTICIPANTS: int = 4
RANDOMNESS: str = "d1c29dce46f979f9748210d24bce4eae8be91272f5ca1a6aea2832d3dd676f51"


class BaseRoundTestClass(ExternalBaseRoundTestClass):
    """Base test class for Rounds."""

    _synchronized_data_class = SynchronizedData
    _event_class = Event


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
            AbciAppDB(setup_data=dict(participants=[frozenset(test_round.collection)]))
        )

        res = test_round.end_block()
        assert res is not None
        synchronized_data, event = res
        assert (
            cast(SynchronizedData, synchronized_data).participants
            == cast(SynchronizedData, actual_next_behaviour).participants
        )
        assert event == Event.DONE


class TestCollectRandomnessRound(BaseRoundTestClass):
    """Tests for CollectRandomnessRound."""

    def test_run(
        self,
    ) -> None:
        """Run tests."""

        test_round = CollectRandomnessRound(
            synchronized_data=self.synchronized_data,
            consensus_params=self.consensus_params,
        )
        first_payload, *payloads = [
            CollectRandomnessPayload(
                sender=participant, randomness=RANDOMNESS, round_id=0
            )
            for participant in self.participants
        ]

        test_round.process_payload(first_payload)
        assert test_round.collection[first_payload.sender] == first_payload
        assert test_round.end_block() is None

        self._test_no_majority_event(test_round)

        for payload in payloads:
            test_round.process_payload(payload)

        actual_next_behaviour = self.synchronized_data.update(
            participant_to_randomness=test_round.collection,
            most_voted_randomness=test_round.most_voted_payload,
        )

        res = test_round.end_block()
        assert res is not None
        synchronized_data, event = res
        assert all(
            [
                key
                in cast(SynchronizedData, synchronized_data).participant_to_randomness
                for key in cast(
                    SynchronizedData, actual_next_behaviour
                ).participant_to_randomness
            ]
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
            participant_to_selection=test_round.collection,
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

        printed_messages = [
            cast(PrintMessagePayload, payload).message
            for payload in test_round.collection.values()
        ]

        actual_next_behaviour = SynchronizedData(
            AbciAppDB(
                setup_data=dict(
                    participants=[test_round.collection],
                    printed_messages=[printed_messages],
                )
            )
        )

        res = test_round.end_block()
        assert res is not None
        synchronized_data, event = res

        assert (
            cast(SynchronizedData, synchronized_data).participants
            == cast(SynchronizedData, actual_next_behaviour).participants
        )
        assert (
            cast(SynchronizedData, synchronized_data).printed_messages
            == cast(SynchronizedData, actual_next_behaviour).printed_messages
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

    participants = frozenset([f"agent_{i}" for i in range(MAX_PARTICIPANTS)])
    participant_to_randomness = {
        participant: CollectRandomnessPayload(
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

    synchronized_data = SynchronizedData(
        AbciAppDB(
            setup_data=AbciAppDB.data_to_lists(
                dict(
                    participants=participants,
                    setup_params={},
                    participant_to_randomness=participant_to_randomness,
                    most_voted_randomness=most_voted_randomness,
                    participant_to_selection=participant_to_selection,
                    most_voted_keeper_address=most_voted_keeper_address,
                )
            ),
        )
    )

    assert synchronized_data.participants == participants
    assert synchronized_data.period_count == 0
    assert synchronized_data.participant_to_randomness == participant_to_randomness
    assert synchronized_data.most_voted_randomness == most_voted_randomness
    assert synchronized_data.participant_to_selection == participant_to_selection
    assert synchronized_data.most_voted_keeper_address == most_voted_keeper_address
    assert synchronized_data.sorted_participants == sorted(participants)
    actual_keeper_randomness = int(most_voted_randomness, base=16) / MAX_INT_256
    assert (
        abs(synchronized_data.keeper_randomness - actual_keeper_randomness) < 1e-10
    )  # avoid equality comparisons between floats
