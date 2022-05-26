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

"""This module contains the data classes for the oracle deployment ABCI application."""

from typing import Generator, Optional, Set, Type, cast

from aea_ledger_ethereum import EthereumApi

from packages.valory.contracts.offchain_aggregator.contract import (
    OffchainAggregatorContract,
)
from packages.valory.protocols.contract_api import ContractApiMessage
from packages.valory.skills.abstract_round_abci.behaviour_utils import BaseBehaviour
from packages.valory.skills.abstract_round_abci.behaviours import AbstractRoundBehaviour
from packages.valory.skills.abstract_round_abci.common import (
    RandomnessBehaviour,
    SelectKeeperBehaviour,
)
from packages.valory.skills.oracle_deployment_abci.models import Params
from packages.valory.skills.oracle_deployment_abci.payloads import (
    DeployOraclePayload,
    RandomnessPayload,
    SelectKeeperPayload,
    ValidateOraclePayload,
)
from packages.valory.skills.oracle_deployment_abci.rounds import (
    DeployOracleRound,
    OracleDeploymentAbciApp,
    RandomnessOracleRound,
    SelectKeeperOracleRound,
    SynchronizedData,
    ValidateOracleRound,
)


class OracleDeploymentBaseBehaviour(BaseBehaviour):
    """Base behaviour for the common apps' skill."""

    @property
    def synchronized_data(self) -> SynchronizedData:
        """Return the synchronized data."""
        return cast(SynchronizedData, super().synchronized_data)

    @property
    def params(self) -> Params:
        """Return the synchronized data."""
        return cast(Params, super().params)


class RandomnessOracleBehaviour(RandomnessBehaviour):
    """Retrieve randomness for oracle deployment."""

    behaviour_id = "retrieve_randomness_oracle"
    matching_round = RandomnessOracleRound
    payload_class = RandomnessPayload


class SelectKeeperOracleBehaviour(SelectKeeperBehaviour):
    """Select the keeper agent."""

    behaviour_id = "select_keeper_oracle"
    matching_round = SelectKeeperOracleRound
    payload_class = SelectKeeperPayload


class DeployOracleBehaviour(OracleDeploymentBaseBehaviour):
    """Deploy oracle."""

    behaviour_id = "deploy_oracle"
    matching_round = DeployOracleRound

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
                "I am the designated sender, deploying the oracle contract..."
            )
            contract_address = yield from self._send_deploy_transaction()
            if contract_address is None:
                # The oracle_deployment_abci app should only be used in staging.
                # If the oracle contract deployment fails we abort. Alternatively,
                # we could send a None payload and then transition into an appropriate
                # round to handle the deployment failure.
                raise RuntimeError("Oracle deployment failed!")  # pragma: nocover
            payload = DeployOraclePayload(self.context.agent_address, contract_address)

        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            self.context.logger.info(f"Oracle contract address: {contract_address}")
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()

    def _send_deploy_transaction(self) -> Generator[None, None, Optional[str]]:
        min_answer = self.params.oracle_params["min_answer"]
        max_answer = self.params.oracle_params["max_answer"]
        decimals = self.params.oracle_params["decimals"]
        description = self.params.oracle_params["description"]
        contract_api_response = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_DEPLOY_TRANSACTION,  # type: ignore
            contract_address=None,
            contract_id=str(OffchainAggregatorContract.contract_id),
            contract_callable="get_deploy_transaction",
            deployer_address=self.context.agent_address,
            _minAnswer=min_answer,
            _maxAnswer=max_answer,
            _decimals=decimals,
            _description=description,
            _transmitters=[self.synchronized_data.safe_contract_address],
        )
        if (
            contract_api_response.performative
            != ContractApiMessage.Performative.RAW_TRANSACTION
        ):  # pragma: nocover
            self.context.logger.warning("get_deploy_transaction unsuccessful!")
            return None
        tx_digest, _ = yield from self.send_raw_transaction(
            contract_api_response.raw_transaction
        )
        if tx_digest is None:  # pragma: nocover
            self.context.logger.warning("send_raw_transaction unsuccessful!")
            return None
        tx_receipt = yield from self.get_transaction_receipt(tx_digest)
        if tx_receipt is None:  # pragma: nocover
            self.context.logger.warning("get_transaction_receipt unsuccessful!")
            return None
        contract_address = EthereumApi.get_contract_address(tx_receipt)
        self.context.logger.info(f"Deployment tx digest: {tx_digest}")
        return contract_address


class ValidateOracleBehaviour(OracleDeploymentBaseBehaviour):
    """Validate oracle."""

    behaviour_id = "validate_oracle"
    matching_round = ValidateOracleRound

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
            payload = ValidateOraclePayload(self.context.agent_address, is_correct)

        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()

    def has_correct_contract_been_deployed(self) -> Generator[None, None, bool]:
        """Contract deployment verification."""
        contract_api_response = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_STATE,  # type: ignore
            contract_address=self.synchronized_data.oracle_contract_address,
            contract_id=str(OffchainAggregatorContract.contract_id),
            contract_callable="verify_contract",
        )
        if (
            contract_api_response.performative != ContractApiMessage.Performative.STATE
        ):  # pragma: nocover
            self.context.logger.warning("verify_contract unsuccessful!")
            return False
        verified = cast(bool, contract_api_response.state.body["verified"])
        return verified


class OracleDeploymentRoundBehaviour(AbstractRoundBehaviour):
    """This behaviour manages the consensus stages for the oracle deployment."""

    initial_behaviour_cls = RandomnessOracleBehaviour
    abci_app_cls = OracleDeploymentAbciApp
    behaviours: Set[Type[BaseBehaviour]] = {  # type: ignore
        RandomnessOracleBehaviour,  # type: ignore
        SelectKeeperOracleBehaviour,  # type: ignore
        DeployOracleBehaviour,  # type: ignore
        ValidateOracleBehaviour,  # type: ignore
    }
