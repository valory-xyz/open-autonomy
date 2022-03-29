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
from collections import deque
from types import MappingProxyType
from typing import Deque, Dict, FrozenSet, List, Optional, cast

import pytest

from packages.valory.skills.abstract_round_abci.base import ABCIAppInternalError
from packages.valory.skills.abstract_round_abci.base import (
    BasePeriodState as PeriodState,
)
from packages.valory.skills.abstract_round_abci.base import StateDB
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
    SynchronizeLateMessagesPayload,
    ValidatePayload,
)
from packages.valory.skills.transaction_settlement_abci.rounds import (
    CheckTransactionHistoryRound,
    CollectSignatureRound,
)
from packages.valory.skills.transaction_settlement_abci.rounds import (
    Event as TransactionSettlementEvent,
)
from packages.valory.skills.transaction_settlement_abci.rounds import (
    FinalizationRound,
    FinalizationRoundAfterTimeout,
)
from packages.valory.skills.transaction_settlement_abci.rounds import (
    PeriodState as TransactionSettlementPeriodState,
)
from packages.valory.skills.transaction_settlement_abci.rounds import (
    ResetRound,
    SelectKeeperTransactionSubmissionRoundA,
    SelectKeeperTransactionSubmissionRoundB,
    SelectKeeperTransactionSubmissionRoundBAfterTimeout,
    SynchronizeLateMessagesRound,
    ValidateTransactionRound,
)

from tests.test_skills.test_abstract_round_abci.test_base_rounds import (
    BaseCollectDifferentUntilThresholdRoundTest,
    BaseCollectNonEmptyUntilThresholdRound,
    BaseCollectSameUntilThresholdRoundTest,
    BaseOnlyKeeperSendsRoundTest,
)
from tests.test_skills.test_oracle_deployment_abci.test_rounds import (
    BaseSelectKeeperRoundTest,
    BaseValidateRoundTest,
)


MAX_PARTICIPANTS: int = 4
RANDOMNESS: str = "d1c29dce46f979f9748210d24bce4eae8be91272f5ca1a6aea2832d3dd676f51"
DUMMY_RANDOMNESS = 0.1  # for coverage purposes


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


def get_participant_to_late_arriving_tx_hashes(
    participants: FrozenSet[str],
) -> Dict[str, SynchronizeLateMessagesPayload]:
    """participant_to_selection"""
    return {
        participant: SynchronizeLateMessagesPayload(
            sender=participant, tx_hashes="1" * 64 + "2" * 64
        )
        for participant in participants
    }


def get_late_arriving_tx_hashes() -> List[str]:
    """Get dummy late-arriving tx hashes."""
    # We want the tx hashes to have a size which can be divided by 64 to be able to parse it.
    # Otherwise, they are not valid.
    return ["t" * 64, "e" * 64, "s" * 64, "t" * 64]


def get_keepers() -> Deque[str]:
    """Get dummy keepers."""
    return deque(["agent_1", "agent_3"])


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


class TestSelectKeeperTransactionSubmissionRoundBAfterTimeout(
    TestSelectKeeperTransactionSubmissionRoundB
):
    """Test SelectKeeperTransactionSubmissionRoundBAfterTimeout."""

    test_class = SelectKeeperTransactionSubmissionRoundBAfterTimeout
    _period_state_class = TransactionSettlementPeriodState

    @pytest.mark.parametrize(
        "attrs, exit_event",
        (
            (
                {
                    "missed_messages": 10,
                    # These are the `consecutive_finalizations` before entering the round.
                    # Therefore, the `consecutive_finalizations` will become 2 after entering the round.
                    "consecutive_finalizations": 1,
                },
                # Since we have 4 participants, and we now have 2 keepers that have retried,
                # we should return a `CHECK_HISTORY` event.
                TransactionSettlementEvent.CHECK_HISTORY,
            ),
            (
                {
                    "missed_messages": 10,
                    "consecutive_finalizations": 0,
                },
                TransactionSettlementEvent.DONE,
            ),
        ),
    )
    def test_run(  # type: ignore
        self, attrs: Dict[str, int], exit_event: TransactionSettlementEvent
    ) -> None:
        """Test `SelectKeeperTransactionSubmissionRoundBAfterTimeout`."""
        self._exit_event = exit_event
        self.period_state.update(**attrs)  # type: ignore
        super().test_run()
        assert all(
            getattr(self.period_state, attr_name) == attr_value + 1
            for attr_name, attr_value in attrs.items()
        )


class TestFinalizationRound(BaseOnlyKeeperSendsRoundTest):
    """Test FinalizationRound."""

    _period_state_class = TransactionSettlementPeriodState
    _event_class = TransactionSettlementEvent
    _round_class = FinalizationRound

    def _update_keepers_hist(
        self,
        keepers_hist: Deque[str],
        keeper: str,
        exit_event: TransactionSettlementEvent,
    ) -> None:
        """Update keepers hist."""
        if exit_event == TransactionSettlementEvent.DONE:
            keepers_hist.append(keeper)

    @pytest.mark.parametrize(
        "tx_hashes_history, tx_digest, missed_messages, status, exit_event",
        (
            (
                [],
                "",
                1,
                VerificationStatus.ERROR.value,
                TransactionSettlementEvent.CHECK_LATE_ARRIVING_MESSAGE,
            ),
            (
                [],
                "",
                0,
                VerificationStatus.ERROR.value,
                TransactionSettlementEvent.FINALIZATION_FAILED,
            ),
            (
                ["test"],
                "",
                0,
                VerificationStatus.VERIFIED.value,
                TransactionSettlementEvent.CHECK_HISTORY,
            ),
            (
                ["test"],
                "",
                0,
                VerificationStatus.ERROR.value,
                TransactionSettlementEvent.CHECK_HISTORY,
            ),
            (
                [],
                "",
                0,
                VerificationStatus.PENDING.value,
                TransactionSettlementEvent.FINALIZATION_FAILED,
            ),
            (
                [],
                "tx_digest",
                0,
                VerificationStatus.PENDING.value,
                TransactionSettlementEvent.DONE,
            ),
            (
                ["test"],
                "tx_digest",
                0,
                VerificationStatus.PENDING.value,
                TransactionSettlementEvent.DONE,
            ),
        ),
    )
    def test_finalization_round(
        self,
        tx_hashes_history: List[str],
        tx_digest: str,
        missed_messages: int,
        status: int,
        exit_event: TransactionSettlementEvent,
    ) -> None:
        """Runs tests."""

        keeper = sorted(list(self.participants))[0]
        keepers_hist = deque(["agent2", "agent3"])
        self.period_state = cast(
            PeriodState,
            self.period_state.update(
                most_voted_keeper_address=keeper,
                missed_messages=missed_messages,
                tx_hashes_history=tx_hashes_history,
                keepers=keepers_hist.copy(),
            ),
        )
        tx_hashes_history.append(
            tx_digest
        ) if exit_event == TransactionSettlementEvent.DONE else tx_hashes_history
        self._update_keepers_hist(keepers_hist, keeper, exit_event)

        test_round = self._round_class(
            state=self.period_state,
            consensus_params=self.consensus_params,
        )

        self._complete_run(
            self._test_round(
                test_round=test_round,
                keeper_payloads=FinalizationTxPayload(
                    sender=keeper,
                    tx_data={
                        "status": status,
                        "tx_digest": tx_digest,
                        "nonce": 0,
                        "max_fee_per_gas": 0,
                        "max_priority_fee_per_gas": 0,
                    },
                ),
                state_update_fn=lambda _period_state, _: _period_state.update(
                    tx_hashes_history=tx_hashes_history, keepers=keepers_hist
                ),
                state_attr_checks=[
                    lambda state: state.keepers,
                    lambda state: state.tx_hashes_history,
                ],
                exit_event=exit_event,
            )
        )


class TestFinalizationRoundAfterTimeout(TestFinalizationRound):
    """Test FinalizationRoundAfterTimeout."""

    _period_state_class = TransactionSettlementPeriodState
    _event_class = TransactionSettlementEvent
    _round_class = FinalizationRoundAfterTimeout

    def _update_keepers_hist(
        self,
        keepers_hist: Deque[str],
        keeper: str,
        exit_event: TransactionSettlementEvent,
    ) -> None:
        """Update keepers hist."""
        current_keeper = keepers_hist.popleft()
        keepers_hist.append(current_keeper)


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


class TestValidateTransactionRound(BaseValidateRoundTest):
    """Test ValidateRound."""

    test_class = ValidateTransactionRound
    _event_class = TransactionSettlementEvent
    _period_state_class = TransactionSettlementPeriodState


class TestCheckTransactionHistoryRound(BaseCollectSameUntilThresholdRoundTest):
    """Test CheckTransactionHistoryRound"""

    _event_class = TransactionSettlementEvent
    _period_state_class = TransactionSettlementPeriodState

    @pytest.mark.parametrize(
        "expected_status, expected_tx_hash, missed_messages, expected_event",
        (
            (
                "0000000000000000000000000000000000000000000000000000000000000001",
                "b0e6add595e00477cf347d09797b156719dc5233283ac76e4efce2a674fe72d9",
                0,
                TransactionSettlementEvent.DONE,
            ),
            (
                "0000000000000000000000000000000000000000000000000000000000000002",
                "b0e6add595e00477cf347d09797b156719dc5233283ac76e4efce2a674fe72d9",
                0,
                TransactionSettlementEvent.NEGATIVE,
            ),
            (
                "0000000000000000000000000000000000000000000000000000000000000003",
                "b0e6add595e00477cf347d09797b156719dc5233283ac76e4efce2a674fe72d9",
                0,
                TransactionSettlementEvent.NONE,
            ),
            (
                "0000000000000000000000000000000000000000000000000000000000000002",
                "b0e6add595e00477cf347d09797b156719dc5233283ac76e4efce2a674fe72d9",
                1,
                TransactionSettlementEvent.CHECK_LATE_ARRIVING_MESSAGE,
            ),
        ),
    )
    def test_run(
        self,
        expected_status: str,
        expected_tx_hash: str,
        missed_messages: int,
        expected_event: TransactionSettlementEvent,
    ) -> None:
        """Run tests."""
        keepers = deque(["keeper2", "keeper1"])
        self.period_state.update(missed_messages=missed_messages, keepers=keepers)

        test_round = CheckTransactionHistoryRound(
            state=self.period_state, consensus_params=self.consensus_params
        )

        keepers = (
            deque()
            if expected_event
            in (TransactionSettlementEvent.DONE, TransactionSettlementEvent.NONE)
            else keepers
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
                    keepers=keepers,
                ),
                state_attr_checks=[
                    lambda state: state.final_verification_status,
                    lambda state: state.final_tx_hash,
                    lambda state: state.keepers,
                ]
                if expected_event
                not in {
                    TransactionSettlementEvent.NEGATIVE,
                    TransactionSettlementEvent.CHECK_LATE_ARRIVING_MESSAGE,
                }
                else [
                    lambda state: state.final_verification_status,
                    lambda state: state.keepers,
                ],
                most_voted_payload=expected_status + expected_tx_hash,
                exit_event=expected_event,
            )
        )


class TestSynchronizeLateMessagesRound(BaseCollectNonEmptyUntilThresholdRound):
    """Test `SynchronizeLateMessagesRound`."""

    _event_class = TransactionSettlementEvent
    _period_state_class = TransactionSettlementPeriodState

    @pytest.mark.parametrize(
        "missed_messages, expected_event",
        (
            (0, TransactionSettlementEvent.MISSED_AND_LATE_MESSAGES_MISMATCH),
            (8, TransactionSettlementEvent.DONE),
        ),
    )
    def test_runs(
        self, missed_messages: int, expected_event: TransactionSettlementEvent
    ) -> None:
        """Runs tests."""
        self.period_state.update(missed_messages=missed_messages)
        test_round = SynchronizeLateMessagesRound(
            state=self.period_state, consensus_params=self.consensus_params
        )
        self._complete_run(
            self._test_round(
                test_round=test_round,
                round_payloads=get_participant_to_late_arriving_tx_hashes(
                    self.participants
                ),
                state_update_fn=lambda _period_state, _: _period_state.update(
                    late_arriving_tx_hashes=["1" * 64, "2" * 64]
                ),
                state_attr_checks=[],
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
    most_voted_tx_hash = get_most_voted_tx_hash()
    participant_to_signature = get_participant_to_signature(participants)
    final_tx_hash = get_final_tx_hash()
    actual_keeper_randomness = float(
        (int(most_voted_randomness, base=16) // 10 ** 0 % 10) / 10
    )
    late_arriving_tx_hashes = get_late_arriving_tx_hashes()
    keepers = get_keepers()

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
                most_voted_tx_hash=most_voted_tx_hash,
                participant_to_signature=participant_to_signature,
                final_tx_hash=final_tx_hash,
                late_arriving_tx_hashes=late_arriving_tx_hashes,
                keepers=keepers,
            ),
        )
    )
    assert period_state_____.keeper_randomness == actual_keeper_randomness
    assert period_state_____.most_voted_randomness == most_voted_randomness
    assert period_state_____.most_voted_keeper_address == most_voted_keeper_address
    assert period_state_____.safe_contract_address == safe_contract_address
    assert period_state_____.most_voted_tx_hash == most_voted_tx_hash
    assert period_state_____.participant_to_signature == participant_to_signature
    assert period_state_____.final_tx_hash == final_tx_hash
    assert period_state_____.late_arriving_tx_hashes == late_arriving_tx_hashes
    assert period_state_____.keepers == keepers
    assert period_state_____.keeper_in_priority == keepers.popleft()

    # test wrong tx hashes serialization
    period_state_____.update(late_arriving_tx_hashes=["test"])
    with pytest.raises(
        ABCIAppInternalError,
        match="internal error: Cannot parse late arriving hashes: test!",
    ):
        _ = period_state_____.late_arriving_tx_hashes


class TestResetRound(BaseCollectSameUntilThresholdRoundTest):
    """Test ResetRound."""

    _period_state_class = TransactionSettlementPeriodState
    _event_class = TransactionSettlementEvent

    def test_runs(
        self,
    ) -> None:
        """Runs tests."""

        period_state = self.period_state.update(
            keeper_randomness=DUMMY_RANDOMNESS,
        )
        period_state._db._cross_period_persisted_keys = ["keeper_randomness"]
        test_round = ResetRound(
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
                    all_participants=self.participants,
                    keeper_randomness=DUMMY_RANDOMNESS,
                ),
                state_attr_checks=[],  # [lambda state: state.participants],
                most_voted_payload=next_period_count,
                exit_event=self._event_class.DONE,
            )
        )
