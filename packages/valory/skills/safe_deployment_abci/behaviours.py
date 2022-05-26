# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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

"""This module contains the data classes for the safe deployment ABCI application."""

from typing import Generator, Optional, Set, Type, cast

from aea_ledger_ethereum import EthereumApi

from packages.valory.contracts.gnosis_safe.contract import GnosisSafeContract
from packages.valory.protocols.contract_api import ContractApiMessage
from packages.valory.skills.abstract_round_abci.behaviour_utils import BaseBehaviour
from packages.valory.skills.abstract_round_abci.behaviours import AbstractRoundBehaviour
from packages.valory.skills.abstract_round_abci.common import (
    RandomnessBehaviour,
    SelectKeeperBehaviour,
)
from packages.valory.skills.safe_deployment_abci.payloads import (
    DeploySafePayload,
    RandomnessPayload,
    SelectKeeperPayload,
    ValidatePayload,
)
from packages.valory.skills.safe_deployment_abci.rounds import (
    DeploySafeRound,
    RandomnessSafeRound,
    SafeDeploymentAbciApp,
    SelectKeeperSafeRound,
    SynchronizedData,
    ValidateSafeRound,
)


class SafeDeploymentBaseBehaviour(BaseBehaviour):
    """Base behaviour for the common apps' skill."""

    @property
    def synchronized_data(self) -> SynchronizedData:
        """Return the synchronized data."""
        return cast(SynchronizedData, super().synchronized_data)


class RandomnessSafeBehaviour(RandomnessBehaviour):
    """Retrieve randomness for oracle deployment."""

    behaviour_id = "randomness_safe"
    matching_round = RandomnessSafeRound
    payload_class = RandomnessPayload


class SelectKeeperSafeBehaviour(SelectKeeperBehaviour):
    """Select the keeper agent."""

    behaviour_id = "select_keeper_safe"
    matching_round = SelectKeeperSafeRound
    payload_class = SelectKeeperPayload


class DeploySafeBehaviour(SafeDeploymentBaseBehaviour):
    """Deploy Safe."""

    behaviour_id = "deploy_safe"
    matching_round = DeploySafeRound

    def async_act(self) -> Generator:
        """
        Do the action.

        Steps:
        - If the agent is the designated deployer, then prepare the deployment
          transaction and send it.
        - Otherwise, wait until the next round.
        - If a timeout is hit, set exit A event, otherwise set done event.
        """
        if (
            self.context.agent_address
            != self.synchronized_data.most_voted_keeper_address
        ):
            yield from self._not_deployer_act()
        else:
            yield from self._deployer_act()

    def _not_deployer_act(self) -> Generator:
        """Do the non-deployer action."""
        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.wait_until_round_end()
            self.set_done()

    def _deployer_act(self) -> Generator:
        """Do the deployer action."""

        with self.context.benchmark_tool.measure(self.behaviour_id).local():
            self.context.logger.info(
                "I am the designated sender, deploying the safe contract..."
            )
            contract_address = yield from self._send_deploy_transaction()
            if contract_address is None:
                # The safe_deployment_abci app should only be used in staging.
                # If the safe contract deployment fails we abort. Alternatively,
                # we could send a None payload and then transition into an appropriate
                # round to handle the deployment failure.
                raise RuntimeError("Safe deployment failed!")  # pragma: nocover
            payload = DeploySafePayload(self.context.agent_address, contract_address)

        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            self.context.logger.info(f"Safe contract address: {contract_address}")
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()

    def _send_deploy_transaction(self) -> Generator[None, None, Optional[str]]:
        owners = self.synchronized_data.sorted_participants
        threshold = self.params.consensus_params.consensus_threshold
        contract_api_response = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_DEPLOY_TRANSACTION,  # type: ignore
            contract_address=None,
            contract_id=str(GnosisSafeContract.contract_id),
            contract_callable="get_deploy_transaction",
            owners=owners,
            threshold=threshold,
            deployer_address=self.context.agent_address,
        )
        if (
            contract_api_response.performative
            != ContractApiMessage.Performative.RAW_TRANSACTION
        ):  # pragma: nocover
            self.context.logger.warning("get_deploy_transaction unsuccessful!")
            return None
        contract_address = cast(
            str, contract_api_response.raw_transaction.body.pop("contract_address")
        )
        tx_digest, _ = yield from self.send_raw_transaction(
            contract_api_response.raw_transaction
        )
        if tx_digest is None:  # pragma: nocover
            self.context.logger.warning("send_raw_transaction unsuccessful!")
            return None
        tx_receipt = yield from self.get_transaction_receipt(
            tx_digest,
            self.params.retry_timeout,
            self.params.retry_attempts,
        )
        if tx_receipt is None:  # pragma: nocover
            self.context.logger.warning("get_transaction_receipt unsuccessful!")
            return None
        _ = EthereumApi.get_contract_address(
            tx_receipt
        )  # returns None as the contract is created via a proxy
        self.context.logger.info(f"Deployment tx digest: {tx_digest}")
        return contract_address


class ValidateSafeBehaviour(SafeDeploymentBaseBehaviour):
    """Validate Safe."""

    behaviour_id = "validate_safe"
    matching_round = ValidateSafeRound

    def async_act(self) -> Generator:
        """
        Do the action.

        Steps:
        - Validate that the contract address provided by the keeper points to a
          valid contract.
        - Send the transaction with the validation result and wait for it to be
          mined.
        - Wait until ABCI application transitions to the next round.
        - Go to the next behaviour (set done event).
        """

        with self.context.benchmark_tool.measure(self.behaviour_id).local():
            is_correct = yield from self.has_correct_contract_been_deployed()
            payload = ValidatePayload(self.context.agent_address, is_correct)

        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()

    def has_correct_contract_been_deployed(self) -> Generator[None, None, bool]:
        """Contract deployment verification."""
        contract_api_response = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_STATE,  # type: ignore
            contract_address=self.synchronized_data.safe_contract_address,
            contract_id=str(GnosisSafeContract.contract_id),
            contract_callable="verify_contract",
        )
        if (
            contract_api_response.performative != ContractApiMessage.Performative.STATE
        ):  # pragma: nocover
            self.context.logger.warning("verify_contract unsuccessful!")
            return False
        verified = cast(bool, contract_api_response.state.body["verified"])
        return verified


class SafeDeploymentRoundBehaviour(AbstractRoundBehaviour):
    """This behaviour manages the consensus stages for the safe deployment."""

    initial_behaviour_cls = RandomnessSafeBehaviour
    abci_app_cls = SafeDeploymentAbciApp  # type: ignore
    behaviours: Set[Type[BaseBehaviour]] = {  # type: ignore
        RandomnessSafeBehaviour,  # type: ignore
        SelectKeeperSafeBehaviour,  # type: ignore
        DeploySafeBehaviour,  # type: ignore
        ValidateSafeBehaviour,  # type: ignore
    }
