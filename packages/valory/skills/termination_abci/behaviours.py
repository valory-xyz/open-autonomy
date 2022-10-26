# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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

"""This module contains the background behaviour and round classes."""
from enum import Enum
from mailbox import Message
from typing import (
    Any,
    Callable,
    Dict,
    Generator,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    cast,
)

from hexbytes import HexBytes

from packages.valory.contracts.gnosis_safe.contract import (
    GnosisSafeContract,
    SafeOperation,
)
from packages.valory.contracts.multisend.contract import (
    MultiSendContract,
    MultiSendOperation,
)
from packages.valory.contracts.service_registry.contract import ServiceRegistryContract
from packages.valory.protocols.contract_api import ContractApiMessage
from packages.valory.skills.abstract_round_abci.abci_app_chain import chain
from packages.valory.skills.abstract_round_abci.base import (
    AbciApp,
    AbciAppTransitionFunction,
    AbstractRound,
    AppState,
    BaseSynchronizedData,
    BaseTxPayload,
    CollectSameUntilThresholdRound,
    DegenerateRound,
)
from packages.valory.skills.abstract_round_abci.behaviour_utils import (
    AsyncBehaviour,
    BaseBehaviour,
)
from packages.valory.skills.abstract_round_abci.behaviours import AbstractRoundBehaviour
from packages.valory.skills.transaction_settlement_abci.behaviours import (
    TransactionSettlementRoundBehaviour,
)
from packages.valory.skills.transaction_settlement_abci.payload_tools import (
    hash_payload_to_hex,
)
from packages.valory.skills.transaction_settlement_abci.rounds import (
    FailedRound,
    FinishedTransactionSubmissionRound,
    TransactionSubmissionAbciApp,
)


# setting the safe gas to 0 means that all available gas will be used
# which is what we want in most cases
# more info here: https://safe-docs.dev.gnosisdev.com/safe/docs/contracts_tx_execution/
_SAFE_GAS = 0

# hardcoded to 0 because we don't need to send any ETH when handing over multisig ownership
_ETHER_VALUE = 0

NULL_ADDRESS: str = "0x" + "0" * 40
MAX_UINT256 = 2 ** 256 - 1


class TransactionType(Enum):
    """Defines the possible transaction types."""

    BACKGROUND = "background"


class BackgroundPayload(BaseTxPayload):
    """Defines the background round payload."""

    transaction_type = TransactionType.BACKGROUND

    def __init__(self, sender: str, background_data: str, **kwargs: Any) -> None:
        """Initialize a 'Termination' transaction payload.
        :param sender: the sender (Ethereum) address
        :param background_data: serialized tx.
        :param kwargs: the keyword arguments
        """
        super().__init__(sender, **kwargs)
        self._background_data = background_data

    @property
    def background_data(self) -> str:
        """Get the termination data."""
        return self._background_data

    @property
    def data(self) -> Dict:
        """Get the data."""
        return dict(background_data=self.background_data)


class SynchronizedData(BaseSynchronizedData):
    """
    Class to represent the synchronized data.

    This data is replicated by the tendermint application.
    """

    @property
    def safe_contract_address(self) -> Optional[str]:
        """Get the safe contract address."""
        return cast(Optional[str], self.db.get("safe_contract_address", None))

    @property
    def termination_majority_reached(self) -> bool:
        """Get termination_majority_reached."""
        return cast(bool, self.db.get("termination_majority_reached", False))


class BackgroundBehaviour(BaseBehaviour):
    """A behaviour responsible for picking up the termination signal, it runs concurrently with other behaviours."""

    behaviour_id = "background_behaviour"

    _service_owner_address: Optional[str] = None

    def async_act(self) -> Generator:
        """
        Performs the termination logic.

        This method responsible for checking whether the on-chain termination signal is present.
        When an agent picks up the termination signal, it prepares a multisend transaction,
        on which the majority of agents in the service have to reach consensus on.

        :return: None
        :yield: None
        """
        if self._is_termination_majority():
            # if termination majority has already been reached
            # there is no need to run the rest of this method
            yield
            return

        signal_present = yield from self.check_for_signal()
        if not signal_present:
            yield from self.sleep(self.params.sleep_time)
            return

        self.context.logger.info(
            "Terminate signal was received, preparing termination transaction."
        )

        background_data = yield from self.get_multisend_payload()
        termination_payload = BackgroundPayload(
            self.context.agent_address, background_data=background_data
        )
        yield from self.send_a2a_transaction(termination_payload)
        yield from self.wait_for_termination_majority()

    @property
    def synchronized_data(self) -> SynchronizedData:
        """Return the synchronized data."""
        return cast(SynchronizedData, super().synchronized_data)

    def check_for_signal(self) -> Generator[None, None, bool]:
        """
        This method checks for the termination signal.

        We check for the signal by looking at the "SafeReceived" events on the safe contract.
        https://github.com/safe-global/safe-contracts/blob/v1.3.0/contracts/common/EtherPaymentFallback.sol#L10
        In order for an SafeReceived event to qualify as a termination signal it has to fulfill the following:
            1. It MUST be sent by the service owner (self._service_owner).
            2. It MUST be 0 value tx.

        :returns: True if the termination signal is found, false otherwise
        """
        if self._service_owner_address is None:
            self._service_owner_address = yield from self.get_service_owner()

        termination_signal = yield from self._get_latest_termination_signal()
        if termination_signal is None:
            # no termination signal has ever been sent to safe
            return False

        service_owner_removal = yield from self._get_latest_removed_owner_event()
        if service_owner_removal is None:
            # the service owner has never been removed from the safe
            # this means that the observed `termination_signal` is the
            # first termination signal ever sent to this safe contract
            # as such it is valid signal for terminating the service
            return True

        # if both the `termination_signal` and the `service_owner` removal events are present,
        # we need to make sure this is not a previous termination that is already taken care of
        # if a termination has been previously made, we assume that:
        #   1. the service owner has been previously set as the safe owner
        #   2. since the service is running again, the ownership of the safe has been handed back to the agent instances
        # for 2. to happen, the service owner needs to be removed from being an owner of the safe. When this is done,
        # a `RemovedOwner` event is thrown, which is what `_get_latest_removed_owner_event()` captures.

        termination_signal_occurrence = int(termination_signal.get("block_number"))
        service_owner_removal_occurrence = int(termination_signal.get("block_number"))

        # if the termination signal has occurred after the owner has been removed the service should terminate,
        # otherwise it's a signal that has already been handled previously
        return termination_signal_occurrence > service_owner_removal_occurrence

    def _get_latest_removed_owner_event(self) -> Generator[None, None, Optional[Dict]]:
        """Returns the latest event in which the service owner was removed from the set of owners of the safe."""
        response = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_STATE,
            contract_id=str(GnosisSafeContract.contract_id),
            contract_callable="get_removed_owner_events",
            contract_address=self.synchronized_data.safe_contract_address,
            removed_owner=self._service_owner_address,
        )
        if response.performative != ContractApiMessage.Performative.STATE:
            self.context.logger.error(
                f"Couldn't get the latest `RemovedOwner` event. "
                f"Expected response performative {ContractApiMessage.Performative.STATE.value}, "
                f"received {response.performative.value}."
            )
            return None

        removed_owner_events = cast(List[Dict], response.state.body.get("data"))
        if len(removed_owner_events) == 0:
            return None

        latest_removed_owner_event = removed_owner_events[0]
        for removed_owner_event in removed_owner_events[1:]:
            if int(removed_owner_event.get("block_number")) > int(
                latest_removed_owner_event.get("block_number")
            ):
                latest_removed_owner_event = removed_owner_event

        return latest_removed_owner_event

    def _get_latest_termination_signal(self) -> Generator[None, None, Optional[Dict]]:
        """Get the latest termination signal sent by the service owner."""
        response = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_STATE,
            contract_id=str(GnosisSafeContract.contract_id),
            contract_callable="get_zero_transfer_events",
            contract_address=self.synchronized_data.safe_contract_address,
            sender_address=self._service_owner_address,
        )
        if response.performative != ContractApiMessage.Performative.STATE:
            self.context.logger.error(
                f"Couldn't get the latest Zero Transfer (`SafeReceived`) event. "
                f"Expected response performative {ContractApiMessage.Performative.STATE.value}, "
                f"received {response.performative.value}."
            )
            return None

        zero_transfer_events = cast(List[Dict], response.state.body.get("data"))
        if len(zero_transfer_events) == 0:
            return None

        latest_zero_transfer_event = zero_transfer_events[0]
        for zero_transfer_event in zero_transfer_events[1:]:
            if int(zero_transfer_event.get("block_number")) > int(
                latest_zero_transfer_event.get("block_number")
            ):
                latest_zero_transfer_event = zero_transfer_event

        return latest_zero_transfer_event

    def get_service_owner(self) -> Generator[None, None, Optional[str]]:
        """Method that returns the service owner."""
        response = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_STATE,
            contract_id=str(ServiceRegistryContract.contract_id),
            contract_callable="get_service_owner",
            contract_address=self.params.service_registry_address,
            service_id=self.params.service_id,
        )

        if response.performative != ContractApiMessage.Performative.STATE:
            self.context.logger.error(
                f"Couldn't get the service owner for service with id={self.params.service_id}. "
                f"Expected response performative {ContractApiMessage.Performative.STATE.value}, "
                f"received {response.performative.value}."
            )
            return None

        service_owner = cast(
            Optional[str], response.state.body.get("service_owner", None)
        )
        return service_owner

    def get_multisend_payload(self) -> Generator[None, None, Optional[str]]:
        """Prepares and returns the multisend to hand over safe ownership to the service_owner."""
        multisend_data_str = yield from self._get_multisend_tx()
        if multisend_data_str is None:
            return None
        multisend_data = bytes.fromhex(multisend_data_str)
        tx_hash = yield from self._get_safe_tx_hash(multisend_data)
        if tx_hash is None:
            return None

        payload_data = hash_payload_to_hex(
            safe_tx_hash=tx_hash,
            ether_value=_ETHER_VALUE,
            safe_tx_gas=_SAFE_GAS,
            operation=SafeOperation.DELEGATE_CALL.value,
            to_address=self.params.multisend_address,
            data=multisend_data,
        )
        return payload_data

    def _get_safe_owners(self) -> Generator[None, None, Optional[List[str]]]:
        """Retrieves safe owners."""
        response = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_STATE,
            contract_id=str(GnosisSafeContract.contract_id),
            contract_callable="get_owners",
            contract_address=self.synchronized_data.safe_contract_address,
        )

        if response.performative != ContractApiMessage.Performative.STATE:
            self.context.logger.error(
                f"Couldn't get the safe owners for safe deployed at {self.synchronized_data.safe_contract_address}. "
                f"Expected response performative {ContractApiMessage.Performative.STATE.value}, "
                f"received {response.performative.value}."
            )
            return None

        owners = cast(Optional[str], response.state.body.get("owners", None))
        return owners

    def _get_remove_owner_tx(
        self, prev_owner: str, owner: str, threshold: int
    ) -> Generator[None, None, Optional[str]]:
        """
        Gets a remove owner tx.

        :param prev_owner: the owner that pointed to the owner to be removed.
        :param owner: the owner to be removed.
        :param threshold: the new safe threshold to be set.
        :return: the tx data
        """
        response = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_STATE,
            contract_id=str(GnosisSafeContract.contract_id),
            contract_callable="get_remove_owner_data",
            contract_address=self.synchronized_data.safe_contract_address,
            prev_owner=prev_owner,
            owner=owner,
            threshold=threshold,
        )

        if response.performative != ContractApiMessage.Performative.STATE:
            self.context.logger.error(
                f"Couldn't get a remove owner tx. "
                f"Expected response performative {ContractApiMessage.Performative.STATE.value}, "
                f"received {response.performative.value}."
            )
            return None

        tx_data = cast(Optional[str], response.state.body.get("data", None))
        return tx_data

    def _get_swap_owner_tx(
        self, prev_owner: str, old_owner: str, new_owner: str
    ) -> Generator[None, None, Optional[str]]:
        """
        Gets a swap owner tx.

        :param prev_owner: the owner that pointed to the owner to be replaced.
        :param old_owner: the owner to be removed.
        :param new_owner: the new safe threshold to be set.
        :return: the tx data
        """
        response = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_STATE,
            contract_id=str(GnosisSafeContract.contract_id),
            contract_callable="get_swap_owner_data",
            contract_address=self.synchronized_data.safe_contract_address,
            prev_owner=prev_owner,
            old_owner=old_owner,
            new_owner=new_owner,
        )

        if response.performative != ContractApiMessage.Performative.STATE:
            self.context.logger.error(
                f"Couldn't get a swap owner tx. "
                f"Expected response performative {ContractApiMessage.Performative.STATE.value}, "
                f"received {response.performative.value}."
            )
            return None

        tx_data = cast(Optional[str], response.state.body.get("data", None))
        return tx_data

    def _get_safe_tx_hash(self, data: bytes) -> Generator[None, None, Optional[str]]:
        """
        Prepares and returns the safe tx hash.

        :param data: the safe tx data.
        :return: the tx hash
        """
        response = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_STATE,  # type: ignore
            contract_address=self.synchronized_data.safe_contract_address,
            contract_id=str(GnosisSafeContract.contract_id),
            contract_callable="get_raw_safe_transaction_hash",
            to_address=self.params.multisend_address,
            value=_ETHER_VALUE,
            data=data,
            safe_tx_gas=_SAFE_GAS,
            operation=SafeOperation.DELEGATE_CALL.value,
        )

        if response.performative != ContractApiMessage.Performative.STATE:
            self.context.logger.error(
                f"Couldn't get safe hash. "
                f"Expected response performative {ContractApiMessage.Performative.STATE.value}, "
                f"received {response.performative.value}."
            )
            return None

        # strip "0x" from the response hash
        tx_hash = cast(str, response.state.body["tx_hash"])[2:]
        return tx_hash

    def _get_multisend_tx(self) -> Generator[None, None, Optional[str]]:
        """This method compiles a multisend transaction to give ownership of the safe contract to the service owner."""
        transactions: List[Dict] = []
        owner_to_be_swapped: Optional[str] = None
        threshold = 1
        safe_owners = yield from self._get_safe_owners()
        if safe_owners is None:
            return None

        # we remove all but one safe owner
        for owner in safe_owners:
            if owner_to_be_swapped is None:
                owner_to_be_swapped = owner
                continue

            # we generate a tx to remove the current owner
            remove_tx = yield from self._get_remove_owner_tx(
                owner_to_be_swapped, owner, threshold
            )
            if remove_tx is None:
                return None

            # we append it to the list of the multisend txs
            transactions.append(
                {
                    "operation": MultiSendOperation.CALL,
                    "to": self.synchronized_data.safe_contract_address,
                    "value": _ETHER_VALUE,
                    "data": HexBytes(remove_tx),
                }
            )

        # we swap the last owner with the service owner
        swap_tx = yield from self._get_swap_owner_tx(
            owner_to_be_swapped,
            owner_to_be_swapped,
            self._service_owner_address,
        )
        if swap_tx is None:
            return None

        transactions.append(
            {
                "operation": MultiSendOperation.CALL,
                "to": self.synchronized_data.safe_contract_address,
                "value": _ETHER_VALUE,
                "data": HexBytes(swap_tx),
            }
        )

        response = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
            contract_address=self.params.multisend_address,
            contract_id=str(MultiSendContract.contract_id),
            contract_callable="get_tx_data",
            multi_send_txs=transactions,
        )
        if response.performative != ContractApiMessage.Performative.RAW_MESSAGE:
            self.context.logger.error(
                f"Couldn't compile the multisend tx. "
                f"Expected response performative {ContractApiMessage.Performative.RAW_MESSAGE.value}, "
                f"received {response.performative.value}."
            )
            return None

        multisend_data = cast(str, response.raw_transaction.body["data"])[2:]
        return multisend_data

    def wait_for_termination_majority(self) -> Generator:
        """
        Wait until we reach majority on the termination transaction.
        :yield: None
        """
        yield from self.wait_for_condition(self._is_termination_majority)

    def _is_termination_majority(self) -> bool:
        """Rely on the round to decide when majority is reached."""
        return self.synchronized_data.termination_majority_reached

    def get_callback_request(self) -> Callable[[Message, "BaseBehaviour"], None]:
        """Wrapper for callback_request(), overridden to avoid mix-ups with normal (non-background) behaviours."""

        def callback_request(
            message: Message, _current_behaviour: BaseBehaviour
        ) -> None:
            """
            This method gets called when a response for a prior request is received.

            Overridden to remove the check that checks whether the behaviour that made the request is still active.
            The received message gets passed to the behaviour that invoked it, in this case it's always the
            background behaviour.

            :param message: the response.
            :param _current_behaviour: not used, left in to satisfy the interface.
            :return: none
            """
            if self.is_stopped:
                self.context.logger.debug(
                    "dropping message as behaviour has stopped: %s", message
                )
                return

            if self.state != AsyncBehaviour.AsyncState.WAITING_MESSAGE:
                self.context.logger.warning(
                    f"could not send message {message} to {self.behaviour_id}"
                )
                return

            self.try_send(message)

        return callback_request

    def is_round_ended(self, round_id: str) -> Callable[[], bool]:
        """
        Get a callable to check whether the current round has ended.

        We consider the background round ended when we have majority on the termination transaction.
        Overriden to allow for the behaviour to send transactions at any time.

        :return: the termination majority callable
        """
        return self._is_termination_majority


class Event(Enum):
    """Defines the (background) round events."""

    TERMINATE = "terminate"


class BackgroundRound(CollectSameUntilThresholdRound):
    """Defines the background round, which runs concurrently with other rounds."""

    round_id: str = "background_round"
    allowed_tx_type = BackgroundPayload.transaction_type
    payload_attribute: str = "background_data"
    synchronized_data_class = SynchronizedData

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            state = self.synchronized_data.update(
                synchronized_data_class=self.synchronized_data_class,
                termination_majority_reached=True,
                most_voted_tx_hash=self.most_voted_payload,
            )
            return state, Event.TERMINATE

        return None
