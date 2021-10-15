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
import re
from types import MappingProxyType
from typing import Dict, Set, cast

import pytest
from aea.exceptions import AEAEnforceError

from packages.valory.skills.abstract_round_abci.base import (
    ABCIAppInternalError,
    ConsensusParams,
    TransactionNotValidError,
)
from packages.valory.skills.price_estimation_abci.payloads import (
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
from packages.valory.skills.price_estimation_abci.rounds import (
    CollectObservationRound,
    CollectSignatureRound,
    ConsensusReachedRound,
    DeploySafeRound,
    EstimateConsensusRound,
    FinalizationRound,
    PeriodState,
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


def get_participants() -> Set[str]:
    """Participants"""
    return {f"agent_{i}" for i in range(MAX_PARTICIPANTS)}


def get_participant_to_randomness(
    participants: Set[str], round_id: int
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


def get_most_voted_randomness() -> str:
    """most_voted_randomness"""
    return RANDOMNESS


def get_participant_to_selection(
    participants: Set[str],
) -> Dict[str, SelectKeeperPayload]:
    """participant_to_selection"""
    return {
        participant: SelectKeeperPayload(sender=participant, keeper="keeper")
        for participant in participants
    }


def get_most_voted_keeper_address() -> str:
    """most_voted_keeper_address"""
    return "keeper"


def get_safe_contract_address() -> str:
    """safe_contract_address"""
    return "0x6f6ab56aca12"


def get_participant_to_votes(
    participants: Set[str], vote: bool = True
) -> Dict[str, ValidatePayload]:
    """participant_to_votes"""
    return {
        participant: ValidatePayload(sender=participant, vote=vote)
        for participant in participants
    }


def get_participant_to_observations(
    participants: Set[str],
) -> Dict[str, ObservationPayload]:
    """participant_to_observations"""
    return {
        participant: ObservationPayload(sender=participant, observation=1.0)
        for participant in participants
    }


def get_participant_to_estimate(
    participants: Set[str],
) -> Dict[str, EstimatePayload]:
    """participant_to_estimate"""
    return {
        participant: EstimatePayload(sender=participant, estimate=1.0)
        for participant in participants
    }


def get_estimate() -> float:
    """Estimate"""
    return 1.0


def get_most_voted_estimate() -> float:
    """most_voted_estimate"""
    return 1.0


def get_participant_to_tx_hash(
    participants: Set[str],
) -> Dict[str, TransactionHashPayload]:
    """participant_to_tx_hash"""
    return {
        participant: TransactionHashPayload(sender=participant, tx_hash="tx_hash")
        for participant in participants
    }


def get_most_voted_tx_hash() -> str:
    """most_voted_tx_hash"""
    return "tx_hash"


def get_participant_to_signature(participants: Set[str]) -> Dict[str, str]:
    """participant_to_signature"""
    return {participant: "signature" for participant in participants}


def get_final_tx_hash() -> str:
    """final_tx_hash"""
    return "tx_hash"


class BaseRoundTestClass:
    """Base test class for Rounds."""

    period_state: PeriodState
    consensus_params: ConsensusParams
    participants: Set[str]

    @classmethod
    def setup(
        cls,
    ) -> None:
        """Setup the test class."""

        cls.participants = get_participants()
        cls.period_state = PeriodState(participants=frozenset(cls.participants))
        cls.consensus_params = ConsensusParams(max_participants=MAX_PARTICIPANTS)


class TestRegistrationRound(BaseRoundTestClass):
    """Test RegistrationRound."""

    def test_run(
        self,
    ) -> None:
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

        res = test_round.end_block()
        assert res is not None
        state, next_round = res
        assert (
            cast(PeriodState, state).participants
            == cast(PeriodState, actual_next_state).participants
        )
        assert isinstance(next_round, RandomnessRound)


class TestRandomnessRound(BaseRoundTestClass):
    """Test RandomnessRound."""

    def test_run(
        self,
    ) -> None:
        """Run tests."""

        test_round = RandomnessRound(self.period_state, self.consensus_params)

        test_round.randomness(
            RandomnessPayload(sender="sender", round_id=0, randomness=RANDOMNESS)
        )
        assert "sender" not in test_round.participant_to_randomness

        randomness_payloads = get_participant_to_randomness(self.participants, 1)
        first_payload = randomness_payloads.pop(list(randomness_payloads.keys())[0])
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

        for randomness_payload in randomness_payloads.values():
            test_round.randomness(randomness_payload)
        assert test_round.most_voted_randomness == RANDOMNESS
        assert test_round.threshold_reached

        actual_next_state = self.period_state.update(
            participant_to_randomness=MappingProxyType(
                dict(get_participant_to_randomness(self.participants, 1))
            )
        )

        res = test_round.end_block()
        assert res is not None
        state, next_round = res
        assert (
            cast(PeriodState, state).participant_to_randomness.keys()
            == cast(PeriodState, actual_next_state).participant_to_randomness.keys()
        )
        assert isinstance(next_round, SelectKeeperARound)


class TestSelectKeeperRound(BaseRoundTestClass):
    """Test SelectKeeperRound"""

    def test_run(
        self,
    ) -> None:
        """Run tests."""

        test_round = SelectKeeperRound(
            state=self.period_state, consensus_params=self.consensus_params
        )

        select_keeper_payloads = get_participant_to_selection(self.participants)
        first_payload = select_keeper_payloads.pop(
            list(select_keeper_payloads.keys())[0]
        )

        test_round.select_keeper(first_payload)
        assert (
            test_round.participant_to_selection[first_payload.sender] == first_payload
        )
        assert not test_round.selection_threshold_reached
        assert test_round.end_block() is None

        with pytest.raises(ABCIAppInternalError, match="keeper has not enough votes"):
            _ = test_round.most_voted_keeper_address

        with pytest.raises(
            ABCIAppInternalError,
            match=re.escape(
                "internal error: sender sender is not in the set of participants: ['agent_0', 'agent_1', 'agent_2', 'agent_3']"
            ),
        ):
            test_round.select_keeper(SelectKeeperPayload(sender="sender", keeper=""))

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
                SelectKeeperPayload(sender="sender", keeper="keeper")
            )

        for payload in select_keeper_payloads.values():
            test_round.select_keeper(payload)
        assert test_round.selection_threshold_reached
        assert test_round.most_voted_keeper_address == "keeper"

        actual_next_state = self.period_state.update(
            participant_to_selection=MappingProxyType(
                dict(get_participant_to_selection(self.participants))
            )
        )

        test_round.next_round_class = DeploySafeRound
        res = test_round.end_block()
        assert res is not None
        state, next_round = res
        assert (
            cast(PeriodState, state).participant_to_selection.keys()
            == cast(PeriodState, actual_next_state).participant_to_selection.keys()
        )
        assert isinstance(next_round, DeploySafeRound)


class TestDeploySafeRound(BaseRoundTestClass):
    """Test DeploySafeRound."""

    def test_run(
        self,
    ) -> None:
        """Run tests."""

        self.period_state = cast(
            PeriodState,
            self.period_state.update(
                most_voted_keeper_address=list(self.participants)[0]
            ),
        )

        test_round = DeploySafeRound(
            state=self.period_state, consensus_params=self.consensus_params
        )

        with pytest.raises(
            TransactionNotValidError,
            match=re.escape(
                "sender sender is not in the set of participants: ['agent_0', 'agent_1', 'agent_2', 'agent_3']"
            ),
        ):
            test_round.check_deploy_safe(
                DeploySafePayload(
                    sender="sender", safe_contract_address=get_safe_contract_address()
                )
            )

        with pytest.raises(
            TransactionNotValidError,
            match="sender agent_1 is not the elected sender: agent_0",
        ):
            test_round.check_deploy_safe(
                DeploySafePayload(
                    sender=list(self.participants)[1],
                    safe_contract_address=get_safe_contract_address(),
                )
            )

        assert not test_round.is_contract_set
        assert test_round.end_block() is None

        with pytest.raises(
            ABCIAppInternalError,
            match=re.escape(
                "internal error: sender sender is not in the set of participants: ['agent_0', 'agent_1', 'agent_2', 'agent_3']"
            ),
        ):
            test_round.deploy_safe(
                DeploySafePayload(
                    sender="sender", safe_contract_address=get_safe_contract_address()
                )
            )

        with pytest.raises(
            ABCIAppInternalError,
            match="internal error: sender agent_1 is not the elected sender: agent_0",
        ):
            test_round.deploy_safe(
                DeploySafePayload(
                    sender=list(self.participants)[1],
                    safe_contract_address=get_safe_contract_address(),
                )
            )

        test_round.deploy_safe(
            DeploySafePayload(
                sender=list(self.participants)[0],
                safe_contract_address=get_safe_contract_address(),
            )
        )

        with pytest.raises(
            ABCIAppInternalError,
            match="internal error: sender agent_0 has already sent the contract address: 0x6f6ab56aca12",
        ):
            test_round.deploy_safe(
                DeploySafePayload(
                    sender=list(self.participants)[0],
                    safe_contract_address=get_safe_contract_address(),
                )
            )

        with pytest.raises(
            TransactionNotValidError,
            match="sender agent_0 has already sent the contract address: 0x6f6ab56aca12",
        ):
            test_round.check_deploy_safe(
                DeploySafePayload(
                    sender=list(self.participants)[0],
                    safe_contract_address=get_safe_contract_address(),
                )
            )

        assert test_round.is_contract_set
        actual_state = self.period_state.update(
            safe_contract_address=get_safe_contract_address()
        )
        res = test_round.end_block()
        assert res is not None
        state, next_round = res
        assert (
            cast(PeriodState, state).safe_contract_address
            == cast(PeriodState, actual_state).safe_contract_address
        )
        assert isinstance(next_round, ValidateSafeRound)


class TestValidateRound(BaseRoundTestClass):
    """Test ValidateRound."""

    def test_positive_votes(
        self,
    ) -> None:
        """Test ValidateRound."""

        test_round = ValidateRound(
            state=self.period_state, consensus_params=self.consensus_params
        )

        with pytest.raises(
            TransactionNotValidError,
            match=re.escape(
                "sender sender is not in the set of participants: ['agent_0', 'agent_1', 'agent_2', 'agent_3']"
            ),
        ):
            test_round.validate(ValidatePayload(sender="sender", vote=True))

        with pytest.raises(
            TransactionNotValidError,
            match=re.escape(
                "sender sender is not in the set of participants: ['agent_0', 'agent_1', 'agent_2', 'agent_3']"
            ),
        ):
            test_round.check_validate(ValidatePayload(sender="sender", vote=True))

        participant_to_votes_payloads = get_participant_to_votes(self.participants)
        first_payload = participant_to_votes_payloads.pop(
            list(participant_to_votes_payloads.keys())[0]
        )
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
        for payload in participant_to_votes_payloads.values():
            test_round.validate(payload)

        assert test_round.positive_vote_threshold_reached

        test_round.positive_next_round_class = CollectObservationRound
        actual_next_state = self.period_state.update(
            participant_to_votes=MappingProxyType(
                dict(get_participant_to_votes(self.participants))
            )
        )
        res = test_round.end_block()
        assert res is not None
        state, next_round = res
        assert (
            cast(PeriodState, state).participant_to_votes.keys()
            == cast(PeriodState, actual_next_state).participant_to_votes.keys()
        )
        assert isinstance(next_round, CollectObservationRound)

    def test_negative_votes(
        self,
    ) -> None:
        """Test ValidateRound."""

        test_round = ValidateRound(
            state=self.period_state, consensus_params=self.consensus_params
        )

        participant_to_votes_payloads = get_participant_to_votes(
            self.participants, vote=False
        )
        first_payload = participant_to_votes_payloads.pop(
            list(participant_to_votes_payloads.keys())[0]
        )
        test_round.validate(first_payload)

        assert test_round.participant_to_votes[first_payload.sender] == first_payload
        assert test_round.end_block() is None
        assert not test_round.negative_vote_threshold_reached
        for payload in participant_to_votes_payloads.values():
            test_round.validate(payload)

        assert test_round.negative_vote_threshold_reached

        test_round.negative_next_round_class = CollectObservationRound
        res = test_round.end_block()
        assert res is not None
        state, next_round = res
        assert isinstance(next_round, CollectObservationRound)
        with pytest.raises(
            AEAEnforceError, match="'participant_to_votes' field is None"
        ):
            _ = cast(PeriodState, state).participant_to_votes


class TestCollectObservationRound(BaseRoundTestClass):
    """Test CollectObservationRound."""

    def test_run(
        self,
    ) -> None:
        """Runs tests."""

        test_round = CollectObservationRound(
            state=self.period_state, consensus_params=self.consensus_params
        )

        with pytest.raises(
            ABCIAppInternalError,
            match=re.escape(
                "internal error: sender sender is not in the set of participants: ['agent_0', 'agent_1', 'agent_2', 'agent_3']"
            ),
        ):
            test_round.observation(
                ObservationPayload(
                    sender="sender",
                    observation=1.0,
                )
            )

        with pytest.raises(
            TransactionNotValidError,
            match=re.escape(
                "sender sender is not in the set of participants: ['agent_0', 'agent_1', 'agent_2', 'agent_3']"
            ),
        ):
            test_round.check_observation(
                ObservationPayload(
                    sender="sender",
                    observation=1.0,
                )
            )

        participant_to_observations_payloads = get_participant_to_observations(
            self.participants
        )
        first_payload = participant_to_observations_payloads.pop(
            list(participant_to_observations_payloads.keys())[0]
        )

        test_round.observation(first_payload)
        assert (
            test_round.participant_to_observations[first_payload.sender]
            == first_payload
        )
        assert not test_round.observation_threshold_reached
        assert test_round.end_block() is None

        with pytest.raises(
            ABCIAppInternalError,
            match="internal error: sender agent_0 has already sent its observation: 1.0",
        ):
            test_round.observation(first_payload)

        with pytest.raises(
            TransactionNotValidError,
            match="sender agent_0 has already sent its observation: 1.0",
        ):
            test_round.check_observation(
                ObservationPayload(
                    sender=list(self.participants)[0],
                    observation=1.0,
                )
            )

        for payload in participant_to_observations_payloads.values():
            test_round.observation(payload)

        assert test_round.observation_threshold_reached
        actual_next_state = self.period_state.update(
            participant_to_observations=dict(
                get_participant_to_observations(self.participants)
            )
        )
        res = test_round.end_block()
        assert res is not None
        state, next_round = res
        assert (
            cast(PeriodState, state).participant_to_observations.keys()
            == cast(PeriodState, actual_next_state).participant_to_observations.keys()
        )
        assert isinstance(next_round, EstimateConsensusRound)


class TestEstimateConsensusRound(BaseRoundTestClass):
    """Test EstimateConsensusRound."""

    def test_run(
        self,
    ) -> None:
        """Runs test."""

        test_round = EstimateConsensusRound(
            state=self.period_state, consensus_params=self.consensus_params
        )

        with pytest.raises(
            ABCIAppInternalError,
            match=re.escape(
                "internal error: sender sender is not in the set of participants: ['agent_0', 'agent_1', 'agent_2', 'agent_3']"
            ),
        ):
            test_round.estimate(EstimatePayload(sender="sender", estimate=1.0))

        with pytest.raises(
            TransactionNotValidError,
            match=re.escape(
                "sender sender is not in the set of participants: ['agent_0', 'agent_1', 'agent_2', 'agent_3']"
            ),
        ):
            test_round.check_estimate(EstimatePayload(sender="sender", estimate=1.0))

        participant_to_estimate_payloads = get_participant_to_estimate(
            self.participants
        )

        first_payload = participant_to_estimate_payloads.pop(
            list(participant_to_estimate_payloads.keys())[0]
        )
        test_round.estimate(first_payload)

        assert test_round.participant_to_estimate[first_payload.sender] == first_payload
        assert test_round.end_block() is None
        assert not test_round.estimate_threshold_reached

        with pytest.raises(ABCIAppInternalError, match="estimate has not enough votes"):
            _ = test_round.most_voted_estimate

        with pytest.raises(
            ABCIAppInternalError,
            match="internal error: sender agent_0 has already sent the estimate: 1.0",
        ):
            test_round.estimate(first_payload)

        with pytest.raises(
            TransactionNotValidError,
            match="sender agent_0 has already sent the estimate: 1.0",
        ):
            test_round.check_estimate(
                EstimatePayload(sender=list(self.participants)[0], estimate=1.0)
            )

        for payload in participant_to_estimate_payloads.values():
            test_round.estimate(payload)

        assert test_round.estimate_threshold_reached
        assert test_round.most_voted_estimate == 1.0

        actual_next_state = self.period_state.update(
            participant_to_estimate=dict(
                get_participant_to_estimate(self.participants)
            ),
            most_voted_estimate=test_round.most_voted_estimate,
        )
        res = test_round.end_block()
        assert res is not None
        state, next_round = res
        assert (
            cast(PeriodState, state).participant_to_estimate.keys()
            == cast(PeriodState, actual_next_state).participant_to_estimate.keys()
        )
        assert isinstance(next_round, TxHashRound)


class TestTxHashRound(BaseRoundTestClass):
    """Test TxHashRound."""

    def test_run(
        self,
    ) -> None:
        """Runs test."""

        test_round = TxHashRound(
            state=self.period_state, consensus_params=self.consensus_params
        )

        participant_to_tx_hash_payloads = get_participant_to_tx_hash(self.participants)
        first_payload = participant_to_tx_hash_payloads.pop(
            list(participant_to_tx_hash_payloads.keys())[0]
        )

        test_round.tx_hash(first_payload)

        with pytest.raises(
            ABCIAppInternalError,
            match=re.escape(
                "internal error: sender sender is not in the set of participants: ['agent_0', 'agent_1', 'agent_2', 'agent_3']"
            ),
        ):
            test_round.tx_hash(
                TransactionHashPayload(sender="sender", tx_hash="tx_hash")
            )

        with pytest.raises(
            TransactionNotValidError,
            match=re.escape(
                "sender sender is not in the set of participants: ['agent_0', 'agent_1', 'agent_2', 'agent_3']"
            ),
        ):
            test_round.check_tx_hash(
                TransactionHashPayload(sender="sender", tx_hash="tx_hash")
            )

        assert test_round.participant_to_tx_hash[first_payload.sender] == first_payload
        assert test_round.end_block() is None
        assert not test_round.tx_threshold_reached

        with pytest.raises(ABCIAppInternalError, match="tx hash has not enough votes"):
            _ = test_round.most_voted_tx_hash

        with pytest.raises(
            ABCIAppInternalError,
            match="internal error: sender agent_0 has already sent the tx hash: tx_hash",
        ):
            test_round.tx_hash(first_payload)

        with pytest.raises(
            TransactionNotValidError,
            match="sender agent_0 has already sent the tx hash: tx_hash",
        ):
            test_round.check_tx_hash(first_payload)

        for payload in participant_to_tx_hash_payloads.values():
            test_round.tx_hash(payload)

        assert test_round.tx_threshold_reached
        assert test_round.most_voted_tx_hash == "tx_hash"
        res = test_round.end_block()
        assert res is not None
        _, next_round = res
        assert isinstance(next_round, CollectSignatureRound)


class TestCollectSignatureRound(BaseRoundTestClass):
    """Test CollectSignatureRound."""

    def test_run(
        self,
    ) -> None:
        """Runs tests."""

        test_round = CollectSignatureRound(
            state=self.period_state, consensus_params=self.consensus_params
        )

        with pytest.raises(
            ABCIAppInternalError,
            match=re.escape(
                "internal error: sender sender is not in the set of participants: ['agent_0', 'agent_1', 'agent_2', 'agent_3']"
            ),
        ):
            test_round.signature(
                SignaturePayload(sender="sender", signature="signature")
            )

        with pytest.raises(
            TransactionNotValidError,
            match=re.escape(
                "sender sender is not in the set of participants: ['agent_0', 'agent_1', 'agent_2', 'agent_3']"
            ),
        ):
            test_round.check_signature(
                SignaturePayload(sender="sender", signature="signature")
            )

        participant_to_signature = {
            participant: SignaturePayload(sender=participant, signature=signature)
            for participant, signature in get_participant_to_signature(
                self.participants
            ).items()
        }
        first_payload = participant_to_signature.pop(
            list(participant_to_signature.keys())[0]
        )

        test_round.signature(first_payload)
        assert not test_round.signature_threshold_reached
        assert (
            test_round.signatures_by_participant[first_payload.sender]
            == first_payload.signature
        )
        assert test_round.end_block() is None

        with pytest.raises(
            ABCIAppInternalError,
            match="internal error: sender agent_0 has already sent its signature: signature",
        ):
            test_round.signature(first_payload)

        with pytest.raises(
            TransactionNotValidError,
            match="sender agent_0 has already sent its signature: signature",
        ):
            test_round.check_signature(first_payload)

        for payload in participant_to_signature.values():
            test_round.signature(payload)

        res = test_round.end_block()
        assert res is not None
        _, next_round = res
        assert isinstance(next_round, FinalizationRound)


class TestFinalizationRound(BaseRoundTestClass):
    """Test FinalizationRound."""

    def test_run(
        self,
    ) -> None:
        """Runs tests."""

        self.period_state = cast(
            PeriodState,
            self.period_state.update(
                most_voted_keeper_address=list(self.participants)[0]
            ),
        )

        test_round = FinalizationRound(
            state=self.period_state,
            consensus_params=self.consensus_params,
        )

        with pytest.raises(
            ABCIAppInternalError,
            match=re.escape(
                "internal error: sender sender is not in the set of participants: ['agent_0', 'agent_1', 'agent_2', 'agent_3']"
            ),
        ):
            test_round.finalization(
                FinalizationTxPayload(sender="sender", tx_hash=get_final_tx_hash())
            )

        with pytest.raises(
            TransactionNotValidError,
            match=re.escape(
                "sender sender is not in the set of participants: ['agent_0', 'agent_1', 'agent_2', 'agent_3']"
            ),
        ):
            test_round.check_finalization(
                FinalizationTxPayload(sender="sender", tx_hash=get_final_tx_hash())
            )

        with pytest.raises(
            ABCIAppInternalError,
            match="internal error: sender agent_1 is not the elected sender: agent_0",
        ):
            test_round.finalization(
                FinalizationTxPayload(
                    sender=list(self.participants)[1], tx_hash=get_final_tx_hash()
                )
            )

        with pytest.raises(
            TransactionNotValidError,
            match="sender agent_1 is not the elected sender: agent_0",
        ):
            test_round.check_finalization(
                FinalizationTxPayload(
                    sender=list(self.participants)[1], tx_hash=get_final_tx_hash()
                )
            )

        assert not test_round.tx_hash_set
        assert test_round.end_block() is None

        test_round.finalization(
            FinalizationTxPayload(
                sender=list(self.participants)[0], tx_hash=get_final_tx_hash()
            )
        )

        assert test_round.tx_hash_set

        with pytest.raises(
            ABCIAppInternalError,
            match="internal error: sender agent_0 has already sent the tx hash: tx_hash",
        ):
            test_round.finalization(
                FinalizationTxPayload(
                    sender=list(self.participants)[0], tx_hash=get_final_tx_hash()
                )
            )

        with pytest.raises(
            TransactionNotValidError,
            match="sender agent_0 has already sent the tx hash: tx_hash",
        ):
            test_round.check_finalization(
                FinalizationTxPayload(
                    sender=list(self.participants)[0], tx_hash=get_final_tx_hash()
                )
            )

        actual_next_state = self.period_state.update(final_tx_hash=get_final_tx_hash())
        res = test_round.end_block()
        assert res is not None
        state, next_round = res
        assert (
            cast(PeriodState, state).final_tx_hash
            == cast(PeriodState, actual_next_state).final_tx_hash
        )
        assert isinstance(next_round, ValidateTransactionRound)


class TestSelectKeeperARound(BaseRoundTestClass):
    """Test SelectKeeperARound"""

    def test_run(
        self,
    ) -> None:
        """Run tests."""

        test_round = SelectKeeperARound(
            state=self.period_state, consensus_params=self.consensus_params
        )

        select_keeper_payloads = get_participant_to_selection(self.participants)
        first_payload = select_keeper_payloads.pop(
            list(select_keeper_payloads.keys())[0]
        )

        test_round.select_keeper(first_payload)
        assert (
            test_round.participant_to_selection[first_payload.sender] == first_payload
        )
        assert not test_round.selection_threshold_reached
        assert test_round.end_block() is None

        with pytest.raises(ABCIAppInternalError, match="keeper has not enough votes"):
            _ = test_round.most_voted_keeper_address

        with pytest.raises(ABCIAppInternalError):
            test_round.select_keeper_a(SelectKeeperPayload(sender="sender", keeper=""))

        with pytest.raises(
            ABCIAppInternalError,
            match="internal error: sender agent_0 has already sent the selection: keeper",
        ):
            test_round.select_keeper_a(first_payload)

        with pytest.raises(
            TransactionNotValidError,
            match="sender agent_0 has already sent the selection: keeper",
        ):
            test_round.check_select_keeper_a(first_payload)

        with pytest.raises(
            TransactionNotValidError,
            match=re.escape(
                "sender sender is not in the set of participants: ['agent_0', 'agent_1', 'agent_2', 'agent_3']"
            ),
        ):
            test_round.check_select_keeper_a(
                SelectKeeperPayload(sender="sender", keeper="keeper")
            )

        for payload in select_keeper_payloads.values():
            test_round.select_keeper_a(payload)
        assert test_round.selection_threshold_reached
        assert test_round.most_voted_keeper_address == "keeper"

        actual_next_state = self.period_state.update(
            participant_to_selection=MappingProxyType(
                dict(get_participant_to_selection(self.participants))
            )
        )

        test_round.next_round_class = DeploySafeRound
        res = test_round.end_block()
        assert res is not None
        state, next_round = res
        assert (
            cast(PeriodState, state).participant_to_selection.keys()
            == cast(PeriodState, actual_next_state).participant_to_selection.keys()
        )
        assert isinstance(next_round, DeploySafeRound)


class TestSelectKeeperBRound(BaseRoundTestClass):
    """Test SelectKeeperBRound."""

    def test_run(
        self,
    ) -> None:
        """Run tests."""

        test_round = SelectKeeperBRound(
            state=self.period_state, consensus_params=self.consensus_params
        )

        select_keeper_payloads = get_participant_to_selection(self.participants)
        first_payload = select_keeper_payloads.pop(
            list(select_keeper_payloads.keys())[0]
        )

        test_round.select_keeper(first_payload)
        assert (
            test_round.participant_to_selection[first_payload.sender] == first_payload
        )
        assert not test_round.selection_threshold_reached
        assert test_round.end_block() is None

        with pytest.raises(ABCIAppInternalError, match="keeper has not enough votes"):
            _ = test_round.most_voted_keeper_address

        with pytest.raises(ABCIAppInternalError):
            test_round.select_keeper_b(SelectKeeperPayload(sender="sender", keeper=""))

        with pytest.raises(
            ABCIAppInternalError,
            match="internal error: sender agent_0 has already sent the selection: keeper",
        ):
            test_round.select_keeper_b(first_payload)

        with pytest.raises(
            TransactionNotValidError,
            match="sender agent_0 has already sent the selection: keeper",
        ):
            test_round.check_select_keeper_b(first_payload)

        with pytest.raises(
            TransactionNotValidError,
            match=re.escape(
                "sender sender is not in the set of participants: ['agent_0', 'agent_1', 'agent_2', 'agent_3']"
            ),
        ):
            test_round.check_select_keeper_b(
                SelectKeeperPayload(sender="sender", keeper="keeper")
            )

        for payload in select_keeper_payloads.values():
            test_round.select_keeper_b(payload)
        assert test_round.selection_threshold_reached
        assert test_round.most_voted_keeper_address == "keeper"

        actual_next_state = self.period_state.update(
            participant_to_selection=MappingProxyType(
                dict(get_participant_to_selection(self.participants))
            )
        )

        res = test_round.end_block()
        assert res is not None
        state, next_round = res
        assert (
            cast(PeriodState, state).participant_to_selection.keys()
            == cast(PeriodState, actual_next_state).participant_to_selection.keys()
        )
        assert isinstance(next_round, FinalizationRound)


class TestConsensusReachedRound(BaseRoundTestClass):
    """Test ConsensusReachedRound."""

    def test_runs(
        self,
    ) -> None:
        """Runs tests."""

        test_round = ConsensusReachedRound(
            state=self.period_state, consensus_params=self.consensus_params
        )

        assert test_round.end_block() is None


class TestValidateSafeRound(BaseRoundTestClass):
    """Test ValidateSafeRound."""

    def test_positive_votes(
        self,
    ) -> None:
        """Test ValidateRound."""

        test_round = ValidateSafeRound(
            state=self.period_state, consensus_params=self.consensus_params
        )

        with pytest.raises(
            TransactionNotValidError,
            match=re.escape(
                "sender sender is not in the set of participants: ['agent_0', 'agent_1', 'agent_2', 'agent_3']"
            ),
        ):
            test_round.validate_safe(ValidatePayload(sender="sender", vote=True))

        with pytest.raises(
            TransactionNotValidError,
            match=re.escape(
                "sender sender is not in the set of participants: ['agent_0', 'agent_1', 'agent_2', 'agent_3']"
            ),
        ):
            test_round.check_validate_safe(ValidatePayload(sender="sender", vote=True))

        participant_to_votes_payloads = get_participant_to_votes(self.participants)
        first_payload = participant_to_votes_payloads.pop(
            list(participant_to_votes_payloads.keys())[0]
        )
        test_round.validate_safe(first_payload)

        with pytest.raises(
            ABCIAppInternalError,
            match="internal error: sender agent_0 has already sent its vote: True",
        ):
            test_round.validate_safe(first_payload)

        assert test_round.participant_to_votes[first_payload.sender] == first_payload

        with pytest.raises(
            TransactionNotValidError,
            match="sender agent_0 has already sent its vote: True",
        ):
            test_round.check_validate_safe(first_payload)

        assert test_round.end_block() is None
        assert not test_round.positive_vote_threshold_reached
        for payload in participant_to_votes_payloads.values():
            test_round.validate_safe(payload)

        assert test_round.positive_vote_threshold_reached

        actual_next_state = self.period_state.update(
            participant_to_votes=MappingProxyType(
                dict(get_participant_to_votes(self.participants))
            )
        )
        res = test_round.end_block()
        assert res is not None
        state, next_round = res
        assert (
            cast(PeriodState, state).participant_to_votes.keys()
            == cast(PeriodState, actual_next_state).participant_to_votes.keys()
        )
        assert isinstance(next_round, CollectObservationRound)

    def test_negative_votes(
        self,
    ) -> None:
        """Test ValidateRound."""

        test_round = ValidateSafeRound(
            state=self.period_state, consensus_params=self.consensus_params
        )

        participant_to_votes_payloads = get_participant_to_votes(
            self.participants, vote=False
        )
        first_payload = participant_to_votes_payloads.pop(
            list(participant_to_votes_payloads.keys())[0]
        )
        test_round.validate_safe(first_payload)

        assert test_round.participant_to_votes[first_payload.sender] == first_payload
        assert test_round.end_block() is None
        assert not test_round.negative_vote_threshold_reached
        for payload in participant_to_votes_payloads.values():
            test_round.validate_safe(payload)

        assert test_round.negative_vote_threshold_reached

        res = test_round.end_block()
        assert res is not None
        state, next_round = res
        assert isinstance(next_round, SelectKeeperARound)
        with pytest.raises(
            AEAEnforceError, match="'participant_to_votes' field is None"
        ):
            _ = cast(PeriodState, state).participant_to_votes


class TestValidateTransactionRound(BaseRoundTestClass):
    """Test ValidateRound."""

    def test_positive_votes(
        self,
    ) -> None:
        """Test ValidateRound."""

        test_round = ValidateTransactionRound(
            state=self.period_state, consensus_params=self.consensus_params
        )

        with pytest.raises(
            TransactionNotValidError,
            match=re.escape(
                "sender sender is not in the set of participants: ['agent_0', 'agent_1', 'agent_2', 'agent_3']"
            ),
        ):
            test_round.validate_transaction(ValidatePayload(sender="sender", vote=True))

        with pytest.raises(
            TransactionNotValidError,
            match=re.escape(
                "sender sender is not in the set of participants: ['agent_0', 'agent_1', 'agent_2', 'agent_3']"
            ),
        ):
            test_round.check_validate_transaction(
                ValidatePayload(sender="sender", vote=True)
            )

        participant_to_votes_payloads = get_participant_to_votes(self.participants)
        first_payload = participant_to_votes_payloads.pop(
            list(participant_to_votes_payloads.keys())[0]
        )
        test_round.validate_transaction(first_payload)

        with pytest.raises(
            ABCIAppInternalError,
            match="internal error: sender agent_0 has already sent its vote: True",
        ):
            test_round.validate_transaction(first_payload)

        assert test_round.participant_to_votes[first_payload.sender] == first_payload

        with pytest.raises(
            TransactionNotValidError,
            match="sender agent_0 has already sent its vote: True",
        ):
            test_round.check_validate_transaction(first_payload)

        assert test_round.end_block() is None
        assert not test_round.positive_vote_threshold_reached
        for payload in participant_to_votes_payloads.values():
            test_round.validate_transaction(payload)

        assert test_round.positive_vote_threshold_reached

        actual_next_state = self.period_state.update(
            participant_to_votes=MappingProxyType(
                dict(get_participant_to_votes(self.participants))
            )
        )
        res = test_round.end_block()
        assert res is not None
        state, next_round = res
        assert (
            cast(PeriodState, state).participant_to_votes.keys()
            == cast(PeriodState, actual_next_state).participant_to_votes.keys()
        )
        assert isinstance(next_round, ConsensusReachedRound)

    def test_negative_votes(
        self,
    ) -> None:
        """Test ValidateRound."""

        test_round = ValidateTransactionRound(
            state=self.period_state, consensus_params=self.consensus_params
        )

        participant_to_votes_payloads = get_participant_to_votes(
            self.participants, vote=False
        )
        first_payload = participant_to_votes_payloads.pop(
            list(participant_to_votes_payloads.keys())[0]
        )
        test_round.validate_transaction(first_payload)

        assert test_round.participant_to_votes[first_payload.sender] == first_payload
        assert test_round.end_block() is None
        assert not test_round.negative_vote_threshold_reached
        for payload in participant_to_votes_payloads.values():
            test_round.validate_transaction(payload)

        assert test_round.negative_vote_threshold_reached

        res = test_round.end_block()
        assert res is not None
        state, next_round = res

        assert isinstance(next_round, SelectKeeperRound)
        with pytest.raises(
            AEAEnforceError, match="'participant_to_votes' field is None"
        ):
            _ = cast(PeriodState, state).participant_to_votes


def test_rotate_list_method() -> None:
    """Test `rotate_list` method."""

    ex_list = [1, 2, 3, 4, 5]
    assert rotate_list(ex_list, 2) == [3, 4, 5, 1, 2]


def test_period_state() -> None:
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
        participants=frozenset(participants),
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
