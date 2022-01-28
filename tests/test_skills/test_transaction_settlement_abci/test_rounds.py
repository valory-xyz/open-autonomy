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

"""Tests for valory/registration_abci skill's rounds."""

import logging  # noqa: F401
from types import MappingProxyType
from typing import Dict, FrozenSet, List, Optional, Type, cast

import pytest

from packages.valory.skills.abstract_round_abci.base import (
    BasePeriodState as PeriodState,
)
from packages.valory.skills.abstract_round_abci.base import (
    CollectSameUntilThresholdRound,
    StateDB,
)
from packages.valory.skills.oracle_deployment_abci.payloads import (
    RandomnessPayload,
    SelectKeeperPayload,
)
from packages.valory.skills.transaction_settlement_abci.payload_tools import (
    VerificationStatus,
)
from packages.valory.skills.transaction_settlement_abci.payloads import (
    CheckTransactionHistoryPayload,
    FinalizationTxPayload,
    ResetPayload,
    SignaturePayload,
    ValidatePayload,
)
from packages.valory.skills.transaction_settlement_abci.rounds import (
    CheckTransactionHistoryRound,
    CollectSignatureRound,
)
from packages.valory.skills.transaction_settlement_abci.rounds import (
    Event as TransactionSettlementEvent,
)
from packages.valory.skills.transaction_settlement_abci.rounds import FinalizationRound
from packages.valory.skills.transaction_settlement_abci.rounds import (
    PeriodState as TransactionSettlementPeriodState,
)
from packages.valory.skills.transaction_settlement_abci.rounds import (
    ResetAndPauseRound,
    ResetRound,
    SelectKeeperTransactionSubmissionRoundA,
    SelectKeeperTransactionSubmissionRoundB,
    ValidateTransactionRound,
)

from tests.test_skills.test_abstract_round_abci.test_base_rounds import (
    BaseCollectDifferentUntilThresholdRoundTest,
    BaseCollectSameUntilThresholdRoundTest,
    BaseOnlyKeeperSendsRoundTest,
)
from tests.test_skills.test_oracle_deployment_abci.test_rounds import (
    BaseSelectKeeperRoundTest,
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


def get_oracle_contract_address() -> str:
    """oracle_contract_address"""
    return "0x6f6ab56aca12"


def get_participant_to_votes(
    participants: FrozenSet[str], vote: Optional[bool] = True
) -> Dict[str, ValidatePayload]:
    """participant_to_votes"""
    return {
        participant: ValidatePayload(sender=participant, is_settled=vote)
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


def get_participant_to_tx_result(
    participants: FrozenSet[str],
) -> Dict[str, ValidatePayload]:
    """Get participant_to_tx_result"""
    return {
        participant: ValidatePayload(sender=participant, transfers=[])
        for participant in participants
    }


def get_final_tx_hash() -> str:
    """final_tx_hash"""
    return "tx_hash"


def get_participant_to_check(
    participants: FrozenSet[str],
    status: str,
    tx_hash: str,
) -> Dict[str, CheckTransactionHistoryPayload]:
    """Get participants to check"""
    return {
        participant: CheckTransactionHistoryPayload(
            sender=participant,
            verified_res=status + tx_hash,
        )
        for participant in participants
    }


class TestSelectKeeperTransactionSubmissionRoundA(BaseSelectKeeperRoundTest):
    """Test SelectKeeperTransactionSubmissionRoundA"""

    test_class = SelectKeeperTransactionSubmissionRoundA
    test_payload = SelectKeeperPayload
    _event_class = TransactionSettlementEvent


class TestSelectKeeperTransactionSubmissionRoundB(BaseSelectKeeperRoundTest):
    """Test SelectKeeperTransactionSubmissionRoundB."""

    test_class = SelectKeeperTransactionSubmissionRoundB
    test_payload = SelectKeeperPayload
    _event_class = TransactionSettlementEvent


class TestFinalizationRound(BaseOnlyKeeperSendsRoundTest):
    """Test FinalizationRound."""

    _period_state_class = TransactionSettlementPeriodState
    _event_class = TransactionSettlementEvent

    @pytest.mark.parametrize("tx_hashes_history", (None, [get_final_tx_hash()]))
    def test_run_success(self, tx_hashes_history: Optional[List[str]]) -> None:
        """Runs tests."""

        keeper = sorted(list(self.participants))[0]
        self.period_state = cast(
            PeriodState,
            self.period_state.update(most_voted_keeper_address=keeper),
        )

        test_round = FinalizationRound(
            state=self.period_state,
            consensus_params=self.consensus_params,
        )

        self._complete_run(
            self._test_round(
                test_round=test_round,
                keeper_payloads=FinalizationTxPayload(
                    sender=keeper,
                    tx_data={
                        "tx_digest": "hash",
                        "nonce": 0,
                        "max_fee_per_gas": 0,
                        "max_priority_fee_per_gas": 0,
                    },
                ),
                state_update_fn=lambda _period_state, _: _period_state.update(
                    tx_hashes_history=tx_hashes_history
                ),
                state_attr_checks=[lambda state: state.final_tx_hash],
                exit_event=self._event_class.DONE,
            )
        )

    def test_run_failure(
        self,
    ) -> None:
        """Runs tests."""

        keeper = sorted(list(self.participants))[0]
        self.period_state = cast(
            PeriodState,
            self.period_state.update(most_voted_keeper_address=keeper),
        )

        test_round = FinalizationRound(
            state=self.period_state,
            consensus_params=self.consensus_params,
        )

        self._complete_run(
            self._test_round(
                test_round=test_round,
                keeper_payloads=FinalizationTxPayload(
                    sender=keeper,
                    tx_data={
                        "tx_digest": None,
                        "nonce": 0,
                        "max_fee_per_gas": 0,
                        "max_priority_fee_per_gas": 0,
                    },
                ),
                state_update_fn=lambda _period_state, _: _period_state.update(
                    tx_hashes_history=[get_final_tx_hash()]
                ),
                state_attr_checks=[],
                exit_event=self._event_class.FAILED,
            )
        )


class TestCollectSignatureRound(BaseCollectDifferentUntilThresholdRoundTest):
    """Test CollectSignatureRound."""

    _period_state_class = TransactionSettlementPeriodState
    _event_class = TransactionSettlementEvent

    def test_run(
        self,
    ) -> None:
        """Runs tests."""

        test_round = CollectSignatureRound(
            state=self.period_state, consensus_params=self.consensus_params
        )

        self._complete_run(
            self._test_round(
                test_round=test_round,
                round_payloads=get_participant_to_signature(self.participants),
                state_update_fn=lambda _period_state, _: _period_state,
                state_attr_checks=[],
                exit_event=self._event_class.DONE,
            )
        )

    def test_no_majority_event(self) -> None:
        """Test the no-majority event."""
        test_round = CollectSignatureRound(self.period_state, self.consensus_params)
        self._test_no_majority_event(test_round)


class BaseResetRoundTest(BaseCollectSameUntilThresholdRoundTest):
    """Test ResetRound."""

    test_class: Type[CollectSameUntilThresholdRound]
    _period_state_class = TransactionSettlementPeriodState
    _event_class = TransactionSettlementEvent

    def test_runs(
        self,
    ) -> None:
        """Runs tests."""

        period_state = self.period_state.update(
            oracle_contract_address=get_oracle_contract_address(),
            safe_contract_address=get_safe_contract_address(),
        )
        test_round = self.test_class(
            state=period_state, consensus_params=self.consensus_params
        )
        next_period_count = 1
        self._complete_run(
            self._test_round(
                test_round=test_round,
                round_payloads=get_participant_to_period_count(
                    self.participants, next_period_count
                ),
                state_update_fn=lambda _period_state, _: _period_state.update(
                    period_count=next_period_count,
                    participants=self.participants,
                    oracle_contract_address=_period_state.oracle_contract_address,
                    safe_contract_address=_period_state.safe_contract_address,
                ),
                state_attr_checks=[],  # [lambda state: state.participants],
                most_voted_payload=next_period_count,
                exit_event=self._event_class.DONE,
            )
        )


class TestResetRound(BaseResetRoundTest):
    """Test ResetRound."""

    test_class = ResetRound
    _period_state_class = TransactionSettlementPeriodState
    _event_class = TransactionSettlementEvent


class TestResetAndPauseRound(BaseResetRoundTest):
    """Test ResetAndPauseRound."""

    test_class = ResetAndPauseRound
    _period_state_class = TransactionSettlementPeriodState
    _event_class = TransactionSettlementEvent


class TestValidateTransactionRound(BaseCollectSameUntilThresholdRoundTest):
    """Test ValidateRound."""

    test_class = ValidateTransactionRound
    _event_class = TransactionSettlementEvent
    _period_state_class = TransactionSettlementPeriodState

    def test_run(
        self,
    ) -> None:
        """Run tests."""

class TestCheckTransactionHistoryRound(BaseCollectSameUntilThresholdRoundTest):
    """Test CheckTransactionHistoryRound"""

    _event_class = TransactionSettlementEvent
    _period_state_class = TransactionSettlementPeriodState

    @pytest.mark.parametrize(
        "expected_status, expected_tx_hash, expected_event",
        (
            (
                "0000000000000000000000000000000000000000000000000000000000000001",
                "b0e6add595e00477cf347d09797b156719dc5233283ac76e4efce2a674fe72d9",
                TransactionSettlementEvent.DONE,
            ),
            (
                "0000000000000000000000000000000000000000000000000000000000000002",
                "b0e6add595e00477cf347d09797b156719dc5233283ac76e4efce2a674fe72d9",
                TransactionSettlementEvent.NEGATIVE,
            ),
            (
                "0000000000000000000000000000000000000000000000000000000000000003",
                "b0e6add595e00477cf347d09797b156719dc5233283ac76e4efce2a674fe72d9",
                TransactionSettlementEvent.NONE,
            ),
        ),
    )
    def test_run(
        self,
        expected_status: str,
        expected_tx_hash: str,
        expected_event: TransactionSettlementEvent,
    ) -> None:
        """Run tests."""
        test_round = CheckTransactionHistoryRound(
            state=self.period_state, consensus_params=self.consensus_params
        )

        self._complete_run(
            self._test_round(
                test_round=test_round,
                round_payloads=get_participant_to_check(
                    self.participants, expected_status, expected_tx_hash
                ),
                state_update_fn=lambda period_state, _: period_state.update(
                    participant_to_check=MappingProxyType(
                        dict(
                            get_participant_to_check(
                                self.participants, expected_status, expected_tx_hash
                            )
                        )
                    ),
                    final_verification_status=VerificationStatus(int(expected_status)),
                    tx_hashes_history=[expected_tx_hash],
                ),
                state_attr_checks=[lambda state: state.final_verification_status],
                most_voted_payload=expected_status + expected_tx_hash,
                exit_event=expected_event,
            )
        )


def test_period_states() -> None:
    """Test PeriodState."""

    participants = get_participants()
    participant_to_randomness = get_participant_to_randomness(participants, 1)
    most_voted_randomness = get_most_voted_randomness()
    participant_to_selection = get_participant_to_selection(participants)
    most_voted_keeper_address = get_most_voted_keeper_address()
    safe_contract_address = get_safe_contract_address()
    oracle_contract_address = get_oracle_contract_address()
    most_voted_tx_hash = get_most_voted_tx_hash()
    participant_to_signature = get_participant_to_signature(participants)
    final_tx_hash = get_final_tx_hash()
    actual_keeper_randomness = float(
        (int(most_voted_randomness, base=16) // 10 ** 0 % 10) / 10
    )

    period_state_____ = TransactionSettlementPeriodState(
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
                participant_to_signature=participant_to_signature,
                tx_hashes_history=[final_tx_hash],
            ),
        )
    )
    assert period_state_____.keeper_randomness == actual_keeper_randomness
    assert period_state_____.most_voted_randomness == most_voted_randomness
    assert period_state_____.most_voted_keeper_address == most_voted_keeper_address
    assert period_state_____.safe_contract_address == safe_contract_address
    assert period_state_____.oracle_contract_address == oracle_contract_address
    assert period_state_____.most_voted_tx_hash == most_voted_tx_hash
    assert period_state_____.participant_to_signature == participant_to_signature
    assert period_state_____.final_tx_hash == final_tx_hash
