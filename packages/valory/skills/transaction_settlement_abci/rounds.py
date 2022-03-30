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
from typing import (
    Any,
    Deque,
    Dict,
    List,
    Mapping,
    Optional,
    Set,
    Tuple,
    Type,
    Union,
    cast,
)

from packages.valory.skills.abstract_round_abci.base import (
    ABCIAppInternalError,
    AbciApp,
    AbciAppTransitionFunction,
    AbstractRound,
    AppState,
    BasePeriodState,
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


class Event(Enum):
    """Event enumeration for the price estimation demo."""

    DONE = "done"
    ROUND_TIMEOUT = "round_timeout"
    NO_MAJORITY = "no_majority"
    NEGATIVE = "negative"
    NONE = "none"
    VALIDATE_TIMEOUT = "validate_timeout"
    CHECK_TIMEOUT = "check_timeout"
    RESET_TIMEOUT = "reset_timeout"
    CHECK_HISTORY = "check_history"
    CHECK_LATE_ARRIVING_MESSAGE = "check_late_arriving_message"
    FINALIZATION_FAILED = "finalization_failed"
    MISSED_AND_LATE_MESSAGES_MISMATCH = "missed_and_late_messages_mismatch"


class PeriodState(BasePeriodState):  # pylint: disable=too-many-instance-attributes
    """
    Class to represent a period state.

    This state is replicated by the tendermint application.
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
        return cast(List[str], self.db.get("tx_hashes_history", []))

    @property
    def keepers(self) -> Deque[str]:
        """Get the current cycle's keepers who have tried to submit a transaction."""
        return cast(deque, self.db.get("keepers", deque()))

    @property
    def keeper_in_priority(self) -> str:
        """Get the first in priority keeper to try to re-submit a transaction."""
        return self.keepers[0]

    @property
    def to_be_validated_tx_hash(self) -> str:
        """
        Get the tx hash which is ready for validation.

        This will always be the last hash in the `tx_hashes_history`,
        due to the way we are inserting the hashes in the array.
        We keep the hashes sorted by the time of their finalization.
        If this property is accessed before the finalization succeeds,
        then it is incorrectly used and raises an internal error.

        :return: the tx hash which is ready for validation.
        """
        if len(self.tx_hashes_history) > 0:
            return self.tx_hashes_history[-1]
        raise ABCIAppInternalError(  # pragma: no cover
            "An Error occurred while trying to get the tx hash for validation: "
            "There are no transaction hashes recorded!"
        )

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
    def consecutive_finalizations(self) -> int:
        """Get the number of consecutive finalizations."""
        return cast(int, self.db.get("consecutive_finalizations", 0))

    @property
    def finalizations_threshold_exceeded(self) -> bool:
        """Check if the number of consecutive finalizations has exceeded the allowed limit."""
        malicious_threshold = self.nb_participants // 3
        return self.consecutive_finalizations > malicious_threshold

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
        late_arriving_tx_hashes_unparsed = cast(
            List[str], self.db.get_strict("late_arriving_tx_hashes")
        )
        late_arriving_tx_hashes_parsed = []
        hashes_length = 64
        for unparsed_hash in late_arriving_tx_hashes_unparsed:
            if len(unparsed_hash) % hashes_length != 0:
                # if we cannot parse the hashes, then the developer has serialized them incorrectly.
                raise ABCIAppInternalError(
                    f"Cannot parse late arriving hashes: {unparsed_hash}!"
                )
            parsed_hashes = textwrap.wrap(unparsed_hash, hashes_length)
            late_arriving_tx_hashes_parsed.extend(parsed_hashes)

        return late_arriving_tx_hashes_parsed


class FailedRound(DegenerateRound, ABC):
    """A round that represents that the period failed"""

    round_id = "failed"


class CollectSignatureRound(CollectDifferentUntilThresholdRound):
    """A round in which agents sign the transaction"""

    round_id = "collect_signature"
    allowed_tx_type = SignaturePayload.transaction_type
    payload_attribute = "signature"
    period_state_class = PeriodState
    done_event = Event.DONE
    no_majority_event = Event.NO_MAJORITY
    selection_key = "participant"
    collection_key = "participant_to_signature"


class FinalizationRound(OnlyKeeperSendsRound):
    """A round that represents transaction signing has finished"""

    round_id = "finalization"
    allowed_tx_type = FinalizationTxPayload.transaction_type
    payload_attribute = "tx_data"

    def _get_updated_keepers(self) -> Deque[str]:
        """
        Get the keepers list updated, by adding the current keeper to it.

        This method is responsible to update the queue that we want to store
        with the keepers who have successfully finalized, in order to reuse them if the validation times out.
        Therefore, if the current keeper has not finalized before, the condition will be True,
        and the keeper will be appended to the returned queue.

        :return: the re-prioritized keepers.
        """
        keepers = cast(PeriodState, self.period_state).keepers
        if self.period_state.most_voted_keeper_address not in keepers:
            keepers.append(self.period_state.most_voted_keeper_address)

        return keepers

    def _get_reprioritized_keepers(self) -> Deque[str]:
        """
        Base method to re-prioritize keepers.

        We do not need to re-prioritize for this round.

        :return: the re-prioritized keepers.
        """
        return cast(PeriodState, self.period_state).keepers

    def _get_updated_hashes(self) -> List[str]:
        """Get the tx hashes history updated."""
        hashes = cast(PeriodState, self.period_state).tx_hashes_history
        tx_digest = cast(
            str,
            cast(Dict[str, Union[VerificationStatus, str, int]], self.keeper_payload)[
                "tx_digest"
            ],
        )
        hashes.append(tx_digest)

        return hashes

    def _get_check_or_fail_event(self) -> Event:
        """Return the appropriate check event or fail."""
        if VerificationStatus(
            cast(Dict[str, Union[VerificationStatus, str, int]], self.keeper_payload)[
                "status"
            ]
        ) not in (
            VerificationStatus.ERROR,
            VerificationStatus.VERIFIED,
        ):
            # This means that getting raw safe transaction succeeded,
            # but either requesting tx signature or requesting tx digest failed.
            return Event.FINALIZATION_FAILED
        if len(cast(PeriodState, self.period_state).tx_hashes_history) > 0:
            return Event.CHECK_HISTORY
        if cast(PeriodState, self.period_state).should_check_late_messages:
            return Event.CHECK_LATE_ARRIVING_MESSAGE
        return Event.FINALIZATION_FAILED

    def end_block(self) -> Optional[Tuple[BasePeriodState, Enum]]:
        """Process the end of the block."""
        if not self.has_keeper_sent_payload:
            return None

        if self.keeper_payload is None:  # pragma: no cover
            state = self.period_state.update(
                period_state_class=PeriodState,
                keepers=self._get_reprioritized_keepers(),
            )
            return state, Event.FINALIZATION_FAILED

        # check if the tx digest is not empty, thus we succeeded in finalization.
        # the tx digest will be empty if we receive an error in any of the following cases:
        # 1. Getting raw safe transaction.
        # 2. Requesting transaction signature.
        # 3. Requesting transaction digest.
        if self.keeper_payload["tx_digest"] != "":
            state = self.period_state.update(
                period_state_class=PeriodState,
                tx_hashes_history=self._get_updated_hashes(),
                keepers=self._get_updated_keepers(),
                final_verification_status=VerificationStatus(
                    self.keeper_payload["status"]
                ),
                consecutive_finalizations=0,
            )
            return state, Event.DONE

        state = self.period_state.update(
            period_state_class=PeriodState,
            final_verification_status=VerificationStatus(self.keeper_payload["status"]),
            keepers=self._get_reprioritized_keepers(),
        )
        return state, self._get_check_or_fail_event()


class FinalizationRoundAfterTimeout(FinalizationRound):
    """A round in which finalization is performed after a `VALIDATE_TIMEOUT`."""

    round_id = "finalization_after_timeout"

    def _get_updated_keepers(self) -> Deque[str]:
        """
        Get the keepers list updated.

        If the validation has timed out, we do not want to update the list again,
        until we manage to settle. Instead, we always want to re-prioritize the keepers after someone tries to finalize,
        so that we constantly try to replace one of the pending transactions.

        :return: the re-prioritized keepers.
        """
        return self._get_reprioritized_keepers()

    def _get_reprioritized_keepers(self) -> Deque[str]:
        """
        Update the keepers list to give priority to the next keeper and set the current to last.

        We do this in order to make sure that:
            1. We do not get stuck retrying with the same keeper all the time.
            2. We cycle through all the keepers to try to resubmit.

        :return: the re-prioritized keepers.
        """
        keepers = cast(PeriodState, self.period_state).keepers
        current_keeper = keepers.popleft()
        keepers.append(current_keeper)

        return keepers


class RandomnessTransactionSubmissionRound(CollectSameUntilThresholdRound):
    """A round for generating randomness"""

    round_id = "randomness_transaction_submission"
    allowed_tx_type = RandomnessPayload.transaction_type
    payload_attribute = "randomness"
    period_state_class = PeriodState
    done_event = Event.DONE
    no_majority_event = Event.NO_MAJORITY
    collection_key = "participant_to_randomness"
    selection_key = "most_voted_randomness"


class SelectKeeperTransactionSubmissionRoundA(CollectSameUntilThresholdRound):
    """A round in which a keeper is selected for transaction submission"""

    round_id = "select_keeper_transaction_submission_a"
    allowed_tx_type = SelectKeeperPayload.transaction_type
    payload_attribute = "keeper"
    period_state_class = PeriodState
    done_event = Event.DONE
    no_majority_event = Event.NO_MAJORITY
    collection_key = "participant_to_selection"
    selection_key = "most_voted_keeper_address"


class SelectKeeperTransactionSubmissionRoundB(CollectSameUntilThresholdRound):
    """A round in which a new keeper is selected for transaction submission"""

    round_id = "select_keeper_transaction_submission_b"
    allowed_tx_type = SelectKeeperPayload.transaction_type
    payload_attribute = "keeper"
    period_state_class = PeriodState
    done_event = Event.DONE
    no_majority_event = Event.NO_MAJORITY
    collection_key = "participant_to_selection"
    selection_key = "most_voted_keeper_address"


class SelectKeeperTransactionSubmissionRoundBAfterTimeout(
    SelectKeeperTransactionSubmissionRoundB
):
    """A round in which a new keeper is selected for tx submission after a round timeout of the previous keeper"""

    round_id = "select_keeper_transaction_submission_b_after_timeout"

    def _get_state_update_params(self) -> Dict[str, Any]:
        """Get the state's update parameters."""
        state = cast(PeriodState, self.period_state)

        return dict(
            missed_messages=state.missed_messages + 1,
            consecutive_finalizations=state.consecutive_finalizations + 1,
        )

    def end_block(self) -> Optional[Tuple[BasePeriodState, Enum]]:
        """Process the end of the block."""
        if self.threshold_reached:
            state = cast(
                PeriodState,
                self.period_state.update(**self._get_state_update_params()),
            )
            if state.finalizations_threshold_exceeded:
                # we only stop re-selection if there are any previous transaction hashes or any missed messages.
                if len(state.tx_hashes_history) > 0:
                    return state, Event.CHECK_HISTORY
                if state.should_check_late_messages:
                    return state, Event.CHECK_LATE_ARRIVING_MESSAGE
        return super().end_block()


class SelectKeeperTransactionSubmissionRoundBAfterFail(
    SelectKeeperTransactionSubmissionRoundBAfterTimeout
):
    """A round in which a new keeper is selected for tx submission after a failure of the previous keeper"""

    round_id = "select_keeper_transaction_submission_b_after_fail"

    def _get_state_update_params(self) -> Dict[str, Any]:
        """Get the state's update parameters."""
        state = cast(PeriodState, self.period_state)

        return dict(
            consecutive_finalizations=state.consecutive_finalizations + 1,
        )


class ValidateTransactionRound(VotingRound):
    """A round in which agents validate the transaction"""

    round_id = "validate_transaction"
    allowed_tx_type = ValidatePayload.transaction_type
    payload_attribute = "vote"
    period_state_class = PeriodState
    done_event = Event.DONE
    negative_event = Event.NEGATIVE
    none_event = Event.NONE
    no_majority_event = Event.NO_MAJORITY
    collection_key = "participant_to_votes"

    def end_block(self) -> Optional[Tuple[BasePeriodState, Enum]]:
        """Process the end of the block."""
        # if reached participant threshold, set the result
        if self.positive_vote_threshold_reached:
            # We only set the final tx hash if we are about to exit from the transaction settlement skill.
            # Then, the skills which use the transaction settlement can check the tx hash
            # and if it is None, then it means that the transaction has failed.
            state = self.period_state.update(
                period_state_class=self.period_state_class,
                participant_to_votes=self.collection,
                final_verification_status=VerificationStatus.VERIFIED,
                final_tx_hash=cast(PeriodState, self.period_state).tx_hashes_history[
                    -1
                ],
                keepers=deque(),
            )  # type: ignore
            return state, self.done_event
        if self.negative_vote_threshold_reached:
            return self.period_state, self.negative_event
        if self.none_vote_threshold_reached:
            return self.period_state, self.none_event
        if not self.is_majority_possible(
            self.collection, self.period_state.nb_participants
        ):
            return self.period_state, self.no_majority_event
        return None


class CheckTransactionHistoryRound(CollectSameUntilThresholdRound):
    """A round in which agents check the transaction history to see if any previous tx has been validated"""

    round_id = "check_transaction_history"
    allowed_tx_type = CheckTransactionHistoryPayload.transaction_type
    payload_attribute = "verified_res"
    period_state_class = PeriodState
    selection_key = "most_voted_check_result"

    def end_block(self) -> Optional[Tuple[BasePeriodState, Enum]]:
        """Process the end of the block."""
        if self.threshold_reached:
            return_status, return_tx_hash = tx_hist_hex_to_payload(
                self.most_voted_payload
            )

            if return_status == VerificationStatus.NOT_VERIFIED:
                # We don't update the state as we need to repeat all checks again later
                state = self.period_state
            else:
                # We only set the final tx hash if we are about to exit from the transaction settlement skill.
                # Then, the skills which use the transaction settlement can check the tx hash
                # and if it is None, then it means that the transaction has failed.
                state = self.period_state.update(
                    period_state_class=self.period_state_class,
                    participant_to_check=self.collection,
                    final_verification_status=return_status,
                    final_tx_hash=return_tx_hash,
                    keepers=deque(),
                )

            if return_status == VerificationStatus.VERIFIED:
                return state, Event.DONE
            if (
                return_status == VerificationStatus.NOT_VERIFIED
                and cast(PeriodState, self.period_state).should_check_late_messages
            ):
                return state, Event.CHECK_LATE_ARRIVING_MESSAGE
            if return_status == VerificationStatus.NOT_VERIFIED:
                return state, Event.NEGATIVE

            return state, Event.NONE

        if not self.is_majority_possible(
            self.collection, self.period_state.nb_participants
        ):
            return self.period_state, Event.NO_MAJORITY
        return None


class CheckLateTxHashesRound(CheckTransactionHistoryRound):
    """A round in which agents check the late-arriving transaction hashes to see if any of them has been validated"""

    round_id = "check_late_tx_hashes"


class SynchronizeLateMessagesRound(CollectNonEmptyUntilThresholdRound):
    """A round in which agents synchronize potentially late arriving messages"""

    round_id = "synchronize_late_messages"
    allowed_tx_type = SynchronizeLateMessagesPayload.transaction_type
    payload_attribute = "tx_hashes"
    period_state_class = PeriodState
    done_event = Event.DONE
    no_majority_event = Event.NO_MAJORITY
    none_event = Event.NONE
    selection_key = "participant"
    collection_key = "late_arriving_tx_hashes"

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        state_event = super().end_block()
        if state_event is None:
            return None

        state, event = cast(Tuple[BasePeriodState, Event], state_event)

        period_state = cast(PeriodState, self.period_state)
        n_late_arriving_tx_hashes = len(period_state.late_arriving_tx_hashes)
        if n_late_arriving_tx_hashes > period_state.missed_messages:
            return state, Event.MISSED_AND_LATE_MESSAGES_MISMATCH

        state = state.update(
            missed_messages=period_state.missed_messages - n_late_arriving_tx_hashes
        )
        return state, event


class FinishedTransactionSubmissionRound(DegenerateRound, ABC):
    """A round that represents the transition to the ResetAndPauseRound"""

    round_id = "pre_reset_and_pause"


class ResetRound(CollectSameUntilThresholdRound):
    """A round that represents the reset of a period"""

    round_id = "reset"
    allowed_tx_type = ResetPayload.transaction_type
    payload_attribute = "period_count"

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            state_data = self.period_state.db.get_all()
            state = self.period_state.update(
                period_count=self.most_voted_payload,
                **state_data,
            )
            return state, Event.DONE
        if not self.is_majority_possible(
            self.collection, self.period_state.nb_participants
        ):
            return self.period_state, Event.NO_MAJORITY
        return None


class TransactionSubmissionAbciApp(AbciApp[Event]):
    """TransactionSubmissionAbciApp

    Initial round: RandomnessTransactionSubmissionRound

    Initial states: {RandomnessTransactionSubmissionRound}

    Transition states:
        0. RandomnessTransactionSubmissionRound
            - done: 1.
            - round timeout: 12.
            - no majority: 0.
        1. SelectKeeperTransactionSubmissionRoundA
            - done: 2.
            - round timeout: 12.
            - no majority: 12.
        2. CollectSignatureRound
            - done: 3.
            - round timeout: 12.
            - no majority: 12.
        3. FinalizationRound
            - done: 4.
            - check history: 6.
            - round timeout: 8.
            - finalization failed: 9.
            - check late arriving message: 10.
        4. ValidateTransactionRound
            - done: 13.
            - negative: 6.
            - none: 3.
            - validate timeout: 5.
            - no majority: 4.
        5. FinalizationRoundAfterTimeout
            - done: 4.
            - check history: 6.
            - round timeout: 8.
            - finalization failed: 7.
            - check late arriving message: 10.
        6. CheckTransactionHistoryRound
            - done: 13.
            - negative: 7.
            - none: 14.
            - check timeout: 6.
            - no majority: 6.
            - check late arriving message: 10.
        7. SelectKeeperTransactionSubmissionRoundB
            - done: 3.
            - round timeout: 12.
            - no majority: 12.
        8. SelectKeeperTransactionSubmissionRoundBAfterTimeout
            - done: 3.
            - check history: 6.
            - check late arriving message: 10.
            - round timeout: 12.
            - no majority: 12.
        9. SelectKeeperTransactionSubmissionRoundBAfterFail
            - done: 3.
            - check history: 6.
            - check late arriving message: 10.
            - round timeout: 12.
            - no majority: 12.
        10. SynchronizeLateMessagesRound
            - done: 11.
            - round timeout: 10.
            - no majority: 10.
            - none: 14.
            - missed and late messages mismatch: 14.
        11. CheckLateTxHashesRound
            - done: 13.
            - negative: 14.
            - none: 14.
            - check timeout: 11.
            - no majority: 14.
            - check late arriving message: 10.
        12. ResetRound
            - done: 0.
            - reset timeout: 14.
            - no majority: 14.
        13. FinishedTransactionSubmissionRound
        14. FailedRound

    Final states: {FailedRound, FinishedTransactionSubmissionRound}

    Timeouts:
        round timeout: 30.0
        validate timeout: 30.0
        check timeout: 30.0
        reset timeout: 30.0
    """

    initial_round_cls: Type[AbstractRound] = RandomnessTransactionSubmissionRound
    transition_function: AbciAppTransitionFunction = {
        RandomnessTransactionSubmissionRound: {
            Event.DONE: SelectKeeperTransactionSubmissionRoundA,
            Event.ROUND_TIMEOUT: ResetRound,
            Event.NO_MAJORITY: RandomnessTransactionSubmissionRound,
        },
        SelectKeeperTransactionSubmissionRoundA: {
            Event.DONE: CollectSignatureRound,
            Event.ROUND_TIMEOUT: ResetRound,
            Event.NO_MAJORITY: ResetRound,
        },
        CollectSignatureRound: {
            Event.DONE: FinalizationRound,
            Event.ROUND_TIMEOUT: ResetRound,
            Event.NO_MAJORITY: ResetRound,
        },
        FinalizationRound: {
            Event.DONE: ValidateTransactionRound,
            Event.CHECK_HISTORY: CheckTransactionHistoryRound,
            Event.ROUND_TIMEOUT: SelectKeeperTransactionSubmissionRoundBAfterTimeout,
            Event.FINALIZATION_FAILED: SelectKeeperTransactionSubmissionRoundBAfterFail,
            Event.CHECK_LATE_ARRIVING_MESSAGE: SynchronizeLateMessagesRound,
        },
        ValidateTransactionRound: {
            Event.DONE: FinishedTransactionSubmissionRound,
            Event.NEGATIVE: CheckTransactionHistoryRound,
            Event.NONE: FinalizationRound,
            Event.VALIDATE_TIMEOUT: FinalizationRoundAfterTimeout,
            Event.NO_MAJORITY: ValidateTransactionRound,
        },
        FinalizationRoundAfterTimeout: {
            Event.DONE: ValidateTransactionRound,
            Event.CHECK_HISTORY: CheckTransactionHistoryRound,
            Event.ROUND_TIMEOUT: SelectKeeperTransactionSubmissionRoundBAfterTimeout,
            Event.FINALIZATION_FAILED: SelectKeeperTransactionSubmissionRoundB,
            Event.CHECK_LATE_ARRIVING_MESSAGE: SynchronizeLateMessagesRound,
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
            Event.ROUND_TIMEOUT: ResetRound,
            Event.NO_MAJORITY: ResetRound,
        },
        SelectKeeperTransactionSubmissionRoundBAfterTimeout: {
            Event.DONE: FinalizationRound,
            Event.CHECK_HISTORY: CheckTransactionHistoryRound,
            Event.CHECK_LATE_ARRIVING_MESSAGE: SynchronizeLateMessagesRound,
            Event.ROUND_TIMEOUT: ResetRound,
            Event.NO_MAJORITY: ResetRound,
        },
        SelectKeeperTransactionSubmissionRoundBAfterFail: {
            Event.DONE: FinalizationRound,
            Event.CHECK_HISTORY: CheckTransactionHistoryRound,
            Event.CHECK_LATE_ARRIVING_MESSAGE: SynchronizeLateMessagesRound,
            Event.ROUND_TIMEOUT: ResetRound,
            Event.NO_MAJORITY: ResetRound,
        },
        SynchronizeLateMessagesRound: {
            Event.DONE: CheckLateTxHashesRound,
            Event.ROUND_TIMEOUT: SynchronizeLateMessagesRound,
            Event.NO_MAJORITY: SynchronizeLateMessagesRound,
            Event.NONE: FailedRound,
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
        Event.VALIDATE_TIMEOUT: 30.0,
        Event.CHECK_TIMEOUT: 30.0,
        Event.RESET_TIMEOUT: 30.0,
    }
