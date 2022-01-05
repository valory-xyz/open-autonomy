# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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
from typing import Dict, FrozenSet, Optional

from packages.valory.skills.abstract_round_abci.base import (
    BasePeriodState as PeriodState,
)
from packages.valory.skills.abstract_round_abci.base import StateDB
from packages.valory.skills.oracle_deployment_abci.payloads import (
    RandomnessPayload,
    SelectKeeperPayload,
)
from packages.valory.skills.price_estimation_abci.payloads import (
    EstimatePayload,
    ObservationPayload,
    TransactionHashPayload,
)
from packages.valory.skills.price_estimation_abci.rounds import (
    CollectObservationRound,
    EstimateConsensusRound,
)
from packages.valory.skills.price_estimation_abci.rounds import (
    Event as PriceEstimationEvent,
)
from packages.valory.skills.price_estimation_abci.rounds import (
    PeriodState as PriceEstimationPeriodState,
)
from packages.valory.skills.price_estimation_abci.rounds import TxHashRound
from packages.valory.skills.registration_abci.rounds import (
    BasePeriodState as RegistrationPeriodState,
)
from packages.valory.skills.transaction_settlement_abci.payloads import (
    ResetPayload,
    ValidatePayload,
)
from packages.valory.skills.transaction_settlement_abci.rounds import (
    Event as TransactionSettlementEvent,
)
from packages.valory.skills.transaction_settlement_abci.rounds import (
    PeriodState as TransactionSettlementPeriodState,
)
from packages.valory.skills.transaction_settlement_abci.rounds import (
    RandomnessTransactionSubmissionRound,
    rotate_list,
)

from tests.test_skills.test_abstract_round_abci.test_base_rounds import (
    BaseCollectDifferentUntilThresholdRoundTest,
    BaseCollectSameUntilThresholdRoundTest,
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


class TestRandomnessTransactionSubmissionRound(BaseCollectSameUntilThresholdRoundTest):
    """Test RandomnessTransactionSubmissionRound."""

    _period_state_class = TransactionSettlementPeriodState
    _event_class = TransactionSettlementEvent

    def test_run(
        self,
    ) -> None:
        """Run tests."""

        test_round = RandomnessTransactionSubmissionRound(
            self.period_state, self.consensus_params
        )
        self._complete_run(
            self._test_round(
                test_round=test_round,
                round_payloads=get_participant_to_randomness(self.participants, 1),
                state_update_fn=lambda _period_state, _test_round: _period_state.update(
                    participant_to_randomness=MappingProxyType(
                        dict(get_participant_to_randomness(self.participants, 1))
                    )
                ),
                state_attr_checks=[
                    lambda state: state.participant_to_randomness.keys()
                ],
                most_voted_payload=RANDOMNESS,
                exit_event=TransactionSettlementEvent.DONE,
            )
        )


class TestCollectObservationRound(BaseCollectDifferentUntilThresholdRoundTest):
    """Test CollectObservationRound."""

    _period_state_class = PriceEstimationPeriodState
    _event_class = PriceEstimationEvent

    def test_run_a(
        self,
    ) -> None:
        """Runs tests."""

        test_round = CollectObservationRound(
            state=self.period_state, consensus_params=self.consensus_params
        )
        self._complete_run(
            self._test_round(
                test_round=test_round,
                round_payloads=get_participant_to_observations(self.participants),
                state_update_fn=lambda _period_state, _: _period_state.update(
                    participant_to_observations=get_participant_to_observations(
                        self.participants
                    )
                ),
                state_attr_checks=[
                    lambda state: state.participant_to_observations.keys()
                ],
                exit_event=self._event_class.DONE,
            )
        )

    def test_run_b(
        self,
    ) -> None:
        """Runs tests with one less observation."""

        test_round = CollectObservationRound(
            state=self.period_state, consensus_params=self.consensus_params
        )

        self._complete_run(
            self._test_round(
                test_round=test_round,
                round_payloads=get_participant_to_observations(
                    frozenset(list(self.participants)[:-1])
                ),
                state_update_fn=lambda _period_state, _: _period_state.update(
                    participant_to_observations=get_participant_to_observations(
                        frozenset(list(self.participants)[:-1])
                    )
                ),
                state_attr_checks=[
                    lambda state: state.participant_to_observations.keys()
                ],
                exit_event=self._event_class.DONE,
            )
        )


class TestEstimateConsensusRound(BaseCollectSameUntilThresholdRoundTest):
    """Test EstimateConsensusRound."""

    _period_state_class = PriceEstimationPeriodState
    _event_class = PriceEstimationEvent

    def test_run(
        self,
    ) -> None:
        """Runs test."""

        test_round = EstimateConsensusRound(
            state=self.period_state, consensus_params=self.consensus_params
        )
        self._complete_run(
            self._test_round(
                test_round=test_round,
                round_payloads=get_participant_to_estimate(self.participants),
                state_update_fn=lambda _period_state, _test_round: _period_state.update(
                    participant_to_estimate=dict(
                        get_participant_to_estimate(self.participants)
                    ),
                    most_voted_estimate=_test_round.most_voted_payload,
                ),
                state_attr_checks=[lambda state: state.participant_to_estimate.keys()],
                most_voted_payload=1.0,
                exit_event=self._event_class.DONE,
            )
        )


class TestTxHashRound(BaseCollectSameUntilThresholdRoundTest):
    """Test TxHashRound."""

    _period_state_class = PriceEstimationPeriodState
    _event_class = PriceEstimationEvent

    def test_run(
        self,
    ) -> None:
        """Runs test."""

        test_round = TxHashRound(
            state=self.period_state, consensus_params=self.consensus_params
        )

        hash_ = "tx_hash"
        self._complete_run(
            self._test_round(
                test_round=test_round,
                round_payloads=get_participant_to_tx_hash(self.participants, hash_),
                state_update_fn=lambda _period_state, _test_round: _period_state,
                state_attr_checks=[],
                most_voted_payload=hash_,
                exit_event=self._event_class.DONE,
            )
        )

    def test_run_none(
        self,
    ) -> None:
        """Runs test."""

        test_round = TxHashRound(
            state=self.period_state, consensus_params=self.consensus_params
        )

        hash_ = None
        self._complete_run(
            self._test_round(
                test_round=test_round,
                round_payloads=get_participant_to_tx_hash(self.participants, hash_),
                state_update_fn=lambda _period_state, _test_round: _period_state,
                state_attr_checks=[],
                most_voted_payload=hash_,
                exit_event=self._event_class.NONE,
            )
        )


def test_rotate_list_method() -> None:
    """Test `rotate_list` method."""

    ex_list = [1, 2, 3, 4, 5]
    assert rotate_list(ex_list, 2) == [3, 4, 5, 1, 2]


def test_period_states() -> None:
    """Test PeriodState."""

    participants = get_participants()
    participant_to_randomness = get_participant_to_randomness(participants, 1)
    most_voted_randomness = get_most_voted_randomness()
    participant_to_selection = get_participant_to_selection(participants)
    most_voted_keeper_address = get_most_voted_keeper_address()
    safe_contract_address = get_safe_contract_address()
    oracle_contract_address = get_safe_contract_address()
    participant_to_votes = get_participant_to_votes(participants)
    most_voted_tx_hash = get_most_voted_tx_hash()
    participant_to_observations = get_participant_to_observations(participants)
    estimate = get_estimate()
    most_voted_estimate = get_most_voted_estimate()

    period_state = PeriodState(
        StateDB(
            initial_period=0,
            initial_data=dict(
                participants=participants,
                participant_to_randomness=participant_to_randomness,
                most_voted_randomness=most_voted_randomness,
                participant_to_selection=participant_to_selection,
                most_voted_keeper_address=most_voted_keeper_address,
                participant_to_votes=participant_to_votes,
            ),
        )
    )

    actual_keeper_randomness = float(
        (int(most_voted_randomness, base=16) // 10 ** 0 % 10) / 10
    )
    assert period_state.keeper_randomness == actual_keeper_randomness
    assert period_state.most_voted_randomness == most_voted_randomness
    assert period_state.most_voted_keeper_address == most_voted_keeper_address
    assert period_state.participant_to_votes == participant_to_votes

    period_state____ = RegistrationPeriodState(
        StateDB(
            initial_period=0,
            initial_data=dict(
                participants=participants,
                participant_to_randomness=participant_to_randomness,
                most_voted_randomness=most_voted_randomness,
                participant_to_selection=participant_to_selection,
                most_voted_keeper_address=most_voted_keeper_address,
            ),
        )
    )

    assert period_state____.keeper_randomness == actual_keeper_randomness
    assert period_state____.most_voted_randomness == most_voted_randomness
    assert period_state____.most_voted_keeper_address == most_voted_keeper_address

    period_state______ = PriceEstimationPeriodState(
        StateDB(
            initial_period=0,
            initial_data=dict(
                participants=participants,
                participant_to_randomness=participant_to_randomness,
                most_voted_randomness=most_voted_randomness,
                participant_to_selection=participant_to_selection,
                most_voted_keeper_address=most_voted_keeper_address,
                safe_contract_address=safe_contract_address,
                oracle_contract_address=oracle_contract_address,
                most_voted_tx_hash=most_voted_tx_hash,
                most_voted_estimate=most_voted_estimate,
                participant_to_observations=participant_to_observations,
            ),
        )
    )

    period_state______.set_aggregator_method("median")

    assert period_state______.keeper_randomness == actual_keeper_randomness
    assert period_state______.most_voted_randomness == most_voted_randomness
    assert period_state______.most_voted_keeper_address == most_voted_keeper_address
    assert period_state______.safe_contract_address == safe_contract_address
    assert period_state______.oracle_contract_address == oracle_contract_address
    assert period_state______.most_voted_tx_hash == most_voted_tx_hash
    assert period_state______.most_voted_estimate == most_voted_estimate
    assert period_state______.participant_to_observations == participant_to_observations
    assert period_state______.estimate == estimate
