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

"""Tests for rounds.py file in valory/liquidity_provision."""

import json
from types import MappingProxyType
from typing import Dict, FrozenSet, Mapping, Optional  # noqa : F401
from unittest import mock

from packages.valory.skills.abstract_round_abci.base import StateDB
from packages.valory.skills.liquidity_provision.payloads import (
    StrategyEvaluationPayload,
)
from packages.valory.skills.liquidity_provision.rounds import (  # noqa: F401
    Event,
    PeriodState,
    StrategyEvaluationRound,
    TransactionHashBaseRound,
    TransactionSendBaseRound,
    TransactionSignatureBaseRound,
    TransactionValidationBaseRound,
)
from packages.valory.skills.price_estimation_abci.payloads import TransactionHashPayload
from packages.valory.skills.transaction_settlement_abci.payloads import (
    FinalizationTxPayload,
)

from tests.test_skills.test_abstract_round_abci.test_base_rounds import (
    BaseCollectDifferentUntilThresholdRoundTest,
    BaseCollectSameUntilThresholdRoundTest,
    BaseOnlyKeeperSendsRoundTest,
    BaseVotingRoundTest,
)
from tests.test_skills.test_price_estimation_abci.test_rounds import (
    get_participant_to_votes,
)
from tests.test_skills.test_transaction_settlement_abci.test_rounds import (
    get_participant_to_signature,
)


MAX_PARTICIPANTS: int = 4


def get_participants() -> FrozenSet[str]:
    """Returns test value for participants"""
    return frozenset([f"agent_{i}" for i in range(MAX_PARTICIPANTS)])


def get_participant_to_strategy(
    participants: FrozenSet[str],
) -> Mapping[str, StrategyEvaluationPayload]:
    """Returns test value for participant_to_strategy"""
    return dict(
        [
            (participant, StrategyEvaluationPayload(sender=participant, strategy={}))
            for participant in participants
        ]
    )


def get_participant_to_tx_hash(
    participants: FrozenSet[str],
    hash_: Optional[str] = "tx_hash",
    data_: Optional[str] = "tx_data",
) -> Mapping[str, TransactionHashPayload]:
    """participant_to_tx_hash"""
    return {
        participant: TransactionHashPayload(
            sender=participant, tx_hash=json.dumps({"tx_hash": hash_, "tx_data": data_})
        )
        for participant in participants
    }


class TestTransactionHashBaseRound(BaseCollectSameUntilThresholdRoundTest):
    """Test TransactionHashBaseRound"""

    _period_state_class = PeriodState
    _event_class = Event

    def test_run(
        self,
    ) -> None:
        """Run tests."""

        test_round = TransactionHashBaseRound(self.period_state, self.consensus_params)
        payloads = get_participant_to_tx_hash(self.participants)
        self._complete_run(
            self._test_round(
                test_round=test_round,
                round_payloads=payloads,
                state_update_fn=lambda _period_state, _test_round: _period_state.update(
                    participant_to_tx_hash=MappingProxyType(payloads),
                    most_voted_tx_hash=json.loads(_test_round.most_voted_payload)[
                        "tx_hash"
                    ],
                    most_voted_tx_data=json.loads(_test_round.most_voted_payload)[
                        "tx_data"
                    ],
                ),
                state_attr_checks=[
                    lambda state: state.participant_to_tx_hash.keys(),
                ],
                most_voted_payload=payloads["agent_1"].tx_hash,
                exit_event=Event.DONE,
            )
        )


class TestTransactionSignatureBaseRound(BaseCollectDifferentUntilThresholdRoundTest):
    """Test TransactionSignatureBaseRound."""

    _period_state_class = PeriodState
    _event_class = Event

    def test_run(
        self,
    ) -> None:
        """Run tests."""
        test_round = TransactionSignatureBaseRound(
            self.period_state, self.consensus_params
        )
        self._complete_run(
            self._test_round(
                test_round=test_round,
                round_payloads=get_participant_to_tx_hash(self.participants),
                state_update_fn=lambda _period_state, _test_round: _period_state.update(
                    participant_to_signature=MappingProxyType(
                        get_participant_to_signature(self.participants)
                    ),
                ),
                state_attr_checks=[
                    lambda state: state.participant_to_signature.keys(),
                ],
                exit_event=Event.DONE,
            )
        )

    def test_no_majority(
        self,
    ) -> None:
        """Test no majority."""
        test_round = TransactionSignatureBaseRound(
            self.period_state, self.consensus_params
        )
        self._test_no_majority_event(test_round)


class TestTransactionSendBaseRound(BaseOnlyKeeperSendsRoundTest):
    """Test TransactionSendBaseRound."""

    _period_state_class = PeriodState
    _event_class = Event

    def test_run(
        self,
    ) -> None:
        """Run tests."""

        keeper_payload = FinalizationTxPayload(
            sender="agent_0",
            tx_data={
                "tx_digest": "hash",
                "max_fee_per_gas": 0,
                "max_priority_fee_per_gas": 0,
            },
        )
        test_round = TransactionSendBaseRound(
            self.period_state.update(
                most_voted_keeper_address=keeper_payload.sender,
            ),
            self.consensus_params,
        )
        self._complete_run(
            self._test_round(
                test_round=test_round,
                keeper_payloads=keeper_payload,
                state_update_fn=lambda _period_state, _test_round: _period_state.update(
                    final_tx_hash=_test_round.keeper_payload
                ),
                state_attr_checks=[
                    lambda state: state.final_tx_hash,
                ],
                exit_event=Event.DONE,
            )
        )


class TestTransactionValidationBaseRound(BaseVotingRoundTest):
    """Test TransactionValidationBaseRound"""

    _period_state_class = PeriodState
    _event_class = Event

    def test_run(
        self,
    ) -> None:
        """Run tests."""
        test_round = TransactionValidationBaseRound(
            self.period_state, self.consensus_params
        )
        self._complete_run(
            self._test_voting_round_positive(
                test_round=test_round,
                round_payloads=get_participant_to_votes(self.participants),
                state_update_fn=lambda _period_state, _test_round: _period_state.update(
                    participant_to_votes=MappingProxyType(
                        get_participant_to_votes(self.participants)
                    ),
                ),
                state_attr_checks=[
                    lambda state: state.participant_to_votes.keys(),
                ],
                exit_event=Event.DONE,
            )
        )

    def test_negative_votes(
        self,
    ) -> None:
        """Run tests."""
        test_round = TransactionValidationBaseRound(
            self.period_state, self.consensus_params
        )
        self._complete_run(
            self._test_voting_round_negative(
                test_round=test_round,
                round_payloads=get_participant_to_votes(self.participants, False),
                state_update_fn=lambda _period_state, _test_round: _period_state.update(
                    participant_to_votes=MappingProxyType(
                        get_participant_to_votes(self.participants)
                    ),
                ),
                state_attr_checks=[
                    lambda state: None,
                ],
                exit_event=Event.EXIT,
            )
        )


class TestStrategyEvaluationRound(BaseCollectSameUntilThresholdRoundTest):
    """Test StrategyEvaluationRound"""

    _period_state_class = PeriodState
    _event_class = Event

    def test_run(
        self,
    ) -> None:
        """Run tests."""
        test_round = StrategyEvaluationRound(self.period_state, self.consensus_params)
        with mock.patch.object(
            StrategyEvaluationPayload, "strategy", return_value="strategy"
        ):
            self._complete_run(
                self._test_round(
                    test_round=test_round,
                    round_payloads=get_participant_to_strategy(self.participants),
                    state_update_fn=lambda _period_state, _test_round: _period_state.update(
                        participant_to_strategy=get_participant_to_strategy(
                            self.participants
                        ),
                        most_voted_strategy=test_round.most_voted_payload,
                    ),
                    state_attr_checks=[
                        lambda state: state.participant_to_strategy.keys(),
                    ],
                    most_voted_payload=StrategyEvaluationPayload.strategy,
                    exit_event=Event.RESET_TIMEOUT,
                )
            )


def test_period_state() -> None:
    """Test PeriodState."""

    participants = get_participants()
    period_count = 0
    period_setup_params: Dict = {}
    most_voted_strategy: Dict = {}
    most_voted_keeper_address = "0x_keeper"
    safe_contract_address = "0x_contract"
    multisend_contract_address = "0x_multisend"
    most_voted_tx_hash = "tx_hash"
    final_tx_hash = "tx_hash"
    participant_to_votes = get_participant_to_votes(participants)
    participant_to_tx_hash = get_participant_to_tx_hash(participants)
    participant_to_signature = get_participant_to_signature(participants)
    participant_to_strategy = get_participant_to_strategy(participants)

    period_state = PeriodState(
        StateDB(
            initial_period=period_count,
            initial_data=dict(
                participants=participants,
                period_setup_params=period_setup_params,
                most_voted_strategy=most_voted_strategy,
                most_voted_keeper_address=most_voted_keeper_address,
                safe_contract_address=safe_contract_address,
                multisend_contract_address=multisend_contract_address,
                most_voted_tx_hash=most_voted_tx_hash,
                final_tx_hash=final_tx_hash,
                participant_to_votes=participant_to_votes,
                participant_to_tx_hash=participant_to_tx_hash,
                participant_to_signature=participant_to_signature,
                participant_to_strategy=participant_to_strategy,
            ),
        )
    )

    assert period_state.participants == participants
    assert period_state.period_count == period_count
    assert period_state.most_voted_strategy == most_voted_strategy
    assert period_state.most_voted_keeper_address == most_voted_keeper_address
    assert period_state.safe_contract_address == safe_contract_address
    assert period_state.multisend_contract_address == multisend_contract_address
    assert period_state.most_voted_tx_hash == most_voted_tx_hash
    assert period_state.final_tx_hash == final_tx_hash
    assert period_state.participant_to_votes == participant_to_votes
    assert period_state.participant_to_tx_hash == participant_to_tx_hash
    assert period_state.participant_to_signature == participant_to_signature
    assert period_state.participant_to_strategy == participant_to_strategy
