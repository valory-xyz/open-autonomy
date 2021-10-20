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
from collections import Counter
from enum import Enum
from operator import itemgetter
from types import MappingProxyType
from typing import AbstractSet, Any
from typing import Counter as CounterType
from typing import (
    Dict,
    FrozenSet,
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

from packages.valory.skills.abstract_round_abci.base import (
    ABCIAppInternalError,
    AbciApp,
    AbciAppTransitionFunction,
    AbstractRound,
    BasePeriodState,
    BaseTxPayload,
    TransactionNotValidError,
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

    @classmethod
    def _sender_not_in_participants_error_message(
        cls, sender: str, participants: FrozenSet[str]
    ) -> str:
        """Get the error message for sender not in participants set."""
        return (
            f"sender {sender} is not in the set of participants: {sorted(participants)}"
        )

    @classmethod
    def _sender_already_sent_item(
        cls, sender: str, item_name: str, item_value: Any
    ) -> str:
        """Get the error message for sender already sent item."""
        return f"sender {sender} has already sent {item_name}: {item_value}"

    @classmethod
    def _sender_already_sent_signature(cls, sender: str, item_value: Any) -> str:
        """Get the error message for sender already sent signature."""
        return cls._sender_already_sent_item(sender, "its signature", item_value)

    @classmethod
    def _sender_already_sent_observation(cls, sender: str, item_value: Any) -> str:
        """Get the error message for sender already sent observation."""
        return cls._sender_already_sent_item(sender, "its observation", item_value)

    @classmethod
    def _sender_already_sent_estimate(cls, sender: str, item_value: Any) -> str:
        """Get the error message for sender already sent estimate."""
        return cls._sender_already_sent_item(sender, "the estimate", item_value)

    @classmethod
    def _sender_already_sent_selection(cls, sender: str, item_value: Any) -> str:
        """Get the error message for sender already sent selection."""
        return cls._sender_already_sent_item(sender, "the selection", item_value)

    @classmethod
    def _sender_already_sent_randomness(cls, sender: str, item_value: Any) -> str:
        """Get the error message for sender already sent randomness."""
        return cls._sender_already_sent_item(sender, "the randomness", item_value)

    @classmethod
    def _sender_already_sent_tx_hash(cls, sender: str, item_value: Any) -> str:
        """Get the error message for sender already sent the tx hash."""
        return cls._sender_already_sent_item(sender, "the tx hash", item_value)

    @classmethod
    def _sender_already_sent_vote(cls, sender: str, item_value: Any) -> str:
        """Get the error message for sender already sent its vote."""
        return cls._sender_already_sent_item(sender, "its vote", item_value)

    @classmethod
    def _sender_already_sent_contract_address(cls, sender: str, item_value: Any) -> str:
        """Get the error message for sender already sent the contract address."""
        return cls._sender_already_sent_item(sender, "the contract address", item_value)

    @classmethod
    def _sender_not_elected(cls, sender: str, elected_sender: str) -> str:
        """Get the error message for sender not being the elected sender."""
        return f"sender {sender} is not the elected sender: {elected_sender}"


class RegistrationRound(PriceEstimationAbstractRound):
    """
    This class represents the registration round.

    Input: None
    Output: a period state with the set of participants.

    It schedules the SelectKeeperARound.
    """

    # REFACTOR: collect-different-until-all

    round_id = "registration"
    allowed_tx_type = RegistrationPayload.transaction_type

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the registration round."""
        super().__init__(*args, **kwargs)

        # a collection of addresses
        self.participants: Set[str] = set()

    def process_payload(self, payload: RegistrationPayload) -> None:  # type: ignore
        """Handle a registration payload."""
        sender = payload.sender

        # we don't care if it was already there
        self.participants.add(sender)

    def check_payload(  # type: ignore  # pylint: disable=no-self-use
        self, _payload: RegistrationPayload
    ) -> None:
        """
        Check a registration payload can be applied to the current state.

        A registration can happen only when we are in the registration state.

        :param: _payload: the payload.
        """

    @property
    def registration_threshold_reached(self) -> bool:
        """Check that the registration threshold has been reached."""
        return len(self.participants) == self._consensus_params.max_participants

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        # if reached participant threshold, set the result
        if self.registration_threshold_reached:
            state = PeriodState(participants=self.participants)
            return state, Event.DONE
        return None


class RandomnessRound(PriceEstimationAbstractRound, ABC):
    """
    This class represents the randomness round.

    Input: a set of participants (addresses)
    Output: a set of participants (addresses) and randomness

    It schedules the SelectKeeperARound.
    """

    # REFACTOR: collect-same-until-threshold

    round_id = "randomness"
    allowed_tx_type = RandomnessPayload.transaction_type

    def __init__(self, *args: Any, **kwargs: Any):
        """Initialize the 'select-keeper' round."""
        super().__init__(*args, **kwargs)
        self.participant_to_randomness: Dict[str, RandomnessPayload] = {}

    def process_payload(self, payload: RandomnessPayload) -> None:  # type: ignore
        """Handle a 'randomness' payload."""
        sender = payload.sender
        if sender not in self.period_state.participants:
            raise ABCIAppInternalError(
                self._sender_not_in_participants_error_message(
                    sender, self.period_state.participants
                )
            )

        if sender in self.participant_to_randomness:
            raise ABCIAppInternalError(
                self._sender_already_sent_randomness(
                    sender,
                    self.participant_to_randomness[sender].randomness,
                )
            )

        self.participant_to_randomness[sender] = payload

    def check_payload(self, payload: RandomnessPayload) -> None:  # type: ignore
        """
        Check an randomness payload can be applied to the current state.

        An randomness transaction can be applied only if:
        - the round is in the 'randomness' state;
        - the sender belongs to the set of participants
        - the sender has not sent its selection yet

        :param: payload: the payload.
        """
        sender_in_participant_set = payload.sender in self.period_state.participants
        if not sender_in_participant_set:
            raise TransactionNotValidError(
                self._sender_not_in_participants_error_message(
                    payload.sender, self.period_state.participants
                )
            )

        sender_has_not_sent_randomness_yet = (
            payload.sender not in self.participant_to_randomness
        )
        if not sender_has_not_sent_randomness_yet:
            raise TransactionNotValidError(
                self._sender_already_sent_randomness(
                    payload.sender,
                    self.participant_to_randomness[payload.sender].randomness,
                )
            )

    @property
    def threshold_reached(self) -> bool:
        """Check that the threshold has been reached."""
        counter: CounterType = Counter()
        counter.update(
            payload.randomness for payload in self.participant_to_randomness.values()
        )
        # check that a single selection has at least the consensus # of votes
        consensus_n = self._consensus_params.consensus_threshold
        return any(count >= consensus_n for count in counter.values())

    @property
    def most_voted_randomness(self) -> float:
        """Get the most voted randomness."""
        counter = Counter()  # type: ignore
        counter.update(
            payload.randomness for payload in self.participant_to_randomness.values()
        )
        most_voted_randomness, max_votes = max(counter.items(), key=itemgetter(1))
        if max_votes < self._consensus_params.consensus_threshold:
            raise ABCIAppInternalError("not enough randomness")
        return most_voted_randomness

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            state = self.period_state.update(
                participant_to_randomness=MappingProxyType(
                    self.participant_to_randomness
                ),
                most_voted_randomness=self.most_voted_randomness,
            )
            return state, Event.DONE
        # TODO: threshold cannot be reached, Event.FAIL
        return None


class SelectKeeperRound(PriceEstimationAbstractRound, ABC):
    """
    This class represents the select keeper round.

    Input: a set of participants (addresses)
    Output: the selected keeper.
    """

    # REFACTOR: collect-same-until-threshold

    allowed_tx_type = SelectKeeperPayload.transaction_type

    def __init__(self, *args: Any, **kwargs: Any):
        """Initialize the 'select-keeper' round."""
        super().__init__(*args, **kwargs)
        self.participant_to_selection: Dict[str, SelectKeeperPayload] = {}

    def process_payload(self, payload: SelectKeeperPayload) -> None:  # type: ignore
        """Handle a 'select_keeper' payload."""
        sender = payload.sender
        if sender not in self.period_state.participants:
            raise ABCIAppInternalError(
                self._sender_not_in_participants_error_message(
                    sender, self.period_state.participants
                )
            )

        if sender in self.participant_to_selection:
            raise ABCIAppInternalError(
                self._sender_already_sent_selection(
                    sender,
                    self.participant_to_selection[sender].keeper,
                )
            )

        self.participant_to_selection[sender] = payload

    def check_payload(self, payload: SelectKeeperPayload) -> None:  # type: ignore
        """
        Check an select_keeper payload can be applied to the current state.

        An select_keeper transaction can be applied only if:
        - the round is in the 'select_keeper' state;
        - the sender belongs to the set of participants
        - the sender has not sent its selection yet

        :param: payload: the payload.
        """
        sender = payload.sender
        sender_in_participant_set = sender in self.period_state.participants
        if not sender_in_participant_set:
            raise TransactionNotValidError(
                self._sender_not_in_participants_error_message(
                    sender, self.period_state.participants
                )
            )

        sender_has_not_sent_selection_yet = sender not in self.participant_to_selection
        if not sender_has_not_sent_selection_yet:
            raise TransactionNotValidError(
                self._sender_already_sent_selection(
                    sender,
                    self.participant_to_selection[sender].keeper,
                )
            )

    @property
    def selection_threshold_reached(self) -> bool:
        """Check that the selection threshold has been reached."""
        selections_counter: CounterType = Counter()
        selections_counter.update(
            payload.keeper for payload in self.participant_to_selection.values()
        )
        # check that a single selection has at least the consensus # of votes
        consensus_n = self._consensus_params.consensus_threshold
        return any(count >= consensus_n for count in selections_counter.values())

    @property
    def most_voted_keeper_address(self) -> float:
        """Get the most voted keeper."""
        keepers_counter = Counter()  # type: ignore
        keepers_counter.update(
            payload.keeper for payload in self.participant_to_selection.values()
        )
        most_voted_keeper_address, max_votes = max(
            keepers_counter.items(), key=itemgetter(1)
        )
        if max_votes < self._consensus_params.consensus_threshold:
            raise ABCIAppInternalError("keeper has not enough votes")
        return most_voted_keeper_address

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        if self.selection_threshold_reached:
            state = self.period_state.update(
                participant_to_selection=MappingProxyType(
                    self.participant_to_selection
                ),
                most_voted_keeper_address=self.most_voted_keeper_address,
            )
            return state, Event.DONE
        # TODO: threshold cannot be reached, Event.FAIL
        return None


class DeploySafeRound(PriceEstimationAbstractRound):
    """
    This class represents the deploy Safe round.

    Input: a set of participants (addresses) and a keeper
    Output: a period state with the set of participants, the keeper and the Safe contract address.

    It schedules the ValidateSafeRound.
    """

    # REFACTOR: keeper-only-sends

    round_id = "deploy_safe"
    allowed_tx_type = DeploySafePayload.transaction_type

    def __init__(self, *args: Any, **kwargs: Any):
        """Initialize the 'collect-observation' round."""
        super().__init__(*args, **kwargs)
        self._contract_address: Optional[str] = None

    def process_payload(self, payload: DeploySafePayload) -> None:  # type: ignore
        """Handle a deploy safe payload."""
        sender = payload.sender

        if sender not in self.period_state.participants:
            raise ABCIAppInternalError(
                self._sender_not_in_participants_error_message(
                    sender, self.period_state.participants
                )
            )

        if sender != self.period_state.most_voted_keeper_address:
            raise ABCIAppInternalError(
                self._sender_not_elected(
                    sender, self.period_state.most_voted_keeper_address
                )
            )

        if self._contract_address is not None:
            raise ABCIAppInternalError(
                self._sender_already_sent_contract_address(
                    sender, self._contract_address
                )
            )

        self._contract_address = payload.safe_contract_address

    def check_payload(self, payload: DeploySafePayload) -> None:  # type: ignore
        """
        Check a deploy safe payload can be applied to the current state.

        A deploy safe transaction can be applied only if:
        - the sender belongs to the set of participants
        - the sender is the elected sender
        - the sender has not already sent the contract address

        :param: payload: the payload.
        """
        sender = payload.sender
        sender_in_participant_set = sender in self.period_state.participants
        if not sender_in_participant_set:
            raise TransactionNotValidError(
                self._sender_not_in_participants_error_message(
                    sender, self.period_state.participants
                )
            )

        sender_is_elected_sender = sender == self.period_state.most_voted_keeper_address
        if not sender_is_elected_sender:
            raise TransactionNotValidError(
                self._sender_not_elected(
                    sender, self.period_state.most_voted_keeper_address
                )
            )

        contract_address_not_set_yet = self._contract_address is None
        if not contract_address_not_set_yet:
            raise TransactionNotValidError(
                self._sender_already_sent_contract_address(
                    sender, self._contract_address
                )
            )

    @property
    def is_contract_set(self) -> bool:
        """Check that the contract has been set."""
        return self._contract_address is not None

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        # if reached participant threshold, set the result
        if self.is_contract_set:
            state = self.period_state.update(
                safe_contract_address=self._contract_address
            )
            return state, Event.DONE
        return None


class ValidateRound(PriceEstimationAbstractRound, ABC):
    """
    This class represents the validate round.

    Input: a period state with the set of participants, the keeper and the Safe contract address.
    Output: a period state with the set of participants, the keeper, the Safe contract address and a validation of the Safe contract address.
    """

    # REFACTOR: voting-round

    allowed_tx_type = ValidatePayload.transaction_type
    exit_event: Event

    def __init__(self, *args: Any, **kwargs: Any):
        """Initialize the 'collect-observation' round."""
        super().__init__(*args, **kwargs)
        self.participant_to_votes: Dict[str, ValidatePayload] = {}

    def process_payload(self, payload: ValidatePayload) -> None:  # type: ignore
        """Handle a validate safe payload."""
        sender = payload.sender

        if sender not in self.period_state.participants:
            raise TransactionNotValidError(
                self._sender_not_in_participants_error_message(
                    sender, self.period_state.participants
                )
            )

        if sender in self.participant_to_votes:
            raise ABCIAppInternalError(
                self._sender_already_sent_vote(
                    sender,
                    self.participant_to_votes[sender].vote,
                )
            )

        self.participant_to_votes[sender] = payload

    def check_payload(self, payload: ValidatePayload) -> None:  # type: ignore
        """
        Check a validate payload can be applied to the current state.

        A validate transaction can be applied only if:
        - the sender belongs to the set of participants
        - the sender has not already submitted the transaction

        :param: payload: the payload.
        """
        sender = payload.sender
        sender_in_participant_set = sender in self.period_state.participants
        if not sender_in_participant_set:
            raise TransactionNotValidError(
                self._sender_not_in_participants_error_message(
                    sender, self.period_state.participants
                )
            )

        sender_has_not_sent_vote_yet = sender not in self.participant_to_votes
        if not sender_has_not_sent_vote_yet:
            raise TransactionNotValidError(
                self._sender_already_sent_vote(
                    sender,
                    str(self.participant_to_votes[sender].vote),
                )
            )

    @property
    def positive_vote_threshold_reached(self) -> bool:
        """Check that the vote threshold has been reached."""
        true_votes = sum(
            [payload.vote for payload in self.participant_to_votes.values()]
        )
        # check that "true" has at least the consensus # of votes
        consensus_threshold = self._consensus_params.consensus_threshold
        return true_votes >= consensus_threshold

    @property
    def negative_vote_threshold_reached(self) -> bool:
        """Check that the vote threshold has been reached."""
        false_votes = len(self.participant_to_votes) - sum(
            [payload.vote for payload in self.participant_to_votes.values()]
        )
        # check that "false" has at least the consensus # of votes
        consensus_threshold = self._consensus_params.consensus_threshold
        return false_votes >= consensus_threshold

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        # if reached participant threshold, set the result
        if self.positive_vote_threshold_reached:
            state = self.period_state.update(
                participant_to_votes=MappingProxyType(self.participant_to_votes)
            )
            return state, Event.DONE
        if self.negative_vote_threshold_reached:
            state = self.period_state.update()
            return state, self.exit_event
        # TODO: no threshold can be reached, Event.FAIL
        return None


class CollectObservationRound(PriceEstimationAbstractRound):
    """
    This class represents the 'collect-observation' round.

    Input: a period state with the prior round data
    Ouptut: a new period state with the prior round data and the observations

    It schedules the EstimateConsensusRound.
    """

    # REFACTOR: collect-different-until-threshold

    round_id = "collect_observation"
    allowed_tx_type = ObservationPayload.transaction_type

    def __init__(self, *args: Any, **kwargs: Any):
        """Initialize the 'collect-observation' round."""
        super().__init__(*args, **kwargs)
        self.participant_to_observations: Dict[str, ObservationPayload] = {}

    def process_payload(self, payload: ObservationPayload) -> None:  # type: ignore
        """Handle an 'observation' payload."""
        sender = payload.sender
        if sender not in self.period_state.participants:
            raise ABCIAppInternalError(
                self._sender_not_in_participants_error_message(
                    sender, self.period_state.participants
                )
            )

        if sender in self.participant_to_observations:
            raise ABCIAppInternalError(
                self._sender_already_sent_observation(
                    sender,
                    self.participant_to_observations[sender].observation,
                )
            )

        self.participant_to_observations[sender] = payload

    def check_payload(self, payload: ObservationPayload) -> None:  # type: ignore
        """
        Check an observation payload can be applied to the current state.

        An observation transaction can be applied only if:
        - the sender belongs to the set of participants
        - the sender has not already sent its observation

        :param: payload: the payload.
        """
        sender = payload.sender
        sender_in_participant_set = sender in self.period_state.participants
        if not sender_in_participant_set:
            raise TransactionNotValidError(
                self._sender_not_in_participants_error_message(
                    sender, self.period_state.participants
                )
            )

        sender_has_not_sent_observation_yet = (
            sender not in self.participant_to_observations
        )
        if not sender_has_not_sent_observation_yet:
            raise TransactionNotValidError(
                self._sender_already_sent_observation(
                    sender,
                    self.participant_to_observations[sender].observation,
                )
            )

    @property
    def observation_threshold_reached(self) -> bool:
        """Check that the observation threshold has been reached."""
        return (
            len(self.participant_to_observations)
            >= self._consensus_params.consensus_threshold
        )

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        # if reached observation threshold, set the result
        if self.observation_threshold_reached:
            observations = [
                payload.observation
                for payload in self.participant_to_observations.values()
            ]
            estimate = aggregate(*observations)
            state = self.period_state.update(
                participant_to_observations=MappingProxyType(
                    self.participant_to_observations
                ),
                estimate=estimate,
            )
            return state, Event.DONE
        return None


class EstimateConsensusRound(PriceEstimationAbstractRound):
    """
    This class represents the 'estimate_consensus' round.

    Input: a period state with the prior round data
    Ouptut: a new period state with the prior round data and the votes for each estimate

    It schedules the TxHashRound.
    """

    # REFACTOR: collect-same-until-threshold

    round_id = "estimate_consensus"
    allowed_tx_type = EstimatePayload.transaction_type

    def __init__(self, *args: Any, **kwargs: Any):
        """Initialize the 'estimate consensus' round."""
        super().__init__(*args, **kwargs)
        self.participant_to_estimate: Dict[str, EstimatePayload] = {}

    def process_payload(self, payload: EstimatePayload) -> None:  # type: ignore
        """Handle an 'estimate' payload."""
        sender = payload.sender
        if sender not in self.period_state.participants:
            raise ABCIAppInternalError(
                self._sender_not_in_participants_error_message(
                    sender, self.period_state.participants
                )
            )

        if sender in self.participant_to_estimate:
            raise ABCIAppInternalError(
                self._sender_already_sent_estimate(
                    sender,
                    self.participant_to_estimate[sender].estimate,
                )
            )

        self.participant_to_estimate[sender] = payload

    def check_payload(self, payload: EstimatePayload) -> None:  # type: ignore
        """
        Check an estimate payload can be applied to the current state.

        An estimate transaction can be applied only if:
        - the round is in the 'estimate_consensus' state;
        - the sender belongs to the set of participants
        - the sender has not sent its estimate yet
        :param: payload: the payload.
        """
        sender = payload.sender
        sender_in_participant_set = sender in self.period_state.participants
        if not sender_in_participant_set:
            raise TransactionNotValidError(
                self._sender_not_in_participants_error_message(
                    sender, self.period_state.participants
                )
            )

        sender_has_not_sent_estimate_yet = sender not in self.participant_to_estimate
        if not sender_has_not_sent_estimate_yet:
            raise TransactionNotValidError(
                self._sender_already_sent_estimate(
                    sender,
                    self.participant_to_estimate[sender].estimate,
                )
            )

    @property
    def estimate_threshold_reached(self) -> bool:
        """Check that the estimate threshold has been reached."""
        estimates_counter: CounterType = Counter()
        estimates_counter.update(
            payload.estimate for payload in self.participant_to_estimate.values()
        )
        # check that a single estimate has at least the consensu # of votes
        consensus_threshold = self._consensus_params.consensus_threshold
        return any(count >= consensus_threshold for count in estimates_counter.values())

    @property
    def most_voted_estimate(self) -> float:
        """Get the most voted estimate."""
        estimates_counter = Counter()  # type: ignore
        estimates_counter.update(
            payload.estimate for payload in self.participant_to_estimate.values()
        )
        most_voted_estimate, max_votes = max(
            estimates_counter.items(), key=itemgetter(1)
        )
        if max_votes < self._consensus_params.consensus_threshold:
            raise ABCIAppInternalError("estimate has not enough votes")
        return most_voted_estimate

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        if self.estimate_threshold_reached:
            state = self.period_state.update(
                participant_to_estimate=MappingProxyType(self.participant_to_estimate),
                most_voted_estimate=self.most_voted_estimate,
            )
            return state, Event.DONE
        # TODO: if threshold can no longer be reached, Event.FAIL
        return None


class TxHashRound(PriceEstimationAbstractRound):
    """
    This class represents the 'tx-hash' round.

    Input: a period state with the prior round data
    Ouptut: a new period state with the prior round data and the votes for each tx hash

    It schedules the CollectSignatureRound.
    """

    # REFACTOR: collect-same-until-threshold

    round_id = "tx_hash"
    allowed_tx_type = TransactionHashPayload.transaction_type

    def __init__(self, *args: Any, **kwargs: Any):
        """Initialize the 'collect-signature' round."""
        super().__init__(*args, **kwargs)
        self.participant_to_tx_hash: Dict[str, TransactionHashPayload] = {}

    def process_payload(self, payload: TransactionHashPayload) -> None:  # type: ignore
        """Handle a 'tx_hash' payload."""
        sender = payload.sender
        if sender not in self.period_state.participants:
            raise ABCIAppInternalError(
                self._sender_not_in_participants_error_message(
                    sender, self.period_state.participants
                )
            )

        if sender in self.participant_to_tx_hash:
            raise ABCIAppInternalError(
                self._sender_already_sent_tx_hash(
                    sender,
                    self.participant_to_tx_hash[sender].tx_hash,
                )
            )

        self.participant_to_tx_hash[sender] = payload

    def check_payload(self, payload: TransactionHashPayload) -> None:  # type: ignore
        """
        Check a signature payload can be applied to the current state.

        This can happen only if:
        - the round is in the 'tx_hash' state;
        - the sender belongs to the set of participants
        - the sender has not sent the tx_hash yet

        :param payload: the payload to check
        """
        sender = payload.sender
        sender_in_participant_set = sender in self.period_state.participants
        if not sender_in_participant_set:
            raise TransactionNotValidError(
                self._sender_not_in_participants_error_message(
                    sender, self.period_state.participants
                )
            )
        sender_has_not_sent_tx_hash_yet = sender not in self.participant_to_tx_hash
        if not sender_has_not_sent_tx_hash_yet:
            raise TransactionNotValidError(
                self._sender_already_sent_tx_hash(
                    sender,
                    self.participant_to_tx_hash[sender].tx_hash,
                )
            )

    @property
    def tx_threshold_reached(self) -> bool:
        """Check that the tx threshold has been reached."""
        tx_counter: CounterType = Counter()
        tx_counter.update(
            payload.tx_hash for payload in self.participant_to_tx_hash.values()
        )
        # check that a single estimate has at least the consensus # of votes
        consensus_threshold = self._consensus_params.consensus_threshold
        return any(count >= consensus_threshold for count in tx_counter.values())

    @property
    def most_voted_tx_hash(self) -> str:
        """Get the most voted tx hash."""
        tx_counter = Counter()  # type: ignore
        tx_counter.update(
            payload.tx_hash for payload in self.participant_to_tx_hash.values()
        )
        most_voted_tx_hash, max_votes = max(tx_counter.items(), key=itemgetter(1))
        if max_votes < self._consensus_params.consensus_threshold:
            raise ABCIAppInternalError("tx hash has not enough votes")
        return most_voted_tx_hash

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        if self.tx_threshold_reached:
            state = self.period_state.update(
                participant_to_tx_hash=MappingProxyType(self.participant_to_tx_hash),
                most_voted_tx_hash=self.most_voted_tx_hash,
            )
            return state, Event.DONE
        # TODO: if threshold can no longer be reached, Event.FAIL
        return None


class CollectSignatureRound(PriceEstimationAbstractRound):
    """
    This class represents the 'collect-signature' round.

    Input: a period state with the prior round data
    Ouptut: a new period state with the prior round data and the signatures

    It schedules the FinalizationRound.
    """

    # REFACTOR: collect-different-until-threshold

    round_id = "collect_signature"
    allowed_tx_type = SignaturePayload.transaction_type

    def __init__(self, *args: Any, **kwargs: Any):
        """Initialize the 'collect-signature' round."""
        super().__init__(*args, **kwargs)
        self.signatures_by_participant: Dict[str, str] = {}

    def process_payload(self, payload: SignaturePayload) -> None:  # type: ignore
        """Handle a 'signature' payload."""
        sender = payload.sender
        if sender not in self.period_state.participants:
            raise ABCIAppInternalError(
                self._sender_not_in_participants_error_message(
                    sender, self.period_state.participants
                )
            )

        if sender in self.signatures_by_participant:
            raise ABCIAppInternalError(
                self._sender_already_sent_signature(
                    sender,
                    self.signatures_by_participant[sender],
                )
            )

        self.signatures_by_participant[sender] = payload.signature

    def check_payload(self, payload: SignaturePayload) -> None:  # type: ignore
        """
        Check a signature payload can be applied to the current state.

        A signature transaction can be applied only if:
        - the round is in the 'collect-signature' state;
        - the sender belongs to the set of participants
        - the sender has not sent its signature yet

        :param: payload: the payload.
        """
        sender = payload.sender
        sender_in_participant_set = sender in self.period_state.participants
        if not sender_in_participant_set:
            raise TransactionNotValidError(
                self._sender_not_in_participants_error_message(
                    sender, self.period_state.participants
                )
            )

        sender_has_not_sent_signature_yet = sender not in self.signatures_by_participant
        if not sender_has_not_sent_signature_yet:
            raise TransactionNotValidError(
                self._sender_already_sent_signature(
                    sender,
                    self.signatures_by_participant[sender],
                )
            )

    @property
    def signature_threshold_reached(self) -> bool:
        """Check that the signature threshold has been reached."""
        consensus_threshold = self._consensus_params.consensus_threshold
        return len(self.signatures_by_participant) >= consensus_threshold

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        if self.signature_threshold_reached:
            state = self.period_state.update(
                participant_to_signature=MappingProxyType(
                    self.signatures_by_participant
                ),
            )
            return state, Event.DONE
        return None


class FinalizationRound(PriceEstimationAbstractRound):
    """
    This class represents the finalization Safe round.

    Input: a period state with the prior round data
    Output: a new period state with the prior round data and the hash of the Safe transaction

    It schedules the ValidateTransactionRound.
    """

    round_id = "finalization"
    allowed_tx_type = FinalizationTxPayload.transaction_type

    # REFACTOR: keeper-only-sends

    def __init__(self, *args: Any, **kwargs: Any):
        """Initialize the 'finalization' round."""
        super().__init__(*args, **kwargs)
        self._tx_hash: Optional[str] = None

    def process_payload(self, payload: FinalizationTxPayload) -> None:  # type: ignore
        """Handle a finalization payload."""
        sender = payload.sender

        if sender not in self.period_state.participants:
            raise ABCIAppInternalError(
                self._sender_not_in_participants_error_message(
                    sender, self.period_state.participants
                )
            )

        if sender != self.period_state.most_voted_keeper_address:
            raise ABCIAppInternalError(
                self._sender_not_elected(
                    sender, self.period_state.most_voted_keeper_address
                )
            )

        if self._tx_hash is not None:
            raise ABCIAppInternalError(
                self._sender_already_sent_tx_hash(sender, self._tx_hash)
            )

        self._tx_hash = payload.tx_hash

    def check_payload(self, payload: FinalizationTxPayload) -> None:  # type: ignore
        """
        Check a finalization payload can be applied to the current state.

        A finalization transaction can be applied only if:
        - the sender belongs to the set of participants
        - the sender is the elected sender
        - the sender has not already sent the transaction hash

        :param: payload: the payload.
        """
        sender = payload.sender
        sender_in_participant_set = sender in self.period_state.participants
        if not sender_in_participant_set:
            raise TransactionNotValidError(
                self._sender_not_in_participants_error_message(
                    sender, self.period_state.participants
                )
            )
        sender_is_elected_sender = sender == self.period_state.most_voted_keeper_address
        if not sender_is_elected_sender:
            raise TransactionNotValidError(
                self._sender_not_elected(
                    sender, self.period_state.most_voted_keeper_address
                )
            )
        tx_hash_not_set_yet = self._tx_hash is None
        if not tx_hash_not_set_yet:
            raise TransactionNotValidError(
                self._sender_already_sent_tx_hash(sender, self._tx_hash)
            )

    @property
    def tx_hash_set(self) -> bool:
        """Check that the tx hash has been set."""
        return self._tx_hash is not None

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        # if reached participant threshold, set the result
        if self.tx_hash_set:
            state = self.period_state.update(final_tx_hash=self._tx_hash)
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
            Event.FAIL: RegistrationRound,
        },
        SelectKeeperARound: {
            Event.DONE: DeploySafeRound,
            Event.FAIL: RegistrationRound,
        },
        DeploySafeRound: {
            Event.DONE: ValidateSafeRound,
            Event.EXIT: SelectKeeperARound,
        },
        ValidateSafeRound: {
            Event.DONE: CollectObservationRound,
            Event.EXIT: DeploySafeRound,
            Event.FAIL: RegistrationRound,
        },
        CollectObservationRound: {
            Event.DONE: EstimateConsensusRound,
        },
        EstimateConsensusRound: {
            Event.DONE: TxHashRound,
            Event.FAIL: RegistrationRound,
        },
        TxHashRound: {
            Event.DONE: CollectSignatureRound,
            Event.FAIL: RegistrationRound,
        },
        CollectSignatureRound: {Event.DONE: FinalizationRound},
        FinalizationRound: {
            Event.DONE: ValidateTransactionRound,
            Event.EXIT: SelectKeeperBRound,
        },
        ValidateTransactionRound: {
            Event.DONE: ConsensusReachedRound,
            Event.EXIT: FinalizationRound,
            Event.FAIL: RegistrationRound,
        },
        SelectKeeperBRound: {
            Event.DONE: FinalizationRound,
            Event.FAIL: RegistrationRound,
        },
    }
    event_to_timeout: Dict[Event, float] = {
        Event.EXIT: 5.0,
        Event.FAIL: 5.0,
        Event.RETRY_TIMEOUT: 10.0,  # TODO: incorporate in mappings
        Event.ROUND_TIMEOUT: 30.0,  # TODO: incorporate in mappings
    }
