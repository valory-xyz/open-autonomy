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

"""Tests for valory/registration_abci skill's rounds."""

# pylint: skip-file

import hashlib
import logging  # noqa: F401
from collections import deque
from typing import (
    Any,
    Deque,
    Dict,
    FrozenSet,
    List,
    Mapping,
    Optional,
    Type,
    Union,
    cast,
)
from unittest import mock
from unittest.mock import MagicMock

import pytest

from packages.valory.skills.abstract_round_abci.base import (
    ABCIAppInternalError,
    AbciAppDB,
)
from packages.valory.skills.abstract_round_abci.base import (
    BaseSynchronizedData as SynchronizedData,
)
from packages.valory.skills.abstract_round_abci.base import (
    BaseTxPayload,
    CollectSameUntilThresholdRound,
    CollectionRound,
    MAX_INT_256,
    TransactionNotValidError,
    VotingRound,
)
from packages.valory.skills.abstract_round_abci.test_tools.rounds import (
    BaseCollectDifferentUntilThresholdRoundTest,
    BaseCollectNonEmptyUntilThresholdRound,
    BaseCollectSameUntilThresholdRoundTest,
    BaseOnlyKeeperSendsRoundTest,
    BaseVotingRoundTest,
)
from packages.valory.skills.transaction_settlement_abci.payload_tools import (
    VerificationStatus,
)
from packages.valory.skills.transaction_settlement_abci.payloads import (
    CheckTransactionHistoryPayload,
    FinalizationTxPayload,
    RandomnessPayload,
    ResetPayload,
    SelectKeeperPayload,
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
    ResetRound,
    SelectKeeperTransactionSubmissionARound,
    SelectKeeperTransactionSubmissionBAfterTimeoutRound,
    SelectKeeperTransactionSubmissionBRound,
    SynchronizeLateMessagesRound,
)
from packages.valory.skills.transaction_settlement_abci.rounds import (
    SynchronizedData as TransactionSettlementSynchronizedSata,
)
from packages.valory.skills.transaction_settlement_abci.rounds import (
    TX_HASH_LENGTH,
    ValidateTransactionRound,
)


MAX_PARTICIPANTS: int = 4
RANDOMNESS: str = "d1c29dce46f979f9748210d24bce4eae8be91272f5ca1a6aea2832d3dd676f51"
DUMMY_RANDOMNESS = hashlib.sha256("hash".encode() + str(0).encode()).hexdigest()


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
    keepers: str,
) -> Dict[str, SelectKeeperPayload]:
    """participant_to_selection"""
    return {
        participant: SelectKeeperPayload(sender=participant, keepers=keepers)
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


def get_participant_to_votes_serialized(
    participants: FrozenSet[str], vote: Optional[bool] = True
) -> Dict[str, Dict[str, Any]]:
    """participant_to_votes"""
    return CollectionRound.serialize_collection(
        get_participant_to_votes(participants, vote)
    )


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
            sender=participant, tx_hashes="1" * TX_HASH_LENGTH + "2" * TX_HASH_LENGTH
        )
        for participant in participants
    }


def get_late_arriving_tx_hashes_deserialized() -> Dict[str, List[str]]:
    """Get dummy late-arriving tx hashes."""
    # We want the tx hashes to have a size which can be divided by 64 to be able to parse it.
    # Otherwise, they are not valid.
    return {
        "sender": [
            "t" * TX_HASH_LENGTH,
            "e" * TX_HASH_LENGTH,
            "s" * TX_HASH_LENGTH,
            "t" * TX_HASH_LENGTH,
        ]
    }


def get_late_arriving_tx_hashes_serialized() -> Dict[str, str]:
    """Get dummy late-arriving tx hashes."""
    # We want the tx hashes to have a size which can be divided by 64 to be able to parse it.
    # Otherwise, they are not valid.
    deserialized = get_late_arriving_tx_hashes_deserialized()
    return {sender: "".join(hash_) for sender, hash_ in deserialized.items()}


def get_keepers(keepers: Deque[str], retries: int = 1) -> str:
    """Get dummy keepers."""
    return retries.to_bytes(32, "big").hex() + "".join(keepers)


class BaseValidateRoundTest(BaseVotingRoundTest):
    """Test BaseValidateRound."""

    test_class: Type[VotingRound]
    test_payload: Type[ValidatePayload]

    def test_positive_votes(
        self,
    ) -> None:
        """Test ValidateRound."""

        self.synchronized_data.update(tx_hashes_history="t" * 66)

        test_round = self.test_class(
            synchronized_data=self.synchronized_data,
            context=MagicMock(),
        )

        self._complete_run(
            self._test_voting_round_positive(
                test_round=test_round,
                round_payloads=get_participant_to_votes(self.participants),
                synchronized_data_update_fn=lambda _synchronized_data, _: _synchronized_data.update(
                    participant_to_votes=get_participant_to_votes_serialized(
                        self.participants
                    )
                ),
                synchronized_data_attr_checks=[
                    lambda _synchronized_data: _synchronized_data.participant_to_votes.keys()
                ],
                exit_event=self._event_class.DONE,
            )
        )

    def test_negative_votes(
        self,
    ) -> None:
        """Test ValidateRound."""

        test_round = self.test_class(
            synchronized_data=self.synchronized_data,
            context=MagicMock(),
        )

        self._complete_run(
            self._test_voting_round_negative(
                test_round=test_round,
                round_payloads=get_participant_to_votes(self.participants, vote=False),
                synchronized_data_update_fn=lambda _synchronized_data, _: _synchronized_data.update(
                    participant_to_votes=get_participant_to_votes_serialized(
                        self.participants, vote=False
                    )
                ),
                synchronized_data_attr_checks=[],
                exit_event=self._event_class.NEGATIVE,
            )
        )

    def test_none_votes(
        self,
    ) -> None:
        """Test ValidateRound."""

        test_round = self.test_class(
            synchronized_data=self.synchronized_data,
            context=MagicMock(),
        )

        self._complete_run(
            self._test_voting_round_none(
                test_round=test_round,
                round_payloads=get_participant_to_votes(self.participants, vote=None),
                synchronized_data_update_fn=lambda _synchronized_data, _: _synchronized_data.update(
                    participant_to_votes=get_participant_to_votes_serialized(
                        self.participants, vote=None
                    )
                ),
                synchronized_data_attr_checks=[],
                exit_event=self._event_class.NONE,
            )
        )


class BaseSelectKeeperRoundTest(BaseCollectSameUntilThresholdRoundTest):
    """Test SelectKeeperTransactionSubmissionARound"""

    test_class: Type[CollectSameUntilThresholdRound]
    test_payload: Type[BaseTxPayload]

    _synchronized_data_class = SynchronizedData

    @staticmethod
    def _participant_to_selection(
        participants: FrozenSet[str], keepers: str
    ) -> Mapping[str, BaseTxPayload]:
        """Get participant to selection"""
        return get_participant_to_selection(participants, keepers)

    def test_run(
        self,
        most_voted_payload: str = "keeper",
        keepers: str = "",
        exit_event: Optional[Any] = None,
    ) -> None:
        """Run tests."""
        test_round = self.test_class(
            synchronized_data=self.synchronized_data.update(
                keepers=keepers,
            ),
            context=MagicMock(),
        )

        self._complete_run(
            self._test_round(
                test_round=test_round,
                round_payloads=self._participant_to_selection(
                    self.participants, most_voted_payload
                ),
                synchronized_data_update_fn=lambda _synchronized_data, _test_round: _synchronized_data.update(
                    participant_to_selection=CollectionRound.serialize_collection(
                        self._participant_to_selection(
                            self.participants, most_voted_payload
                        )
                    )
                ),
                synchronized_data_attr_checks=[
                    lambda _synchronized_data: _synchronized_data.participant_to_selection.keys()
                    if exit_event is None
                    else None
                ],
                most_voted_payload=most_voted_payload,
                exit_event=self._event_class.DONE if exit_event is None else exit_event,
            )
        )


class TestSelectKeeperTransactionSubmissionARound(BaseSelectKeeperRoundTest):
    """Test SelectKeeperTransactionSubmissionARound"""

    test_class = SelectKeeperTransactionSubmissionARound
    test_payload = SelectKeeperPayload
    _synchronized_data_class = TransactionSettlementSynchronizedSata
    _event_class = TransactionSettlementEvent

    @pytest.mark.parametrize(
        "most_voted_payload, keepers, exit_event",
        (
            (
                "incorrectly_serialized",
                "",
                TransactionSettlementEvent.INCORRECT_SERIALIZATION,
            ),
            (
                int(1).to_bytes(32, "big").hex() + "new_keeper" + "-" * 32,
                "",
                TransactionSettlementEvent.DONE,
            ),
        ),
    )
    def test_run(
        self,
        most_voted_payload: str,
        keepers: str,
        exit_event: TransactionSettlementEvent,
    ) -> None:
        """Run tests."""
        super().test_run(most_voted_payload, keepers, exit_event)


class TestSelectKeeperTransactionSubmissionBRound(
    TestSelectKeeperTransactionSubmissionARound
):
    """Test SelectKeeperTransactionSubmissionBRound."""

    test_class = SelectKeeperTransactionSubmissionBRound

    @pytest.mark.parametrize(
        "most_voted_payload, keepers, exit_event",
        (
            (
                int(1).to_bytes(32, "big").hex() + "new_keeper" + "-" * 32,
                "",
                TransactionSettlementEvent.DONE,
            ),
            (
                int(1).to_bytes(32, "big").hex() + "new_keeper" + "-" * 32,
                int(1).to_bytes(32, "big").hex()
                + "".join(
                    [keeper + "-" * 30 for keeper in ("test_keeper1", "test_keeper2")]
                ),
                TransactionSettlementEvent.DONE,
            ),
        ),
    )
    def test_run(
        self,
        most_voted_payload: str,
        keepers: str,
        exit_event: TransactionSettlementEvent,
    ) -> None:
        """Run tests."""
        super().test_run(most_voted_payload, keepers, exit_event)


class TestSelectKeeperTransactionSubmissionBAfterTimeoutRound(
    TestSelectKeeperTransactionSubmissionBRound
):
    """Test SelectKeeperTransactionSubmissionBAfterTimeoutRound."""

    test_class = SelectKeeperTransactionSubmissionBAfterTimeoutRound

    @mock.patch.object(
        TransactionSettlementSynchronizedSata,
        "keepers_threshold_exceeded",
        new_callable=mock.PropertyMock,
    )
    @pytest.mark.parametrize(
        "keepers", (f"{int(1).to_bytes(32, 'big').hex()}keeper" + "-" * 36,)
    )
    @pytest.mark.parametrize(
        "attrs, threshold_exceeded, exit_event",
        (
            (
                {
                    "tx_hashes_history": "t" * 66,
                    "missed_messages": {f"keeper{'-' * 36}": 10},
                },
                True,
                # Since the threshold has been exceeded, we should return a `CHECK_HISTORY` event.
                TransactionSettlementEvent.CHECK_HISTORY,
            ),
            (
                {
                    "missed_messages": {f"keeper{'-' * 36}": 10},
                },
                True,
                TransactionSettlementEvent.CHECK_LATE_ARRIVING_MESSAGE,
            ),
            (
                {
                    "missed_messages": {f"keeper{'-' * 36}": 10},
                },
                False,
                TransactionSettlementEvent.DONE,
            ),
        ),
    )
    def test_run(
        self,
        threshold_exceeded_mock: mock.PropertyMock,
        keepers: str,
        attrs: Dict[str, Union[str, int]],
        threshold_exceeded: bool,
        exit_event: TransactionSettlementEvent,
    ) -> None:
        """Test `SelectKeeperTransactionSubmissionBAfterTimeoutRound`."""
        self.synchronized_data.update(participant_to_selection=dict.fromkeys(self.participants), **attrs)  # type: ignore
        threshold_exceeded_mock.return_value = threshold_exceeded
        most_voted_payload = int(1).to_bytes(32, "big").hex() + "new_keeper" + "-" * 32
        super().test_run(most_voted_payload, keepers, exit_event)
        initial_missed_messages = cast(Dict[str, int], (attrs["missed_messages"]))
        expected_missed_messages = {
            sender: missed + 1 for sender, missed in initial_missed_messages.items()
        }
        synchronized_data = cast(
            TransactionSettlementSynchronizedSata, self.synchronized_data
        )
        assert synchronized_data.missed_messages == expected_missed_messages


class TestFinalizationRound(BaseOnlyKeeperSendsRoundTest):
    """Test FinalizationRound."""

    _synchronized_data_class = TransactionSettlementSynchronizedSata
    _event_class = TransactionSettlementEvent
    _round_class = FinalizationRound

    @pytest.mark.parametrize(
        "tx_hashes_history, tx_digest, missed_messages, status, exit_event",
        (
            (
                "",
                "",
                {"test": 1},
                VerificationStatus.ERROR.value,
                TransactionSettlementEvent.CHECK_LATE_ARRIVING_MESSAGE,
            ),
            (
                "",
                "",
                {},
                VerificationStatus.ERROR.value,
                TransactionSettlementEvent.FINALIZATION_FAILED,
            ),
            (
                "t" * 66,
                "",
                {},
                VerificationStatus.VERIFIED.value,
                TransactionSettlementEvent.CHECK_HISTORY,
            ),
            (
                "t" * 66,
                "",
                {},
                VerificationStatus.ERROR.value,
                TransactionSettlementEvent.CHECK_HISTORY,
            ),
            (
                "",
                "",
                {},
                VerificationStatus.PENDING.value,
                TransactionSettlementEvent.FINALIZATION_FAILED,
            ),
            (
                "",
                "tx_digest" + "t" * 57,
                {},
                VerificationStatus.PENDING.value,
                TransactionSettlementEvent.DONE,
            ),
            (
                "t" * 66,
                "tx_digest" + "t" * 57,
                {},
                VerificationStatus.PENDING.value,
                TransactionSettlementEvent.DONE,
            ),
            (
                "t" * 66,
                "",
                {},
                VerificationStatus.INSUFFICIENT_FUNDS.value,
                TransactionSettlementEvent.INSUFFICIENT_FUNDS,
            ),
        ),
    )
    def test_finalization_round(
        self,
        tx_hashes_history: str,
        tx_digest: str,
        missed_messages: int,
        status: int,
        exit_event: TransactionSettlementEvent,
    ) -> None:
        """Runs tests."""
        keeper_retries = 2
        blacklisted_keepers = ""
        self.participants = frozenset([f"agent_{i}" + "-" * 35 for i in range(4)])
        keepers = deque(("agent_1" + "-" * 35, "agent_3" + "-" * 35))
        self.synchronized_data = cast(
            TransactionSettlementSynchronizedSata,
            self.synchronized_data.update(
                participants=tuple(self.participants),
                missed_messages=missed_messages,
                tx_hashes_history=tx_hashes_history,
                keepers=get_keepers(keepers, keeper_retries),
                blacklisted_keepers=blacklisted_keepers,
            ),
        )

        sender = keepers[0]
        tx_hashes_history += (
            tx_digest
            if exit_event == TransactionSettlementEvent.DONE
            else tx_hashes_history
        )
        if status == VerificationStatus.INSUFFICIENT_FUNDS.value:
            popped = keepers.popleft()
            blacklisted_keepers += popped
            keeper_retries = 1

        test_round = self._round_class(
            synchronized_data=self.synchronized_data,
            context=MagicMock(),
        )

        self._complete_run(
            self._test_round(
                test_round=test_round,
                keeper_payloads=FinalizationTxPayload(
                    sender=sender,
                    tx_data={
                        "status_value": status,
                        "serialized_keepers": get_keepers(keepers, keeper_retries),
                        "blacklisted_keepers": blacklisted_keepers,
                        "tx_hashes_history": tx_hashes_history,
                        "received_hash": bool(tx_digest),
                    },
                ),
                synchronized_data_update_fn=lambda _synchronized_data, _: _synchronized_data.update(
                    tx_hashes_history=tx_hashes_history,
                    blacklisted_keepers=blacklisted_keepers,
                    keepers=get_keepers(keepers, keeper_retries),
                    keeper_retries=keeper_retries,
                    final_verification_status=VerificationStatus(status).value,
                ),
                synchronized_data_attr_checks=[
                    lambda _synchronized_data: _synchronized_data.tx_hashes_history,
                    lambda _synchronized_data: _synchronized_data.blacklisted_keepers,
                    lambda _synchronized_data: _synchronized_data.keepers,
                    lambda _synchronized_data: _synchronized_data.keeper_retries,
                    lambda _synchronized_data: _synchronized_data.final_verification_status,
                ],
                exit_event=exit_event,
            )
        )

    def test_finalization_round_no_tx_data(self) -> None:
        """Test finalization round when `tx_data` is `None`."""
        keepers = deque(("agent_1" + "-" * 35, "agent_3" + "-" * 35))
        keeper_retries = 2
        self.synchronized_data = cast(
            TransactionSettlementSynchronizedSata,
            self.synchronized_data.update(
                participants=tuple(f"agent_{i}" + "-" * 35 for i in range(4)),
                keepers=get_keepers(keepers, keeper_retries),
            ),
        )

        sender = keepers[0]

        test_round = self._round_class(
            synchronized_data=self.synchronized_data,
            context=MagicMock(),
        )

        self._complete_run(
            self._test_round(
                test_round=test_round,
                keeper_payloads=FinalizationTxPayload(
                    sender=sender,
                    tx_data=None,
                ),
                synchronized_data_update_fn=lambda _synchronized_data, _: _synchronized_data,
                synchronized_data_attr_checks=[
                    lambda _synchronized_data: _synchronized_data.tx_hashes_history,
                    lambda _synchronized_data: _synchronized_data.blacklisted_keepers,
                    lambda _synchronized_data: _synchronized_data.keepers,
                    lambda _synchronized_data: _synchronized_data.keeper_retries,
                    lambda _synchronized_data: _synchronized_data.final_verification_status,
                ],
                exit_event=TransactionSettlementEvent.FINALIZATION_FAILED,
            )
        )


class TestCollectSignatureRound(BaseCollectDifferentUntilThresholdRoundTest):
    """Test CollectSignatureRound."""

    _synchronized_data_class = TransactionSettlementSynchronizedSata
    _event_class = TransactionSettlementEvent

    def test_run(
        self,
    ) -> None:
        """Runs tests."""

        test_round = CollectSignatureRound(
            synchronized_data=self.synchronized_data,
            context=MagicMock(),
        )

        self._complete_run(
            self._test_round(
                test_round=test_round,
                round_payloads=get_participant_to_signature(self.participants),
                synchronized_data_update_fn=lambda _synchronized_data, _: _synchronized_data,
                synchronized_data_attr_checks=[],
                exit_event=self._event_class.DONE,
            )
        )


class TestValidateTransactionRound(BaseValidateRoundTest):
    """Test ValidateRound."""

    test_class = ValidateTransactionRound
    _event_class = TransactionSettlementEvent
    _synchronized_data_class = TransactionSettlementSynchronizedSata


class TestCheckTransactionHistoryRound(BaseCollectSameUntilThresholdRoundTest):
    """Test CheckTransactionHistoryRound"""

    _event_class = TransactionSettlementEvent
    _synchronized_data_class = TransactionSettlementSynchronizedSata

    @pytest.mark.parametrize(
        "expected_status, expected_tx_hash, missed_messages, expected_event",
        (
            (
                "0000000000000000000000000000000000000000000000000000000000000001",
                "b0e6add595e00477cf347d09797b156719dc5233283ac76e4efce2a674fe72d9",
                {},
                TransactionSettlementEvent.DONE,
            ),
            (
                "0000000000000000000000000000000000000000000000000000000000000002",
                "b0e6add595e00477cf347d09797b156719dc5233283ac76e4efce2a674fe72d9",
                {},
                TransactionSettlementEvent.NEGATIVE,
            ),
            (
                "0000000000000000000000000000000000000000000000000000000000000003",
                "b0e6add595e00477cf347d09797b156719dc5233283ac76e4efce2a674fe72d9",
                {},
                TransactionSettlementEvent.NONE,
            ),
            (
                "0000000000000000000000000000000000000000000000000000000000000007",
                "b0e6add595e00477cf347d09797b156719dc5233283ac76e4efce2a674fe72d9",
                {},
                TransactionSettlementEvent.NONE,
            ),
            (
                "0000000000000000000000000000000000000000000000000000000000000002",
                "b0e6add595e00477cf347d09797b156719dc5233283ac76e4efce2a674fe72d9",
                {"test": 1},
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
        keepers = get_keepers(deque(("agent_1" + "-" * 35, "agent_3" + "-" * 35)))
        self.synchronized_data.update(missed_messages=missed_messages, keepers=keepers)

        test_round = CheckTransactionHistoryRound(
            synchronized_data=self.synchronized_data,
            context=MagicMock(),
        )

        self._complete_run(
            self._test_round(
                test_round=test_round,
                round_payloads=get_participant_to_check(
                    self.participants, expected_status, expected_tx_hash
                ),
                synchronized_data_update_fn=lambda synchronized_data, _: synchronized_data.update(
                    participant_to_check=CollectionRound.serialize_collection(
                        get_participant_to_check(
                            self.participants, expected_status, expected_tx_hash
                        )
                    ),
                    final_verification_status=int(expected_status),
                    tx_hashes_history=[expected_tx_hash],
                    keepers=keepers,
                    final_tx_hash="0xb0e6add595e00477cf347d09797b156719dc5233283ac76e4efce2a674fe72d9",
                ),
                synchronized_data_attr_checks=[
                    lambda _synchronized_data: _synchronized_data.final_verification_status,
                    lambda _synchronized_data: _synchronized_data.final_tx_hash,
                    lambda _synchronized_data: _synchronized_data.keepers,
                ]
                if expected_event
                not in {
                    TransactionSettlementEvent.NEGATIVE,
                    TransactionSettlementEvent.CHECK_LATE_ARRIVING_MESSAGE,
                }
                else [
                    lambda _synchronized_data: _synchronized_data.final_verification_status,
                    lambda _synchronized_data: _synchronized_data.keepers,
                ],
                most_voted_payload=expected_status + expected_tx_hash,
                exit_event=expected_event,
            )
        )


class TestSynchronizeLateMessagesRound(BaseCollectNonEmptyUntilThresholdRound):
    """Test `SynchronizeLateMessagesRound`."""

    _event_class = TransactionSettlementEvent
    _synchronized_data_class = TransactionSettlementSynchronizedSata

    @pytest.mark.parametrize(
        "missed_messages, expected_event",
        (
            (
                {f"agent_{i}": 0 for i in range(4)},
                TransactionSettlementEvent.SUSPICIOUS_ACTIVITY,
            ),
            ({f"agent_{i}": 2 for i in range(4)}, TransactionSettlementEvent.DONE),
        ),
    )
    def test_runs(
        self, missed_messages: int, expected_event: TransactionSettlementEvent
    ) -> None:
        """Runs tests."""
        self.synchronized_data.update(missed_messages=missed_messages)
        test_round = SynchronizeLateMessagesRound(
            synchronized_data=self.synchronized_data,
            context=MagicMock(),
        )
        late_arriving_tx_hashes = {
            p: "".join(("1" * TX_HASH_LENGTH, "2" * TX_HASH_LENGTH))
            for p in self.participants
        }
        test_round.required_block_confirmations = 0
        self._complete_run(
            self._test_round(
                test_round=test_round,
                round_payloads=get_participant_to_late_arriving_tx_hashes(
                    self.participants
                ),
                synchronized_data_update_fn=lambda _synchronized_data, _: _synchronized_data.update(
                    late_arriving_tx_hashes=late_arriving_tx_hashes,
                    suspects=tuple()
                    if expected_event == TransactionSettlementEvent.DONE
                    else tuple(sorted(late_arriving_tx_hashes.keys())),
                ),
                synchronized_data_attr_checks=[
                    lambda _synchronized_data: _synchronized_data.late_arriving_tx_hashes,
                    lambda _synchronized_data: _synchronized_data.suspects,
                ],
                exit_event=expected_event,
            )
        )

    @pytest.mark.parametrize("correct_serialization", (True, False))
    def test_check_payload(self, correct_serialization: bool) -> None:
        """Test the `check_payload` method."""

        test_round = SynchronizeLateMessagesRound(
            synchronized_data=self.synchronized_data,
            context=MagicMock(),
        )
        sender = list(test_round.accepting_payloads_from).pop()
        hash_length = TX_HASH_LENGTH
        if not correct_serialization:
            hash_length -= 1
        tx_hashes = "0" * hash_length
        payload = SynchronizeLateMessagesPayload(sender=sender, tx_hashes=tx_hashes)

        if correct_serialization:
            test_round.check_payload(payload)
            return

        with pytest.raises(
            TransactionNotValidError, match="Expecting serialized data of chunk size"
        ):
            test_round.check_payload(payload)

        with pytest.raises(
            ABCIAppInternalError, match="Expecting serialized data of chunk size"
        ):
            test_round.process_payload(payload)
        assert payload not in test_round.collection


def test_synchronized_datas() -> None:
    """Test SynchronizedData."""

    participants = get_participants()
    participant_to_randomness = get_participant_to_randomness(participants, 1)
    participant_to_randomness_serialized = CollectionRound.serialize_collection(
        participant_to_randomness
    )
    most_voted_randomness = get_most_voted_randomness()
    participant_to_selection = get_participant_to_selection(participants, "test")
    participant_to_selection_serialized = CollectionRound.serialize_collection(
        participant_to_selection
    )
    safe_contract_address = get_safe_contract_address()
    most_voted_tx_hash = get_most_voted_tx_hash()
    participant_to_signature = get_participant_to_signature(participants)
    participant_to_signature_serialized = CollectionRound.serialize_collection(
        participant_to_signature
    )
    final_tx_hash = get_final_tx_hash()
    actual_keeper_randomness = int(most_voted_randomness, base=16) / MAX_INT_256
    late_arriving_tx_hashes_serialized = get_late_arriving_tx_hashes_serialized()
    late_arriving_tx_hashes_deserialized = get_late_arriving_tx_hashes_deserialized()
    keepers = get_keepers(deque(("agent_1" + "-" * 35, "agent_3" + "-" * 35)))
    expected_keepers = deque(["agent_1" + "-" * 35, "agent_3" + "-" * 35])

    # test `keeper_retries` property when no `keepers` are set.
    synchronized_data_____ = TransactionSettlementSynchronizedSata(
        AbciAppDB(setup_data=dict())
    )
    assert synchronized_data_____.keepers == deque()
    assert synchronized_data_____.keeper_retries == 0

    synchronized_data_____ = TransactionSettlementSynchronizedSata(
        AbciAppDB(
            setup_data=AbciAppDB.data_to_lists(
                dict(
                    all_participants=tuple(participants),
                    participants=tuple(participants),
                    consensus_threshold=3,
                    participant_to_randomness=participant_to_randomness_serialized,
                    most_voted_randomness=most_voted_randomness,
                    participant_to_selection=participant_to_selection_serialized,
                    safe_contract_address=safe_contract_address,
                    most_voted_tx_hash=most_voted_tx_hash,
                    participant_to_signature=participant_to_signature_serialized,
                    final_tx_hash=final_tx_hash,
                    late_arriving_tx_hashes=late_arriving_tx_hashes_serialized,
                    keepers=keepers,
                    blacklisted_keepers="t" * 42,
                )
            ),
        )
    )
    assert (
        abs(synchronized_data_____.keeper_randomness - actual_keeper_randomness) < 1e-10
    )  # avoid equality comparisons between floats
    assert synchronized_data_____.most_voted_randomness == most_voted_randomness
    assert synchronized_data_____.safe_contract_address == safe_contract_address
    assert synchronized_data_____.most_voted_tx_hash == most_voted_tx_hash
    assert synchronized_data_____.participant_to_randomness == participant_to_randomness
    assert synchronized_data_____.participant_to_selection == participant_to_selection
    assert synchronized_data_____.participant_to_signature == participant_to_signature
    assert synchronized_data_____.final_tx_hash == final_tx_hash
    assert (
        synchronized_data_____.late_arriving_tx_hashes
        == late_arriving_tx_hashes_deserialized
    )
    assert synchronized_data_____.keepers == expected_keepers
    assert synchronized_data_____.keeper_retries == 1
    assert (
        synchronized_data_____.most_voted_keeper_address == expected_keepers.popleft()
    )
    assert synchronized_data_____.keepers_threshold_exceeded
    assert synchronized_data_____.blacklisted_keepers == {"t" * 42}
    updated_synchronized_data = synchronized_data_____.create()
    assert updated_synchronized_data.blacklisted_keepers == set()


class TestResetRound(BaseCollectSameUntilThresholdRoundTest):
    """Test ResetRound."""

    _synchronized_data_class = TransactionSettlementSynchronizedSata
    _event_class = TransactionSettlementEvent

    def test_runs(
        self,
    ) -> None:
        """Runs tests."""
        randomness = DUMMY_RANDOMNESS
        synchronized_data = self.synchronized_data.update(
            most_voted_randomness=randomness,
            late_arriving_tx_hashes={},
            keepers="",
        )
        synchronized_data._db._cross_period_persisted_keys = frozenset(
            {"most_voted_randomness"}
        )
        test_round = ResetRound(
            synchronized_data=synchronized_data,
            context=MagicMock(),
        )
        next_period_count = 1
        self._complete_run(
            self._test_round(
                test_round=test_round,
                round_payloads=get_participant_to_period_count(
                    self.participants, next_period_count
                ),
                synchronized_data_update_fn=lambda _synchronized_data, _: _synchronized_data.create(),
                synchronized_data_attr_checks=[],  # [lambda _synchronized_data: _synchronized_data.participants],
                most_voted_payload=next_period_count,
                exit_event=self._event_class.DONE,
            )
        )
