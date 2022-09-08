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
from typing import Dict, FrozenSet, Optional

from packages.valory.skills.abstract_round_abci.base import AbciAppDB
from packages.valory.skills.abstract_round_abci.base import (
    BaseSynchronizedData as SynchronizedData,
)
from packages.valory.skills.abstract_round_abci.base import MAX_INT_256
from packages.valory.skills.abstract_round_abci.test_tools.rounds import (
    BaseCollectDifferentUntilThresholdRoundTest,
    BaseCollectSameUntilThresholdRoundTest,
)
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
    BaseSynchronizedData as RegistrationSynchronizedSata,
)
from packages.valory.skills.price_estimation_abci.rounds import (
    CollectObservationRound,
    EstimateConsensusRound,
)
from packages.valory.skills.price_estimation_abci.rounds import (
    Event as PriceEstimationEvent,
)
from packages.valory.skills.price_estimation_abci.rounds import (
    SynchronizedData as PriceEstimationSynchronizedSata,
)
from packages.valory.skills.price_estimation_abci.rounds import TxHashRound
from packages.valory.skills.transaction_settlement_abci.payloads import ValidatePayload
from packages.valory.skills.transaction_settlement_abci.rounds import (
    Event as TransactionSettlementEvent,
)
from packages.valory.skills.transaction_settlement_abci.rounds import (
    RandomnessTransactionSubmissionRound,
)
from packages.valory.skills.transaction_settlement_abci.rounds import (
    SynchronizedData as TransactionSettlementSynchronizedSata,
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

    _synchronized_data_class = TransactionSettlementSynchronizedSata
    _event_class = TransactionSettlementEvent

    def test_run(
        self,
    ) -> None:
        """Run tests."""

        test_round = RandomnessTransactionSubmissionRound(
            self.synchronized_data, self.consensus_params
        )
        self._complete_run(
            self._test_round(
                test_round=test_round,
                round_payloads=get_participant_to_randomness(self.participants, 1),
                synchronized_data_update_fn=lambda _synchronized_data, _test_round: _synchronized_data.update(
                    participant_to_randomness=MappingProxyType(
                        dict(get_participant_to_randomness(self.participants, 1))
                    )
                ),
                synchronized_data_attr_checks=[
                    lambda _synchronized_data: _synchronized_data.participant_to_randomness.keys()
                ],
                most_voted_payload=RANDOMNESS,
                exit_event=TransactionSettlementEvent.DONE,
            )
        )


class TestCollectObservationRound(BaseCollectDifferentUntilThresholdRoundTest):
    """Test CollectObservationRound."""

    _synchronized_data_class = PriceEstimationSynchronizedSata
    _event_class = PriceEstimationEvent

    def test_run_a(
        self,
    ) -> None:
        """Runs tests."""

        test_round = CollectObservationRound(
            synchronized_data=self.synchronized_data,
            consensus_params=self.consensus_params,
        )
        self._complete_run(
            self._test_round(
                test_round=test_round,
                round_payloads=get_participant_to_observations(self.participants),
                synchronized_data_update_fn=lambda _synchronized_data, _: _synchronized_data.update(
                    participant_to_observations=get_participant_to_observations(
                        self.participants
                    )
                ),
                synchronized_data_attr_checks=[
                    lambda _synchronized_data: _synchronized_data.participant_to_observations.keys()
                ],
                exit_event=self._event_class.DONE,
            )
        )

    def test_run_b(
        self,
    ) -> None:
        """Runs tests with one less observation."""

        test_round = CollectObservationRound(
            synchronized_data=self.synchronized_data,
            consensus_params=self.consensus_params,
        )

        self._complete_run(
            self._test_round(
                test_round=test_round,
                round_payloads=get_participant_to_observations(
                    frozenset(list(self.participants)[:-1])
                ),
                synchronized_data_update_fn=lambda _synchronized_data, _: _synchronized_data.update(
                    participant_to_observations=get_participant_to_observations(
                        frozenset(list(self.participants)[:-1])
                    )
                ),
                synchronized_data_attr_checks=[
                    lambda _synchronized_data: _synchronized_data.participant_to_observations.keys()
                ],
                exit_event=self._event_class.DONE,
            )
        )


class TestEstimateConsensusRound(BaseCollectSameUntilThresholdRoundTest):
    """Test EstimateConsensusRound."""

    _synchronized_data_class = PriceEstimationSynchronizedSata
    _event_class = PriceEstimationEvent

    def test_run(
        self,
    ) -> None:
        """Runs test."""

        test_round = EstimateConsensusRound(
            synchronized_data=self.synchronized_data,
            consensus_params=self.consensus_params,
        )
        self._complete_run(
            self._test_round(
                test_round=test_round,
                round_payloads=get_participant_to_estimate(self.participants),
                synchronized_data_update_fn=lambda _synchronized_data, _test_round: _synchronized_data.update(
                    participant_to_estimate=dict(
                        get_participant_to_estimate(self.participants)
                    ),
                    most_voted_estimate=_test_round.most_voted_payload,
                ),
                synchronized_data_attr_checks=[
                    lambda _synchronized_data: _synchronized_data.participant_to_estimate.keys()
                ],
                most_voted_payload=1.0,
                exit_event=self._event_class.DONE,
            )
        )


class TestTxHashRound(BaseCollectSameUntilThresholdRoundTest):
    """Test TxHashRound."""

    _synchronized_data_class = PriceEstimationSynchronizedSata
    _event_class = PriceEstimationEvent

    def test_run(
        self,
    ) -> None:
        """Runs test."""

        test_round = TxHashRound(
            synchronized_data=self.synchronized_data,
            consensus_params=self.consensus_params,
        )

        hash_ = "tx_hash"
        self._complete_run(
            self._test_round(
                test_round=test_round,
                round_payloads=get_participant_to_tx_hash(self.participants, hash_),
                synchronized_data_update_fn=lambda _synchronized_data, _test_round: _synchronized_data,
                synchronized_data_attr_checks=[],
                most_voted_payload=hash_,
                exit_event=self._event_class.DONE,
            )
        )

    def test_run_none(
        self,
    ) -> None:
        """Runs test."""

        test_round = TxHashRound(
            synchronized_data=self.synchronized_data,
            consensus_params=self.consensus_params,
        )

        hash_ = None
        self._complete_run(
            self._test_round(
                test_round=test_round,
                round_payloads=get_participant_to_tx_hash(self.participants, hash_),
                synchronized_data_update_fn=lambda _synchronized_data, _test_round: _synchronized_data,
                synchronized_data_attr_checks=[],
                most_voted_payload=hash_,
                exit_event=self._event_class.NONE,
            )
        )


def test_synchronized_datas() -> None:
    """Test SynchronizedData."""

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

    synchronized_data = SynchronizedData(
        AbciAppDB(
            setup_data=AbciAppDB.data_to_lists(
                dict(
                    participants=participants,
                    participant_to_randomness=participant_to_randomness,
                    most_voted_randomness=most_voted_randomness,
                    participant_to_selection=participant_to_selection,
                    most_voted_keeper_address=most_voted_keeper_address,
                    participant_to_votes=participant_to_votes,
                )
            ),
        )
    )

    actual_keeper_randomness = int(most_voted_randomness, base=16) / MAX_INT_256
    assert synchronized_data.keeper_randomness == actual_keeper_randomness
    assert synchronized_data.most_voted_randomness == most_voted_randomness
    assert synchronized_data.most_voted_keeper_address == most_voted_keeper_address
    assert synchronized_data.participant_to_votes == participant_to_votes

    synchronized_data____ = RegistrationSynchronizedSata(
        AbciAppDB(
            setup_data=AbciAppDB.data_to_lists(
                dict(
                    participants=participants,
                    participant_to_randomness=participant_to_randomness,
                    most_voted_randomness=most_voted_randomness,
                    participant_to_selection=participant_to_selection,
                    most_voted_keeper_address=most_voted_keeper_address,
                )
            ),
        )
    )

    assert (
        abs(synchronized_data____.keeper_randomness - actual_keeper_randomness) < 1e-10
    )  # avoid equality comparisons between floats
    assert synchronized_data____.most_voted_randomness == most_voted_randomness
    assert synchronized_data____.most_voted_keeper_address == most_voted_keeper_address

    synchronized_data______ = PriceEstimationSynchronizedSata(
        AbciAppDB(
            setup_data=AbciAppDB.data_to_lists(
                dict(
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
                )
            ),
        )
    )

    synchronized_data______.set_aggregator_method("median")

    assert synchronized_data______.keeper_randomness == actual_keeper_randomness
    assert synchronized_data______.most_voted_randomness == most_voted_randomness
    assert (
        synchronized_data______.most_voted_keeper_address == most_voted_keeper_address
    )
    assert synchronized_data______.safe_contract_address == safe_contract_address
    assert synchronized_data______.oracle_contract_address == oracle_contract_address
    assert synchronized_data______.most_voted_tx_hash == most_voted_tx_hash
    assert synchronized_data______.most_voted_estimate == most_voted_estimate
    assert (
        synchronized_data______.participant_to_observations
        == participant_to_observations
    )
    assert synchronized_data______.estimate == estimate
