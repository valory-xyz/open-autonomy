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

"""This module contains the data classes for the `transaction settlement` ABCI application."""

import textwrap
from abc import ABC
from collections import deque
from enum import Enum
from typing import Deque, Dict, List, Mapping, Optional, Set, Tuple, cast

from packages.valory.skills.abstract_round_abci.base import (
    ABCIAppInternalError,
    AbciApp,
    AbciAppTransitionFunction,
    AppState,
    BaseSynchronizedData,
    BaseTxPayload,
    CollectDifferentUntilThresholdRound,
    CollectNonEmptyUntilThresholdRound,
    CollectSameUntilThresholdRound,
    CollectionRound,
    DegenerateRound,
    OnlyKeeperSendsRound,
    TransactionNotValidError,
    VALUE_NOT_PROVIDED,
    VotingRound,
    get_name,
)
from packages.valory.skills.abstract_round_abci.utils import filter_negative
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
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
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
    def participant_to_signature(self) -> Mapping[str, SignaturePayload]:
        """Get the participant_to_signature."""
        serialized = self.db.get_strict("participant_to_signature")
        deserialized = CollectionRound.deserialize_collection(serialized)
        return cast(Mapping[str, SignaturePayload], deserialized)

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
    def most_voted_randomness_round(self) -> int:  # pragma: no cover
        """Get the first in priority keeper to try to re-submit a transaction."""
        round_ = self.db.get_strict("most_voted_randomness_round")
        return cast(int, round_)

    @property
    def most_voted_keeper_address(self) -> str:
        """Get the first in priority keeper to try to re-submit a transaction."""
        return self.keepers[0]

    @property  # TODO: overrides base property, investigate
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
            raise ValueError(
                "FSM design error: tx hash should exist"
            )  # pragma: no cover
        return self.tx_hashes_history[-1]

    @property
    def final_tx_hash(self) -> str:
        """Get the verified tx hash."""
        return cast(str, self.db.get_strict("final_tx_hash"))

    @property
    def final_verification_status(self) -> VerificationStatus:
        """Get the final verification status."""
        status_value = self.db.get("final_verification_status", None)
        if status_value is None:
            return VerificationStatus.NOT_VERIFIED
        return VerificationStatus(status_value)

    @property
    def most_voted_tx_hash(self) -> str:
        """Get the most_voted_tx_hash."""
        return cast(str, self.db.get_strict("most_voted_tx_hash"))

    @property
    def missed_messages(self) -> Dict[str, int]:
        """The number of missed messages per agent address."""
        default = dict.fromkeys(self.all_participants, 0)
        missed_messages = self.db.get("missed_messages", default)
        return cast(Dict[str, int], missed_messages)

    @property
    def n_missed_messages(self) -> int:
        """The number of missed messages in total."""
        return sum(self.missed_messages.values())

    @property
    def should_check_late_messages(self) -> bool:
        """Check if we should check for late-arriving messages."""
        return self.n_missed_messages > 0

    @property
    def late_arriving_tx_hashes(self) -> Dict[str, List[str]]:
        """Get the late_arriving_tx_hashes."""
        late_arrivals = cast(
            Dict[str, str], self.db.get_strict("late_arriving_tx_hashes")
        )
        parsed_hashes = {
            sender: textwrap.wrap(hashes, TX_HASH_LENGTH)
            for sender, hashes in late_arrivals.items()
        }
        return parsed_hashes

    @property
    def suspects(self) -> Tuple[str]:
        """Get the suspect agents."""
        return cast(Tuple[str], self.db.get("suspects", tuple()))

    @property
    def most_voted_check_result(self) -> str:  # pragma: no cover
        """Get the most voted checked result."""
        return cast(str, self.db.get_strict("most_voted_check_result"))

    @property
    def participant_to_check(
        self,
    ) -> Mapping[str, CheckTransactionHistoryPayload]:  # pragma: no cover
        """Get the mapping from participants to checks."""
        serialized = self.db.get_strict("participant_to_check")
        deserialized = CollectionRound.deserialize_collection(serialized)
        return cast(Mapping[str, CheckTransactionHistoryPayload], deserialized)

    @property
    def participant_to_late_messages(
        self,
    ) -> Mapping[str, SynchronizeLateMessagesPayload]:  # pragma: no cover
        """Get the mapping from participants to checks."""
        serialized = self.db.get_strict("participant_to_late_message")
        deserialized = CollectionRound.deserialize_collection(serialized)
        return cast(Mapping[str, SynchronizeLateMessagesPayload], deserialized)

    def get_chain_id(self, default_chain_id: str) -> str:
        """Get the chain id."""
        return cast(str, self.db.get("chain_id", default_chain_id))


class FailedRound(DegenerateRound, ABC):
    """A round that represents that the period failed"""


class CollectSignatureRound(CollectDifferentUntilThresholdRound):
    """A round in which agents sign the transaction"""

    payload_class = SignaturePayload
    synchronized_data_class = SynchronizedData
    done_event = Event.DONE
    no_majority_event = Event.NO_MAJORITY
    collection_key = get_name(SynchronizedData.participant_to_signature)


class FinalizationRound(OnlyKeeperSendsRound):
    """A round that represents transaction signing has finished"""

    keeper_payload: Optional[FinalizationTxPayload] = None
    payload_class = FinalizationTxPayload
    synchronized_data_class = SynchronizedData

    def end_block(  # pylint: disable=too-many-return-statements
        self,
    ) -> Optional[
        Tuple[BaseSynchronizedData, Enum]
    ]:  # pylint: disable=too-many-return-statements
        """Process the end of the block."""
        if self.keeper_payload is None:
            return None

        if self.keeper_payload.tx_data is None:
            return self.synchronized_data, Event.FINALIZATION_FAILED

        verification_status = VerificationStatus(
            self.keeper_payload.tx_data["status_value"]
        )
        synchronized_data = cast(
            SynchronizedData,
            self.synchronized_data.update(
                synchronized_data_class=self.synchronized_data_class,
                **{
                    get_name(
                        SynchronizedData.tx_hashes_history
                    ): self.keeper_payload.tx_data["tx_hashes_history"],
                    get_name(
                        SynchronizedData.final_verification_status
                    ): verification_status.value,
                    get_name(SynchronizedData.keepers): self.keeper_payload.tx_data[
                        "serialized_keepers"
                    ],
                    get_name(
                        SynchronizedData.blacklisted_keepers
                    ): self.keeper_payload.tx_data["blacklisted_keepers"],
                },
            ),
        )

        # check if we succeeded in finalization.
        # we may fail in any of the following cases:
        # 1. Getting raw safe transaction.
        # 2. Requesting transaction signature.
        # 3. Requesting transaction digest.
        if self.keeper_payload.tx_data["received_hash"]:
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

    payload_class = RandomnessPayload
    synchronized_data_class = SynchronizedData
    done_event = Event.DONE
    no_majority_event = Event.NO_MAJORITY
    collection_key = get_name(SynchronizedData.participant_to_randomness)
    selection_key = (
        get_name(SynchronizedData.most_voted_randomness_round),
        get_name(SynchronizedData.most_voted_randomness),
    )


class SelectKeeperTransactionSubmissionARound(CollectSameUntilThresholdRound):
    """A round in which a keeper is selected for transaction submission"""

    payload_class = SelectKeeperPayload
    synchronized_data_class = SynchronizedData
    done_event = Event.DONE
    no_majority_event = Event.NO_MAJORITY
    collection_key = get_name(SynchronizedData.participant_to_selection)
    selection_key = get_name(SynchronizedData.keepers)

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


class SelectKeeperTransactionSubmissionBRound(SelectKeeperTransactionSubmissionARound):
    """A round in which a new keeper is selected for transaction submission"""


class SelectKeeperTransactionSubmissionBAfterTimeoutRound(
    SelectKeeperTransactionSubmissionBRound
):
    """A round in which a new keeper is selected for tx submission after a round timeout of the previous keeper"""

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Enum]]:
        """Process the end of the block."""
        if self.threshold_reached:
            synchronized_data = cast(SynchronizedData, self.synchronized_data)
            keeper = synchronized_data.most_voted_keeper_address
            missed_messages = synchronized_data.missed_messages
            missed_messages[keeper] += 1

            synchronized_data = cast(
                SynchronizedData,
                self.synchronized_data.update(
                    synchronized_data_class=self.synchronized_data_class,
                    **{get_name(SynchronizedData.missed_messages): missed_messages},
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

    payload_class = ValidatePayload
    synchronized_data_class = SynchronizedData
    done_event = Event.DONE
    negative_event = Event.NEGATIVE
    none_event = Event.NONE
    no_majority_event = Event.NO_MAJORITY
    collection_key = get_name(SynchronizedData.participant_to_votes)

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
                **{
                    self.collection_key: self.serialized_collection,
                    get_name(
                        SynchronizedData.final_verification_status
                    ): VerificationStatus.VERIFIED.value,
                    get_name(SynchronizedData.final_tx_hash): final_tx_hash,
                },
            )
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

    payload_class = CheckTransactionHistoryPayload
    synchronized_data_class = SynchronizedData
    collection_key = get_name(SynchronizedData.participant_to_check)
    selection_key = get_name(SynchronizedData.most_voted_check_result)

    def end_block(  # pylint: disable=too-many-return-statements
        self,
    ) -> Optional[Tuple[BaseSynchronizedData, Enum]]:
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
                    **{
                        self.collection_key: self.serialized_collection,
                        self.selection_key: self.most_voted_payload,
                        get_name(
                            SynchronizedData.final_verification_status
                        ): return_status.value,
                        get_name(SynchronizedData.final_tx_hash): return_tx_hash,
                    },
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
            if return_status == VerificationStatus.BAD_SAFE_NONCE:
                # in case a bad nonce was used, we need to recreate the tx from scratch
                return synchronized_data, Event.NONE

            return synchronized_data, Event.NONE

        if not self.is_majority_possible(
            self.collection, self.synchronized_data.nb_participants
        ):
            return self.synchronized_data, Event.NO_MAJORITY
        return None


class CheckLateTxHashesRound(CheckTransactionHistoryRound):
    """A round in which agents check the late-arriving transaction hashes to see if any of them has been validated"""


class SynchronizeLateMessagesRound(CollectNonEmptyUntilThresholdRound):
    """A round in which agents synchronize potentially late arriving messages"""

    payload_class = SynchronizeLateMessagesPayload
    synchronized_data_class = SynchronizedData
    done_event = Event.DONE
    none_event = Event.NONE
    required_block_confirmations = 3
    selection_key = get_name(SynchronizedData.late_arriving_tx_hashes)
    collection_key = get_name(SynchronizedData.participant_to_late_messages)
    # if the payload is serialized to bytes, we verify that the length specified matches
    _hash_length = TX_HASH_LENGTH

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""
        result = super().end_block()
        if result is None:
            return None

        synchronized_data, event = cast(Tuple[SynchronizedData, Event], result)

        late_arriving_tx_hashes_counts = {
            sender: len(hashes)
            for sender, hashes in synchronized_data.late_arriving_tx_hashes.items()
        }
        missed_after_sync = {
            sender: missed - late_arriving_tx_hashes_counts.get(sender, 0)
            for sender, missed in synchronized_data.missed_messages.items()
        }
        suspects = tuple(filter_negative(missed_after_sync))

        if suspects:
            synchronized_data = cast(
                SynchronizedData,
                synchronized_data.update(
                    synchronized_data_class=self.synchronized_data_class,
                    **{get_name(SynchronizedData.suspects): suspects},
                ),
            )
            return synchronized_data, Event.SUSPICIOUS_ACTIVITY

        synchronized_data = cast(
            SynchronizedData,
            synchronized_data.update(
                synchronized_data_class=self.synchronized_data_class,
                **{get_name(SynchronizedData.missed_messages): missed_after_sync},
            ),
        )
        return synchronized_data, event

    def process_payload(self, payload: BaseTxPayload) -> None:
        """Process payload."""
        # TODO: move check into payload definition via `post_init`
        payload = cast(SynchronizeLateMessagesPayload, payload)
        if self._hash_length:
            content = payload.tx_hashes
            if not content or len(content) % self._hash_length:
                msg = f"Expecting serialized data of chunk size {self._hash_length}"
                raise ABCIAppInternalError(f"{msg}, got: {content} in {self.round_id}")
        super().process_payload(payload)

    def check_payload(self, payload: BaseTxPayload) -> None:
        """Check Payload"""
        # TODO: move check into payload definition via `post_init`
        payload = cast(SynchronizeLateMessagesPayload, payload)
        if self._hash_length:
            content = payload.tx_hashes
            if not content or len(content) % self._hash_length:
                msg = f"Expecting serialized data of chunk size {self._hash_length}"
                raise TransactionNotValidError(
                    f"{msg}, got: {content} in {self.round_id}"
                )
        super().check_payload(payload)


class FinishedTransactionSubmissionRound(DegenerateRound, ABC):
    """A round that represents the transition to the ResetAndPauseRound"""


class ResetRound(CollectSameUntilThresholdRound):
    """A round that represents the reset of a period"""

    payload_class = ResetPayload
    synchronized_data_class = SynchronizedData

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            synchronized_data = cast(SynchronizedData, self.synchronized_data)
            # we could have used the `synchronized_data.create()` here and set the `cross_period_persisted_keys`
            # with the corresponding properties' keys. However, the cross period keys would get passed over
            # for all the following periods, even those that the tx settlement succeeds.
            # Therefore, we need to manually call the db's create method and pass the keys we want to keep only
            # for the next period, which comes after a `NO_MAJORITY` event of the tx settlement skill.
            # TODO investigate the following:
            # This probably indicates an issue with the logic of this skill. We should not increase the period since
            # we have a failure. We could instead just remove the `ResetRound` and transition to the
            # `RandomnessTransactionSubmissionRound` directly. This would save us one round, would allow us to remove
            # this hacky logic for the `create`, and would also not increase the period count in non-successful events
            self.synchronized_data.db.create(
                **{
                    db_key: synchronized_data.db.get(db_key, default)
                    for db_key, default in {
                        "all_participants": VALUE_NOT_PROVIDED,
                        "participants": VALUE_NOT_PROVIDED,
                        "consensus_threshold": VALUE_NOT_PROVIDED,
                        "safe_contract_address": VALUE_NOT_PROVIDED,
                        "tx_hashes_history": "",
                        "keepers": VALUE_NOT_PROVIDED,
                        "missed_messages": dict.fromkeys(
                            synchronized_data.all_participants, 0
                        ),
                        "late_arriving_tx_hashes": VALUE_NOT_PROVIDED,
                        "suspects": tuple(),
                    }.items()
                }
            )
            return self.synchronized_data, Event.DONE
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
        1. SelectKeeperTransactionSubmissionARound
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
            - validate timeout: 5.
            - no majority: 4.
        5. CheckTransactionHistoryRound
            - done: 11.
            - negative: 6.
            - none: 12.
            - check timeout: 5.
            - no majority: 5.
            - check late arriving message: 8.
        6. SelectKeeperTransactionSubmissionBRound
            - done: 3.
            - round timeout: 6.
            - no majority: 10.
            - incorrect serialization: 12.
        7. SelectKeeperTransactionSubmissionBAfterTimeoutRound
            - done: 3.
            - check history: 5.
            - check late arriving message: 8.
            - round timeout: 7.
            - no majority: 10.
            - incorrect serialization: 12.
        8. SynchronizeLateMessagesRound
            - done: 9.
            - round timeout: 8.
            - none: 6.
            - suspicious activity: 12.
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

    initial_round_cls: AppState = RandomnessTransactionSubmissionRound
    initial_states: Set[AppState] = {RandomnessTransactionSubmissionRound}
    transition_function: AbciAppTransitionFunction = {
        RandomnessTransactionSubmissionRound: {
            Event.DONE: SelectKeeperTransactionSubmissionARound,
            Event.ROUND_TIMEOUT: RandomnessTransactionSubmissionRound,
            Event.NO_MAJORITY: RandomnessTransactionSubmissionRound,
        },
        SelectKeeperTransactionSubmissionARound: {
            Event.DONE: CollectSignatureRound,
            Event.ROUND_TIMEOUT: SelectKeeperTransactionSubmissionARound,
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
            Event.FINALIZE_TIMEOUT: SelectKeeperTransactionSubmissionBAfterTimeoutRound,
            Event.FINALIZATION_FAILED: SelectKeeperTransactionSubmissionBRound,
            Event.CHECK_LATE_ARRIVING_MESSAGE: SynchronizeLateMessagesRound,
            Event.INSUFFICIENT_FUNDS: SelectKeeperTransactionSubmissionBRound,
        },
        ValidateTransactionRound: {
            Event.DONE: FinishedTransactionSubmissionRound,
            Event.NEGATIVE: CheckTransactionHistoryRound,
            Event.NONE: SelectKeeperTransactionSubmissionBRound,
            # even in case of timeout we might've sent the transaction
            # so we need to check the history
            Event.VALIDATE_TIMEOUT: CheckTransactionHistoryRound,
            Event.NO_MAJORITY: ValidateTransactionRound,
        },
        CheckTransactionHistoryRound: {
            Event.DONE: FinishedTransactionSubmissionRound,
            Event.NEGATIVE: SelectKeeperTransactionSubmissionBRound,
            Event.NONE: FailedRound,
            Event.CHECK_TIMEOUT: CheckTransactionHistoryRound,
            Event.NO_MAJORITY: CheckTransactionHistoryRound,
            Event.CHECK_LATE_ARRIVING_MESSAGE: SynchronizeLateMessagesRound,
        },
        SelectKeeperTransactionSubmissionBRound: {
            Event.DONE: FinalizationRound,
            Event.ROUND_TIMEOUT: SelectKeeperTransactionSubmissionBRound,
            Event.NO_MAJORITY: ResetRound,
            Event.INCORRECT_SERIALIZATION: FailedRound,
        },
        SelectKeeperTransactionSubmissionBAfterTimeoutRound: {
            Event.DONE: FinalizationRound,
            Event.CHECK_HISTORY: CheckTransactionHistoryRound,
            Event.CHECK_LATE_ARRIVING_MESSAGE: SynchronizeLateMessagesRound,
            Event.ROUND_TIMEOUT: SelectKeeperTransactionSubmissionBAfterTimeoutRound,
            Event.NO_MAJORITY: ResetRound,
            Event.INCORRECT_SERIALIZATION: FailedRound,
        },
        SynchronizeLateMessagesRound: {
            Event.DONE: CheckLateTxHashesRound,
            Event.ROUND_TIMEOUT: SynchronizeLateMessagesRound,
            Event.NONE: SelectKeeperTransactionSubmissionBRound,
            Event.SUSPICIOUS_ACTIVITY: FailedRound,
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
    db_pre_conditions: Dict[AppState, Set[str]] = {
        RandomnessTransactionSubmissionRound: {
            get_name(SynchronizedData.most_voted_tx_hash),
            get_name(SynchronizedData.participants),
        }
    }
    db_post_conditions: Dict[AppState, Set[str]] = {
        FinishedTransactionSubmissionRound: {
            get_name(SynchronizedData.final_tx_hash),
            get_name(SynchronizedData.final_verification_status),
        },
        FailedRound: set(),
    }
