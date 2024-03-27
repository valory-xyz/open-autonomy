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

"""This module contains the slashing background behaviours."""

import json
from abc import ABC
from calendar import timegm
from dataclasses import dataclass
from typing import (
    Any,
    Callable,
    Dict,
    FrozenSet,
    Generator,
    List,
    Optional,
    Set,
    Type,
    cast,
)

from aea.protocols.base import Message

from packages.valory.contracts.gnosis_safe.contract import GnosisSafeContract
from packages.valory.contracts.service_registry.contract import ServiceRegistryContract
from packages.valory.protocols.contract_api import ContractApiMessage
from packages.valory.skills.abstract_round_abci.base import OffenceStatus, RoundSequence
from packages.valory.skills.abstract_round_abci.behaviour_utils import (
    AsyncBehaviour,
    BaseBehaviour,
)
from packages.valory.skills.abstract_round_abci.behaviours import AbstractRoundBehaviour
from packages.valory.skills.abstract_round_abci.utils import inverse
from packages.valory.skills.slashing_abci.composition import SlashingAbciApp
from packages.valory.skills.slashing_abci.models import SharedState
from packages.valory.skills.slashing_abci.payloads import (
    SlashingTxPayload,
    StatusResetPayload,
)
from packages.valory.skills.slashing_abci.rounds import (
    SlashingCheckRound,
    StatusResetRound,
)
from packages.valory.skills.slashing_abci.rounds import (
    SynchronizedData as SlashingSyncedData,
)
from packages.valory.skills.transaction_settlement_abci.behaviours import (
    TransactionSettlementRoundBehaviour,
)
from packages.valory.skills.transaction_settlement_abci.payload_tools import (
    hash_payload_to_hex,
)
from packages.valory.skills.transaction_settlement_abci.rounds import (
    SynchronizedData as TxSettlementSyncedData,
)
from packages.valory.skills.transaction_settlement_abci.rounds import TX_HASH_LENGTH


# setting the safe gas to 0 means that all available gas will be used
# which is what we want in most cases
# more info here: https://safe-docs.dev.gnosisdev.com/safe/docs/contracts_tx_execution/
_SAFE_GAS = 0
# hardcoded to 0 because we don't need to send any ETH when slashing
_ETHER_VALUE = 0


class SlashingBaseBehaviour(BaseBehaviour, ABC):
    """Represents the base class for the slashing background FSM."""

    @property
    def shared_state(self) -> SharedState:
        """Get the round sequence from the shared state."""
        return cast(SharedState, self.context.state)

    @property
    def round_sequence(self) -> RoundSequence:
        """Get the round sequence from the shared state."""
        return self.shared_state.round_sequence

    @property
    def offence_status(self) -> Dict[str, OffenceStatus]:
        """Get the offence status from the round sequence."""
        return self.round_sequence.offence_status

    @offence_status.setter
    def offence_status(self, status: Dict[str, OffenceStatus]) -> None:
        """Set the offence status in the round sequence."""
        self.round_sequence.offence_status = status


class SlashingCheckBehaviour(SlashingBaseBehaviour):
    """
    A behaviour responsible for checking if there are any slashable events.

    Running concurrently with the other behaviours.
    """

    matching_round = SlashingCheckRound

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the slashing check behaviour."""
        super().__init__(**kwargs)
        self._slash_amounts: Dict[str, float] = {}

    @property
    def synchronized_data(self) -> SlashingSyncedData:
        """
        Return the synchronized data.

        Note: we instantiate here, rather than cast, as this runs
        concurrently and so the instantiation needs to happen somewhere.
        """
        return SlashingSyncedData(db=super().synchronized_data.db)

    @property
    def slashable_instances(self) -> List[str]:
        """Get the agent instances that are pending to be slashed."""
        return list(self._slash_amounts.keys())

    @property
    def slashable_amounts(self) -> List[float]:
        """Get the amounts that are pending to be slashed."""
        return list(self._slash_amounts.values())

    def is_majority_possible(self) -> bool:
        """Checks whether the service has enough participants to reach consensus."""
        return (
            self.synchronized_data.nb_participants
            >= self.synchronized_data.consensus_threshold
        )

    def is_slashing_majority_reached(self) -> bool:
        """Rely on the round to decide when the majority is reached."""
        return self.synchronized_data.slashing_majority_reached

    def is_round_ended(self, round_id: str) -> Callable[[], bool]:
        """
        Get a callable to check whether the current round has ended.

        We consider the background round ended when we have majority on the termination transaction.
        Overriden to allow for the behaviour to send transactions at any time.

        :return: the termination majority callable
        """
        return self.is_slashing_majority_reached

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

    def _check_offence_status(self) -> None:
        """Check the offence status, calculate the slash amount per operator, and assign it to `_slash_amounts`."""
        self._slash_amounts = {}

        for agent, status in self.offence_status.items():
            amount = status.slash_amount(
                self.params.light_slash_unit_amount,
                self.params.serious_slash_unit_amount,
            )
            # If an agent has not been slashed, then it is not included in the timestamps.
            # To facilitate the comparison in the subsequent code,
            # we assign a timestamp to the negative value of the wait time between slashes(`slash_cooldown_hours`).
            # This ensures that the comparison being performed is against 0.
            last_slashed_timestamp = self.synchronized_data.slash_timestamps.get(
                agent, -self.params.slash_cooldown_hours
            )
            last_round_transition_timestamp = timegm(
                self.round_sequence.last_round_transition_timestamp.utctimetuple()
            )

            if (
                amount > self.params.slash_threshold_amount
                and last_round_transition_timestamp
                > last_slashed_timestamp + self.params.slash_cooldown_hours
            ):
                # Check whether the threshold has been met, essentially bundling up offences.
                # Otherwise, we might end up in a situation where the slash tx is more expensive than the slash amount.
                # This in itself might be an attack vector, i.e., some malicious agent keeps sending bad payloads,
                # so that it drains the funds of the agents.
                # Moreover, only store amounts for agents which are not inside the slash wait window,
                # i.e., have not been slashed recently.
                self._slash_amounts[agent] = amount

    def _get_slash_data(self) -> Generator[None, None, Optional[bytes]]:
        """Get the slash tx data encoded."""
        response_msg = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
            contract_address=self.params.service_registry_address,
            contract_id=str(ServiceRegistryContract.contract_id),
            contract_callable="get_slash_data",
            agent_instances=self.slashable_instances,
            amounts=self.slashable_amounts,
            service_id=self.params.on_chain_service_id,
            chain_id=self.params.default_chain_id,
        )
        if response_msg.performative != ContractApiMessage.Performative.RAW_TRANSACTION:
            self.context.logger.error(
                f"Could not get the data for the slash transaction: {response_msg}"
            )
            return None

        slash_data = response_msg.raw_transaction.body.get("data", None)
        if slash_data is None:
            self.context.logger.error(
                "Something went wrong while trying to encode the slash data."
            )

        return slash_data

    def _get_safe_tx_hash(self, data: bytes) -> Generator[None, None, Optional[str]]:
        """
        Prepares and returns the safe tx hash.

        :param data: the safe tx data.
        :return: the tx hash
        """
        response_msg = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
            contract_address=self.synchronized_data.safe_contract_address,
            contract_id=str(GnosisSafeContract.contract_id),
            contract_callable="get_raw_safe_transaction_hash",
            to_address=self.params.service_registry_address,
            value=_ETHER_VALUE,
            data=data,
            safe_tx_gas=_SAFE_GAS,
            chain_id=self.params.default_chain_id,
        )

        if response_msg.performative != ContractApiMessage.Performative.RAW_TRANSACTION:
            self.context.logger.error(
                "Couldn't get safe tx hash. Expected response performative "
                f"{ContractApiMessage.Performative.RAW_TRANSACTION.value}, received {response_msg}."  # type: ignore
            )
            return None

        tx_hash = response_msg.raw_transaction.body.get("tx_hash", None)
        if tx_hash is None or len(tx_hash) != TX_HASH_LENGTH:
            self.context.logger.error(
                "Something went wrong while trying to get the slash transaction's hash. "
                f"Invalid hash {tx_hash!r} was returned."
            )
            return None

        # strip "0x" from the response hash
        return tx_hash[2:]

    def async_act(self) -> Generator:
        """
        Performs the slashing check logic.

        This method is responsible for checking whether there is any slashable event.
        When an agent detects a slashable event, it prepares a multisend transaction,
        on which the majority of the agents in the service have to reach consensus on.

        :return: None
        :yield: None
        """
        if not self.is_majority_possible() or self.synchronized_data.slashing_in_flight:
            # If the service does not have enough participants to reach consensus, there is no need to run the act.
            # Additionally, we verify whether a slashing operation has already been triggered to avoid duplication.
            yield from self.sleep(self.params.sleep_time)
            return

        if self.params.service_registry_address is None:  # pragma: no cover
            raise ValueError(
                "Service registry address not set, but is required for slashing!"
            )

        self._check_offence_status()
        if len(self._slash_amounts) == 0:
            # no slashable events are present, so we sleep and try again
            yield from self.sleep(self.params.sleep_time)
            return

        self.context.logger.info(
            f"Slashable events detected for agent instances: {self.slashable_instances}. "
            f"Preparing slashing transaction with amounts: {self.slashable_amounts}."
        )

        data = yield from self._get_slash_data()
        if data is None:
            self.context.logger.error(
                "Cannot construct the safe tx without the slash data."
            )
            return

        safe_tx_hash = yield from self._get_safe_tx_hash(data)
        if safe_tx_hash is None:
            self.context.logger.error("Cannot slash without a safe tx hash.")
            return

        slashing_tx_hex = hash_payload_to_hex(
            safe_tx_hash,
            _ETHER_VALUE,
            _SAFE_GAS,
            str(self.params.service_registry_address),
            data,
        )

        slashing_tx_payload = SlashingTxPayload(
            self.context.agent_address, slashing_tx_hex
        )

        self.context.logger.info("Successfully prepared slashing tx payload.")
        yield from self.send_a2a_transaction(slashing_tx_payload)
        yield from self.wait_for_condition(self.is_slashing_majority_reached)


@dataclass
class OperatorSlashedEventLog:
    """The logs' structure of an operator slashed event."""

    amount: int
    operator: str
    serviceId: int


@dataclass
class OperatorSlashedInfo:
    """The slash receipt's information after being parsed."""

    slash_timestamp: int
    events: List[OperatorSlashedEventLog]

    def __post_init__(self) -> None:
        """Post initialization process for the events."""
        if all(isinstance(event, dict) for event in self.events):
            events = cast(dict, self.events)
            self.events = [OperatorSlashedEventLog(**event) for event in events]


class StatusResetBehaviour(SlashingBaseBehaviour):
    """Behaviour that runs after a slash tx has been verified."""

    matching_round = StatusResetRound

    @property
    def slashing_synced_data(self) -> SlashingSyncedData:
        """Return the synchronized data."""
        return cast(SlashingSyncedData, self.shared_state.synchronized_data)

    @property
    def tx_settlement_synced_data(self) -> TxSettlementSyncedData:
        """Return the synchronized data."""
        return TxSettlementSyncedData(db=super().synchronized_data.db)

    def _process_slash_receipt(
        self, slash_tx_hash: str
    ) -> Generator[None, None, Optional[OperatorSlashedInfo]]:
        """Process the slash tx' s receipt."""
        response_msg = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
            contract_address=self.params.service_registry_address,
            contract_id=str(ServiceRegistryContract.contract_id),
            contract_callable="process_slash_receipt",
            tx_hash=slash_tx_hash,
            chain_id=self.params.default_chain_id,
        )

        if response_msg.performative != ContractApiMessage.Performative.RAW_TRANSACTION:
            self.context.logger.error(
                "Couldn't process slashing transaction's receipt. Expected response performative "
                f"{ContractApiMessage.Performative.RAW_TRANSACTION.value}, received {response_msg}."  # type: ignore
            )
            return None

        if response_msg.raw_transaction.body is None:  # pragma: no cover
            # error is logged in the contract
            return None

        return OperatorSlashedInfo(**response_msg.raw_transaction.body)

    def _get_instances_mapping(
        self,
        agent_instances: FrozenSet[str],
    ) -> Generator[None, None, Optional[Dict[str, str]]]:
        """
        Retrieve a mapping of the given agent instances to their operators.

        Please keep in mind that this method performs a call for each agent instance.

        :param agent_instances: the agent instances to be mapped.
        :return: a mapping of the given agent instances to their operators.
        """
        # Ideally, `mapOperatorAndServiceIdAgentInstances` should be used instead of `mapAgentInstanceOperators`,
        # so that we have operators mapped to lists of agent instances for the given service id
        response_msg = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
            contract_address=self.params.service_registry_address,
            contract_id=str(ServiceRegistryContract.contract_id),
            contract_callable="get_operators_mapping",
            agent_instances=agent_instances,
            chain_id=self.params.default_chain_id,
        )

        if response_msg.performative != ContractApiMessage.Performative.RAW_TRANSACTION:
            self.context.logger.error(
                "Couldn't get operators mapping. Expected response performative "
                f"{ContractApiMessage.Performative.RAW_TRANSACTION.value}, received {response_msg}."  # type: ignore
            )
            return None

        return response_msg.raw_transaction.body

    def async_act(self) -> Generator:
        """
        Performs the slash result check and the status reset logic.

        This behaviour is responsible for checking the `OperatorSlashed` event
        to determine whether the slashing tx was successful.
        If that is the case, it proceeds with resetting the offence status of the slashed agents.
        """
        # the `OperatorSlashed` event returns the operators and not the agent instances, so we will need a mapping
        operators_mapping = self.slashing_synced_data.operators_mapping
        if operators_mapping is None:
            instances_mapping = yield from self._get_instances_mapping(
                self.slashing_synced_data.all_participants
            )
            if instances_mapping is None:
                self.context.logger.error(
                    f"Cannot continue without the agents to operators mapping. "
                    f"Retrying in {self.params.sleep_time} seconds."
                )
                yield from self.sleep(self.params.sleep_time)
                return
            # as also mentioned in `_get_instances_mapping`,
            # it would be better if `mapOperatorAndServiceIdAgentInstances` was used,
            # because getting the inverse here would not be necessary
            # in any case, we need to sort the mapping,
            # as the order in which they are received from the contract is not guaranteed,
            # and we need its content to be deterministic as it is later passed via the payload
            operators_mapping = inverse(dict(sorted(instances_mapping.items())))

        # check `OperatorSlashed` event to see which agents were slashed and if everything went as expected
        slash_info = yield from self._process_slash_receipt(
            self.tx_settlement_synced_data.final_tx_hash
        )
        if slash_info is None:
            # This signifies that we will continue retrying until either we succeed or the round times out.
            # However, this approach carries the risk of getting trapped in a loop!
            #
            # One potential solution could involve introducing a counter to track the number of retries.
            # If the counter would surpass a predefined threshold, we would then proceed to reset the offences
            # providing a mechanism to prevent an indefinite loop.
            self.context.logger.error(
                "Something unexpected happened while checking the slashing operation's result! "
                f"Retrying in {self.params.sleep_time} seconds."
            )
            yield from self.sleep(self.params.sleep_time)
            return

        agent_to_timestamp = {
            agent_instance: slash_info.slash_timestamp
            for event in slash_info.events
            for agent_instance in operators_mapping[event.operator]
        }
        self.context.logger.info(
            f"A slashing operation has been performed for the operator(s) of agents {list(agent_to_timestamp.keys())}."
        )
        self.context.logger.info("Resetting status for the slashed agents.")
        self.offence_status = {
            agent: OffenceStatus() for agent in agent_to_timestamp.keys()
        }
        self.context.logger.info("Successfully reset status for the slashed agents.")

        status_reset_payload = StatusResetPayload(
            self.context.agent_address,
            json.dumps(operators_mapping, sort_keys=True),
            json.dumps(agent_to_timestamp, sort_keys=True),
        )

        yield from self.send_a2a_transaction(status_reset_payload)
        yield from self.wait_until_round_end()
        self.set_done()


class SlashingAbciBehaviours(AbstractRoundBehaviour):
    """This class defines the behaviours required for slashing."""

    initial_behaviour_cls = TransactionSettlementRoundBehaviour.initial_behaviour_cls
    abci_app_cls = SlashingAbciApp
    behaviours: Set[Type[BaseBehaviour]] = {
        SlashingCheckBehaviour,  # type: ignore
        StatusResetBehaviour,  # type: ignore
        *TransactionSettlementRoundBehaviour.behaviours,
    }
