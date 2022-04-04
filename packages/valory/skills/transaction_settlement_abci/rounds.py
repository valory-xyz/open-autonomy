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
    KEEPER_BLACKLISTED = "keeper_blacklisted"


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
        address_length = 42
        retries_length = 64

        if self.is_keeper_set:
            keepers_unparsed = cast(str, self.db.get("keepers", ""))
            if (len(keepers_unparsed) - retries_length) % address_length != 0:
                # if we cannot parse the keepers, then the developer has serialized them incorrectly.
                raise ABCIAppInternalError(f"Cannot parse keepers: {keepers_unparsed}!")
            keepers_parsed = textwrap.wrap(
                keepers_unparsed[retries_length:], address_length
            )
            return deque(keepers_parsed)

        return deque()

    @property
    def blacklisted_keepers(self) -> Set[str]:
        """Get the current cycle's blacklisted keepers who cannot submit a transaction."""
        return cast(Set[str], self.db.get("blacklisted_keepers", {}))

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
        address_length = 42
        retries_length = 64

        if self.is_keeper_set:
            keepers_unparsed = cast(str, self.db.get("keepers", ""))
            if (len(keepers_unparsed) - retries_length) % address_length != 0:
                # if we cannot parse the keepers, then the developer has serialized them incorrectly.
                raise ABCIAppInternalError(f"Cannot parse keepers: {keepers_unparsed}!")
            keeper_retries = int.from_bytes(
                bytes.fromhex(keepers_unparsed[:retries_length]), "big"
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

    def _blacklist_keeper(self) -> Tuple[Deque[str], Set[str]]:
        """Blacklist the current keeper."""
        period_state = cast(PeriodState, self.period_state)
        keepers = period_state.keepers
        blacklisted_keepers = period_state.blacklisted_keepers
        keepers.remove(period_state.most_voted_keeper_address)
        blacklisted_keepers.add(period_state.most_voted_keeper_address)

        return keepers, blacklisted_keepers

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
            return self.period_state, Event.FINALIZATION_FAILED

        # check if the tx digest is not empty, thus we succeeded in finalization.
        # the tx digest will be empty if we receive an error in any of the following cases:
        # 1. Getting raw safe transaction.
        # 2. Requesting transaction signature.
        # 3. Requesting transaction digest.
        if self.keeper_payload["tx_digest"] != "":
            state = self.period_state.update(
                period_state_class=PeriodState,
                tx_hashes_history=self._get_updated_hashes(),
                final_verification_status=VerificationStatus(
                    self.keeper_payload["status"]
                ),
            )
            return state, Event.DONE

        update_params: Dict[str, Any] = dict(
            period_state_class=PeriodState,
            final_verification_status=VerificationStatus(self.keeper_payload["status"]),
        )
        if (
            VerificationStatus(self.keeper_payload["status"])
            == VerificationStatus.BLACKLIST
        ):
            (
                update_params["keepers"],
                update_params["blacklisted_keepers"],
            ) = self._blacklist_keeper()

        state = self.period_state.update(**update_params)
        event = self._get_check_or_fail_event()

        return state, event


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
    payload_attribute = "keepers"
    period_state_class = PeriodState
    done_event = Event.DONE
    no_majority_event = Event.NO_MAJORITY
    collection_key = "participant_to_selection"
    selection_key = "keepers"


class SelectKeeperTransactionSubmissionRoundB(SelectKeeperTransactionSubmissionRoundA):
    """A round in which a new keeper is selected for transaction submission"""

    round_id = "select_keeper_transaction_submission_b"


class SelectKeeperTransactionSubmissionRoundBAfterTimeout(
    SelectKeeperTransactionSubmissionRoundB
):
    """A round in which a new keeper is selected for tx submission after a round timeout of the previous keeper"""

    round_id = "select_keeper_transaction_submission_b_after_timeout"

    def end_block(self) -> Optional[Tuple[BasePeriodState, Enum]]:
        """Process the end of the block."""
        if self.threshold_reached:
            state = cast(
                PeriodState,
                self.period_state.update(
                    missed_messages=cast(PeriodState, self.period_state).missed_messages
                    + 1
                ),
            )
            if state.keepers_threshold_exceeded:
                # we only stop re-selection if there are any previous transaction hashes or any missed messages.
                if len(state.tx_hashes_history) > 0:
                    return state, Event.CHECK_HISTORY
                if state.should_check_late_messages:
                    return state, Event.CHECK_LATE_ARRIVING_MESSAGE
        return super().end_block()


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
            - round timeout: 10.
            - no majority: 0.
        1. SelectKeeperTransactionSubmissionRoundA
            - done: 2.
            - round timeout: 10.
            - no majority: 10.
        2. CollectSignatureRound
            - done: 3.
            - round timeout: 10.
            - no majority: 10.
        3. FinalizationRound
            - done: 4.
            - check history: 5.
            - round timeout: 7.
            - finalization failed: 6.
            - check late arriving message: 8.
        4. ValidateTransactionRound
            - done: 11.
            - negative: 5.
            - none: 3.
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
            - keeper blacklisted: 6.
            - round timeout: 10.
            - no majority: 10.
        7. SelectKeeperTransactionSubmissionRoundBAfterTimeout
            - done: 3.
            - check history: 5.
            - check late arriving message: 8.
            - round timeout: 10.
            - no majority: 10.
        8. SynchronizeLateMessagesRound
            - done: 9.
            - round timeout: 8.
            - no majority: 8.
            - none: 3.
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
            Event.FINALIZATION_FAILED: SelectKeeperTransactionSubmissionRoundB,
            Event.CHECK_LATE_ARRIVING_MESSAGE: SynchronizeLateMessagesRound,
        },
        ValidateTransactionRound: {
            Event.DONE: FinishedTransactionSubmissionRound,
            Event.NEGATIVE: CheckTransactionHistoryRound,
            Event.NONE: FinalizationRound,
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
            Event.KEEPER_BLACKLISTED: SelectKeeperTransactionSubmissionRoundB,
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
        SynchronizeLateMessagesRound: {
            Event.DONE: CheckLateTxHashesRound,
            Event.ROUND_TIMEOUT: SynchronizeLateMessagesRound,
            Event.NO_MAJORITY: SynchronizeLateMessagesRound,
            Event.NONE: FinalizationRound,
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
