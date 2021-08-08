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
import pickle  # nosec
from abc import ABC
from collections import Counter
from enum import Enum
from operator import itemgetter
from typing import Callable, Dict, List, Optional, Sequence, Set, Tuple, cast

from aea.exceptions import enforce
from eth_account import Account
from eth_account.messages import encode_defunct

from packages.valory.protocols.abci.custom_types import Header

# ABCI response code
from packages.valory.skills.price_estimation_abci.params import ConsensusParams


OK_CODE = 0
ERROR_CODE = 1


class RoundStateType(Enum):
    """Enumeration of all the possible round state types."""

    REGISTRATION = "registration"
    COLLECT_OBSERVATIONS = "collect_observation"
    CONSENSUS = "consensus"
    CONSENSUS_REACHED = "consensus_reached"


class TransactionType(Enum):
    """Enumeration of transaction types."""

    REGISTRATION = "registration"
    OBSERVATION = "observation"
    ESTIMATE = "estimate"


class BaseTxPayload(ABC):
    """This class represents a transaction payload."""

    def __init__(self, transaction_type: TransactionType, sender: str) -> None:
        """
        Initialize a transaction payload.

        :param transaction_type: the transaction type.
        :param sender: the sender (Ethereum) address
        """
        self.transaction_type = transaction_type
        self.sender = sender

    def encode(self) -> bytes:
        """Encode the payload."""
        return pickle.dumps(self)  # nosec

    @classmethod
    def decode(cls, obj: bytes) -> "BaseTxPayload":
        """Decode the payload."""
        return pickle.loads(obj)  # nosec


class RegistrationPayload(BaseTxPayload):
    """Represent a transaction payload of type 'registration'."""

    def __init__(self, sender: str) -> None:
        """
        Initialize a 'registration' transaction payload.

        :param sender: the sender (Ethereum) address
        """
        super().__init__(TransactionType.REGISTRATION, sender)


class ObservationPayload(BaseTxPayload):
    """Represent a transaction payload of type 'observation'."""

    def __init__(self, sender: str, observation: float) -> None:
        """Initialize an 'observation' transaction payload.

        :param sender: the sender (Ethereum) address
        :param observation: the observation
        """
        super().__init__(TransactionType.OBSERVATION, sender)
        self._observation = observation

    @property
    def observation(self) -> float:
        """Get the observation."""
        return self._observation


class EstimatePayload(BaseTxPayload):
    """Represent a transaction payload of type 'estimate'."""

    def __init__(self, sender: str, estimate: float) -> None:
        """Initialize an 'estimate' transaction payload.

        :param sender: the sender (Ethereum) address
        :param estimate: the estimate
        """
        super().__init__(TransactionType.ESTIMATE, sender)
        self._estimate = estimate

    @property
    def estimate(self) -> float:
        """Get the estimate."""
        return self._estimate


class Transaction(ABC):
    """Class to represent a transaction."""

    def __init__(self, payload: BaseTxPayload, signature: str) -> None:
        """Initialize a transaction object."""
        self.payload = payload
        self.signature = signature

    def encode(self) -> bytes:
        """Encode the transaction."""
        return pickle.dumps(self)  # nosec

    @classmethod
    def decode(cls, obj: bytes) -> "Transaction":
        """Decode the transaction."""
        transaction_obj = pickle.loads(obj)  # nosec
        enforce(
            isinstance(transaction_obj, Transaction), "not an instance of 'Transaction'"
        )
        transaction_obj = cast(Transaction, transaction_obj)
        return transaction_obj

    def verify(self) -> None:
        """Verify the signature is correct."""
        payload_bytes = self.payload.encode()
        encoded_payload_bytes = encode_defunct(payload_bytes)
        public_key = Account.recover_message(
            encoded_payload_bytes, signature=self.signature
        )
        if public_key != self.payload.sender:
            raise ValueError("signature not valid.")


class Block:
    """Class to represent (a subset of) data of a Tendermint block."""

    def __init__(
        self,
        header: Header,
        transactions: Sequence[Transaction],
        valid_txs: Sequence[bool],
    ) -> None:
        """Initialize the block."""
        self.header = header
        self._transactions: Tuple[Transaction, ...] = tuple(transactions)

        # remember which transaction are invalid.
        # this can happen as check_tx is run independently
        # with other transactions. The final validity
        # can only be checked when actually executing the
        # transactions in the order that they occur in the block.
        self._valid_txs: Tuple[bool, ...] = tuple(valid_txs)

    @property
    def transactions(self) -> Tuple[Transaction, ...]:
        """Get the transactions."""
        return self._transactions

    @property
    def valid_transactions(self) -> Tuple[bool, ...]:
        """Get the bit-array to check whether a transaction is valid."""
        return self._valid_txs


class Blockchain:
    """
    Class to represent a (naive) Tendermint blockchain.

    The consistency of the data in the blocks is guaranteed by Tendermint.
    """

    def __init__(self) -> None:
        """Initialize the blockchain."""
        self._blocks: List[Block] = []

    def add_block(self, block: Block) -> None:
        """Add a block to the list."""
        expected_height = self.height
        actual_height = block.header.height
        if expected_height != actual_height:
            raise ValueError(f"expected height {expected_height}, got {actual_height}")
        self._blocks.append(block)

    @property
    def height(self) -> int:
        """Get the height."""
        return self.length + 1

    @property
    def length(self) -> int:
        """Get the blockchain length."""
        return len(self._blocks)

    def get_block(self, height: int) -> Block:
        """Get the ith block."""
        if not self.length > height >= 0:
            raise ValueError(
                f"height {height} not valid, must be between {self.length} and 0"
            )
        return self._blocks[height]


class RoundState:
    """
    Class to represent a round state.

    It allows to:
    - check whether a transaction is consistent wrt the current state
      and it is considered valid;
    - add a transaction to update the current state (if valid)
    """

    def __init__(self, consensus_params: ConsensusParams):
        """Initialize the round state."""
        self._consensus_params = consensus_params

        self._type = RoundStateType.REGISTRATION

        # a collection of addresses
        self.participants: Set[str] = set()

        self.participant_to_observations: Dict[str, ObservationPayload] = {}
        self.participant_to_estimate: Dict[str, EstimatePayload] = {}

    @property
    def registration_threshold_reached(self) -> bool:
        """Check that the registration threshold has been reached."""
        return len(self.participants) == self._consensus_params.max_participants

    @property
    def observation_threshold_reached(self) -> bool:
        """Check that the observation threshold has been reached."""
        return (
            len(self.participants) > 0
            and set(self.participant_to_observations.keys()) == self.participants
        )

    @property
    def estimate_threshold_reached(self) -> bool:
        """Check that the estimate threshold has been reached."""
        estimates_counter = Counter()
        estimates_counter.update(self.participant_to_estimate.values())
        # check that a single estimate has at least 2/3 of votes
        two_thirds_n = self._consensus_params.two_thirds_threshold
        return any(count >= two_thirds_n for count in estimates_counter.values())

    @property
    def most_voted_estimate(self) -> float:
        """Get the most voted estimate."""
        estimates_counter = Counter()
        estimates_counter.update(self.participant_to_estimate.values())
        most_voted_estimate, max_votes = max(
            estimates_counter.items(), key=itemgetter(1)
        )
        if max_votes < self._consensus_params.two_thirds_threshold:
            raise ValueError("estimate has not enough votes")
        return most_voted_estimate.estimate

    @property
    def observations(self) -> Tuple[ObservationPayload, ...]:
        """Get the tuple of observations."""
        return tuple(self.participant_to_observations.values())

    def add_transaction(self, transaction: Transaction):
        """Process a transaction."""
        tx_type = transaction.payload.transaction_type.value
        handler: Callable[[BaseTxPayload], None] = getattr(self, tx_type, None)
        if handler is None:
            raise ValueError("request not recognized")
        if not self.check_transaction(transaction):
            raise ValueError("transaction not valid")
        handler(transaction.payload)

    def check_transaction(self, transaction: Transaction) -> bool:
        """
        Check transaction against the current state.

        :param transaction: the transaction
        :return: True if the transaction can be applied to the current
            state, False otherwise.
        """
        tx_type = transaction.payload.transaction_type.value
        handler: Callable[[BaseTxPayload], bool] = getattr(
            self, "check_" + tx_type, None
        )
        if handler is None:
            # request not recognized
            return False
        return handler(transaction.payload)

    def registration(self, payload: RegistrationPayload) -> None:
        """Handle a registration payload."""
        sender = payload.sender
        if self._type != RoundStateType.REGISTRATION:
            # too late to register
            return
        # we don't care if it was already there
        self.participants.add(sender)

        # if reached participant threshold, go to next state
        if self.registration_threshold_reached:
            self._type = RoundStateType.COLLECT_OBSERVATIONS

    def check_registration(self, _payload: RegistrationPayload) -> bool:
        """
        Check a registration payload can be applied to the current state.

        A registration can happen only when we are in the registration state.

        :param: _payload: the payload (not used).
        :return: True if a registration tx is allowed, False otherwise.
        """
        return self._type == RoundStateType.REGISTRATION

    def observation(self, payload: ObservationPayload) -> None:
        """Handle an 'observation' payload."""
        sender = payload.sender
        if self._type != RoundStateType.COLLECT_OBSERVATIONS:
            # not in the 'observation' phase
            return
        if sender not in self.participants:
            # sender not in the set of participants.
            return

        if sender in self.participant_to_observations:
            # sender has already sent its observation
            return

        self.participant_to_observations[sender] = payload

        # if reached participant threshold, go to next state
        if self.observation_threshold_reached:
            self._type = RoundStateType.CONSENSUS

    def check_observation(self, payload: ObservationPayload) -> bool:
        """
        Check an observation payload can be applied to the current state.

        An observation transaction can be applied only if:
        - the round is in the 'collect observation' state;
        - the sender belongs to the set of participants
        - the sender has not already sent its observation

        :param: payload: the payload.
        :return: True if the observation tx is allowed, False otherwise.
        """
        round_state_is_correct = self._type == RoundStateType.COLLECT_OBSERVATIONS
        sender_in_participant_set = payload.sender in self.participants
        sender_has_not_sent_observation_yet = (
            payload.sender not in self.participant_to_observations
        )
        return (
            round_state_is_correct
            and sender_in_participant_set
            and sender_has_not_sent_observation_yet
        )

    def estimate(self, payload: EstimatePayload) -> None:
        """Handle an 'estimate' payload."""
        sender = payload.sender
        if self._type != RoundStateType.CONSENSUS:
            # not in the 'consensus' phase
            return
        if sender not in self.participants:
            # sender not in the set of participants.
            return

        if sender not in self.participant_to_observations:
            # sender has NOT sent its observation
            return

        if sender in self.participant_to_estimate:
            # sender has already sent its estimate
            return

        self.participant_to_estimate[sender] = payload

        # if reached participant threshold, go to next state
        if self.observation_threshold_reached:
            self._type = RoundStateType.CONSENSUS_REACHED

    def check_estimate(self, payload: EstimatePayload) -> bool:
        """
        Check an estimate payload can be applied to the current state.

        An estimate transaction can be applied only if:
        - the round is in the 'consensus' state;
        - the sender belongs to the set of participants
        - the sender has already sent an observation
        - the sender has not sent its estimate yet

        :param: payload: the payload.
        :return: True if the observation tx is allowed, False otherwise.
        """
        round_state_is_correct = self._type == RoundStateType.CONSENSUS
        sender_in_participant_set = payload.sender in self.participants
        sender_has_sent_observation = payload.sender in self.participant_to_observations
        sender_has_not_sent_estimate_yet = (
            payload.sender not in self.participant_to_estimate
        )
        return (
            round_state_is_correct
            and sender_in_participant_set
            and sender_has_sent_observation
            and sender_has_not_sent_estimate_yet
        )


class Round:
    """Class to represent a round."""

    _current_header: Optional[Header]
    _current_transactions: List[Transaction]
    _current_valid_txs: List[bool]

    def __init__(self, consensus_params: ConsensusParams):
        """Initialize the round."""
        self._blockchain = Blockchain()
        self._round_state = RoundState(consensus_params)

        self._reset()

    def begin_block(self, header: Header):
        """Begin block."""
        self._current_header = header

    def deliver_tx(self, transaction: Transaction) -> None:
        """
        Deliver a transaction.

        It breaks down in:
        - check the transaction is valid wrt the current state
        - append the transaction to build the block on 'end_block' later
        - if the transaction was valid, apply the changes to the state

        :param transaction: the transaction.
        """
        is_valid = self.check_transaction(transaction)
        self._current_transactions.append(transaction)
        self._current_valid_txs.append(is_valid)
        if is_valid:
            self._round_state.add_transaction(transaction)

    def end_block(self):
        """End block."""
        # add the block to the local copy of the blockchain
        block = Block(
            cast(Header, self._current_header),
            self._current_transactions,
            self._current_valid_txs,
        )
        self._blockchain.add_block(block)
        self._reset()

    def _reset(self):
        """Reset the temporary data structures."""
        self._current_header = None
        self._current_transactions = []
        self._current_valid_txs = []

    def check_transaction(self, transaction: Transaction) -> bool:
        """
        Check transaction against the current state.

        :param transaction: the transaction
        :return: True if the transaction can be applied to the current
            state, False otherwise.
        """
        return self._round_state.check_transaction(transaction)

    @property
    def registration_threshold_reached(self) -> bool:
        """Check that the registration threshold has been reached."""
        return self._round_state.registration_threshold_reached

    @property
    def observation_threshold_reached(self) -> bool:
        """Check that the observation threshold has been reached."""
        return self._round_state.observation_threshold_reached

    @property
    def estimate_threshold_reached(self) -> bool:
        """Check that the estimate threshold has been reached."""
        return self._round_state.estimate_threshold_reached

    @property
    def observations(self) -> Tuple[ObservationPayload, ...]:
        """Get the tuple of observations."""
        return self._round_state.observations

    @property
    def most_voted_estimate(self) -> float:
        """Get the most voted estimate."""
        return self._round_state.most_voted_estimate
