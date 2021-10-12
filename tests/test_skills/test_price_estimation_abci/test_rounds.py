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
from typing import List, Set, Tuple

import pytest
from aea.exceptions import AEAEnforceError

from packages.valory.skills.abstract_round_abci.base import (
    ABCIAppInternalError,
    ConsensusParams,
    TransactionNotValidError,
)
from packages.valory.skills.price_estimation_abci.payloads import (  # noqa: F401
    DeploySafePayload,
    EstimatePayload,
    FinalizationTxPayload,
    ObservationPayload,
    RandomnessPayload,
    RegistrationPayload,
    SelectKeeperPayload,
    SignaturePayload,
    TransactionHashPayload,
    ValidatePayload,
)
from packages.valory.skills.price_estimation_abci.rounds import (  # noqa: F401
    CollectObservationRound,
    CollectSignatureRound,
    ConsensusReachedRound,
    DeploySafeRound,
    EstimateConsensusRound,
    FinalizationRound,
    PeriodState,
    PriceEstimationAbstractRound,
    RandomnessRound,
    RegistrationRound,
    SelectKeeperARound,
    SelectKeeperBRound,
    SelectKeeperRound,
    TxHashRound,
    ValidateRound,
    ValidateSafeRound,
    ValidateTransactionRound,
    encode_float,
    rotate_list,
)


MAX_PARTICIPANTS: int = 4
RANDOMNESS: str = "d1c29dce46f979f9748210d24bce4eae8be91272f5ca1a6aea2832d3dd676f51"


def get_participants() -> List[str]:
    """Participants"""
    return sorted([f"agent_{i}" for i in range(MAX_PARTICIPANTS)])


def get_participant_to_randomness(
    participants: Set[str], round_id: int
) -> List[Tuple[str, RandomnessPayload]]:
    """participant_to_randomness"""
    return [
        (
            participant,
            RandomnessPayload(
                sender=participant,
                round_id=round_id,
                randomness=RANDOMNESS,
            ),
        )
        for participant in participants
    ]


def get_most_voted_randomness() -> str:
    """most_voted_randomness"""
    return RANDOMNESS


def get_participant_to_selection(
    participants: Set[str],
) -> List[Tuple[str, SelectKeeperPayload]]:
    """participant_to_selection"""
    return [
        (participant, SelectKeeperPayload(sender=participant, keeper="keeper"))
        for participant in participants
    ]


def get_most_voted_keeper_address() -> str:
    """most_voted_keeper_address"""
    return "keeper"


def get_safe_contract_address() -> str:
    """safe_contract_address"""
    return "0x6f6ab56aca12"


def get_participant_to_votes(
    participants: Set[str], vote: bool = True
) -> List[Tuple[str, ValidatePayload]]:
    """participant_to_votes"""
    return [
        (participant, ValidatePayload(sender=participant, vote=vote))
        for participant in participants
    ]


def get_participant_to_observations(
    participants: Set[str],
) -> List[Tuple[str, ObservationPayload]]:
    """participant_to_observations"""
    return [
        (participant, ObservationPayload(sender=participant, observation=1.0))
        for participant in participants
    ]


def get_participant_to_estimate(
    participants: Set[str],
) -> List[Tuple[str, EstimatePayload]]:
    """participant_to_estimate"""
    return [
        (participant, EstimatePayload(sender=participant, estimate=1.0))
        for participant in participants
    ]


def get_estimate() -> float:
    """Estimate"""
    return 1.0


def get_most_voted_estimate() -> float:
    """most_voted_estimate"""
    return 1.0


def get_participant_to_tx_hash(
    participants: Set[str],
) -> List[Tuple[str, TransactionHashPayload]]:
    """participant_to_tx_hash"""
    return [
        (participant, TransactionHashPayload(sender=participant, tx_hash="tx_hash"))
        for participant in participants
    ]


def get_most_voted_tx_hash() -> str:
    """most_voted_tx_hash"""
    return "tx_hash"


def get_participant_to_signature(participants: Set[str]) -> List[Tuple[str, str]]:
    """participant_to_signature"""
    return [(participant, "signature") for participant in participants]


def get_final_tx_hash() -> str:
    """final_tx_hash"""
    return "tx_hash"


class BaseRoundTestClass:
    """Base test class for Rounds."""

    test_round: PriceEstimationAbstractRound
    period_state: PeriodState

    @classmethod
    def setup(
        cls,
    ):
        """Setup the test class."""

        cls.participants = get_participants()
        cls.period_state = PeriodState(participants=cls.participants)
        cls.consensus_params = ConsensusParams(max_participants=MAX_PARTICIPANTS)


class TestRegistrationRound(BaseRoundTestClass):
    """Test RegistrationRound."""

    def test_run(
        self,
    ):
        """Run test."""

        test_round = RegistrationRound(
            state=self.period_state, consensus_params=self.consensus_params
        )

        registration_payloads = [
            RegistrationPayload(sender=participant) for participant in self.participants
        ]

        first_participant = registration_payloads.pop(0)
        test_round.registration(first_participant)
        assert test_round.participants == {
            first_participant.sender,
        }
        assert test_round.end_block() is None

        for participant_payload in registration_payloads:
            test_round.registration(participant_payload)
        assert test_round.registration_threshold_reached

        actual_next_state = PeriodState(participants=frozenset(test_round.participants))
        state, _ = test_round.end_block()
        assert state.participants == actual_next_state.participants


class TestRandomnessRound(BaseRoundTestClass):
    """Test RandomnessRound."""

    def test_run(
        self,
    ):
        """Run tests."""

        test_round = RandomnessRound(self.period_state, self.consensus_params)

        randomness_payloads = get_participant_to_randomness(self.participants, 1)
        _, first_payload = randomness_payloads.pop(0)
        test_round.randomness(first_payload)

        assert (
            test_round.participant_to_randomness[first_payload.sender] == first_payload
        )
        assert not test_round.check_randomness(
            SelectKeeperPayload(sender=first_payload.sender, keeper="agent_0")
        )
        assert not test_round.threshold_reached
        with pytest.raises(ValueError, match="keeper has not enough votes"):
            _ = test_round.most_voted_randomness
        assert test_round.end_block() is None

        for _, randomness_payload in randomness_payloads:
            test_round.randomness(randomness_payload)
        assert test_round.most_voted_randomness == RANDOMNESS
        assert test_round.threshold_reached

        actual_next_state = self.period_state.update(
            participant_to_randomness=MappingProxyType(
                {
                    participant: payload
                    for participant, payload in get_participant_to_randomness(
                        self.participants, 1
                    )
                }
            )
        )

        state, _ = test_round.end_block()
        assert (
            state.participant_to_randomness.keys()
            == actual_next_state.participant_to_randomness.keys()
        )


class TestSelectKeeperRound(BaseRoundTestClass):
    """Test SelectKeeperRound"""

    def test_run(
        self,
    ):
        """Run tests."""

        test_round = SelectKeeperRound(
            state=self.period_state, consensus_params=self.consensus_params
        )

        select_keeper_payloads = get_participant_to_selection(self.participants)
        _, first_payload = select_keeper_payloads.pop(0)

        test_round.select_keeper(first_payload)
        assert (
            test_round.participant_to_selection[first_payload.sender] == first_payload
        )
        assert not test_round.selection_threshold_reached
        assert test_round.end_block() is None

        with pytest.raises(ABCIAppInternalError, match="keeper has not enough votes"):
            _ = test_round.most_voted_keeper_address

        with pytest.raises(ABCIAppInternalError):
            test_round.select_keeper(SelectKeeperPayload(sender="agent_x", keeper=""))

        with pytest.raises(
            ABCIAppInternalError,
            match="internal error: sender agent_0 has already sent the selection: keeper",
        ):
            test_round.select_keeper(first_payload)

        with pytest.raises(
            TransactionNotValidError,
            match="sender agent_0 has already sent the selection: keeper",
        ):
            test_round.check_select_keeper(first_payload)

        with pytest.raises(TransactionNotValidError):
            test_round.check_select_keeper(
                SelectKeeperPayload(sender="agent_x", keeper="keeper")
            )

        for _, payload in select_keeper_payloads:
            test_round.select_keeper(payload)
        assert test_round.selection_threshold_reached
        assert test_round.most_voted_keeper_address == "keeper"

        actual_next_state = self.period_state.update(
            participant_to_selection=MappingProxyType(
                {
                    participant: payload
                    for participant, payload in get_participant_to_selection(
                        self.participants
                    )
                }
            )
        )

        test_round.next_round_class = DeploySafeRound
        state, _ = test_round.end_block()
        assert (
            state.participant_to_selection.keys()
            == actual_next_state.participant_to_selection.keys()
        )


class TestDeploySafeRound(BaseRoundTestClass):
    """Test DeploySafeRound."""

    def test_run(
        self,
    ):
        """Run tests."""

        self.period_state = self.period_state.update(
            most_voted_keeper_address=self.participants[0]
        )

        test_round = DeploySafeRound(
            state=self.period_state, consensus_params=self.consensus_params
        )

        with pytest.raises(
            TransactionNotValidError,
        ):
            test_round.check_deploy_safe(
                DeploySafePayload(
                    sender="agent_x", safe_contract_address=get_safe_contract_address()
                )
            )

        with pytest.raises(
            TransactionNotValidError,
            match="sender agent_1 is not the elected sender: agent_0",
        ):
            test_round.check_deploy_safe(
                DeploySafePayload(
                    sender=self.participants[1],
                    safe_contract_address=get_safe_contract_address(),
                )
            )

        assert not test_round.is_contract_set
        assert test_round.end_block() is None

        with pytest.raises(ABCIAppInternalError):
            test_round.deploy_safe(
                DeploySafePayload(
                    sender="sender", safe_contract_address=get_safe_contract_address()
                )
            )

        with pytest.raises(ABCIAppInternalError):
            test_round.deploy_safe(
                DeploySafePayload(
                    sender=self.participants[1],
                    safe_contract_address=get_safe_contract_address(),
                )
            )

        test_round.deploy_safe(
            DeploySafePayload(
                sender=self.participants[0],
                safe_contract_address=get_safe_contract_address(),
            )
        )

        with pytest.raises(ABCIAppInternalError):
            test_round.deploy_safe(
                DeploySafePayload(
                    sender=self.participants[0],
                    safe_contract_address=get_safe_contract_address(),
                )
            )

        with pytest.raises(
            TransactionNotValidError,
            match="sender agent_0 has already sent the contract address: 0x6f6ab56aca12",
        ):
            test_round.check_deploy_safe(
                DeploySafePayload(
                    sender=self.participants[0],
                    safe_contract_address=get_safe_contract_address(),
                )
            )

        assert test_round.is_contract_set
        actual_state = self.period_state.update(
            safe_contract_address=get_safe_contract_address()
        )
        state, _ = test_round.end_block()
        assert state.safe_contract_address == actual_state.safe_contract_address


class TestValidateRound(BaseRoundTestClass):
    """Test ValidateRound."""

    def test_positive_votes(
        self,
    ):
        """Test ValidateRound."""

        test_round = ValidateRound(
            state=self.period_state, consensus_params=self.consensus_params
        )

        with pytest.raises(TransactionNotValidError):
            test_round.validate(ValidatePayload(sender="sender", vote=True))

        with pytest.raises(TransactionNotValidError):
            test_round.check_validate(ValidatePayload(sender="sender", vote=True))

        participant_to_votes_payloads = get_participant_to_votes(self.participants)
        _, first_payload = participant_to_votes_payloads.pop(0)
        test_round.validate(first_payload)

        with pytest.raises(
            ABCIAppInternalError,
            match="internal error: sender agent_0 has already sent its vote: True",
        ):
            test_round.validate(first_payload)

        assert test_round.participant_to_votes[first_payload.sender] == first_payload

        with pytest.raises(
            TransactionNotValidError,
            match="sender agent_0 has already sent its vote: True",
        ):
            test_round.check_validate(first_payload)

        assert test_round.end_block() is None
        assert not test_round.positive_vote_threshold_reached
        for _, payload in participant_to_votes_payloads:
            test_round.validate(payload)

        assert test_round.positive_vote_threshold_reached

        test_round.positive_next_round_class = CollectObservationRound
        actual_next_state = self.period_state.update(
            participant_to_votes=MappingProxyType(
                dict(get_participant_to_votes(self.participants))
            )
        )
        state, _ = test_round.end_block()
        assert (
            state.participant_to_votes.keys()
            == actual_next_state.participant_to_votes.keys()
        )

    def test_negative_votes(
        self,
    ):
        """Test ValidateRound."""

        test_round = ValidateRound(
            state=self.period_state, consensus_params=self.consensus_params
        )

        participant_to_votes_payloads = get_participant_to_votes(
            self.participants, vote=False
        )
        _, first_payload = participant_to_votes_payloads.pop(0)
        test_round.validate(first_payload)

        assert test_round.participant_to_votes[first_payload.sender] == first_payload
        assert test_round.end_block() is None
        assert not test_round.negative_vote_threshold_reached
        for _, payload in participant_to_votes_payloads:
            test_round.validate(payload)

        assert test_round.negative_vote_threshold_reached

        test_round.negative_next_round_class = CollectObservationRound
        state, _ = test_round.end_block()

        with pytest.raises(
            AEAEnforceError, match="'participant_to_votes' field is None"
        ):
            _ = state.participant_to_votes


def test_period_state():
    """Test PeriodState."""

    participants = get_participants()
    participant_to_randomness = get_participant_to_randomness(participants, 1)
    most_voted_randomness = get_most_voted_randomness()
    participant_to_selection = get_participant_to_selection(participants)
    most_voted_keeper_address = get_most_voted_keeper_address()
    safe_contract_address = get_safe_contract_address()
    participant_to_votes = get_participant_to_votes(participants)
    participant_to_observations = get_participant_to_observations(participants)
    participant_to_estimate = get_participant_to_estimate(participants)
    estimate = get_estimate()
    most_voted_estimate = get_most_voted_estimate()
    participant_to_tx_hash = get_participant_to_tx_hash(participants)
    most_voted_tx_hash = get_most_voted_tx_hash()
    participant_to_signature = get_participant_to_signature(participants)
    final_tx_hash = get_final_tx_hash()

    period_state = PeriodState(
        participants=participants,
        participant_to_randomness=participant_to_randomness,
        most_voted_randomness=most_voted_randomness,
        participant_to_selection=participant_to_selection,
        most_voted_keeper_address=most_voted_keeper_address,
        safe_contract_address=safe_contract_address,
        participant_to_votes=participant_to_votes,
        participant_to_observations=participant_to_observations,
        participant_to_estimate=participant_to_estimate,
        estimate=estimate,
        most_voted_estimate=most_voted_estimate,
        participant_to_tx_hash=participant_to_tx_hash,
        most_voted_tx_hash=most_voted_tx_hash,
        participant_to_signature=participant_to_signature,
        final_tx_hash=final_tx_hash,
    )

    actual_keeper_randomness = float(
        (int(most_voted_randomness, base=16) // 10 ** 0 % 10) / 10
    )
    assert period_state.keeper_randomness == actual_keeper_randomness
    assert period_state.participant_to_randomness == participant_to_randomness
    assert period_state.most_voted_randomness == most_voted_randomness
    assert period_state.participant_to_selection == participant_to_selection
    assert period_state.most_voted_keeper_address == most_voted_keeper_address
    assert period_state.safe_contract_address == safe_contract_address
    assert period_state.participant_to_votes == participant_to_votes
    assert period_state.participant_to_observations == participant_to_observations
    assert period_state.participant_to_estimate == participant_to_estimate
    assert period_state.estimate == estimate
    assert period_state.most_voted_estimate == most_voted_estimate
    assert period_state.most_voted_tx_hash == most_voted_tx_hash
    assert period_state.participant_to_signature == participant_to_signature
    assert period_state.final_tx_hash == final_tx_hash

    assert period_state.encoded_most_voted_estimate == encode_float(most_voted_estimate)
