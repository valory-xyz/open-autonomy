# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2026 Valory AG
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

"""This module contains the behaviours of the IdentifyServiceOwnerAbciApp."""

from abc import ABC
from typing import Generator, Optional, Set, Type, cast

from packages.valory.contracts.service_registry.contract import (
    ServiceRegistryContract,
)
from packages.valory.contracts.service_staking_token.contract import (
    ServiceStakingTokenContract,
)
from packages.valory.protocols.contract_api import ContractApiMessage
from packages.valory.skills.abstract_round_abci.behaviours import (
    AbstractRoundBehaviour,
    BaseBehaviour,
)
from packages.valory.skills.identify_service_owner_abci.models import IdentifyServiceOwnerParams
from packages.valory.skills.identify_service_owner_abci.payloads import IdentifyServiceOwnerPayload
from packages.valory.skills.identify_service_owner_abci.rounds import (
    IdentifyServiceOwnerAbciApp,
    IdentifyServiceOwnerRound,
    SynchronizedData,
)


class IdentifyServiceOwnerBaseBehaviour(BaseBehaviour, ABC):
    """Base behaviour for the identify_service_owner_abci skill."""

    @property
    def synchronized_data(self) -> SynchronizedData:
        """Return the synchronized data."""
        return cast(SynchronizedData, super().synchronized_data)

    @property
    def params(self) -> IdentifyServiceOwnerParams:
        """Return the params."""
        return cast(IdentifyServiceOwnerParams, super().params)


class IdentifyServiceOwnerBehaviour(IdentifyServiceOwnerBaseBehaviour):
    """Behaviour that resolves the real service owner, handling staking indirection."""

    matching_round = IdentifyServiceOwnerRound

    def async_act(self) -> Generator:
        """Resolve the service owner."""
        with self.context.benchmark_tool.measure(self.behaviour_id).local():
            service_owner = yield from self._resolve_service_owner()
            service_id = self.params.on_chain_service_id
            safe_address = self.synchronized_data.safe_contract_address
            if service_owner is not None:
                self.context.logger.info(
                    f"Service owner identified: "
                    f"service_id={service_id}, "
                    f"safe={safe_address}, "
                    f"owner={service_owner}"
                )
            else:
                self.context.logger.warning(
                    f"Could not identify service owner: "
                    f"service_id={service_id}, "
                    f"safe={safe_address}"
                )
            payload = IdentifyServiceOwnerPayload(
                sender=self.context.agent_address,
                service_owner=service_owner,
            )
        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()
        self.set_done()

    def _resolve_service_owner(self) -> Generator[None, None, Optional[str]]:
        """Resolve the real service owner, handling staking contract indirection."""
        service_id = self.params.on_chain_service_id
        registry_address = self.params.service_registry_address

        if service_id is None or registry_address is None:
            self.context.logger.warning(
                "on_chain_service_id or service_registry_address not configured. "
                "Skipping service owner resolution."
            )
            return None

        # Step 1: Verify this agent is registered in the on-chain service
        is_registered = yield from self._verify_agent_registration(
            service_id, registry_address
        )
        if not is_registered:
            return None

        # Step 2: Get the registry owner (may be a staking contract)
        registry_owner = yield from self._get_registry_owner(
            service_id, registry_address
        )
        if registry_owner is None:
            return None

        # Step 3: Try to resolve the real owner from a staking contract.
        # If registry_owner is a staking contract, getServiceInfo will
        # succeed and return the real owner. If it's not a staking contract,
        # the call will fail and we use registry_owner directly.
        real_owner = yield from self._get_owner_from_staking(
            registry_owner, service_id
        )
        if real_owner is not None:
            self.context.logger.info(
                f"Service {service_id} registry owner {registry_owner} "
                f"is a staking contract. Real owner: {real_owner}"
            )
            return real_owner

        self.context.logger.info(
            f"Service {service_id} registry owner {registry_owner} "
            f"is not a staking contract. Using as owner directly."
        )
        return registry_owner

    def _verify_agent_registration(
        self, service_id: int, registry_address: str
    ) -> Generator[None, None, bool]:
        """Verify this agent is registered in the on-chain service."""
        response = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_STATE,  # type: ignore
            contract_address=registry_address,
            contract_id=str(ServiceRegistryContract.contract_id),
            contract_callable="get_agent_instances",
            service_id=service_id,
        )
        if response.performative != ContractApiMessage.Performative.STATE:
            self.context.logger.error(
                f"Could not get agent instances from registry. "
                f"Expected {ContractApiMessage.Performative.STATE.value}, "  # type: ignore
                f"received {response.performative.value}."
            )
            return False

        agent_instances = response.state.body.get("agentInstances", [])
        agent_address = self.context.agent_address
        registered = any(
            inst.lower() == agent_address.lower() for inst in agent_instances
        )
        if not registered:
            self.context.logger.error(
                f"Agent {agent_address} is not registered in service {service_id}. "
                f"Registered instances: {agent_instances}. "
                f"Aborting owner resolution."
            )
        return registered

    def _get_registry_owner(
        self, service_id: int, registry_address: str
    ) -> Generator[None, None, Optional[str]]:
        """Get the service owner from the ServiceRegistry."""
        response = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_STATE,  # type: ignore
            contract_address=registry_address,
            contract_id=str(ServiceRegistryContract.contract_id),
            contract_callable="get_service_owner",
            service_id=service_id,
        )
        if response.performative != ContractApiMessage.Performative.STATE:
            self.context.logger.error(
                f"Could not get service owner from registry. "
                f"Expected {ContractApiMessage.Performative.STATE.value}, "  # type: ignore
                f"received {response.performative.value}."
            )
            return None
        return cast(str, response.state.body["service_owner"])

    def _get_owner_from_staking(
        self, staking_address: str, service_id: int
    ) -> Generator[None, None, Optional[str]]:
        """Try to get the real service owner from a staking contract.

        If the address is not a staking contract, the call will fail
        and None is returned (this is expected, not an error).
        """
        response = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_STATE,  # type: ignore
            contract_address=staking_address,
            contract_id=str(ServiceStakingTokenContract.contract_id),
            contract_callable="get_service_info",
            service_id=service_id,
        )
        if response.performative != ContractApiMessage.Performative.STATE:
            # Call failed — address is not a staking contract
            return None
        # getServiceInfo returns ServiceInfo(multisig, owner, nonces[], ...)
        # owner is at index 1
        info = response.state.body["data"]
        return cast(str, info[1])


class IdentifyServiceOwnerRoundBehaviour(AbstractRoundBehaviour):
    """This behaviour manages the consensus stages for the identify_service_owner_abci skill."""

    initial_behaviour_cls = IdentifyServiceOwnerBehaviour
    abci_app_cls = IdentifyServiceOwnerAbciApp
    behaviours: Set[Type[BaseBehaviour]] = {
        IdentifyServiceOwnerBehaviour,  # type: ignore
    }
