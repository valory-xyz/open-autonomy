# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021 Valory AG
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

"""This module contains the data classes for common apps ABCI application."""
from abc import ABC
from enum import Enum
from types import MappingProxyType
from typing import Dict, List, Mapping, Optional, Set, Tuple, Type, cast

from packages.valory.skills.abstract_round_abci.base import (
    AbciApp,
    AbciAppTransitionFunction,
    AbstractRound,
    AppState,
    BasePeriodState,
    CollectDifferentUntilAllRound,
    CollectDifferentUntilThresholdRound,
    CollectSameUntilThresholdRound,
    OnlyKeeperSendsRound,
    VotingRound,
)
from packages.valory.skills.common_apps.payloads import (
    FinalizationTxPayload,
    RandomnessPayload,
    RegistrationPayload,
    ResetPayload,
    SelectKeeperPayload,
    SignaturePayload,
    TransactionType,
    ValidatePayload,
)


class Event(Enum):
    """Event enumeration for the price estimation demo."""

    DONE = "done"
    ROUND_TIMEOUT = "round_timeout"
    NO_MAJORITY = "no_majority"
    FAST_FORWARD = "fast_forward"
    NEGATIVE = "negative"
    NONE = "none"
    VALIDATE_TIMEOUT = "validate_timeout"
    DEPLOY_TIMEOUT = "deploy_timeout"
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
    def keeper_randomness(self) -> float:
        """Get the keeper's random number [0-1]."""
        res = int(self.most_voted_randomness, base=16) // 10 ** 0 % 10
        return cast(float, res / 10)

    @property
    def is_keeper_set(self) -> bool:
        """Check whether keeper is set."""
        return self.db.get("most_voted_keeper_address", None) is not None

    @property
    def participant_to_randomness(self) -> Mapping[str, RandomnessPayload]:
        """Get the participant_to_randomness."""
        return cast(
            Mapping[str, RandomnessPayload],
            self.db.get_strict("participant_to_randomness"),
        )

    @property
    def most_voted_randomness(self) -> str:
        """Get the most_voted_randomness."""
        return cast(str, self.db.get_strict("most_voted_randomness"))

    @property
    def most_voted_keeper_address(self) -> str:
        """Get the most_voted_keeper_address."""
        return cast(str, self.db.get_strict("most_voted_keeper_address"))

    @property
    def safe_contract_address(self) -> str:
        """Get the safe contract address."""
        return cast(str, self.db.get_strict("safe_contract_address"))

    @property
    def oracle_contract_address(self) -> str:
        """Get the oracle contract address."""
        return cast(str, self.db.get_strict("oracle_contract_address"))

    @property
    def participant_to_selection(self) -> Mapping[str, SelectKeeperPayload]:
        """Get the participant_to_selection."""
        return cast(
            Mapping[str, SelectKeeperPayload],
            self.db.get_strict("participant_to_selection"),
        )

    @property
    def participant_to_votes(self) -> Mapping[str, ValidatePayload]:
        """Get the participant_to_votes."""
        return cast(
            Mapping[str, ValidatePayload], self.db.get_strict("participant_to_votes")
        )

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
    def estimate(self) -> float:
        """Get the estimate."""
        return cast(float, self.db.get_strict("estimate"))

    @property
    def most_voted_estimate(self) -> float:
        """Get the most_voted_estimate."""
        return cast(float, self.db.get_strict("most_voted_estimate"))

    @property
    def is_most_voted_estimate_set(self) -> bool:
        """Check if most_voted_estimate is set."""
        return self.db.get("most_voted_estimate", None) is not None


class CommonAppsAbstractRound(AbstractRound[Event, TransactionType], ABC):
    """Abstract round for the agent registration skill."""

    @property
    def period_state(self) -> PeriodState:
        """Return the period state."""
        return cast(PeriodState, self._state)

    def _return_no_majority_event(self) -> Tuple[PeriodState, Event]:
        """
        Trigger the NO_MAJORITY event.

        :return: a new period state and a NO_MAJORITY event
        """
        return self.period_state, Event.NO_MAJORITY


class FinishedRound(CollectDifferentUntilThresholdRound, CommonAppsAbstractRound):
    """
    This class represents the finished round during operation.

    Input: a period state with the contracts from previous rounds
    Output: a period state with the set of participants.

    It is a sink round.
    """

    round_id = "finished"
    allowed_tx_type = None
    payload_attribute = ""

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """End block."""


class FinishedRegistrationRound(FinishedRound):
    """This class represents the finished round during operation."""

    round_id = "finished_registration"


class FinishedRegistrationFFWRound(FinishedRound):
    """This class represents the finished round during operation."""

    round_id = "finished_registration_ffw"


class RegistrationStartupRound(CollectDifferentUntilAllRound, CommonAppsAbstractRound):
    """
    This class represents the registration round.

    Input: None
    Output: a period state with the set of participants.

    It schedules the SelectKeeperTransactionSubmissionRoundA.
    """

    round_id = "registration_startup"
    allowed_tx_type = RegistrationPayload.transaction_type
    payload_attribute = "sender"
    required_block_confirmations = 1

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        if self.collection_threshold_reached:
            self.block_confirmations += 1
        if (  # fast forward at setup
            self.collection_threshold_reached
            and self.block_confirmations > self.required_block_confirmations
            and self.period_state.db.get("safe_contract_address", None) is not None
            and self.period_state.db.get("oracle_contract_address", None) is not None
        ):
            state = self.period_state.update(
                participants=self.collection,
                safe_contract_address=self.period_state.db.get_strict(
                    "safe_contract_address"
                ),
                oracle_contract_address=self.period_state.db.get_strict(
                    "oracle_contract_address"
                ),
                period_state_class=PeriodState,
            )
            return state, Event.FAST_FORWARD
        if (
            self.collection_threshold_reached
            and self.block_confirmations > self.required_block_confirmations
        ):  # initial deployment round
            state = self.period_state.update(
                participants=self.collection,
                period_state_class=PeriodState,
            )
            return state, Event.DONE
        return None


class RegistrationRound(CollectDifferentUntilThresholdRound, CommonAppsAbstractRound):
    """
    This class represents the registration round during operation.

    Input: a period state with the contracts from previous rounds
    Output: a period state with the set of participants.

    It schedules the SelectKeeperTransactionSubmissionRoundA.
    """

    round_id = "registration"
    allowed_tx_type = RegistrationPayload.transaction_type
    payload_attribute = "sender"
    required_block_confirmations = 10

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        if self.collection_threshold_reached:
            self.block_confirmations += 1
        if (  # contracts are set from previous rounds
            self.collection_threshold_reached
            and self.block_confirmations
            > self.required_block_confirmations  # we also wait here as it gives more (available) agents time to join
        ):
            state = self.period_state.update(
                participants=frozenset(list(self.collection.keys())),
                period_state_class=PeriodState,
            )
            return state, Event.DONE
        return None


class FinishedTransactionSubmissionRound(FinishedRound):
    """This class represents the finished round during operation."""

    round_id = "finished_transaction_submission"


class FailedRound(FinishedRound):
    """This class represents the failed round during operation."""

    round_id = "failed"


class BaseRandomnessRound(CollectSameUntilThresholdRound, CommonAppsAbstractRound):
    """
    This class represents the randomness round.

    Input: a set of participants (addresses)
    Output: a set of participants (addresses) and randomness

    It schedules the SelectKeeperTransactionSubmissionRoundA.
    """

    allowed_tx_type = RandomnessPayload.transaction_type
    payload_attribute = "randomness"
    period_state_class: Type[BasePeriodState] = PeriodState

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            state = self.period_state.update(
                participant_to_randomness=MappingProxyType(self.collection),
                most_voted_randomness=self.most_voted_payload,
                period_state_class=self.period_state_class,
            )
            return state, Event.DONE
        if not self.is_majority_possible(
            self.collection, self.period_state.nb_participants
        ):
            return self._return_no_majority_event()
        return None


class SelectKeeperRound(CollectSameUntilThresholdRound, CommonAppsAbstractRound):
    """
    This class represents the select keeper round.

    Input: a set of participants (addresses)
    Output: the selected keeper.
    """

    allowed_tx_type = SelectKeeperPayload.transaction_type
    payload_attribute = "keeper"

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            state = self.period_state.update(
                participant_to_selection=MappingProxyType(self.collection),
                most_voted_keeper_address=self.most_voted_payload,
            )
            return state, Event.DONE
        if not self.is_majority_possible(
            self.collection, self.period_state.nb_participants
        ):
            return self._return_no_majority_event()
        return None


class ValidateRound(VotingRound, CommonAppsAbstractRound):
    """
    This class represents the validate round.

    Input: a period state with the set of participants, the keeper and the Safe contract address.
    Output: a period state with the set of participants, the keeper, the Safe contract address and a validation of the Safe contract address.
    """

    allowed_tx_type = ValidatePayload.transaction_type
    negative_event: Event
    none_event: Event
    payload_attribute = "vote"

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        # if reached participant threshold, set the result
        if self.positive_vote_threshold_reached:
            state = self.period_state.update(
                participant_to_votes=MappingProxyType(self.collection)
            )
            return state, Event.DONE
        if self.negative_vote_threshold_reached:
            state = self.period_state.update()
            return state, self.negative_event
        if self.none_vote_threshold_reached:
            state = self.period_state.update()
            return state, self.none_event
        if not self.is_majority_possible(
            self.collection, self.period_state.nb_participants
        ):
            return self._return_no_majority_event()
        return None


class CollectSignatureRound(
    CollectDifferentUntilThresholdRound, CommonAppsAbstractRound
):
    """
    This class represents the 'collect-signature' round.

    Input: a period state with the prior round data
    Ouptut: a new period state with the prior round data and the signatures

    It schedules the FinalizationRound.
    """

    round_id = "collect_signature"
    allowed_tx_type = SignaturePayload.transaction_type
    payload_attribute = "signature"

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        if self.collection_threshold_reached:
            state = self.period_state.update(
                participant_to_signature=MappingProxyType(self.collection),
            )
            return state, Event.DONE
        if not self.is_majority_possible(
            self.collection, self.period_state.nb_participants
        ):
            return self._return_no_majority_event()
        return None


class FinalizationRound(OnlyKeeperSendsRound, CommonAppsAbstractRound):
    """
    This class represents the finalization Safe round.

    Input: a period state with the prior round data
    Output: a new period state with the prior round data and the hash of the Safe transaction

    It schedules the ValidateTransactionRound.
    """

    round_id = "finalization"
    allowed_tx_type = FinalizationTxPayload.transaction_type
    payload_attribute = "tx_hash"

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        if self.has_keeper_sent_payload and self.keeper_payload is not None:
            state = self.period_state.update(final_tx_hash=self.keeper_payload)
            return state, Event.DONE
        if self.has_keeper_sent_payload and self.keeper_payload is None:
            return self.period_state, Event.FAILED
        return None


class RandomnessTransactionSubmissionRound(BaseRandomnessRound):
    """Randomness round for operations."""

    round_id = "randomness_transaction_submission"
    period_state_class = PeriodState


class SelectKeeperTransactionSubmissionRoundA(SelectKeeperRound):
    """This class represents the select keeper A round."""

    round_id = "select_keeper_transaction_submission_a"


class SelectKeeperTransactionSubmissionRoundB(SelectKeeperRound):
    """This class represents the select keeper B round."""

    round_id = "select_keeper_transaction_submission_b"


class BaseResetRound(CollectSameUntilThresholdRound, CommonAppsAbstractRound):
    """This class represents the base reset round."""

    allowed_tx_type = ResetPayload.transaction_type
    payload_attribute = "period_count"


class ResetRound(BaseResetRound):
    """This class represents the 'reset' round (if something goes wrong)."""

    round_id = "reset"

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
            return self._return_no_majority_event()
        return None


class ResetAndPauseRound(BaseResetRound):
    """This class represents the 'consensus-reached' round (the final round)."""

    round_id = "reset_and_pause"

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            state = self.period_state.update(
                period_count=self.most_voted_payload,
                participants=self.period_state.participants,
                oracle_contract_address=self.period_state.oracle_contract_address,
                safe_contract_address=self.period_state.safe_contract_address,
            )
            return state, Event.DONE
        if not self.is_majority_possible(
            self.collection, self.period_state.nb_participants
        ):
            return self._return_no_majority_event()
        return None


class ValidateTransactionRound(ValidateRound):
    """
    This class represents the validate transaction round.

    Input: a period state with the prior round data
    Output: a new period state with the prior round data and the validation of the transaction

    It schedules the ResetRound or SelectKeeperTransactionSubmissionRoundA.
    """

    round_id = "validate_transaction"
    negative_event = Event.NEGATIVE
    none_event = Event.NONE


class AgentRegistrationAbciApp(AbciApp[Event]):
    """Registration ABCI application."""

    initial_round_cls: Type[AbstractRound] = RegistrationStartupRound
    initial_states: Set[AppState] = {RegistrationStartupRound, RegistrationRound}
    transition_function: AbciAppTransitionFunction = {
        RegistrationStartupRound: {
            Event.DONE: FinishedRegistrationRound,
            Event.FAST_FORWARD: FinishedRegistrationFFWRound,
        },
        RegistrationRound: {
            Event.DONE: FinishedRegistrationFFWRound,
        },
        FinishedRegistrationRound: {},
        FinishedRegistrationFFWRound: {},
    }
    final_states: Set[AppState] = {
        FinishedRegistrationRound,
        FinishedRegistrationFFWRound,
    }
    event_to_timeout: Dict[Event, float] = {
        Event.ROUND_TIMEOUT: 30.0,
    }


class TransactionSubmissionAbciApp(AbciApp[Event]):
    """Transaction submission ABCI application."""

    initial_round_cls: Type[AbstractRound] = RandomnessTransactionSubmissionRound
    transition_function: AbciAppTransitionFunction = {
        RandomnessTransactionSubmissionRound: {
            Event.DONE: SelectKeeperTransactionSubmissionRoundA,
            Event.ROUND_TIMEOUT: ResetRound,  # if the round times out we reset the period
            Event.NO_MAJORITY: RandomnessTransactionSubmissionRound,  # we can have some agents on either side of an epoch, so we retry
        },
        SelectKeeperTransactionSubmissionRoundA: {
            Event.DONE: CollectSignatureRound,
            Event.ROUND_TIMEOUT: ResetRound,  # if the round times out we reset the period
            Event.NO_MAJORITY: ResetRound,  # if there is no majority we reset the period
        },
        CollectSignatureRound: {
            Event.DONE: FinalizationRound,
            Event.ROUND_TIMEOUT: ResetRound,  # if the round times out we reset the period
            Event.NO_MAJORITY: ResetRound,  # if there is no majority we reset the period
        },
        FinalizationRound: {
            Event.DONE: ValidateTransactionRound,
            Event.ROUND_TIMEOUT: SelectKeeperTransactionSubmissionRoundB,  # if the round times out we try with a new keeper; TODO: what if the keeper does send the tx but doesn't share the hash? need to check for this! simple round timeout won't do here, need an intermediate step.
            Event.FAILED: SelectKeeperTransactionSubmissionRoundB,  # the keeper was unsuccessful;
        },
        ValidateTransactionRound: {
            Event.DONE: ResetAndPauseRound,
            Event.NEGATIVE: ResetRound,  # if the round reaches a negative vote we continue; TODO: introduce additional behaviour to resolve what's the issue (this is quite serious, a tx the agents disagree on has been included!)
            Event.NONE: ResetRound,  # if the round reaches a none vote we continue; TODO: introduce additional logic to resolve the tx still not being confirmed; either we cancel it or we wait longer.
            Event.VALIDATE_TIMEOUT: ResetRound,  # the tx validation logic has its own timeout, this is just a safety check; TODO: see above
            Event.NO_MAJORITY: ValidateTransactionRound,  # if there is no majority we re-run the round (agents have different observations of the chain-state and need to agree before we can continue)
        },
        SelectKeeperTransactionSubmissionRoundB: {
            Event.DONE: FinalizationRound,
            Event.ROUND_TIMEOUT: ResetRound,  # if the round times out we reset the period
            Event.NO_MAJORITY: ResetRound,  # if there is no majority we reset the period
        },
        ResetRound: {
            Event.DONE: RandomnessTransactionSubmissionRound,
            Event.RESET_TIMEOUT: FailedRound,  # if the round times out we see if we can assemble a new group of agents
            Event.NO_MAJORITY: FailedRound,  # if we cannot agree we see if we can assemble a new group of agents
        },
        ResetAndPauseRound: {
            Event.DONE: FinishedTransactionSubmissionRound,
            Event.RESET_AND_PAUSE_TIMEOUT: FailedRound,  # if the round times out we see if we can assemble a new group of agents
            Event.NO_MAJORITY: FailedRound,  # if we cannot agree we see if we can assemble a new group of agents
        },
        FinishedTransactionSubmissionRound: {},
        FailedRound: {},
    }
    final_states: Set[AppState] = {FinishedTransactionSubmissionRound, FailedRound}
    event_to_timeout: Dict[Event, float] = {
        Event.ROUND_TIMEOUT: 30.0,
        Event.VALIDATE_TIMEOUT: 30.0,
        Event.RESET_TIMEOUT: 30.0,
    }
