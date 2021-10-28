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
    ABCIAppInternalError,
    AbciApp,
    AbciAppTransitionFunction,
    AbstractRound,
    BasePeriodState,
    BaseTxPayload,
    CollectDifferentUntilAllRound,
    CollectDifferentUntilThresholdRound,
    CollectSameUntilThresholdRound,
    OnlyKeeperSendsRound,
    TransactionNotValidError,
    VotingRound,
)
from packages.valory.skills.price_estimation_abci.payloads import (
    DeploySafePayload,
    EstimatePayload,
    FinalizationTxPayload,
    ObservationPayload,
    RandomnessPayload,
    RegistrationPayload,
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
    EXIT = "exit"
    RETRY_TIMEOUT = "retry_timeout"
    ROUND_TIMEOUT = "round_timeout"
    NO_MAJORITY = "no_majority"


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
        participant_to_randomness: Optional[Mapping[str, RandomnessPayload]] = None,
        most_voted_randomness: Optional[str] = None,
        participant_to_selection: Optional[Mapping[str, SelectKeeperPayload]] = None,
        most_voted_keeper_address: Optional[str] = None,
        safe_contract_address: Optional[str] = None,
        participant_to_votes: Optional[Mapping[str, ValidatePayload]] = None,
        participant_to_observations: Optional[Mapping[str, ObservationPayload]] = None,
        participant_to_estimate: Optional[Mapping[str, EstimatePayload]] = None,
        estimate: Optional[float] = None,
        most_voted_estimate: Optional[float] = None,
        participant_to_tx_hash: Optional[Mapping[str, TransactionHashPayload]] = None,
        most_voted_tx_hash: Optional[str] = None,
        participant_to_signature: Optional[Mapping[str, str]] = None,
        final_tx_hash: Optional[str] = None,
    ) -> None:
        """Initialize a period state."""
        super().__init__(participants=participants)
        self._participant_to_randomness = participant_to_randomness
        self._most_voted_randomness = most_voted_randomness
        self._most_voted_keeper_address = most_voted_keeper_address
        self._safe_contract_address = safe_contract_address
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
    def participant_to_signature(self) -> Mapping[str, str]:
        """Get the participant_to_signature."""
        enforce(
            self._participant_to_signature is not None,
            "'participant_to_signature' field is None",
        )
        return cast(Mapping[str, str], self._participant_to_signature)

    @property
    def final_tx_hash(self) -> str:
        """Get the final_tx_hash."""
        enforce(
            self._final_tx_hash is not None,
            "'final_tx_hash' field is None",
        )
        return cast(str, self._final_tx_hash)

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
        # if reached participant threshold, set the result
        if self.collection_threshold_reached:
            state = PeriodState(participants=self.collection)
            return state, Event.DONE
        return None


class RandomnessRound(CollectSameUntilThresholdRound, PriceEstimationAbstractRound):
    """
    This class represents the randomness round.

    Input: a set of participants (addresses)
    Output: a set of participants (addresses) and randomness

    It schedules the SelectKeeperARound.
    """

    round_id = "randomness"
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


class ValidateRound(VotingRound, PriceEstimationAbstractRound):
    """
    This class represents the validate round.

    Input: a period state with the set of participants, the keeper and the Safe contract address.
    Output: a period state with the set of participants, the keeper, the Safe contract address and a validation of the Safe contract address.
    """

    allowed_tx_type = ValidatePayload.transaction_type
    exit_event: Event
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
            return state, self.exit_event
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
        if self.threshold_reached:
            state = self.period_state.update(
                participant_to_tx_hash=MappingProxyType(self.collection),
                most_voted_tx_hash=self.most_voted_payload,
            )
            return state, Event.DONE
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
        # if reached participant threshold, set the result
        if self.has_keeper_sent_payload:
            state = self.period_state.update(final_tx_hash=self.keeper_payload)
            return state, Event.DONE
        return None


class SelectKeeperARound(SelectKeeperRound):
    """This class represents the select keeper A round."""

    round_id = "select_keeper_a"


class SelectKeeperBRound(SelectKeeperRound):
    """This class represents the select keeper B round."""

    round_id = "select_keeper_b"


class ConsensusReachedRound(PriceEstimationAbstractRound):
    """This class represents the 'consensus-reached' round (the final round)."""

    round_id = "consensus_reached"
    allowed_tx_type = None

    def process_payload(self, payload: BaseTxPayload) -> None:  # type: ignore
        """Process the payload."""
        raise ABCIAppInternalError("this round does not accept transactions")

    def check_payload(self, payload: BaseTxPayload) -> None:  # type: ignore
        """Check the payload"""
        raise TransactionNotValidError("this round does not accept transactions")

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        return None


class ValidateSafeRound(ValidateRound):
    """
    This class represents the validate Safe round.

    Input: a period state with the prior round data
    Output: a new period state with the prior round data and the validation of the contract address

    It schedules the CollectObservationRound or SelectKeeperARound.
    """

    round_id = "validate_safe"
    exit_event = Event.EXIT


class ValidateTransactionRound(ValidateRound):
    """
    This class represents the validate transaction round.

    Input: a period state with the prior round data
    Output: a new period state with the prior round data and the validation of the transaction

    It schedules the ConsensusReachedRound or SelectKeeperARound.
    """

    round_id = "validate_transaction"
    exit_event = Event.EXIT


class PriceEstimationAbciApp(AbciApp[Event]):
    """Price estimation ABCI application."""

    initial_round_cls: Type[AbstractRound] = RegistrationRound
    transition_function: AbciAppTransitionFunction = {
        RegistrationRound: {Event.DONE: RandomnessRound},
        RandomnessRound: {
            Event.DONE: SelectKeeperARound,
            Event.ROUND_TIMEOUT: RegistrationRound,
        },
        SelectKeeperARound: {
            Event.DONE: DeploySafeRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
        },
        DeploySafeRound: {
            Event.DONE: ValidateSafeRound,
            Event.EXIT: SelectKeeperARound,
        },
        ValidateSafeRound: {
            Event.DONE: CollectObservationRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
        },
        CollectObservationRound: {
            Event.DONE: EstimateConsensusRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
        },
        EstimateConsensusRound: {
            Event.DONE: TxHashRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
        },
        TxHashRound: {
            Event.DONE: CollectSignatureRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
        },
        CollectSignatureRound: {
            Event.DONE: FinalizationRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
        },
        FinalizationRound: {
            Event.DONE: ValidateTransactionRound,
            Event.EXIT: SelectKeeperBRound,
        },
        ValidateTransactionRound: {
            Event.DONE: ConsensusReachedRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
        },
        SelectKeeperBRound: {
            Event.DONE: FinalizationRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
        },
    }
    event_to_timeout: Dict[Event, float] = {
        Event.EXIT: 5.0,
        Event.RETRY_TIMEOUT: 10.0,
        Event.ROUND_TIMEOUT: 30.0,
    }
