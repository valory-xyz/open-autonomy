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

"""This module contains the data classes for the price estimation ABCI application."""
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
    Tuple,
    Type,
    cast,
)

from aea.exceptions import enforce

from packages.valory.skills.abstract_round_abci.base import (
    AbciApp,
    AbciAppTransitionFunction,
    AbstractRound,
    BasePeriodState,
    CollectDifferentUntilAllRound,
    CollectDifferentUntilThresholdRound,
    CollectSameUntilThresholdRound,
    OnlyKeeperSendsRound,
    VotingRound,
)
from packages.valory.skills.price_estimation_abci.payloads import (
    DeployOraclePayload,
    DeploySafePayload,
    EstimatePayload,
    FinalizationTxPayload,
    ObservationPayload,
    RandomnessPayload,
    RegistrationPayload,
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
        participant_to_randomness: Optional[Mapping[str, RandomnessPayload]] = None,
        most_voted_randomness: Optional[str] = None,
        participant_to_selection: Optional[Mapping[str, SelectKeeperPayload]] = None,
        most_voted_keeper_address: Optional[str] = None,
        safe_contract_address: Optional[str] = None,
        oracle_contract_address: Optional[str] = None,
        participant_to_votes: Optional[Mapping[str, ValidatePayload]] = None,
        participant_to_observations: Optional[Mapping[str, ObservationPayload]] = None,
        participant_to_estimate: Optional[Mapping[str, EstimatePayload]] = None,
        estimate: Optional[float] = None,
        most_voted_estimate: Optional[float] = None,
        participant_to_tx_hash: Optional[Mapping[str, TransactionHashPayload]] = None,
        most_voted_tx_hash: Optional[str] = None,
        participant_to_signature: Optional[Mapping[str, SignaturePayload]] = None,
        final_tx_hash: Optional[str] = None,
    ) -> None:
        """Initialize a period state."""
        super().__init__(
            participants=participants,
            period_count=period_count,
            period_setup_params=period_setup_params,
        )
        self._participant_to_randomness = participant_to_randomness
        self._most_voted_randomness = most_voted_randomness
        self._most_voted_keeper_address = most_voted_keeper_address
        self._safe_contract_address = safe_contract_address
        self._oracle_contract_address = oracle_contract_address
        self._participant_to_selection = participant_to_selection
        self._participant_to_votes = participant_to_votes
        self._participant_to_observations = participant_to_observations
        self._participant_to_estimate = participant_to_estimate
        self._most_voted_estimate = most_voted_estimate
        self._estimate = estimate
        self._participant_to_tx_hash = participant_to_tx_hash
        self._most_voted_tx_hash = most_voted_tx_hash
        self._participant_to_signature = participant_to_signature
        self._final_tx_hash = final_tx_hash

    @property
    def keeper_randomness(self) -> float:
        """Get the keeper's random number [0-1]."""
        res = int(self.most_voted_randomness, base=16) // 10 ** 0 % 10
        return cast(float, res / 10)

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

    @property
    def are_contracts_set(self) -> bool:
        """Check whether contracts are set."""
        return (
            self._safe_contract_address is not None
            and self._oracle_contract_address is not None
        )

    @property
    def is_keeper_set(self) -> bool:
        """Check whether keeper is set."""
        return self._most_voted_keeper_address is not None

    @property
    def participant_to_randomness(self) -> Mapping[str, RandomnessPayload]:
        """Get the participant_to_randomness."""
        enforce(
            self._participant_to_randomness is not None,
            "'participant_to_randomness' field is None",
        )
        return cast(Mapping[str, RandomnessPayload], self._participant_to_randomness)

    @property
    def most_voted_randomness(self) -> str:
        """Get the most_voted_randomness."""
        enforce(
            self._most_voted_randomness is not None,
            "'most_voted_randomness' field is None",
        )
        return cast(str, self._most_voted_randomness)

    @property
    def most_voted_keeper_address(self) -> str:
        """Get the most_voted_keeper_address."""
        enforce(
            self._most_voted_keeper_address is not None,
            "'most_voted_keeper_address' field is None",
        )
        return cast(str, self._most_voted_keeper_address)

    @property
    def safe_contract_address(self) -> str:
        """Get the safe contract address."""
        enforce(
            self._safe_contract_address is not None,
            "'safe_contract_address' field is None",
        )
        return cast(str, self._safe_contract_address)

    @property
    def oracle_contract_address(self) -> str:
        """Get the oracle contract address."""
        enforce(
            self._oracle_contract_address is not None,
            "'oracle_contract_address' field is None",
        )
        return cast(str, self._oracle_contract_address)

    @property
    def participant_to_selection(self) -> Mapping[str, SelectKeeperPayload]:
        """Get the participant_to_selection."""
        enforce(
            self._participant_to_selection is not None,
            "'participant_to_selection' field is None",
        )
        return cast(Mapping[str, SelectKeeperPayload], self._participant_to_selection)

    @property
    def participant_to_votes(self) -> Mapping[str, ValidatePayload]:
        """Get the participant_to_votes."""
        enforce(
            self._participant_to_votes is not None,
            "'participant_to_votes' field is None",
        )
        return cast(Mapping[str, ValidatePayload], self._participant_to_votes)

    @property
    def participant_to_observations(self) -> Mapping[str, ObservationPayload]:
        """Get the participant_to_observations."""
        enforce(
            self._participant_to_observations is not None,
            "'participant_to_observations' field is None",
        )
        return cast(Mapping[str, ObservationPayload], self._participant_to_observations)

    @property
    def participant_to_estimate(self) -> Mapping[str, EstimatePayload]:
        """Get the participant_to_estimate."""
        enforce(
            self._participant_to_estimate is not None,
            "'participant_to_estimate' field is None",
        )
        return cast(Mapping[str, EstimatePayload], self._participant_to_estimate)

    @property
    def participant_to_signature(self) -> Mapping[str, SignaturePayload]:
        """Get the participant_to_signature."""
        enforce(
            self._participant_to_signature is not None,
            "'participant_to_signature' field is None",
        )
        return cast(Mapping[str, SignaturePayload], self._participant_to_signature)

    @property
    def final_tx_hash(self) -> str:
        """Get the final_tx_hash."""
        enforce(
            self._final_tx_hash is not None,
            "'final_tx_hash' field is None",
        )
        return cast(str, self._final_tx_hash)

    @property
    def is_final_tx_hash_set(self) -> bool:
        """Check if final_tx_hash is set."""
        return self._final_tx_hash is not None

    @property
    def estimate(self) -> float:
        """Get the estimate."""
        enforce(self._estimate is not None, "'estimate' field is None")
        return cast(float, self._estimate)

    @property
    def most_voted_estimate(self) -> float:
        """Get the most_voted_estimate."""
        enforce(
            self._most_voted_estimate is not None, "'most_voted_estimate' field is None"
        )
        return cast(float, self._most_voted_estimate)

    @property
    def is_most_voted_estimate_set(self) -> bool:
        """Check if most_voted_estimate is set."""
        return self._most_voted_estimate is not None

    @property
    def encoded_most_voted_estimate(self) -> bytes:
        """Get the encoded (most voted) estimate."""
        return encode_float(self.most_voted_estimate)

    @property
    def most_voted_tx_hash(self) -> str:
        """Get the most_voted_tx_hash."""
        enforce(
            self._most_voted_tx_hash is not None, "'most_voted_tx_hash' field is None"
        )
        return cast(str, self._most_voted_tx_hash)


class PriceEstimationAbstractRound(AbstractRound[Event, TransactionType], ABC):
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


class RegistrationRound(CollectDifferentUntilAllRound, PriceEstimationAbstractRound):
    """
    This class represents the registration round.

    Input: None
    Output: a period state with the set of participants.

    It schedules the SelectKeeperARound.
    """

    round_id = "registration"
    allowed_tx_type = RegistrationPayload.transaction_type
    payload_attribute = "sender"

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        if (  # fast forward at setup
            self.collection_threshold_reached
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
                safe_contract_address=self.period_state.period_setup_params.get(
                    "safe_contract_address"
                ),
                oracle_contract_address=self.period_state.period_setup_params.get(
                    "oracle_contract_address"
                ),
            )
            return state, Event.FAST_FORWARD
        if (  # contracts are set from previos rounds
            self.collection_threshold_reached
            and hasattr(self.period_state, "are_contracts_set")
            and self.period_state.are_contracts_set
        ):
            state = PeriodState(
                participants=self.collection,
                period_count=self.period_state.period_count,
                safe_contract_address=self.period_state.safe_contract_address,
                oracle_contract_address=self.period_state.oracle_contract_address,
            )
            return state, Event.FAST_FORWARD
        if self.collection_threshold_reached:  # initial deployment round
            state = PeriodState(
                participants=self.collection,
                period_count=self.period_state.period_count,
            )
            return state, Event.DONE
        return None


class BaseRandomnessRound(CollectSameUntilThresholdRound, PriceEstimationAbstractRound):
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


class SelectKeeperRound(CollectSameUntilThresholdRound, PriceEstimationAbstractRound):
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


class DeploySafeRound(OnlyKeeperSendsRound, PriceEstimationAbstractRound):
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


class DeployOracleRound(OnlyKeeperSendsRound, PriceEstimationAbstractRound):
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


class ValidateRound(VotingRound, PriceEstimationAbstractRound):
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


class CollectObservationRound(
    CollectDifferentUntilThresholdRound, PriceEstimationAbstractRound
):
    """
    This class represents the 'collect-observation' round.

    Input: a period state with the prior round data
    Ouptut: a new period state with the prior round data and the observations

    It schedules the EstimateConsensusRound.
    """

    round_id = "collect_observation"
    allowed_tx_type = ObservationPayload.transaction_type
    payload_attribute = "observation"

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        # if reached observation threshold, set the result
        if self.collection_threshold_reached:
            observations = [
                getattr(payload, self.payload_attribute)
                for payload in self.collection.values()
            ]
            estimate = aggregate(*observations)
            state = self.period_state.update(
                participant_to_observations=MappingProxyType(self.collection),
                estimate=estimate,
            )
            return state, Event.DONE
        return None


class EstimateConsensusRound(
    CollectSameUntilThresholdRound, PriceEstimationAbstractRound
):
    """
    This class represents the 'estimate_consensus' round.

    Input: a period state with the prior round data
    Ouptut: a new period state with the prior round data and the votes for each estimate

    It schedules the TxHashRound.
    """

    round_id = "estimate_consensus"
    allowed_tx_type = EstimatePayload.transaction_type
    payload_attribute = "estimate"

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            state = self.period_state.update(
                participant_to_estimate=MappingProxyType(self.collection),
                most_voted_estimate=self.most_voted_payload,
            )
            return state, Event.DONE
        if not self.is_majority_possible(
            self.collection, self.period_state.nb_participants
        ):
            return self._return_no_majority_event()
        return None


class TxHashRound(CollectSameUntilThresholdRound, PriceEstimationAbstractRound):
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
    CollectDifferentUntilThresholdRound, PriceEstimationAbstractRound
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


class FinalizationRound(OnlyKeeperSendsRound, PriceEstimationAbstractRound):
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


class RandomnessStartupRound(BaseRandomnessRound):
    """Randomness round for startup."""

    round_id = "randomness_startup"


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


class BaseResetRound(CollectSameUntilThresholdRound, PriceEstimationAbstractRound):
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


class PriceEstimationAbciApp(AbciApp[Event]):
    """Price estimation ABCI application."""

    initial_round_cls: Type[AbstractRound] = RegistrationRound
    transition_function: AbciAppTransitionFunction = {
        RegistrationRound: {
            Event.DONE: RandomnessStartupRound,
            Event.FAST_FORWARD: RandomnessRound,
        },
        RandomnessStartupRound: {
            Event.DONE: SelectKeeperAStartupRound,
            Event.ROUND_TIMEOUT: RandomnessStartupRound,  # if the round times out we restart
            Event.NO_MAJORITY: RandomnessStartupRound,  # we can have some agents on either side of an epoch, so we retry
        },
        SelectKeeperAStartupRound: {
            Event.DONE: DeploySafeRound,
            Event.ROUND_TIMEOUT: RegistrationRound,  # if the round times out we restart
            Event.NO_MAJORITY: RegistrationRound,  # if the round has no majority we restart
        },
        DeploySafeRound: {
            Event.DONE: ValidateSafeRound,
            Event.DEPLOY_TIMEOUT: SelectKeeperAStartupRound,  # if the round times out we try with a new keeper; TODO: what if the keeper does send the tx but doesn't share the hash? need to check for this! simple round timeout won't do here, need an intermediate step.
        },
        ValidateSafeRound: {
            Event.DONE: DeployOracleRound,
            Event.NEGATIVE: RegistrationRound,  # if the round does not reach a positive vote we restart
            Event.NONE: RegistrationRound,  # NOTE: unreachable
            Event.VALIDATE_TIMEOUT: RegistrationRound,  # the tx validation logic has its own timeout, this is just a safety check
            Event.NO_MAJORITY: RegistrationRound,  # if the round has no majority we restart
        },
        DeployOracleRound: {
            Event.DONE: ValidateOracleRound,
            Event.DEPLOY_TIMEOUT: SelectKeeperBStartupRound,  # if the round times out we try with a new keeper; TODO: what if the keeper does send the tx but doesn't share the hash? need to check for this! simple round timeout won't do here, need an intermediate step.
        },
        SelectKeeperBStartupRound: {
            Event.DONE: DeployOracleRound,
            Event.ROUND_TIMEOUT: RegistrationRound,  # if the round times out we restart
            Event.NO_MAJORITY: RegistrationRound,  # if the round has no majority we restart
        },
        ValidateOracleRound: {
            Event.DONE: RandomnessRound,
            Event.NEGATIVE: RegistrationRound,  # if the round does not reach a positive vote we restart
            Event.NONE: RegistrationRound,  # NOTE: unreachable
            Event.VALIDATE_TIMEOUT: RegistrationRound,  # the tx validation logic has its own timeout, this is just a safety check
            Event.NO_MAJORITY: RegistrationRound,  # if the round has no majority we restart
        },
        RandomnessRound: {
            Event.DONE: SelectKeeperARound,
            Event.ROUND_TIMEOUT: ResetRound,  # if the round times out we reset the period
            Event.NO_MAJORITY: RandomnessRound,  # we can have some agents on either side of an epoch, so we retry
        },
        SelectKeeperARound: {
            Event.DONE: CollectObservationRound,
            Event.ROUND_TIMEOUT: ResetRound,  # if the round times out we reset the period
            Event.NO_MAJORITY: ResetRound,  # if there is no majority we reset the period
        },
        CollectObservationRound: {
            Event.DONE: EstimateConsensusRound,
            Event.ROUND_TIMEOUT: ResetRound,  # if the round times out we reset the period
        },
        EstimateConsensusRound: {
            Event.DONE: TxHashRound,
            Event.ROUND_TIMEOUT: ResetRound,  # if the round times out we reset the period
            Event.NO_MAJORITY: ResetRound,  # if there is no majority we reset the period
        },
        TxHashRound: {
            Event.DONE: CollectSignatureRound,
            Event.NONE: ResetRound,  # if the agents cannot produce the hash we reset the period
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
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
        ResetAndPauseRound: {
            Event.DONE: RandomnessRound,
            Event.RESET_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
    }
    event_to_timeout: Dict[Event, float] = {
        Event.ROUND_TIMEOUT: 30.0,
        Event.VALIDATE_TIMEOUT: 30.0,
        Event.DEPLOY_TIMEOUT: 30.0,
        Event.RESET_TIMEOUT: 30.0,
    }
