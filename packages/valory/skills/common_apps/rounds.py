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
import struct
from abc import ABC
from enum import Enum
from types import MappingProxyType
from typing import (
    AbstractSet,
    Dict,
    List,
    Mapping,
    Optional,
    Sequence,
    Set,
    Tuple,
    Type,
    cast,
)

from aea.exceptions import enforce

from packages.valory.skills.abstract_round_abci.abci_app_chain import (
    AbciAppTransitionMapping,
    chain,
)
from packages.valory.skills.abstract_round_abci.base import (
    AbciApp,
    AbciAppTransitionFunction,
    AbstractRound,
    AppState,
    BasePeriodState,
    CollectDifferentUntilThresholdRound,
    CollectSameUntilThresholdRound,
    OnlyKeeperSendsRound,
    VotingRound,
)
from packages.valory.skills.agent_registration_abci.rounds import (
    AgentRegistrationAbciApp,
    FinishedERound,
    FinishedFRound,
    RegistrationRound,
)
from packages.valory.skills.price_estimation_abci.payloads import (
    DeployOraclePayload,
    DeploySafePayload,
    EstimatePayload,
    FinalizationTxPayload,
    ObservationPayload,
    RandomnessPayload,
    ResetPayload,
    SelectKeeperPayload,
    SignaturePayload,
    TransactionHashPayload,
    TransactionType,
    ValidatePayload,
)
from packages.valory.skills.price_estimation_abci.tools import aggregate

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


def encode_float(value: float) -> bytes:
    """Encode a float value."""
    return struct.pack("d", value)


def rotate_list(my_list: list, positions: int) -> List[str]:
    """Rotate a list n positions."""
    return my_list[positions:] + my_list[:positions]


class PeriodState(BasePeriodState):  # pylint: disable=too-many-instance-attributes
    """
    Class to represent a period state.

    This state is replicated by the tendermint application.
    """

    def __init__(  # pylint: disable=too-many-arguments,too-many-locals
        self,
        participants: Optional[AbstractSet[str]] = None,
        period_count: Optional[int] = None,
        period_setup_params: Optional[Dict] = None,
    ) -> None:
        """Initialize a period state."""
        super().__init__(
            participants=participants,
            period_count=period_count,
            period_setup_params=period_setup_params,
        )

    @property
    def sorted_participants(self) -> Sequence[str]:
        """
        Get the sorted participants' addresses.

        The addresses are sorted according to their hexadecimal value;
        this is the reason we use key=str.lower as comparator.

        This property is useful when interacting with the Safe contract.

        :return: the sorted participants' addresses
        """
        return sorted(self.participants, key=str.lower)


class AgentRegistrationAbstractRound(AbstractRound[Event, TransactionType], ABC):
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


class FinishedRound(
    CollectDifferentUntilThresholdRound, AgentRegistrationAbstractRound
):
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


class FinishedERound(FinishedRound):
    """This class represents the finished round during operation."""

    round_id = "finished_e"


class FinishedFRound(FinishedRound):
    """This class represents the finished round during operation."""

    round_id = "finished_f"


class RegistrationStartupRound(
    CollectDifferentUntilAllRound, AgentRegistrationAbstractRound
):
    """
    This class represents the registration round.

    Input: None
    Output: a period state with the set of participants.

    It schedules the SelectKeeperARound.
    """

    round_id = "registration_at_startup"
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
            and self.period_state.period_setup_params != {}
            and self.period_state.period_setup_params.get("safe_contract_address", None)
            is not None
            and self.period_state.period_setup_params.get(
                "oracle_contract_address", None
            )
            is not None
        ):
            state = PeriodState(
                participants=self.collection,
                period_count=self.period_state.period_count,
            )
            return state, Event.FAST_FORWARD
        if (
            self.collection_threshold_reached
            and self.block_confirmations > self.required_block_confirmations
        ):  # initial deployment round
            state = PeriodState(
                participants=self.collection,
                period_count=self.period_state.period_count,
            )
            return state, Event.DONE
        return None


class RegistrationRound(
    CollectDifferentUntilThresholdRound, AgentRegistrationAbstractRound
):
    """
    This class represents the registration round during operation.

    Input: a period state with the contracts from previous rounds
    Output: a period state with the set of participants.

    It schedules the SelectKeeperARound.
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
            state = PeriodState(
                participants=frozenset(list(self.collection.keys())),
                period_count=self.period_state.period_count,
            )
            return state, Event.DONE
        return None



class CommonAppsAbstractRound(AbstractRound[Event, TransactionType], ABC):
    """Abstract round for the price estimation skill."""

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


class FinishedARound(FinishedRound):
    """This class represents the finished round during operation."""

    round_id = "finished_a"


class FinishedBRound(FinishedRound):
    """This class represents the finished round during operation."""

    round_id = "finished_b"


class FinishedCRound(FinishedRound):
    """This class represents the finished round during operation."""

    round_id = "finished_c"


class FinishedDRound(FinishedRound):
    """This class represents the finished round during operation."""

    round_id = "finished_d"


class FailedRound(FinishedRound):
    """This class represents the failed round during operation."""

    round_id = "failed"


class BaseRandomnessRound(CollectSameUntilThresholdRound, CommonAppsAbstractRound):
    """
    This class represents the randomness round.

    Input: a set of participants (addresses)
    Output: a set of participants (addresses) and randomness

    It schedules the SelectKeeperARound.
    """

    allowed_tx_type = RandomnessPayload.transaction_type
    payload_attribute = "randomness"

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            state = self.period_state.update(
                participant_to_randomness=MappingProxyType(self.collection),
                most_voted_randomness=self.most_voted_payload,
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


class DeploySafeRound(OnlyKeeperSendsRound, CommonAppsAbstractRound):
    """
    This class represents the deploy Safe round.

    Input: a set of participants (addresses) and a keeper
    Output: a period state with the set of participants, the keeper and the Safe contract address.

    It schedules the ValidateSafeRound.
    """

    round_id = "deploy_safe"
    allowed_tx_type = DeploySafePayload.transaction_type
    payload_attribute = "safe_contract_address"

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        # if reached participant threshold, set the result
        if self.has_keeper_sent_payload:
            state = self.period_state.update(safe_contract_address=self.keeper_payload)
            return state, Event.DONE
        return None


class DeployOracleRound(OnlyKeeperSendsRound, CommonAppsAbstractRound):
    """
    This class represents the deploy Oracle round.

    Input: a set of participants (addresses) and a keeper
    Output: a period state with the set of participants, the keeper and the Oracle contract address.

    It schedules the ValidateOracleRound.
    """

    round_id = "deploy_oracle"
    allowed_tx_type = DeployOraclePayload.transaction_type
    payload_attribute = "oracle_contract_address"

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        # if reached participant threshold, set the result
        if self.has_keeper_sent_payload:
            state = self.period_state.update(
                oracle_contract_address=self.keeper_payload
            )
            return state, Event.DONE
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


class TxHashRound(CollectSameUntilThresholdRound, CommonAppsAbstractRound):
    """
    This class represents the 'tx-hash' round.

    Input: a period state with the prior round data
    Ouptut: a new period state with the prior round data and the votes for each tx hash

    It schedules the CollectSignatureRound.
    """

    round_id = "tx_hash"
    allowed_tx_type = TransactionHashPayload.transaction_type
    payload_attribute = "tx_hash"

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        if self.threshold_reached and self.most_voted_payload is not None:
            state = self.period_state.update(
                participant_to_tx_hash=MappingProxyType(self.collection),
                most_voted_tx_hash=self.most_voted_payload,
            )
            return state, Event.DONE
        if self.threshold_reached and self.most_voted_payload is None:
            return self.period_state, Event.NONE
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


class RandomnessAStartupRound(BaseRandomnessRound):
    """Randomness round for startup."""

    round_id = "randomness_a_startup"


class RandomnessBStartupRound(BaseRandomnessRound):
    """Randomness round for startup."""

    round_id = "randomness_b_startup"


class RandomnessRound(BaseRandomnessRound):
    """Randomness round for operations."""

    round_id = "randomness"


class SelectKeeperAStartupRound(SelectKeeperRound):
    """SelectKeeperA round for startup."""

    round_id = "select_keeper_a_startup"


class SelectKeeperBStartupRound(SelectKeeperRound):
    """SelectKeeperB round for startup."""

    round_id = "select_keeper_b_startup"


class SelectKeeperARound(SelectKeeperRound):
    """This class represents the select keeper A round."""

    round_id = "select_keeper_a"


class SelectKeeperBRound(SelectKeeperRound):
    """This class represents the select keeper B round."""

    round_id = "select_keeper_b"


class SelectKeeperCRound(SelectKeeperRound):
    """This class represents the select keeper C round."""

    round_id = "select_keeper_c"


class SelectKeeperDRound(SelectKeeperRound):
    """This class represents the select keeper D round."""

    round_id = "select_keeper_d"


class BaseResetRound(CollectSameUntilThresholdRound, CommonAppsAbstractRound):
    """This class represents the base reset round."""

    allowed_tx_type = ResetPayload.transaction_type
    payload_attribute = "period_count"

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            state = self.period_state.update(
                period_count=self.most_voted_payload,
                participant_to_randomness=None,
                most_voted_randomness=None,
                participant_to_selection=None,
                most_voted_keeper_address=None,
                participant_to_votes=None,
                participant_to_observations=None,
                participant_to_estimate=None,
                estimate=None,
                most_voted_estimate=None,
                participant_to_tx_hash=None,
                most_voted_tx_hash=None,
                participant_to_signature=None,
                final_tx_hash=None,
            )
            return state, Event.DONE
        if not self.is_majority_possible(
            self.collection, self.period_state.nb_participants
        ):
            return self._return_no_majority_event()
        return None


class ResetRound(BaseResetRound):
    """This class represents the 'reset' round (if something goes wrong)."""

    round_id = "reset"


class ResetAndPauseRound(BaseResetRound):
    """This class represents the 'consensus-reached' round (the final round)."""

    round_id = "reset_and_pause"


class ValidateSafeRound(ValidateRound):
    """
    This class represents the validate Safe round.

    Input: a period state with the prior round data
    Output: a new period state with the prior round data and the validation of the contract address

    It schedules the CollectObservationRound or SelectKeeperARound.
    """

    round_id = "validate_safe"
    negative_event = Event.NEGATIVE
    none_event = Event.NONE


class ValidateOracleRound(ValidateRound):
    """
    This class represents the validate Oracle round.

    Input: a period state with the prior round data
    Output: a new period state with the prior round data and the validation of the contract address

    It schedules the CollectObservationRound or SelectKeeperARound.
    """

    round_id = "validate_oracle"
    negative_event = Event.NEGATIVE
    none_event = Event.NONE


class ValidateTransactionRound(ValidateRound):
    """
    This class represents the validate transaction round.

    Input: a period state with the prior round data
    Output: a new period state with the prior round data and the validation of the transaction

    It schedules the ResetRound or SelectKeeperARound.
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
            Event.DONE: FinishedERound,
            Event.FAST_FORWARD: FinishedFRound,
        },
        RegistrationRound: {
            Event.DONE: FinishedFRound,
        },
        FinishedERound: {},
        FinishedFRound: {},
    }
    final_states: Set[AppState] = {FinishedERound, FinishedFRound}
    event_to_timeout: Dict[Event, float] = {
        Event.ROUND_TIMEOUT: 30.0,
    }

class TransactionSubmissionAbciApp(AbciApp[Event]):
    """Transaction submission ABCI application."""

    initial_round_cls: Type[AbstractRound] = RandomnessRound
    transition_function: AbciAppTransitionFunction = {
        RandomnessRound: {
            Event.DONE: SelectKeeperARound,
            Event.ROUND_TIMEOUT: ResetRound,  # if the round times out we reset the period
            Event.NO_MAJORITY: RandomnessRound,  # we can have some agents on either side of an epoch, so we retry
        },
        SelectKeeperARound: {
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
            Event.ROUND_TIMEOUT: SelectKeeperBRound,  # if the round times out we try with a new keeper; TODO: what if the keeper does send the tx but doesn't share the hash? need to check for this! simple round timeout won't do here, need an intermediate step.
            Event.FAILED: SelectKeeperBRound,  # the keeper was unsuccessful;
        },
        ValidateTransactionRound: {
            Event.DONE: ResetAndPauseRound,
            Event.NEGATIVE: ResetRound,  # if the round reaches a negative vote we continue; TODO: introduce additional behaviour to resolve what's the issue (this is quite serious, a tx the agents disagree on has been included!)
            Event.NONE: ResetRound,  # if the round reaches a none vote we continue; TODO: introduce additional logic to resolve the tx still not being confirmed; either we cancel it or we wait longer.
            Event.VALIDATE_TIMEOUT: ResetRound,  # the tx validation logic has its own timeout, this is just a safety check; TODO: see above
            Event.NO_MAJORITY: ValidateTransactionRound,  # if there is no majority we re-run the round (agents have different observations of the chain-state and need to agree before we can continue)
        },
        SelectKeeperBRound: {
            Event.DONE: FinalizationRound,
            Event.ROUND_TIMEOUT: ResetRound,  # if the round times out we reset the period
            Event.NO_MAJORITY: ResetRound,  # if there is no majority we reset the period
        },
        ResetRound: {
            Event.DONE: RandomnessRound,
            Event.RESET_TIMEOUT: FailedRound,  # if the round times out we see if we can assemble a new group of agents
            Event.NO_MAJORITY: FailedRound,  # if we cannot agree we see if we can assemble a new group of agents
        },
        ResetAndPauseRound: {
            Event.DONE: FinishedDRound,
            Event.RESET_AND_PAUSE_TIMEOUT: FailedRound,  # if the round times out we see if we can assemble a new group of agents
            Event.NO_MAJORITY: FailedRound,  # if we cannot agree we see if we can assemble a new group of agents
        },
        FinishedDRound: {},
        FailedRound: {},
    }
    final_states: Set[AppState] = {FinishedDRound, FailedRound}
    event_to_timeout: Dict[Event, float] = {
        Event.ROUND_TIMEOUT: 30.0,
        Event.VALIDATE_TIMEOUT: 30.0,
        Event.RESET_TIMEOUT: 30.0,
    }