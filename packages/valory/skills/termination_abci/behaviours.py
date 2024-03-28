# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022-2024 Valory AG
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

"""This module contains the termination behaviour classes."""
import sys
from typing import Callable, Dict, Generator, List, Optional, Set, Type, cast

from aea.protocols.base import Message
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
from packages.valory.skills.abstract_round_abci.behaviour_utils import (
    AsyncBehaviour,
    BaseBehaviour,
)
from packages.valory.skills.abstract_round_abci.behaviours import AbstractRoundBehaviour
from packages.valory.skills.termination_abci.models import TerminationParams
from packages.valory.skills.termination_abci.payloads import BackgroundPayload
from packages.valory.skills.termination_abci.rounds import (
    BackgroundRound,
    SynchronizedData,
    TerminationAbciApp,
    TerminationRound,
)
from packages.valory.skills.transaction_settlement_abci.behaviours import (
    TransactionSettlementRoundBehaviour,
)
from packages.valory.skills.transaction_settlement_abci.payload_tools import (
    hash_payload_to_hex,
)


# setting the safe gas to 0 means that all available gas will be used
# which is what we want in most cases
# more info here: https://safe-docs.dev.gnosisdev.com/safe/docs/contracts_tx_execution/
_SAFE_GAS = 0

# hardcoded to 0 because we don't need to send any ETH when handing over multisig ownership
_ETHER_VALUE = 0

# payload to represent a non-existing event
_NO_EVENT_FOUND: Dict = {}


class BackgroundBehaviour(BaseBehaviour):
    """A behaviour responsible for picking up the termination signal, it runs concurrently with other behaviours."""

    matching_round = BackgroundRound
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
        if not self._is_majority_possible() or self._is_termination_majority():
            # if the service has not enough participants to reach
            # consensus or if termination majority has already
            # been reached, ie the multisend transaction has been
            # prepared by enough participants,
            # there is no need to run the rest of the act
            return

        signal_present = yield from self.check_for_signal()
        if signal_present is None:
            # if the response is None, something went wrong
            self.context.logger.error("Failed checking the termination signal.")
            return
        if not signal_present:
            # the signal is not present, so we sleep and try again
            yield from self.sleep(self.params.termination_sleep)
            return

        self.context.logger.info(
            "Termination signal was picked up, preparing termination transaction."
        )

        background_data = yield from self.get_multisend_payload()
        if background_data is None:
            self.context.logger.error(
                "Couldn't prepare multisend transaction for termination."
            )
            return

        self.context.logger.info("Successfully prepared termination multisend tx.")
        termination_payload = BackgroundPayload(
            self.context.agent_address, background_data=background_data
        )
        yield from self.send_a2a_transaction(termination_payload)
        yield from self.wait_for_termination_majority()

    @property
    def synchronized_data(self) -> SynchronizedData:
        """
        Return the synchronized data.

        Note: we instantiate here, rather than cast, as this runs
        concurrently and so the instantiation needs to happen somewhere.
        """
        return SynchronizedData(db=super().synchronized_data.db)

    @property
    def params(self) -> TerminationParams:
        """Return the params."""
        return cast(TerminationParams, super().params)

    def check_for_signal(self) -> Generator[None, None, Optional[bool]]:
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
            self._service_owner_address = yield from self._get_service_owner()

        termination_signal = yield from self._get_latest_termination_signal()
        if termination_signal is None:
            # something went wrong, we stop executing the rest of the logic
            return None
        if termination_signal == _NO_EVENT_FOUND:
            # no termination signal has ever been sent to safe
            return False

        service_owner_removal = yield from self._get_latest_removed_owner_event()
        if service_owner_removal is None:
            # something went wrong, we stop executing the rest of the logic
            return None
        if service_owner_removal == _NO_EVENT_FOUND:
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

        termination_signal_occurrence = int(termination_signal["block_number"])
        service_owner_removal_occurrence = int(service_owner_removal["block_number"])

        # if the termination signal has occurred after the owner has been removed the service should terminate,
        # otherwise it's a signal that has already been handled previously
        return termination_signal_occurrence > service_owner_removal_occurrence

    def _get_latest_removed_owner_event(self) -> Generator[None, None, Optional[Dict]]:
        """Returns the latest event in which the service owner was removed from the set of owners of the safe."""
        response = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_STATE,  # type: ignore
            contract_id=str(GnosisSafeContract.contract_id),
            contract_callable="get_removed_owner_events",
            contract_address=self.synchronized_data.safe_contract_address,
            removed_owner=self._service_owner_address,
            from_block=self.params.termination_from_block,
            chain_id=self.params.default_chain_id,
        )
        if response.performative != ContractApiMessage.Performative.STATE:
            self.context.logger.error(
                f"Couldn't get the latest `RemovedOwner` event. "
                f"Expected response performative {ContractApiMessage.Performative.STATE.value}, "  # type: ignore
                f"received {response.performative.value}."
            )
            return None

        removed_owner_events = cast(List[Dict], response.state.body.get("data"))
        if len(removed_owner_events) == 0:
            return _NO_EVENT_FOUND

        latest_removed_owner_event = removed_owner_events[0]
        for removed_owner_event in removed_owner_events[1:]:
            if int(removed_owner_event["block_number"]) > int(
                latest_removed_owner_event["block_number"]
            ):
                latest_removed_owner_event = removed_owner_event

        return latest_removed_owner_event

    def _get_latest_termination_signal(self) -> Generator[None, None, Optional[Dict]]:
        """Get the latest termination signal sent by the service owner."""
        self.context.logger.info(
            f"Retrieving termination events on chain '{self.params.default_chain_id}' from block {self.params.termination_from_block}"
        )
        response = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_STATE,  # type: ignore
            contract_id=str(GnosisSafeContract.contract_id),
            contract_callable="get_zero_transfer_events",
            contract_address=self.synchronized_data.safe_contract_address,
            sender_address=self._service_owner_address,
            from_block=self.params.termination_from_block,
            chain_id=self.params.default_chain_id,
        )
        if response.performative != ContractApiMessage.Performative.STATE:
            self.context.logger.error(
                f"Couldn't get the latest Zero Transfer (`SafeReceived`) event. "
                f"Expected response performative {ContractApiMessage.Performative.STATE.value}, "  # type: ignore
                f"received {response.performative.value}."
            )
            return None

        zero_transfer_events = cast(List[Dict], response.state.body.get("data"))
        if len(zero_transfer_events) == 0:
            return _NO_EVENT_FOUND

        latest_zero_transfer_event = zero_transfer_events[0]
        for zero_transfer_event in zero_transfer_events[1:]:
            if int(zero_transfer_event["block_number"]) > int(
                latest_zero_transfer_event["block_number"]
            ):
                latest_zero_transfer_event = zero_transfer_event

        return latest_zero_transfer_event

    def _get_service_owner(self) -> Generator[None, None, Optional[str]]:
        """Method that returns the service owner."""
        response = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_STATE,  # type: ignore
            contract_id=str(ServiceRegistryContract.contract_id),
            contract_callable="get_service_owner",
            contract_address=self.params.service_registry_address,
            service_id=self.params.on_chain_service_id,
            chain_id=self.params.default_chain_id,
        )

        if response.performative != ContractApiMessage.Performative.STATE:
            self.context.logger.error(
                f"Couldn't get the service owner for service with id={self.params.on_chain_service_id}. "
                f"Expected response performative {ContractApiMessage.Performative.STATE.value}, "  # type: ignore
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
            performative=ContractApiMessage.Performative.GET_STATE,  # type: ignore
            contract_id=str(GnosisSafeContract.contract_id),
            contract_callable="get_owners",
            contract_address=self.synchronized_data.safe_contract_address,
            chain_id=self.params.default_chain_id,
        )

        if response.performative != ContractApiMessage.Performative.STATE:
            self.context.logger.error(
                f"Couldn't get the safe owners for safe deployed at {self.synchronized_data.safe_contract_address}. "
                f"Expected response performative {ContractApiMessage.Performative.STATE.value}, "  # type: ignore
                f"received {response.performative.value}."
            )
            return None

        owners = cast(Optional[List[str]], response.state.body.get("owners", None))
        return owners

    def _get_remove_owner_tx(
        self, owner: str, threshold: int
    ) -> Generator[None, None, Optional[str]]:
        """
        Gets a remove owner tx.

        :param owner: the owner to be removed.
        :param threshold: the new safe threshold to be set.
        :return: the tx data
        """
        response = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_STATE,  # type: ignore
            contract_id=str(GnosisSafeContract.contract_id),
            contract_callable="get_remove_owner_data",
            contract_address=self.synchronized_data.safe_contract_address,
            owner=owner,
            threshold=threshold,
            chain_id=self.params.default_chain_id,
        )

        if response.performative != ContractApiMessage.Performative.STATE:
            self.context.logger.error(
                f"Couldn't get a remove owner tx. "
                f"Expected response performative {ContractApiMessage.Performative.STATE.value}, "  # type: ignore
                f"received {response.performative.value}."
            )
            return None

        # strip "0x" from the response
        tx_data = cast(str, response.state.body.get("data", None))[2:]
        return tx_data

    def _get_swap_owner_tx(
        self, old_owner: str, new_owner: str
    ) -> Generator[None, None, Optional[str]]:
        """
        Gets a swap owner tx.

        :param old_owner: the owner to be removed.
        :param new_owner: the new safe threshold to be set.
        :return: the tx data
        """
        response = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_STATE,  # type: ignore
            contract_id=str(GnosisSafeContract.contract_id),
            contract_callable="get_swap_owner_data",
            contract_address=self.synchronized_data.safe_contract_address,
            old_owner=old_owner,
            new_owner=new_owner,
            chain_id=self.params.default_chain_id,
        )

        if response.performative != ContractApiMessage.Performative.STATE:
            self.context.logger.error(
                f"Couldn't get a swap owner tx. "
                f"Expected response performative {ContractApiMessage.Performative.STATE.value}, "  # type: ignore
                f"received {response.performative.value}."
            )
            return None

        # strip "0x" from the response
        tx_data = cast(str, response.state.body.get("data", None))[2:]
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
            chain_id=self.params.default_chain_id,
        )

        if response.performative != ContractApiMessage.Performative.STATE:
            self.context.logger.error(
                f"Couldn't get safe hash. "
                f"Expected response performative {ContractApiMessage.Performative.STATE.value}, "  # type: ignore
                f"received {response.performative.value}."
            )
            return None

        # strip "0x" from the response hash
        tx_hash = cast(str, response.state.body["tx_hash"])[2:]
        return tx_hash

    def _get_multisend_tx(self) -> Generator[None, None, Optional[str]]:
        """This method compiles a multisend transaction to give ownership of the safe contract to the service owner."""
        transactions: List[Dict] = []
        threshold = 1
        safe_owners = yield from self._get_safe_owners()
        if safe_owners is None:
            return None
        owner_to_be_swapped = safe_owners[0]
        # we remove all but one safe owner
        # reverse the list to avoid errors when removing owners
        # this is because the owners are stored as a linked list
        # in the safe, hence the order is important
        safe_owners = list(reversed(safe_owners[1:]))
        for owner in safe_owners:
            # we generate a tx to remove the current owner
            remove_tx_str = yield from self._get_remove_owner_tx(owner, threshold)
            if remove_tx_str is None:
                return None
            remove_tx = bytes.fromhex(remove_tx_str)
            # we append it to the list of the multisend txs
            transactions.append(
                {
                    "operation": MultiSendOperation.CALL,
                    "to": self.synchronized_data.safe_contract_address,
                    "value": _ETHER_VALUE,
                    "data": HexBytes(remove_tx),
                }
            )

        if owner_to_be_swapped != cast(str, self._service_owner_address):
            # if the service owner is not the owner to be swapped
            # we swap, otherwise it's not necessary
            swap_tx = yield from self._get_swap_owner_tx(
                owner_to_be_swapped,
                cast(str, self._service_owner_address),
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
            chain_id=self.params.default_chain_id,
        )
        if response.performative != ContractApiMessage.Performative.RAW_TRANSACTION:
            self.context.logger.error(
                f"Couldn't compile the multisend tx. "
                f"Expected response performative {ContractApiMessage.Performative.RAW_TRANSACTION.value}, "  # type: ignore
                f"received {response.performative.value}."
            )
            return None

        # strip "0x" from the response
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

    def _is_majority_possible(self) -> bool:
        """Checks whether the service has enough participants to reach consensus."""
        return (
            self.synchronized_data.nb_participants
            >= self.synchronized_data.consensus_threshold
        )

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
                self.context.logger.info(
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


class TerminationBehaviour(BaseBehaviour):
    """Behaviour responsible for terminating the agent."""

    matching_round = TerminationRound

    def async_act(self) -> Generator:
        """Logs termination and terminates."""
        self.context.logger.info("Terminating the agent.")
        sys.exit()
        yield


class TerminationAbciBehaviours(AbstractRoundBehaviour):
    """This class defines the behaviours required in terminating a service."""

    initial_behaviour_cls = TransactionSettlementRoundBehaviour.initial_behaviour_cls
    abci_app_cls = TerminationAbciApp
    behaviours: Set[Type[BaseBehaviour]] = {
        BackgroundBehaviour,  # type: ignore
        TerminationBehaviour,  # type: ignore
        *TransactionSettlementRoundBehaviour.behaviours,
    }
