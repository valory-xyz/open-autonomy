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
from abc import ABC
from enum import Enum
from typing import Dict, List, Mapping, Optional, Set, Tuple, Type, cast

from packages.valory.skills.abstract_round_abci.base import (
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
    RESET_TIMEOUT = "reset_timeout"
    RESET_AND_PAUSE_TIMEOUT = "reset_and_pause_timeout"
    CHECK_HISTORY = "check_history"
    CHECK_LATE_ARRIVING_MESSAGE = "check_late_arriving_message"
    FAILED = "failed"


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
    def tx_hashes_history(self) -> Optional[List[str]]:
        """Get the tx hashes history."""
        return cast(List[str], self.db.get("tx_hashes_history", None))

    @property
    def final_tx_hash(self) -> str:
        """Get the final_tx_hash."""
        return cast(str, self.db.get_strict("tx_hashes_history")[-1])

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
    def is_final_tx_hash_set(self) -> bool:
        """Check if most_voted_estimate is set."""
        return self.tx_hashes_history is not None

    @property
    def late_arriving_tx_hashes(self) -> List[str]:
        """Get the late_arriving_tx_hashes."""
        return cast(List[str], self.db.get_strict("late_arriving_tx_hashes"))


class FinishedRegistrationRound(DegenerateRound, ABC):
    """A round representing that agent registration has finished"""

    round_id = "finished_registration"


class FinishedRegistrationFFWRound(DegenerateRound, ABC):
    """A fast-forward round representing that agent registration has finished"""

    round_id = "finished_registration_ffw"


class FinishedTransactionSubmissionRound(DegenerateRound, ABC):
    """A round that represents that transaction submission has finished"""

    round_id = "finished_transaction_submission"


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

    def end_block(self) -> Optional[Tuple[BasePeriodState, Enum]]:
        """Process the end of the block."""
        if self.has_keeper_sent_payload:
            # if reached participant threshold, set the results
            if (
                self.keeper_payload is not None
                and self.keeper_payload["tx_digest"] != ""
            ):
                hashes = cast(PeriodState, self.period_state).tx_hashes_history
                if hashes is None:
                    hashes = []
                if self.keeper_payload["tx_digest"] not in hashes:
                    hashes.append(self.keeper_payload["tx_digest"])

                state = self.period_state.update(
                    period_state_class=PeriodState,
                    tx_hashes_history=hashes,
                    final_verification_status=VerificationStatus(
                        self.keeper_payload["status"]
                    ),
                )
                return state, Event.DONE

            if self.keeper_payload is not None and VerificationStatus(
                self.keeper_payload["status"]
            ) in (VerificationStatus.ERROR, VerificationStatus.VERIFIED):
                state = self.period_state.update(
                    period_state_class=PeriodState,
                    final_verification_status=VerificationStatus(
                        self.keeper_payload["status"]
                    ),
                )
                if cast(PeriodState, self.period_state).tx_hashes_history is not None:
                    return state, Event.CHECK_HISTORY
                return state, Event.CHECK_LATE_ARRIVING_MESSAGE

            if self.keeper_payload is None or self.keeper_payload["tx_digest"] == "":
                return self.period_state, Event.FAILED

        return None


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
    """A round in which a keeper is selected for transaction submission"""

    round_id = "select_keeper_transaction_submission_b"
    allowed_tx_type = SelectKeeperPayload.transaction_type
    payload_attribute = "keeper"
    period_state_class = PeriodState
    done_event = Event.DONE
    no_majority_event = Event.NO_MAJORITY
    collection_key = "participant_to_selection"
    selection_key = "most_voted_keeper_address"


class ResetRound(CollectSameUntilThresholdRound):
    """A round that represents the reset of a period"""

    round_id = "reset"
    allowed_tx_type = ResetPayload.transaction_type
    payload_attribute = "period_count"

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            state_data = self.period_state.db.get_all()
            state_data["tx_hashes_history"] = None
            state = self.period_state.update(
                period_count=self.most_voted_payload, **state_data
            )
            return state, Event.DONE
        if not self.is_majority_possible(
            self.collection, self.period_state.nb_participants
        ):
            return self.period_state, Event.NO_MAJORITY
        return None


class ResetAndPauseRound(CollectSameUntilThresholdRound):
    """A round that represents that consensus is reached (the final round)"""

    round_id = "reset_and_pause"
    allowed_tx_type = ResetPayload.transaction_type
    payload_attribute = "period_count"

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            extra_kwargs = {}
            for key in self.period_state.db.cross_period_persisted_keys:
                extra_kwargs[key] = self.period_state.db.get_strict(key)
            state = self.period_state.update(
                period_count=self.most_voted_payload,
                participants=self.period_state.participants,
                **extra_kwargs,
            )
            return state, Event.DONE
        if not self.is_majority_possible(
            self.collection, self.period_state.nb_participants
        ):
            return self.period_state, Event.NO_MAJORITY
        return None


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
            state = self.period_state.update(
                period_state_class=self.period_state_class,
                participant_to_votes=self.collection,
                final_verification_status=VerificationStatus.VERIFIED,
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

            # We replace the whole tx history with the returned tx hash, only if the threshold has been reached.
            # This means that we only replace the history with the verified tx's hash if we have succeeded
            # or with `None` if we have failed.
            # Therefore, we only replace the history if we are about to exit from the transaction settlement skill.
            # Then, the skills which use the transaction settlement can check the tx hash
            # and if it is None, then it means that the transaction has failed.
            state = self.period_state.update(
                period_state_class=self.period_state_class,
                participant_to_check=self.collection,
                final_verification_status=return_status,
                tx_hashes_history=[return_tx_hash],
            )

            if return_status == VerificationStatus.VERIFIED:
                return state, Event.DONE

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
    allowed_tx_type = CheckTransactionHistoryPayload.transaction_type
    payload_attribute = "verified_res"
    period_state_class = PeriodState
    selection_key = "most_voted_check_result"


class SynchronizeLateMessagesRound(CollectNonEmptyUntilThresholdRound):
    """A round in which agents synchronize potentially late arriving messages"""

    round_id = "synchronize_late_messages"
    allowed_tx_type = SynchronizeLateMessagesPayload.transaction_type
    payload_attribute = "tx_hash"
    period_state_class = PeriodState
    done_event = Event.DONE
    no_majority_event = Event.NO_MAJORITY
    none_event = Event.NONE
    selection_key = "participant"
    collection_key = "late_arriving_tx_hashes"


class TransactionSubmissionAbciApp(AbciApp[Event]):
    """TransactionSubmissionAbciApp

    Initial round: RandomnessTransactionSubmissionRound

    Initial states: {RandomnessTransactionSubmissionRound}

    Transition states:
    0. RandomnessTransactionSubmissionRound
        - done: 1.
        - round timeout: 7.
        - no majority: 0.
    1. SelectKeeperTransactionSubmissionRoundA
        - done: 2.
        - round timeout: 7.
        - no majority: 7.
    2. CollectSignatureRound
        - done: 3.
        - round timeout: 7.
        - no majority: 7.
    3. FinalizationRound
        - done: 4.
        - round timeout: 6.
        - failed: 6.
    4. ValidateTransactionRound
        - done: 8.
        - negative: 5.
        - none: 3.
        - validate timeout: 3.
        - no majority: 4.
    5. CheckTransactionHistoryRound
        - done: 9.
        - negative: 10.
        - none: 10.
        - round timeout: 5.
        - no majority: 10.
    6. SelectKeeperTransactionSubmissionRoundB
        - done: 3.
        - round timeout: 7.
        - no majority: 7.
    7. ResetRound
        - done: 0.
        - reset timeout: 10.
        - no majority: 10.
    8. ResetAndPauseRound
        - done: 9.
        - reset and pause timeout: 10.
        - no majority: 10.
    9. FinishedTransactionSubmissionRound
    10. FailedRound

    Final states: {FinishedTransactionSubmissionRound, FailedRound}

    Timeouts:
        round timeout: 30.0
        validate timeout: 30.0
        reset timeout: 30.0
        reset and pause timeout: 30.0
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
            Event.ROUND_TIMEOUT: SelectKeeperTransactionSubmissionRoundB,
            Event.FAILED: SelectKeeperTransactionSubmissionRoundB,
            Event.CHECK_LATE_ARRIVING_MESSAGE: SynchronizeLateMessagesRound,
        },
        ValidateTransactionRound: {
            Event.DONE: ResetAndPauseRound,
            Event.NEGATIVE: CheckTransactionHistoryRound,
            Event.NONE: FinalizationRound,
            Event.VALIDATE_TIMEOUT: FinalizationRound,
            Event.NO_MAJORITY: ValidateTransactionRound,
        },
        CheckTransactionHistoryRound: {
            Event.DONE: ResetAndPauseRound,
            Event.NEGATIVE: FailedRound,
            Event.NONE: FailedRound,
            Event.ROUND_TIMEOUT: CheckTransactionHistoryRound,
            Event.NO_MAJORITY: FailedRound,
        },
        SelectKeeperTransactionSubmissionRoundB: {
            Event.DONE: FinalizationRound,
            Event.ROUND_TIMEOUT: ResetRound,
            Event.NO_MAJORITY: ResetRound,
        },
        SynchronizeLateMessagesRound: {
            Event.DONE: CheckLateTxHashesRound,
            Event.ROUND_TIMEOUT: SynchronizeLateMessagesRound,
            Event.NO_MAJORITY: SynchronizeLateMessagesRound,
            Event.NONE: FailedRound,
        },
        CheckLateTxHashesRound: {
            Event.DONE: ResetAndPauseRound,
            Event.NEGATIVE: FailedRound,
            Event.NONE: FailedRound,
            Event.ROUND_TIMEOUT: CheckLateTxHashesRound,
            Event.NO_MAJORITY: FailedRound,
        },
        ResetRound: {
            Event.DONE: RandomnessTransactionSubmissionRound,
            Event.RESET_TIMEOUT: FailedRound,
            Event.NO_MAJORITY: FailedRound,
        },
        ResetAndPauseRound: {
            Event.DONE: FinishedTransactionSubmissionRound,
            Event.RESET_AND_PAUSE_TIMEOUT: FailedRound,
            Event.NO_MAJORITY: FailedRound,
        },
        FinishedTransactionSubmissionRound: {},
        FailedRound: {},
    }
    final_states: Set[AppState] = {FinishedTransactionSubmissionRound, FailedRound}
    event_to_timeout: Dict[Event, float] = {
        Event.ROUND_TIMEOUT: 30.0,
        Event.VALIDATE_TIMEOUT: 30.0,
        Event.RESET_TIMEOUT: 30.0,
        Event.RESET_AND_PAUSE_TIMEOUT: 30.0,
    }
