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
from enum import Enum
from typing import Dict, List, Mapping, Optional, Set, Tuple, Type, cast

from packages.valory.skills.abstract_round_abci.base import (
    AbciApp,
    AbciAppTransitionFunction,
    AbstractRound,
    AppState,
    BasePeriodState,
    CollectDifferentUntilThresholdRound,
    CollectSameUntilThresholdRound,
    DegenerateRound,
    OnlyKeeperSendsRound,
)
from packages.valory.skills.transaction_settlement_abci.payloads import (
    FinalizationTxPayload,
    RandomnessPayload,
    ResetPayload,
    SelectKeeperPayload,
    SignaturePayload,
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
    FAILED = "failed"


def rotate_list(my_list: list, positions: int) -> List[str]:
    """Rotate a list n positions."""
    return my_list[positions:] + my_list[:positions]


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
    def oracle_contract_address(self) -> str:
        """Get the oracle contract address."""
        return cast(str, self.db.get_strict("oracle_contract_address"))

    @property
    def participant_to_signature(self) -> Mapping[str, SignaturePayload]:
        """Get the participant_to_signature."""
        return cast(
            Mapping[str, SignaturePayload],
            self.db.get_strict("participant_to_signature"),
        )

    @property
    def final_tx_hash(self) -> str:
        """Get the final_tx_hash."""
        return cast(str, self.db.get_strict("final_tx_hash"))

    @property
    def most_voted_tx_hash(self) -> str:
        """Get the most_voted_tx_hash."""
        return cast(str, self.db.get_strict("most_voted_tx_hash"))

    @property
    def is_final_tx_hash_set(self) -> bool:
        """Check if most_voted_estimate is set."""
        return self.db.get("final_tx_hash", None) is not None

    @property
    def most_voted_estimate(self) -> float:
        """Get the most_voted_estimate."""
        return cast(float, self.db.get_strict("most_voted_estimate"))

    @property
    def is_most_voted_estimate_set(self) -> bool:
        """Check if most_voted_estimate is set."""
        return self.db.get("most_voted_estimate", None) is not None

    @property
    def most_voted_amount(self) -> int:
        """Get the most_voted_amount."""
        return self.db.get_strict("most_voted_amount")


class FinishedRegistrationRound(DegenerateRound):
    """A round representing that agent registration has finished"""

    round_id = "finished_registration"


class FinishedRegistrationFFWRound(DegenerateRound):
    """A fast-forward round representing that agent registration has finished"""

    round_id = "finished_registration_ffw"


class FinishedTransactionSubmissionRound(DegenerateRound):
    """A round that represents that transaction submission has finished"""

    round_id = "finished_transaction_submission"


class FailedRound(DegenerateRound):
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
    payload_attribute = "tx_hash"
    period_state_class = PeriodState
    done_event = Event.DONE
    fail_event = Event.FAILED
    payload_key = "final_tx_hash"


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
            state = self.period_state.update(
                period_count=self.most_voted_payload, **self.period_state.db.get_all()
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
            state = self.period_state.update(
                period_count=self.most_voted_payload,
                participants=self.period_state.participants,
                oracle_contract_address=self.period_state.db.get_strict(
                    "oracle_contract_address"
                ),
                safe_contract_address=self.period_state.db.get_strict(
                    "safe_contract_address"
                ),
            )
            return state, Event.DONE
        if not self.is_majority_possible(
            self.collection, self.period_state.nb_participants
        ):
            return self.period_state, Event.NO_MAJORITY
        return None


class ValidateTransactionRound(CollectSameUntilThresholdRound):
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

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            state = self.period_state.update(
                participants=self.period_state.participants,
                most_voted_amount=self.most_voted_payload.amount,
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
        - round timeout: 6.
        - no majority: 0.
    1. SelectKeeperTransactionSubmissionRoundA
        - done: 2.
        - round timeout: 6.
        - no majority: 6.
    2. CollectSignatureRound
        - done: 3.
        - round timeout: 6.
        - no majority: 6.
    3. FinalizationRound
        - done: 4.
        - round timeout: 5.
        - failed: 5.
    4. ValidateTransactionRound
        - done: 7.
        - negative: 6.
        - none: 6.
        - validate timeout: 6.
        - no majority: 4.
    5. SelectKeeperTransactionSubmissionRoundB
        - done: 3.
        - round timeout: 6.
        - no majority: 6.
    6. ResetRound
        - done: 0.
        - reset timeout: 9.
        - no majority: 9.
    7. ResetAndPauseRound
        - done: 8.
        - reset and pause timeout: 9.
        - no majority: 9.
    8. FinishedTransactionSubmissionRound
    9. FailedRound

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
            Event.ROUND_TIMEOUT: SelectKeeperTransactionSubmissionRoundB,  # TODO: what if the keeper does send the tx but doesn't share the hash? need to check for this! simple round timeout won't do here, need an intermediate step.
            Event.FAILED: SelectKeeperTransactionSubmissionRoundB,
        },
        ValidateTransactionRound: {
            Event.DONE: ResetAndPauseRound,
            Event.NEGATIVE: ResetRound,  # TODO: introduce additional behaviour to resolve what's the issue (this is quite serious, a tx the agents disagree on has been included!)
            Event.NONE: ResetRound,  # TODO: introduce additional logic to resolve the tx still not being confirmed; either we cancel it or we wait longer.
            Event.VALIDATE_TIMEOUT: ResetRound,  # TODO: see above
            Event.NO_MAJORITY: ValidateTransactionRound,
        },
        SelectKeeperTransactionSubmissionRoundB: {
            Event.DONE: FinalizationRound,
            Event.ROUND_TIMEOUT: ResetRound,
            Event.NO_MAJORITY: ResetRound,
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
