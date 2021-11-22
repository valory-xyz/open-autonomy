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
import copy
import logging  # noqa: F401
import re
from types import MappingProxyType
from typing import Dict, FrozenSet, Optional, Type, cast
from unittest import mock

import pytest
from aea.exceptions import AEAEnforceError

from packages.valory.skills.abstract_round_abci.base import (
    ABCIAppInternalError,
    AbstractRound,
    BaseTxPayload,
    ConsensusParams,
    TransactionNotValidError,
)
from packages.valory.skills.price_estimation_abci.payloads import (
    DeployOraclePayload,
    DeploySafePayload,
    EstimatePayload,
    FinalizationTxPayload,
    ObservationPayload,
    RandomnessPayload,
    RegistrationPayload,
    ResetPayload,
    SelectKeeperPayload,
    SignaturePayload,
    TransactionHashPayload,
    ValidatePayload,
)
from packages.valory.skills.price_estimation_abci.rounds import (
    CollectObservationRound,
    CollectSignatureRound,
    DeployOracleRound,
    DeploySafeRound,
    EstimateConsensusRound,
    Event,
    FinalizationRound,
    PeriodState,
    RandomnessRound,
    RegistrationRound,
)
from packages.valory.skills.price_estimation_abci.rounds import (
    ResetRound as ConsensusReachedRound,
)
from packages.valory.skills.price_estimation_abci.rounds import (
    SelectKeeperARound,
    SelectKeeperAStartupRound,
    SelectKeeperBRound,
    SelectKeeperBStartupRound,
    SelectKeeperRound,
    TxHashRound,
    ValidateOracleRound,
    ValidateRound,
    ValidateSafeRound,
    ValidateTransactionRound,
    encode_float,
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


def get_most_voted_randomness() -> str:
    """most_voted_randomness"""
    return RANDOMNESS


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


def get_most_voted_keeper_address() -> str:
    """most_voted_keeper_address"""
    return "keeper"


def get_safe_contract_address() -> str:
    """safe_contract_address"""
    return "0x6f6ab56aca12"


def get_participant_to_votes(
    participants: FrozenSet[str], vote: Optional[bool] = True
) -> Dict[str, ValidatePayload]:
    """participant_to_votes"""
    return {
        participant: ValidatePayload(sender=participant, vote=vote)
        for participant in participants
    }


def get_participant_to_observations(
    participants: FrozenSet[str],
) -> Dict[str, ObservationPayload]:
    """participant_to_observations"""
    return {
        participant: ObservationPayload(sender=participant, observation=1.0)
        for participant in participants
    }


def get_participant_to_estimate(
    participants: FrozenSet[str],
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
    participants: FrozenSet[str], hash_: Optional[str] = "tx_hash"
) -> Dict[str, TransactionHashPayload]:
    """participant_to_tx_hash"""
    return {
        participant: TransactionHashPayload(sender=participant, tx_hash=hash_)
        for participant in participants
    }


def get_most_voted_tx_hash() -> str:
    """most_voted_tx_hash"""
    return "tx_hash"


def get_participant_to_signature(
    participants: FrozenSet[str],
) -> Dict[str, SignaturePayload]:
    """participant_to_signature"""
    return {
        participant: SignaturePayload(sender=participant, signature="signature")
        for participant in participants
    }


def get_final_tx_hash() -> str:
    """final_tx_hash"""
    return "tx_hash"


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
    """Test RegistrationRound."""

    def test_run_fastforward(
        self,
    ) -> None:
        """Run test."""

        self.period_state = cast(
            PeriodState,
            self.period_state.update(
                period_setup_params={
                    "safe_contract_address": "stub_safe_contract_address",
                    "oracle_contract_address": "stub_oracle_contract_address",
                }
            ),
        )

        test_round = RegistrationRound(
            state=self.period_state, consensus_params=self.consensus_params
        )
        self._run_with_round(test_round, Event.FAST_FORWARD, 1)

    def test_run_fastforward_contracts_set(
        self,
    ) -> None:
        """Run test."""

        self.period_state = cast(
            PeriodState,
            self.period_state.update(
                safe_contract_address="stub_safe_contract_address",
                oracle_contract_address="stub_oracle_contract_address",
            ),
        )

        test_round = RegistrationRound(
            state=self.period_state, consensus_params=self.consensus_params
        )
        self._run_with_round(test_round, Event.FAST_FORWARD)

    def test_run_default(
        self,
    ) -> None:
        """Run test."""

        test_round = RegistrationRound(
            state=self.period_state, consensus_params=self.consensus_params
        )
        self._run_with_round(test_round, Event.DONE, 1)

    def test_run_default_not_finished(
        self,
    ) -> None:
        """Run test."""

        test_round = RegistrationRound(
            state=self.period_state, consensus_params=self.consensus_params
        )
        self._run_with_round(test_round)

    def _run_with_round(
        self,
        test_round: RegistrationRound,
        expected_event: Optional[Event] = None,
        confirmations: Optional[int] = None,
    ) -> None:
        """Run with given round."""
        registration_payloads = [
            RegistrationPayload(sender=participant) for participant in self.participants
        ]

        first_participant = registration_payloads.pop(0)
        test_round.process_payload(first_participant)
        assert test_round.collection == {
            first_participant.sender,
        }
        assert test_round.end_block() is None

        with pytest.raises(
            TransactionNotValidError,
            match=f"payload attribute sender with value {first_participant.sender} has already been added for round: registration",
        ):
            test_round.check_payload(first_participant)

        with pytest.raises(
            ABCIAppInternalError,
            match=f"payload attribute sender with value {first_participant.sender} has already been added for round: registration",
        ):
            test_round.process_payload(first_participant)

        for participant_payload in registration_payloads:
            test_round.process_payload(participant_payload)
        assert test_round.collection_threshold_reached

        if confirmations is not None:
            test_round.block_confirmations = confirmations

        prior_confirmations = test_round.block_confirmations

        actual_next_state = PeriodState(participants=test_round.collection)

        res = test_round.end_block()
        assert test_round.block_confirmations == prior_confirmations + 1

        if expected_event is None:
            assert res is expected_event
        else:
            assert res is not None
            state, event = res
            assert (
                cast(PeriodState, state).participants
                == cast(PeriodState, actual_next_state).participants
            )
            assert event == expected_event


class TestRandomnessRound(BaseRoundTestClass):
    """Test RandomnessRound."""

    def test_run(
        self,
    ) -> None:
        """Run tests."""

        test_round = RandomnessRound(self.period_state, self.consensus_params)

        randomness_payloads = get_participant_to_randomness(self.participants, 1)
        first_payload = randomness_payloads.pop(
            sorted(list(randomness_payloads.keys()))[0]
        )
        test_round.process_payload(first_payload)

        assert test_round.collection[first_payload.sender] == first_payload
        assert not test_round.threshold_reached
        assert test_round.end_block() is None

        with pytest.raises(
            ABCIAppInternalError, match="internal error: not enough votes"
        ):
            _ = test_round.most_voted_payload

        with pytest.raises(
            ABCIAppInternalError,
            match=re.escape(
                "internal error: sender not in list of participants: ['agent_0', 'agent_1', 'agent_2', 'agent_3']"
            ),
        ):
            test_round.process_payload(
                RandomnessPayload(sender="sender", round_id=0, randomness="")
            )

        with pytest.raises(
            ABCIAppInternalError,
            match="internal error: sender agent_0 has already sent value for round: randomness",
        ):
            test_round.process_payload(first_payload)

        with pytest.raises(
            TransactionNotValidError,
            match="sender agent_0 has already sent value for round: randomness",
        ):
            test_round.check_payload(first_payload)

        with pytest.raises(TransactionNotValidError):
            test_round.check_payload(
                RandomnessPayload(sender="sender", round_id=0, randomness="")
            )

        for randomness_payload in randomness_payloads.values():
            test_round.process_payload(randomness_payload)
        assert test_round.most_voted_payload == RANDOMNESS
        assert test_round.threshold_reached

        actual_next_state = self.period_state.update(
            participant_to_randomness=MappingProxyType(
                dict(get_participant_to_randomness(self.participants, 1))
            )
        )

        res = test_round.end_block()
        assert res is not None
        state, event = res
        assert (
            cast(PeriodState, state).participant_to_randomness.keys()
            == cast(PeriodState, actual_next_state).participant_to_randomness.keys()
        )
        assert event == Event.DONE

    def test_no_majority_event(self) -> None:
        """Test the no-majority event."""
        test_round = RandomnessRound(self.period_state, self.consensus_params)
        self._test_no_majority_event(test_round)


class TestSelectKeeperRound(BaseRoundTestClass):
    """Test SelectKeeperRound"""

    @classmethod
    def setup(cls) -> None:
        """Set up the test."""
        super().setup()
        SelectKeeperRound.round_id = "round_id"

    def teardown(self) -> None:
        """Tear down the test."""
        delattr(SelectKeeperRound, "round_id")

    def test_run(
        self,
    ) -> None:
        """Run tests."""

        test_round = SelectKeeperRound(
            state=self.period_state, consensus_params=self.consensus_params
        )

        select_keeper_payloads = get_participant_to_selection(self.participants)
        first_payload = select_keeper_payloads.pop(
            sorted(list(select_keeper_payloads.keys()))[0]
        )

        test_round.process_payload(first_payload)
        assert test_round.collection[first_payload.sender] == first_payload
        assert not test_round.threshold_reached
        assert test_round.end_block() is None

        with pytest.raises(
            ABCIAppInternalError, match="internal error: not enough votes"
        ):
            _ = test_round.most_voted_payload

        with pytest.raises(
            ABCIAppInternalError,
            match=re.escape(
                "internal error: sender not in list of participants: ['agent_0', 'agent_1', 'agent_2', 'agent_3']"
            ),
        ):
            test_round.process_payload(SelectKeeperPayload(sender="sender", keeper=""))

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

        with pytest.raises(TransactionNotValidError):
            test_round.check_payload(
                SelectKeeperPayload(sender="sender", keeper="keeper")
            )

        for payload in select_keeper_payloads.values():
            test_round.process_payload(payload)
        assert test_round.threshold_reached
        assert test_round.most_voted_payload == "keeper"

        actual_next_state = self.period_state.update(
            participant_to_selection=MappingProxyType(
                dict(get_participant_to_selection(self.participants))
            )
        )

        res = test_round.end_block()
        assert res is not None
        state, event = res
        assert (
            cast(PeriodState, state).participant_to_selection.keys()
            == cast(PeriodState, actual_next_state).participant_to_selection.keys()
        )
        assert event == Event.DONE


class BaseDeployTestClass(BaseRoundTestClass):
    """Test DeploySafeRound."""

    round_class: Type[AbstractRound]
    payload_class: Type[BaseTxPayload]
    update_keyword: str

    def test_run(
        self,
    ) -> None:
        """Run tests."""

        self.period_state = cast(
            PeriodState,
            self.period_state.update(
                most_voted_keeper_address=sorted(list(self.participants))[0]
            ),
        )

        test_round = self.round_class(
            state=self.period_state, consensus_params=self.consensus_params
        )

        with pytest.raises(
            TransactionNotValidError,
            match=re.escape(
                "sender not in list of participants: ['agent_0', 'agent_1', 'agent_2', 'agent_3']"
            ),
        ):
            test_round.check_payload(
                self.payload_class("sender", get_safe_contract_address())
            )

        with pytest.raises(
            TransactionNotValidError,
            match="agent_1 not elected as keeper",
        ):
            test_round.check_payload(
                self.payload_class(
                    sorted(list(self.participants))[1],
                    get_safe_contract_address(),
                )
            )

        assert not test_round.has_keeper_sent_payload  # type: ignore
        assert test_round.end_block() is None

        with pytest.raises(
            ABCIAppInternalError,
            match=re.escape(
                "internal error: sender not in list of participants: ['agent_0', 'agent_1', 'agent_2', 'agent_3']"
            ),
        ):
            test_round.process_payload(
                self.payload_class("sender", get_safe_contract_address())
            )

        with pytest.raises(
            ABCIAppInternalError,
            match="internal error: agent_1 not elected as keeper.",
        ):
            test_round.process_payload(
                self.payload_class(
                    sorted(list(self.participants))[1],
                    get_safe_contract_address(),
                )
            )

        test_round.process_payload(
            self.payload_class(
                sorted(list(self.participants))[0],
                get_safe_contract_address(),
            )
        )

        with pytest.raises(
            ABCIAppInternalError,
            match="internal error: keeper already set the payload.",
        ):
            test_round.process_payload(
                self.payload_class(
                    sorted(list(self.participants))[0],
                    get_safe_contract_address(),
                )
            )

        with pytest.raises(
            TransactionNotValidError,
            match="keeper payload value already set.",
        ):
            test_round.check_payload(
                self.payload_class(
                    sorted(list(self.participants))[0],
                    get_safe_contract_address(),
                )
            )

        assert test_round.has_keeper_sent_payload  # type: ignore
        actual_state = self.period_state.update(
            **{self.update_keyword: get_safe_contract_address()}
        )
        res = test_round.end_block()
        assert res is not None
        state, event = res
        assert getattr(cast(PeriodState, state), self.update_keyword) == getattr(
            cast(PeriodState, actual_state), self.update_keyword
        )
        assert event == Event.DONE


class TestDeploySafeRound(BaseDeployTestClass):
    """Test DeploySafeRound."""

    round_class = DeploySafeRound
    payload_class = DeploySafePayload
    update_keyword = "safe_contract_address"


class TestDeployOracleRound(BaseDeployTestClass):
    """Test DeployOracleRound."""

    round_class = DeployOracleRound
    payload_class = DeployOraclePayload
    update_keyword = "oracle_contract_address"


class TestCollectObservationRound(BaseRoundTestClass):
    """Test CollectObservationRound."""

    def test_run_a(
        self,
    ) -> None:
        """Runs tests."""

        test_round = CollectObservationRound(
            state=self.period_state, consensus_params=self.consensus_params
        )
        payload_0 = ObservationPayload(
            sender="sender",
            observation=1.0,
        )

        participant_to_observations_payloads = get_participant_to_observations(
            self.participants
        )
        actual_next_state = cast(
            PeriodState,
            self.period_state.update(
                participant_to_observations=copy.copy(
                    participant_to_observations_payloads
                )
            ),
        )
        first_payload = participant_to_observations_payloads.pop(
            sorted(list(participant_to_observations_payloads.keys()))[0]
        )
        next_event = Event.DONE
        self._run(
            test_round,
            payload_0,
            first_payload,
            participant_to_observations_payloads,
            actual_next_state,
            next_event,
        )

    def test_run_b(
        self,
    ) -> None:
        """Runs tests with one less observation."""

        test_round = CollectObservationRound(
            state=self.period_state, consensus_params=self.consensus_params
        )
        payload_0 = ObservationPayload(
            sender="sender",
            observation=1.0,
        )

        participant_to_observations_payloads = get_participant_to_observations(
            frozenset(list(self.participants)[:-1])
        )
        actual_next_state = cast(
            PeriodState,
            self.period_state.update(
                participant_to_observations=copy.copy(
                    participant_to_observations_payloads
                )
            ),
        )
        first_payload = participant_to_observations_payloads.pop(
            sorted(list(participant_to_observations_payloads.keys()))[0]
        )
        next_event = Event.DONE
        self._run(
            test_round,
            payload_0,
            first_payload,
            participant_to_observations_payloads,
            actual_next_state,
            next_event,
        )

    def _run(
        self,
        test_round: CollectObservationRound,
        payload_0: ObservationPayload,
        first_payload: ObservationPayload,
        participant_to_observations_payloads: dict,
        actual_next_state: PeriodState,
        next_event: Event,
    ) -> None:
        """Runs tests."""

        with pytest.raises(
            ABCIAppInternalError,
            match=re.escape(
                "internal error: sender not in list of participants: ['agent_0', 'agent_1', 'agent_2', 'agent_3']"
            ),
        ):
            test_round.process_payload(payload_0)

        with pytest.raises(
            TransactionNotValidError,
            match=re.escape(
                "sender not in list of participants: ['agent_0', 'agent_1', 'agent_2', 'agent_3']"
            ),
        ):
            test_round.check_payload(payload_0)

        test_round.process_payload(first_payload)
        assert test_round.collection[first_payload.sender] == first_payload
        assert not test_round.collection_threshold_reached
        assert test_round.end_block() is None

        with pytest.raises(
            ABCIAppInternalError,
            match=f"internal error: sender {first_payload.sender} has already sent value for round: collect_observation",
        ):
            test_round.process_payload(first_payload)

        with pytest.raises(
            TransactionNotValidError,
            match=f"sender {first_payload.sender} has already sent value for round: collect_observation",
        ):
            test_round.check_payload(first_payload)

        for payload in participant_to_observations_payloads.values():
            test_round.process_payload(payload)

        assert test_round.collection_threshold_reached

        res = test_round.end_block()
        assert res is not None
        state, event = res
        assert (
            cast(PeriodState, state).participant_to_observations.keys()
            == actual_next_state.participant_to_observations.keys()
        )
        assert event == next_event


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
                "internal error: sender not in list of participants: ['agent_0', 'agent_1', 'agent_2', 'agent_3']"
            ),
        ):
            test_round.process_payload(EstimatePayload(sender="sender", estimate=1.0))

        with pytest.raises(
            TransactionNotValidError,
            match=re.escape(
                "sender not in list of participants: ['agent_0', 'agent_1', 'agent_2', 'agent_3']"
            ),
        ):
            test_round.check_payload(EstimatePayload(sender="sender", estimate=1.0))

        participant_to_estimate_payloads = get_participant_to_estimate(
            self.participants
        )

        first_payload = participant_to_estimate_payloads.pop(
            sorted(list(participant_to_estimate_payloads.keys()))[0]
        )
        test_round.process_payload(first_payload)

        assert test_round.collection[first_payload.sender] == first_payload
        assert test_round.end_block() is None
        assert not test_round.threshold_reached

        with pytest.raises(
            ABCIAppInternalError, match="internal error: not enough votes"
        ):
            _ = test_round.most_voted_payload

        with pytest.raises(
            ABCIAppInternalError,
            match="internal error: sender agent_0 has already sent value for round: estimate_consensus",
        ):
            test_round.process_payload(first_payload)

        with pytest.raises(
            TransactionNotValidError,
            match="sender agent_0 has already sent value for round: estimate_consensus",
        ):
            test_round.check_payload(
                EstimatePayload(sender=sorted(list(self.participants))[0], estimate=1.0)
            )

        for payload in participant_to_estimate_payloads.values():
            test_round.process_payload(payload)

        assert test_round.threshold_reached
        assert test_round.most_voted_payload == 1.0

        actual_next_state = self.period_state.update(
            participant_to_estimate=dict(
                get_participant_to_estimate(self.participants)
            ),
            most_voted_estimate=test_round.most_voted_payload,
        )
        res = test_round.end_block()
        assert res is not None
        state, event = res
        assert (
            cast(PeriodState, state).participant_to_estimate.keys()
            == cast(PeriodState, actual_next_state).participant_to_estimate.keys()
        )
        assert event == Event.DONE

    def test_no_majority_event(self) -> None:
        """Test the no-majority event."""
        test_round = EstimateConsensusRound(self.period_state, self.consensus_params)
        self._test_no_majority_event(test_round)


class TestTxHashRound(BaseRoundTestClass):
    """Test TxHashRound."""

    def test_run(
        self,
    ) -> None:
        """Runs test."""

        test_round = TxHashRound(
            state=self.period_state, consensus_params=self.consensus_params
        )

        hash_ = "tx_hash"
        participant_to_tx_hash_payloads = get_participant_to_tx_hash(
            self.participants, hash_
        )
        first_payload = participant_to_tx_hash_payloads.pop(
            sorted(list(participant_to_tx_hash_payloads.keys()))[0]
        )
        next_event = Event.DONE
        self._run(
            test_round,
            participant_to_tx_hash_payloads,
            first_payload,
            next_event,
            hash_,
        )

    def test_run_none(
        self,
    ) -> None:
        """Runs test."""

        test_round = TxHashRound(
            state=self.period_state, consensus_params=self.consensus_params
        )

        hash_ = None
        participant_to_tx_hash_payloads = get_participant_to_tx_hash(
            self.participants, hash_
        )
        first_payload = participant_to_tx_hash_payloads.pop(
            sorted(list(participant_to_tx_hash_payloads.keys()))[0]
        )
        next_event = Event.NONE
        self._run(
            test_round,
            participant_to_tx_hash_payloads,
            first_payload,
            next_event,
            hash_,
        )

    def _run(
        self,
        test_round: TxHashRound,
        participant_to_tx_hash_payloads: Dict,
        first_payload: TransactionHashPayload,
        next_event: Event,
        hash_: Optional[str],
    ) -> None:
        """Run test."""
        test_round.process_payload(first_payload)

        with pytest.raises(
            ABCIAppInternalError,
            match=re.escape(
                "internal error: sender not in list of participants: ['agent_0', 'agent_1', 'agent_2', 'agent_3']"
            ),
        ):
            test_round.process_payload(
                TransactionHashPayload(sender="sender", tx_hash="tx_hash")
            )

        with pytest.raises(
            TransactionNotValidError,
            match=re.escape(
                "sender not in list of participants: ['agent_0', 'agent_1', 'agent_2', 'agent_3']"
            ),
        ):
            test_round.check_payload(
                TransactionHashPayload(sender="sender", tx_hash="tx_hash")
            )

        assert test_round.collection[first_payload.sender] == first_payload
        assert test_round.end_block() is None
        assert not test_round.threshold_reached

        with pytest.raises(
            ABCIAppInternalError, match="internal error: not enough votes"
        ):
            _ = test_round.most_voted_payload

        with pytest.raises(
            ABCIAppInternalError,
            match=f"internal error: sender {first_payload.sender} has already sent value for round: tx_hash",
        ):
            test_round.process_payload(first_payload)

        with pytest.raises(
            TransactionNotValidError,
            match=f"sender {first_payload.sender} has already sent value for round: tx_hash",
        ):
            test_round.check_payload(first_payload)

        for payload in participant_to_tx_hash_payloads.values():
            test_round.process_payload(payload)

        assert test_round.threshold_reached
        assert test_round.most_voted_payload == hash_
        res = test_round.end_block()
        assert res is not None
        _, event = res
        assert event == next_event

    def test_no_majority_event(self) -> None:
        """Test the no-majority event."""
        test_round = TxHashRound(self.period_state, self.consensus_params)
        self._test_no_majority_event(test_round)


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
                "internal error: sender not in list of participants: ['agent_0', 'agent_1', 'agent_2', 'agent_3']"
            ),
        ):
            test_round.process_payload(
                SignaturePayload(sender="sender", signature="signature")
            )

        with pytest.raises(
            TransactionNotValidError,
            match=re.escape(
                "sender not in list of participants: ['agent_0', 'agent_1', 'agent_2', 'agent_3']"
            ),
        ):
            test_round.check_payload(
                SignaturePayload(sender="sender", signature="signature")
            )

        participant_to_signature = get_participant_to_signature(self.participants)
        first_payload = participant_to_signature.pop(
            sorted(list(participant_to_signature.keys()))[0]
        )

        test_round.process_payload(first_payload)
        assert not test_round.collection_threshold_reached
        assert (
            test_round.collection[first_payload.sender].signature  # type: ignore
            == first_payload.signature
        )
        assert test_round.end_block() is None

        with pytest.raises(
            ABCIAppInternalError,
            match="internal error: sender agent_0 has already sent value for round: collect_signature",
        ):
            test_round.process_payload(first_payload)

        with pytest.raises(
            TransactionNotValidError,
            match="sender agent_0 has already sent value for round: collect_signature",
        ):
            test_round.check_payload(first_payload)

        for payload in participant_to_signature.values():
            test_round.process_payload(payload)

        assert test_round.collection_threshold_reached
        res = test_round.end_block()
        assert res is not None
        _, event = res
        assert event == Event.DONE

    def test_no_majority_event(self) -> None:
        """Test the no-majority event."""
        test_round = CollectSignatureRound(self.period_state, self.consensus_params)
        self._test_no_majority_event(test_round)


class TestFinalizationRound(BaseRoundTestClass):
    """Test FinalizationRound."""

    def test_run_success(
        self,
    ) -> None:
        """Runs tests."""
        self.period_state = cast(
            PeriodState,
            self.period_state.update(
                most_voted_keeper_address=sorted(list(self.participants))[0]
            ),
        )

        test_round = FinalizationRound(
            state=self.period_state,
            consensus_params=self.consensus_params,
        )

        payload_0 = FinalizationTxPayload(
            sender=sorted(list(self.participants))[0], tx_hash=get_final_tx_hash()
        )

        payload_1 = FinalizationTxPayload(
            sender=sorted(list(self.participants))[1],
            tx_hash=get_final_tx_hash(),
        )

        actual_next_state = cast(
            PeriodState, self.period_state.update(final_tx_hash=get_final_tx_hash())
        )

        next_event = Event.DONE

        state = self._run(
            test_round, payload_0, payload_1, actual_next_state, next_event
        )
        assert state.final_tx_hash == actual_next_state.final_tx_hash

    def test_run_failure(
        self,
    ) -> None:
        """Runs tests."""

        self.period_state = cast(
            PeriodState,
            self.period_state.update(
                most_voted_keeper_address=sorted(list(self.participants))[0]
            ),
        )

        test_round = FinalizationRound(
            state=self.period_state,
            consensus_params=self.consensus_params,
        )

        payload_0 = FinalizationTxPayload(
            sender=sorted(list(self.participants))[0], tx_hash=None
        )

        payload_1 = FinalizationTxPayload(
            sender=sorted(list(self.participants))[1],
            tx_hash=get_final_tx_hash(),
        )

        actual_next_state = cast(
            PeriodState, self.period_state.update(final_tx_hash=None)
        )

        next_event = Event.FAILED

        state = self._run(
            test_round, payload_0, payload_1, actual_next_state, next_event
        )
        assert state._final_tx_hash is None

    def _run(
        self,
        test_round: FinalizationRound,
        payload_0: FinalizationTxPayload,
        payload_1: FinalizationTxPayload,
        actual_next_state: PeriodState,
        next_event: Event,
    ) -> PeriodState:
        """Run it."""
        with pytest.raises(
            ABCIAppInternalError,
            match=re.escape(
                "internal error: sender not in list of participants: ['agent_0', 'agent_1', 'agent_2', 'agent_3']"
            ),
        ):
            test_round.process_payload(
                FinalizationTxPayload(sender="sender", tx_hash=get_final_tx_hash())
            )

        with pytest.raises(
            TransactionNotValidError,
            match=re.escape(
                "sender not in list of participants: ['agent_0', 'agent_1', 'agent_2', 'agent_3']"
            ),
        ):
            test_round.check_payload(
                FinalizationTxPayload(sender="sender", tx_hash=get_final_tx_hash())
            )

        with pytest.raises(
            ABCIAppInternalError,
            match="internal error: agent_1 not elected as keeper",
        ):
            test_round.process_payload(payload_1)

        with pytest.raises(
            TransactionNotValidError,
            match="agent_1 not elected as keeper",
        ):
            test_round.check_payload(payload_1)

        assert not test_round.has_keeper_sent_payload
        assert test_round.end_block() is None

        test_round.process_payload(payload_0)

        assert test_round.has_keeper_sent_payload

        with pytest.raises(
            ABCIAppInternalError,
            match="internal error: keeper already set the payload.",
        ):
            test_round.process_payload(payload_0)

        with pytest.raises(
            TransactionNotValidError,
            match="keeper payload value already set.",
        ):
            test_round.check_payload(payload_0)

        res = test_round.end_block()
        assert res is not None
        state, event = res
        assert event == next_event
        return cast(PeriodState, state)


class BaseSelectKeeperRoundTest(BaseRoundTestClass):
    """Test SelectKeeperARound"""

    test_class: Type[SelectKeeperRound]
    test_payload: Type[SelectKeeperPayload]

    def test_run(
        self,
    ) -> None:
        """Run tests."""

        test_round = self.test_class(
            state=self.period_state, consensus_params=self.consensus_params
        )

        select_keeper_payloads = get_participant_to_selection(self.participants)
        first_payload = select_keeper_payloads.pop(
            sorted(list(select_keeper_payloads.keys()))[0]
        )

        test_round.process_payload(first_payload)
        assert test_round.collection[first_payload.sender] == first_payload
        assert not test_round.threshold_reached
        assert test_round.end_block() is None

        with pytest.raises(
            ABCIAppInternalError, match="internal error: not enough votes"
        ):
            _ = test_round.most_voted_payload

        with pytest.raises(ABCIAppInternalError):
            test_round.process_payload(self.test_payload(sender="sender", keeper=""))

        with pytest.raises(
            ABCIAppInternalError,
            match=f"internal error: sender agent_0 has already sent value for round: {self.test_class.round_id}",
        ):
            test_round.process_payload(first_payload)

        with pytest.raises(
            TransactionNotValidError,
            match=f"sender agent_0 has already sent value for round: {self.test_class.round_id}",
        ):
            test_round.check_payload(first_payload)

        with pytest.raises(
            TransactionNotValidError,
            match=re.escape(
                "sender not in list of participants: ['agent_0', 'agent_1', 'agent_2', 'agent_3']"
            ),
        ):
            test_round.check_payload(
                self.test_payload(sender="sender", keeper="keeper")
            )

        for payload in select_keeper_payloads.values():
            test_round.process_payload(payload)
        assert test_round.threshold_reached
        assert test_round.most_voted_payload == "keeper"

        actual_next_state = self.period_state.update(
            participant_to_selection=MappingProxyType(
                dict(get_participant_to_selection(self.participants))
            )
        )

        res = test_round.end_block()
        assert res is not None
        state, event = res
        assert (
            cast(PeriodState, state).participant_to_selection.keys()
            == cast(PeriodState, actual_next_state).participant_to_selection.keys()
        )
        assert event == Event.DONE

    def test_no_majority_event(self) -> None:
        """Test the no-majority event."""
        test_round = self.test_class(self.period_state, self.consensus_params)
        self._test_no_majority_event(test_round)


class TestSelectKeeperARound(BaseSelectKeeperRoundTest):
    """Test SelectKeeperARound"""

    test_class = SelectKeeperARound
    test_payload = SelectKeeperPayload


class TestSelectKeeperBRound(BaseSelectKeeperRoundTest):
    """Test SelectKeeperBRound."""

    test_class = SelectKeeperBRound
    test_payload = SelectKeeperPayload


class TestSelectKeeperAStartupRound(BaseSelectKeeperRoundTest):
    """Test SelectKeeperBRound."""

    test_class = SelectKeeperAStartupRound
    test_payload = SelectKeeperPayload


class TestSelectKeeperBStartupRound(BaseSelectKeeperRoundTest):
    """Test SelectKeeperBRound."""

    test_class = SelectKeeperBStartupRound
    test_payload = SelectKeeperPayload


class TestConsensusReachedRound(BaseRoundTestClass):
    """Test ConsensusReachedRound."""

    def test_runs(
        self,
    ) -> None:
        """Runs tests."""

        test_round = ConsensusReachedRound(
            state=self.period_state, consensus_params=self.consensus_params
        )

        next_period_count = 2
        reset_payloads = get_participant_to_period_count(
            self.participants, next_period_count
        )

        first_payload = reset_payloads.pop(sorted(list(reset_payloads.keys()))[0])
        test_round.process_payload(first_payload)
        assert test_round.collection[first_payload.sender] == first_payload
        assert not test_round.threshold_reached
        assert test_round.end_block() is None

        with pytest.raises(
            TransactionNotValidError,
            match=f"sender {first_payload.sender} has already sent value for round: {test_round.round_id}",
        ):
            test_round.check_payload(first_payload)

        with pytest.raises(
            ABCIAppInternalError,
            match=f"internal error: sender {first_payload.sender} has already sent value for round: {test_round.round_id}",
        ):
            test_round.process_payload(first_payload)

        for participant_payload in reset_payloads.values():
            test_round.process_payload(participant_payload)
        assert test_round.threshold_reached

        actual_next_state = PeriodState(
            participants=self.participants,
            period_count=test_round.most_voted_payload,
        )

        res = test_round.end_block()
        assert res is not None
        state, event = res
        assert (
            cast(PeriodState, state).participants
            == cast(PeriodState, actual_next_state).participants
        )
        assert event == Event.DONE

    def test_no_majority_event(self) -> None:
        """Test the no-majority event."""
        test_round = ConsensusReachedRound(
            state=self.period_state, consensus_params=self.consensus_params
        )
        self._test_no_majority_event(test_round)


class BaseValidateRoundTest(BaseRoundTestClass):
    """Test BaseValidateRound."""

    test_class: Type[ValidateRound]
    test_payload: Type[ValidatePayload]

    def test_positive_votes(
        self,
    ) -> None:
        """Test ValidateRound."""

        test_round = self.test_class(
            state=self.period_state, consensus_params=self.consensus_params
        )

        with pytest.raises(
            TransactionNotValidError,
            match=re.escape(
                "sender not in list of participants: ['agent_0', 'agent_1', 'agent_2', 'agent_3']"
            ),
        ):
            test_round.check_payload(self.test_payload(sender="sender", vote=True))

        with pytest.raises(
            TransactionNotValidError,
            match=re.escape(
                "sender not in list of participants: ['agent_0', 'agent_1', 'agent_2', 'agent_3']"
            ),
        ):
            test_round.check_payload(self.test_payload(sender="sender", vote=True))

        participant_to_votes_payloads = get_participant_to_votes(self.participants)
        first_payload = participant_to_votes_payloads.pop(
            sorted(list(participant_to_votes_payloads.keys()))[0]
        )
        test_round.process_payload(first_payload)

        with pytest.raises(
            ABCIAppInternalError,
            match=f"internal error: sender agent_0 has already sent value for round: {self.test_class.round_id}",
        ):
            test_round.process_payload(first_payload)

        assert test_round.collection[first_payload.sender] == first_payload

        with pytest.raises(
            TransactionNotValidError,
            match=f"sender agent_0 has already sent value for round: {self.test_class.round_id}",
        ):
            test_round.check_payload(first_payload)

        assert test_round.end_block() is None
        assert not test_round.positive_vote_threshold_reached
        for payload in participant_to_votes_payloads.values():
            test_round.process_payload(payload)

        assert test_round.positive_vote_threshold_reached

        actual_next_state = self.period_state.update(
            participant_to_votes=MappingProxyType(
                dict(get_participant_to_votes(self.participants))
            )
        )
        res = test_round.end_block()
        assert res is not None
        state, event = res
        assert (
            cast(PeriodState, state).participant_to_votes.keys()
            == cast(PeriodState, actual_next_state).participant_to_votes.keys()
        )
        assert event == Event.DONE

    def test_negative_votes(
        self,
    ) -> None:
        """Test ValidateRound."""

        test_round = self.test_class(
            state=self.period_state, consensus_params=self.consensus_params
        )

        participant_to_votes_payloads = get_participant_to_votes(
            self.participants, vote=False
        )
        first_payload = participant_to_votes_payloads.pop(
            sorted(list(participant_to_votes_payloads.keys()))[0]
        )
        test_round.process_payload(first_payload)

        assert test_round.collection[first_payload.sender] == first_payload
        assert test_round.end_block() is None
        assert not test_round.negative_vote_threshold_reached
        for payload in participant_to_votes_payloads.values():
            test_round.process_payload(payload)

        assert test_round.negative_vote_threshold_reached

        res = test_round.end_block()
        assert res is not None
        state, event = res
        assert event == Event.NEGATIVE
        with pytest.raises(
            AEAEnforceError, match="'participant_to_votes' field is None"
        ):
            _ = cast(PeriodState, state).participant_to_votes

    def test_none_votes(
        self,
    ) -> None:
        """Test ValidateRound."""

        test_round = self.test_class(
            state=self.period_state, consensus_params=self.consensus_params
        )

        participant_to_votes_payloads = get_participant_to_votes(
            self.participants, vote=None
        )
        first_payload = participant_to_votes_payloads.pop(
            sorted(list(participant_to_votes_payloads.keys()))[0]
        )
        test_round.process_payload(first_payload)

        assert test_round.collection[first_payload.sender] == first_payload
        assert test_round.end_block() is None
        assert not test_round.none_vote_threshold_reached
        for payload in participant_to_votes_payloads.values():
            test_round.process_payload(payload)

        assert test_round.none_vote_threshold_reached

        res = test_round.end_block()
        assert res is not None
        state, event = res
        assert event == Event.NONE
        with pytest.raises(
            AEAEnforceError, match="'participant_to_votes' field is None"
        ):
            _ = cast(PeriodState, state).participant_to_votes

    def test_no_majority_event(self) -> None:
        """Test the no-majority event."""
        test_round = self.test_class(self.period_state, self.consensus_params)
        self._test_no_majority_event(test_round)


class TestValidateSafeRound(BaseValidateRoundTest):
    """Test ValidateSafeRound."""

    test_class = ValidateSafeRound
    test_payload = ValidatePayload


class TestValidateOracleRound(BaseValidateRoundTest):
    """Test ValidateSafeRound."""

    test_class = ValidateOracleRound
    test_payload = ValidatePayload


class TestValidateTransactionRound(BaseValidateRoundTest):
    """Test ValidateRound."""

    test_class = ValidateTransactionRound
    test_payload = ValidatePayload


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
    oracle_contract_address = get_safe_contract_address()
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
        oracle_contract_address=oracle_contract_address,
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
    assert period_state.oracle_contract_address == oracle_contract_address
    assert period_state.participant_to_votes == participant_to_votes
    assert period_state.participant_to_observations == participant_to_observations
    assert period_state.participant_to_estimate == participant_to_estimate
    assert period_state.estimate == estimate
    assert period_state.most_voted_estimate == most_voted_estimate
    assert period_state.is_most_voted_estimate_set is True
    assert period_state.most_voted_tx_hash == most_voted_tx_hash
    assert period_state.participant_to_signature == participant_to_signature
    assert period_state.final_tx_hash == final_tx_hash
    assert period_state.is_final_tx_hash_set is True

    assert period_state.encoded_most_voted_estimate == encode_float(most_voted_estimate)
