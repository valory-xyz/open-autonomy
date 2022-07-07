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

"""This module contains the data classes for the `transaction settlement` ABCI application."""
import textwrap
from abc import ABC
from collections import deque
from enum import Enum
from typing import Deque, Dict, List, Mapping, Optional, Set, Tuple, Type, cast

from packages.valory.skills.abstract_round_abci.base import (
    AbciApp,
    AbciAppDB,
    AbciAppTransitionFunction,
    AbstractRound,
    AppState,
    BaseSynchronizedData,
    CollectDifferentUntilThresholdRound,
    CollectNonEmptyUntilThresholdRound,
    CollectSameUntilThresholdRound,
    DegenerateRound,
    OnlyKeeperSendsRound,
    VotingRound,
)
from packages.valory.skills.transaction_settlement_abci.payload_tools import (
    VerificationStatus,
    tx_hist_hex_to_payload,
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


ADDRESS_LENGTH = 42
TX_HASH_LENGTH = 66
RETRIES_LENGTH = 64


class Event(Enum):
    """Event enumeration for the price estimation demo."""

    DONE = "done"
    ROUND_TIMEOUT = "round_timeout"
    NO_MAJORITY = "no_majority"
    NEGATIVE = "negative"
    NONE = "none"
    FINALIZE_TIMEOUT = "finalize_timeout"
    VALIDATE_TIMEOUT = "validate_timeout"
    CHECK_TIMEOUT = "check_timeout"
    RESET_TIMEOUT = "reset_timeout"
    CHECK_HISTORY = "check_history"
    CHECK_LATE_ARRIVING_MESSAGE = "check_late_arriving_message"
    FINALIZATION_FAILED = "finalization_failed"
    MISSED_AND_LATE_MESSAGES_MISMATCH = "missed_and_late_messages_mismatch"
    INSUFFICIENT_FUNDS = "insufficient_funds"
    INCORRECT_SERIALIZATION = "incorrect_serialization"


class SynchronizedData(
    BaseSynchronizedData
):  # pylint: disable=too-many-instance-attributes
    """
    Class to represent the synchronized data.

    This data is replicated by the tendermint application.
    """

    @property
    def safe_contract_address(self) -> str:
        """Get the safe contract address."""
        return cast(str, self.db.get_strict("safe_contract_address"))

    @property
    def participant_to_signature(self) -> Mapping[str, SignaturePayload]:
        """Get the participant_to_signature."""
        return cast(
            Mapping[str, SignaturePayload],
            self.db.get_strict("participant_to_signature"),
        )

    @property
    def tx_hashes_history(self) -> List[str]:
        """Get the current cycle's tx hashes history, which has not yet been verified."""
        raw = cast(str, self.db.get("tx_hashes_history", ""))
        return textwrap.wrap(raw, TX_HASH_LENGTH)

    @property
    def keepers(self) -> Deque[str]:
        """Get the current cycle's keepers who have tried to submit a transaction."""
        if self.is_keeper_set:
            keepers_unparsed = cast(str, self.db.get_strict("keepers"))
            keepers_parsed = textwrap.wrap(
                keepers_unparsed[RETRIES_LENGTH:], ADDRESS_LENGTH
            )
            return deque(keepers_parsed)
        return deque()

    @property
    def keepers_threshold_exceeded(self) -> bool:
        """Check if the number of selected keepers has exceeded the allowed limit."""
        malicious_threshold = self.nb_participants // 3
        return len(self.keepers) > malicious_threshold

    @property
    def most_voted_keeper_address(self) -> str:
        """Get the first in priority keeper to try to re-submit a transaction."""
        return self.keepers[0]

    @property
    def is_keeper_set(self) -> bool:
        """Check whether keeper is set."""
        return bool(self.db.get("keepers", False))

    @property
    def keeper_retries(self) -> int:
        """Get the number of times the current keeper has retried."""
        if self.is_keeper_set:
            keepers_unparsed = cast(str, self.db.get_strict("keepers"))
            keeper_retries = int.from_bytes(
                bytes.fromhex(keepers_unparsed[:RETRIES_LENGTH]), "big"
            )
            return keeper_retries
        return 0

    @property
    def to_be_validated_tx_hash(self) -> str:
        """
        Get the tx hash which is ready for validation.

        This will always be the last hash in the `tx_hashes_history`,
        due to the way we are inserting the hashes in the array.
        We keep the hashes sorted by the time of their finalization.
        If this property is accessed before the finalization succeeds,
        then it is incorrectly used and raises an error.

        :return: the tx hash which is ready for validation.
        """
        if not self.tx_hashes_history:
            raise ValueError("FSM design error: tx hash should exist")
        return self.tx_hashes_history[-1]

    @property
    def final_tx_hash(self) -> str:
        """Get the verified tx hash."""
        return cast(str, self.db.get_strict("final_tx_hash"))

    @property
    def final_verification_status(self) -> VerificationStatus:
        """Get the final verification status."""
        return cast(
            VerificationStatus,
            self.db.get("final_verification_status", VerificationStatus.NOT_VERIFIED),
        )

    @property
    def most_voted_tx_hash(self) -> str:
        """Get the most_voted_tx_hash."""
        return cast(str, self.db.get_strict("most_voted_tx_hash"))

    @property
    def missed_messages(self) -> int:
        """Check the number of missed messages."""
        return cast(int, self.db.get("missed_messages", 0))

    @property
    def should_check_late_messages(self) -> bool:
        """Check if we should check for late-arriving messages."""
        return self.missed_messages > 0

    @property
    def late_arriving_tx_hashes(self) -> List[str]:
        """Get the late_arriving_tx_hashes."""
        late_arrivals = cast(List[str], self.db.get_strict("late_arriving_tx_hashes"))
        parsed_hashes = map(lambda h: textwrap.wrap(h, TX_HASH_LENGTH), late_arrivals)
        return [h for hashes in parsed_hashes for h in hashes]


class FailedRound(DegenerateRound, ABC):
    """A round that represents that the period failed"""

    round_id = "failed"


class CollectSignatureRound(CollectDifferentUntilThresholdRound):
    """A round in which agents sign the transaction"""

    round_id = "collect_signature"
    allowed_tx_type = SignaturePayload.transaction_type
    payload_attribute = "signature"
    synchronized_data_class = SynchronizedData
    done_event = Event.DONE
    no_majority_event = Event.NO_MAJORITY
    selection_key = "participant"
    collection_key = "participant_to_signature"


class FinalizationRound(OnlyKeeperSendsRound):
    """A round that represents transaction signing has finished"""

    round_id = "finalization"
    allowed_tx_type = FinalizationTxPayload.transaction_type
    payload_attribute = "tx_data"

    def end_block(
        self,
    ) -> Optional[
        Tuple[BaseSynchronizedData, Enum]
    ]:  # pylint: disable=too-many-return-statements
        """Process the end of the block."""
        if not self.has_keeper_sent_payload:
            return None

        if self.keeper_payload is None:  # pragma: no cover
            return self.synchronized_data, Event.FINALIZATION_FAILED

        verification_status = VerificationStatus(self.keeper_payload["status_value"])
        synchronized_data = cast(
            SynchronizedData,
            self.synchronized_data.update(
                synchronized_data_class=SynchronizedData,
                tx_hashes_history=self.keeper_payload["tx_hashes_history"],
                final_verification_status=verification_status,
                keepers=self.keeper_payload["serialized_keepers"],
                blacklisted_keepers=self.keeper_payload["blacklisted_keepers"],
            ),
        )

        # check if we succeeded in finalization.
        # we may fail in any of the following cases:
        # 1. Getting raw safe transaction.
        # 2. Requesting transaction signature.
        # 3. Requesting transaction digest.
        if self.keeper_payload["received_hash"]:
            return synchronized_data, Event.DONE
        # If keeper has been blacklisted, return an `INSUFFICIENT_FUNDS` event.
        if verification_status == VerificationStatus.INSUFFICIENT_FUNDS:
            return synchronized_data, Event.INSUFFICIENT_FUNDS
        # This means that getting raw safe transaction succeeded,
        # but either requesting tx signature or requesting tx digest failed.
        if verification_status not in (
            VerificationStatus.ERROR,
            VerificationStatus.VERIFIED,
        ):
            return synchronized_data, Event.FINALIZATION_FAILED
        # if there is a tx hash history, then check it for validated txs.
        if synchronized_data.tx_hashes_history:
            return synchronized_data, Event.CHECK_HISTORY
        # if there could be any late messages, check if any has arrived.
        if synchronized_data.should_check_late_messages:
            return synchronized_data, Event.CHECK_LATE_ARRIVING_MESSAGE
        # otherwise fail.
        return synchronized_data, Event.FINALIZATION_FAILED


class RandomnessTransactionSubmissionRound(CollectSameUntilThresholdRound):
    """A round for generating randomness"""

    round_id = "randomness_transaction_submission"
    allowed_tx_type = RandomnessPayload.transaction_type
    payload_attribute = "randomness"
    synchronized_data_class = SynchronizedData
    done_event = Event.DONE
    no_majority_event = Event.NO_MAJORITY
    collection_key = "participant_to_randomness"
    selection_key = "most_voted_randomness"


class SelectKeeperTransactionSubmissionRoundA(CollectSameUntilThresholdRound):
    """A round in which a keeper is selected for transaction submission"""

    round_id = "select_keeper_transaction_submission_a"
    allowed_tx_type = SelectKeeperPayload.transaction_type
    payload_attribute = "keepers"
    synchronized_data_class = SynchronizedData
    done_event = Event.DONE
    no_majority_event = Event.NO_MAJORITY
    collection_key = "participant_to_selection"
    selection_key = "keepers"

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Enum]]:
        """Process the end of the block."""

        if self.threshold_reached and self.most_voted_payload is not None:
            if (
                len(self.most_voted_payload) < RETRIES_LENGTH + ADDRESS_LENGTH
                or (len(self.most_voted_payload) - RETRIES_LENGTH) % ADDRESS_LENGTH != 0
            ):
                # if we cannot parse the keepers' payload, then the developer has serialized it incorrectly.
                return self.synchronized_data, Event.INCORRECT_SERIALIZATION

        return super().end_block()


class SelectKeeperTransactionSubmissionRoundB(SelectKeeperTransactionSubmissionRoundA):
    """A round in which a new keeper is selected for transaction submission"""

    round_id = "select_keeper_transaction_submission_b"


class SelectKeeperTransactionSubmissionRoundBAfterTimeout(
    SelectKeeperTransactionSubmissionRoundB
):
    """A round in which a new keeper is selected for tx submission after a round timeout of the previous keeper"""

    round_id = "select_keeper_transaction_submission_b_after_timeout"

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Enum]]:
        """Process the end of the block."""
        if self.threshold_reached:
            synchronized_data = cast(
                SynchronizedData,
                self.synchronized_data.update(
                    missed_messages=cast(
                        SynchronizedData, self.synchronized_data
                    ).missed_messages
                    + 1
                ),
            )
            if synchronized_data.keepers_threshold_exceeded:
                # we only stop re-selection if there are any previous transaction hashes or any missed messages.
                if len(synchronized_data.tx_hashes_history) > 0:
                    return synchronized_data, Event.CHECK_HISTORY
                if synchronized_data.should_check_late_messages:
                    return synchronized_data, Event.CHECK_LATE_ARRIVING_MESSAGE
        return super().end_block()


class ValidateTransactionRound(VotingRound):
    """A round in which agents validate the transaction"""

    round_id = "validate_transaction"
    allowed_tx_type = ValidatePayload.transaction_type
    payload_attribute = "vote"
    synchronized_data_class = SynchronizedData
    done_event = Event.DONE
    negative_event = Event.NEGATIVE
    none_event = Event.NONE
    no_majority_event = Event.NO_MAJORITY
    collection_key = "participant_to_votes"

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Enum]]:
        """Process the end of the block."""
        # if reached participant threshold, set the result

        if self.positive_vote_threshold_reached:
            # We obtain the latest tx hash from the `tx_hashes_history`.
            # We keep the hashes sorted by their finalization time.
            # If this property is accessed before the finalization succeeds,
            # then it is incorrectly used.
            final_tx_hash = cast(
                SynchronizedData, self.synchronized_data
            ).to_be_validated_tx_hash

            # We only set the final tx hash if we are about to exit from the transaction settlement skill.
            # Then, the skills which use the transaction settlement can check the tx hash
            # and if it is None, then it means that the transaction has failed.
            synchronized_data = self.synchronized_data.update(
                synchronized_data_class=self.synchronized_data_class,
                participant_to_votes=self.collection,
                final_verification_status=VerificationStatus.VERIFIED,
                final_tx_hash=final_tx_hash,
            )  # type: ignore
            return synchronized_data, self.done_event
        if self.negative_vote_threshold_reached:
            return self.synchronized_data, self.negative_event
        if self.none_vote_threshold_reached:
            return self.synchronized_data, self.none_event
        if not self.is_majority_possible(
            self.collection, self.synchronized_data.nb_participants
        ):
            return self.synchronized_data, self.no_majority_event
        return None


class CheckTransactionHistoryRound(CollectSameUntilThresholdRound):
    """A round in which agents check the transaction history to see if any previous tx has been validated"""

    round_id = "check_transaction_history"
    allowed_tx_type = CheckTransactionHistoryPayload.transaction_type
    payload_attribute = "verified_res"
    synchronized_data_class = SynchronizedData
    selection_key = "most_voted_check_result"

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Enum]]:
        """Process the end of the block."""
        if self.threshold_reached:
            return_status, return_tx_hash = tx_hist_hex_to_payload(
                self.most_voted_payload
            )

            if return_status == VerificationStatus.NOT_VERIFIED:
                # We don't update the synchronized_data as we need to repeat all checks again later
                synchronized_data = self.synchronized_data
            else:
                # We only set the final tx hash if we are about to exit from the transaction settlement skill.
                # Then, the skills which use the transaction settlement can check the tx hash
                # and if it is None, then it means that the transaction has failed.
                synchronized_data = self.synchronized_data.update(
                    synchronized_data_class=self.synchronized_data_class,
                    participant_to_check=self.collection,
                    final_verification_status=return_status,
                    final_tx_hash=return_tx_hash,
                )

            if return_status == VerificationStatus.VERIFIED:
                return synchronized_data, Event.DONE
            if (
                return_status == VerificationStatus.NOT_VERIFIED
                and cast(
                    SynchronizedData, self.synchronized_data
                ).should_check_late_messages
            ):
                return synchronized_data, Event.CHECK_LATE_ARRIVING_MESSAGE
            if return_status == VerificationStatus.NOT_VERIFIED:
                return synchronized_data, Event.NEGATIVE

            return synchronized_data, Event.NONE

        if not self.is_majority_possible(
            self.collection, self.synchronized_data.nb_participants
        ):
            return self.synchronized_data, Event.NO_MAJORITY
        return None


class CheckLateTxHashesRound(CheckTransactionHistoryRound):
    """A round in which agents check the late-arriving transaction hashes to see if any of them has been validated"""

    round_id = "check_late_tx_hashes"


class SynchronizeLateMessagesRound(CollectNonEmptyUntilThresholdRound):
    """A round in which agents synchronize potentially late arriving messages"""

    round_id = "synchronize_late_messages"
    allowed_tx_type = SynchronizeLateMessagesPayload.transaction_type
    payload_attribute = "tx_hashes"
    synchronized_data_class = SynchronizedData
    done_event = Event.DONE
    no_majority_event = Event.NO_MAJORITY
    none_event = Event.NONE
    selection_key = "participant"
    collection_key = "late_arriving_tx_hashes"
    _hash_length = TX_HASH_LENGTH

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""
        result = super().end_block()
        if result is None:
            return None

        synchronized_data, event = cast(Tuple[BaseSynchronizedData, Event], result)

        synchronized_data = cast(SynchronizedData, self.synchronized_data)
        n_late_arriving_tx_hashes = len(synchronized_data.late_arriving_tx_hashes)
        if n_late_arriving_tx_hashes > synchronized_data.missed_messages:
            return synchronized_data, Event.MISSED_AND_LATE_MESSAGES_MISMATCH

        still_missing = synchronized_data.missed_messages - n_late_arriving_tx_hashes
        synchronized_data = synchronized_data.update(missed_messages=still_missing)
        return synchronized_data, event


class FinishedTransactionSubmissionRound(DegenerateRound, ABC):
    """A round that represents the transition to the ResetAndPauseRound"""

    round_id = "pre_reset_and_pause"


class ResetRound(CollectSameUntilThresholdRound):
    """A round that represents the reset of a period"""

    round_id = "reset"
    allowed_tx_type = ResetPayload.transaction_type
    payload_attribute = "period_count"

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            latest_data = self.synchronized_data.db.get_latest()
            synchronized_data = self.synchronized_data.create(
                synchronized_data_class=self.synchronized_data_class,
                **AbciAppDB.data_to_lists(latest_data),
            )
            return synchronized_data, Event.DONE
        if not self.is_majority_possible(
            self.collection, self.synchronized_data.nb_participants
        ):
            return self.synchronized_data, Event.NO_MAJORITY
        return None


class TransactionSubmissionAbciApp(AbciApp[Event]):
    """TransactionSubmissionAbciApp

    Initial round: RandomnessTransactionSubmissionRound

    Initial states: {RandomnessTransactionSubmissionRound}

    Transition states:
        0. RandomnessTransactionSubmissionRound
            - done: 1.
            - round timeout: 0.
            - no majority: 0.
        1. SelectKeeperTransactionSubmissionRoundA
            - done: 2.
            - round timeout: 1.
            - no majority: 10.
            - incorrect serialization: 12.
        2. CollectSignatureRound
            - done: 3.
            - round timeout: 2.
            - no majority: 10.
        3. FinalizationRound
            - done: 4.
            - check history: 5.
            - finalize timeout: 7.
            - finalization failed: 6.
            - check late arriving message: 8.
            - insufficient funds: 6.
        4. ValidateTransactionRound
            - done: 11.
            - negative: 5.
            - none: 6.
            - validate timeout: 6.
            - no majority: 4.
        5. CheckTransactionHistoryRound
            - done: 11.
            - negative: 6.
            - none: 12.
            - check timeout: 5.
            - no majority: 5.
            - check late arriving message: 8.
        6. SelectKeeperTransactionSubmissionRoundB
            - done: 3.
            - round timeout: 6.
            - no majority: 10.
            - incorrect serialization: 12.
        7. SelectKeeperTransactionSubmissionRoundBAfterTimeout
            - done: 3.
            - check history: 5.
            - check late arriving message: 8.
            - round timeout: 7.
            - no majority: 10.
            - incorrect serialization: 12.
        8. SynchronizeLateMessagesRound
            - done: 9.
            - round timeout: 8.
            - no majority: 8.
            - none: 6.
            - missed and late messages mismatch: 12.
        9. CheckLateTxHashesRound
            - done: 11.
            - negative: 12.
            - none: 12.
            - check timeout: 9.
            - no majority: 12.
            - check late arriving message: 8.
        10. ResetRound
            - done: 0.
            - reset timeout: 12.
            - no majority: 12.
        11. FinishedTransactionSubmissionRound
        12. FailedRound

    Final states: {FailedRound, FinishedTransactionSubmissionRound}

    Timeouts:
        round timeout: 30.0
        finalize timeout: 30.0
        validate timeout: 30.0
        check timeout: 30.0
        reset timeout: 30.0
    """

    initial_round_cls: Type[AbstractRound] = RandomnessTransactionSubmissionRound
    transition_function: AbciAppTransitionFunction = {
        RandomnessTransactionSubmissionRound: {
            Event.DONE: SelectKeeperTransactionSubmissionRoundA,
            Event.ROUND_TIMEOUT: RandomnessTransactionSubmissionRound,
            Event.NO_MAJORITY: RandomnessTransactionSubmissionRound,
        },
        SelectKeeperTransactionSubmissionRoundA: {
            Event.DONE: CollectSignatureRound,
            Event.ROUND_TIMEOUT: SelectKeeperTransactionSubmissionRoundA,
            Event.NO_MAJORITY: ResetRound,
            Event.INCORRECT_SERIALIZATION: FailedRound,
        },
        CollectSignatureRound: {
            Event.DONE: FinalizationRound,
            Event.ROUND_TIMEOUT: CollectSignatureRound,
            Event.NO_MAJORITY: ResetRound,
        },
        FinalizationRound: {
            Event.DONE: ValidateTransactionRound,
            Event.CHECK_HISTORY: CheckTransactionHistoryRound,
            Event.FINALIZE_TIMEOUT: SelectKeeperTransactionSubmissionRoundBAfterTimeout,
            Event.FINALIZATION_FAILED: SelectKeeperTransactionSubmissionRoundB,
            Event.CHECK_LATE_ARRIVING_MESSAGE: SynchronizeLateMessagesRound,
            Event.INSUFFICIENT_FUNDS: SelectKeeperTransactionSubmissionRoundB,
        },
        ValidateTransactionRound: {
            Event.DONE: FinishedTransactionSubmissionRound,
            Event.NEGATIVE: CheckTransactionHistoryRound,
            Event.NONE: SelectKeeperTransactionSubmissionRoundB,
            Event.VALIDATE_TIMEOUT: SelectKeeperTransactionSubmissionRoundB,
            Event.NO_MAJORITY: ValidateTransactionRound,
        },
        CheckTransactionHistoryRound: {
            Event.DONE: FinishedTransactionSubmissionRound,
            Event.NEGATIVE: SelectKeeperTransactionSubmissionRoundB,
            Event.NONE: FailedRound,
            Event.CHECK_TIMEOUT: CheckTransactionHistoryRound,
            Event.NO_MAJORITY: CheckTransactionHistoryRound,
            Event.CHECK_LATE_ARRIVING_MESSAGE: SynchronizeLateMessagesRound,
        },
        SelectKeeperTransactionSubmissionRoundB: {
            Event.DONE: FinalizationRound,
            Event.ROUND_TIMEOUT: SelectKeeperTransactionSubmissionRoundB,
            Event.NO_MAJORITY: ResetRound,
            Event.INCORRECT_SERIALIZATION: FailedRound,
        },
        SelectKeeperTransactionSubmissionRoundBAfterTimeout: {
            Event.DONE: FinalizationRound,
            Event.CHECK_HISTORY: CheckTransactionHistoryRound,
            Event.CHECK_LATE_ARRIVING_MESSAGE: SynchronizeLateMessagesRound,
            Event.ROUND_TIMEOUT: SelectKeeperTransactionSubmissionRoundBAfterTimeout,
            Event.NO_MAJORITY: ResetRound,
            Event.INCORRECT_SERIALIZATION: FailedRound,
        },
        SynchronizeLateMessagesRound: {
            Event.DONE: CheckLateTxHashesRound,
            Event.ROUND_TIMEOUT: SynchronizeLateMessagesRound,
            Event.NO_MAJORITY: SynchronizeLateMessagesRound,
            Event.NONE: SelectKeeperTransactionSubmissionRoundB,
            Event.MISSED_AND_LATE_MESSAGES_MISMATCH: FailedRound,
        },
        CheckLateTxHashesRound: {
            Event.DONE: FinishedTransactionSubmissionRound,
            Event.NEGATIVE: FailedRound,
            Event.NONE: FailedRound,
            Event.CHECK_TIMEOUT: CheckLateTxHashesRound,
            Event.NO_MAJORITY: FailedRound,
            Event.CHECK_LATE_ARRIVING_MESSAGE: SynchronizeLateMessagesRound,
        },
        ResetRound: {
            Event.DONE: RandomnessTransactionSubmissionRound,
            Event.RESET_TIMEOUT: FailedRound,
            Event.NO_MAJORITY: FailedRound,
        },
        FinishedTransactionSubmissionRound: {},
        FailedRound: {},
    }
    final_states: Set[AppState] = {
        FinishedTransactionSubmissionRound,
        FailedRound,
    }
    event_to_timeout: Dict[Event, float] = {
        Event.ROUND_TIMEOUT: 30.0,
        Event.FINALIZE_TIMEOUT: 30.0,
        Event.VALIDATE_TIMEOUT: 30.0,
        Event.CHECK_TIMEOUT: 30.0,
        Event.RESET_TIMEOUT: 30.0,
    }
