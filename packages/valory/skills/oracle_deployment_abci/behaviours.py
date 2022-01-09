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

"""This module contains the data classes for the oracle deployment ABCI application."""

from typing import Generator, Optional, cast

from aea_ledger_ethereum import EthereumApi

from packages.valory.contracts.offchain_aggregator.contract import (
    OffchainAggregatorContract,
)
from packages.valory.protocols.contract_api import ContractApiMessage
from packages.valory.skills.abstract_round_abci.behaviour_utils import BaseState
from packages.valory.skills.abstract_round_abci.common import (
    RandomnessBehaviour,
    SelectKeeperBehaviour,
)
from packages.valory.skills.abstract_round_abci.utils import BenchmarkTool
from packages.valory.skills.oracle_deployment_abci.models import Params
from packages.valory.skills.oracle_deployment_abci.payloads import (
    DeployOraclePayload,
    RandomnessPayload,
    SelectKeeperPayload,
    ValidateOraclePayload,
)
from packages.valory.skills.oracle_deployment_abci.rounds import (
    DeployOracleRound,
    PeriodState,
    RandomnessOracleRound,
    SelectKeeperOracleRound,
    ValidateOracleRound,
)


benchmark_tool = BenchmarkTool()


class OracleDeploymentBaseState(BaseState):
    """Base state behaviour for the common apps skill."""

    @property
    def period_state(self) -> PeriodState:
        """Return the period state."""
        return cast(PeriodState, super().period_state)

    @property
    def params(self) -> Params:
        """Return the period state."""
        return cast(Params, super().params)


class RandomnessOracleBehaviour(RandomnessBehaviour):
    """Retrieve randomness for oracle deployment."""

    state_id = "retrieve_randomness_oracle"
    matching_round = RandomnessOracleRound
    payload_class = RandomnessPayload


class SelectKeeperOracleBehaviour(SelectKeeperBehaviour):
    """Select the keeper agent."""

    state_id = "select_keeper_oracle"
    matching_round = SelectKeeperOracleRound
    payload_class = SelectKeeperPayload


class DeployOracleBehaviour(OracleDeploymentBaseState):
    """Deploy oracle."""

    state_id = "deploy_oracle"
    matching_round = DeployOracleRound

    def async_act(self) -> Generator:
        """Do the action.

        Steps:
        - If the agent is the designated deployer, then prepare the deployment
          transaction and send it.
        - Otherwise, wait until the next round.
        - If a timeout occurs, set exit event, otherwise set done event.
        """
        if self.context.agent_address != self.period_state.most_voted_keeper_address:
            yield from self._not_deployer_act()
        else:
            yield from self._deployer_act()

    def _not_deployer_act(self) -> Generator:
        """Do the non-deployer action: wait till the end of the round"""

        with benchmark_tool.measure(self).consensus():
            yield from self.wait_until_round_end()
            self.set_done()

    def _deployer_act(self) -> Generator:
        """Do the deployer action: deploy the oracle

        Steps:
        - send the deployment transaction and return the contract address
        - initialize an oracle deployment payload
        - send the a2a transaction, awaiting delivery response or timeout
        - wait till the end of the ABCI
        - set done to signal readiness to transition to the next state

        :yields: None
        """

        with benchmark_tool.measure(self).local():
            self.context.logger.info(
                "I am the designated sender, deploying the oracle contract..."
            )
            contract_address = yield from self._send_deploy_transaction()
            if contract_address is None:
                raise RuntimeError(
                    "No contract address, oracle deployment failed!"
                )  # pragma: nocover
            payload = DeployOraclePayload(self.context.agent_address, contract_address)

        with benchmark_tool.measure(self).consensus():
            self.context.logger.info(f"Oracle contract address: {contract_address}")
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()

    def _send_deploy_transaction(self) -> Generator[None, None, Optional[str]]:
        """Send the deployment transaction

        Steps:
        - obtain a contract safe transaction hash (contract api response)
        - send the raw transaction to the ledger, obtain the transaction digest
        - send the transaction digest to obtain a receipt that confirms
          the transaction existence on the blockchain
        - obtain and return the contract address from the receipt

        :yields: None
        :returns: Optional[str]
        """

        performative = ContractApiMessage.Performative.GET_DEPLOY_TRANSACTION
        contract_api_response = yield from self.get_contract_api_response(
            performative=performative,  # type: ignore
            contract_address=None,
            contract_id=str(OffchainAggregatorContract.contract_id),
            contract_callable="get_deploy_transaction",
            deployer_address=self.context.agent_address,
            _minAnswer=self.params.oracle_params["min_answer"],
            _maxAnswer=self.params.oracle_params["max_answer"],
            _decimals=self.params.oracle_params["decimals"],
            _description=self.params.oracle_params["description"],
            _transmitters=[self.period_state.safe_contract_address],
            gas=10 ** 7,
        )
        if (
            contract_api_response.performative
            != ContractApiMessage.Performative.RAW_TRANSACTION
        ):  # pragma: nocover
            self.context.logger.warning("get_deploy_transaction unsuccessful!")
            return None
        tx_digest = yield from self.send_raw_transaction(
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


class ValidateOracleBehaviour(OracleDeploymentBaseState):
    """Validate oracle."""

    state_id = "validate_oracle"
    matching_round = ValidateOracleRound

    def async_act(self) -> Generator:
        """
        Do the action.

        Steps:
        - Validate that the contract address provided by the keeper
          points to a valid contract.
        - Send the transaction with the validation result
          and wait for it to be mined.
        - Wait until ABCI application transitions to the next round.
        - Go to the next behaviour state (set done event).
        """

        with benchmark_tool.measure(self).local():
            is_correct = yield from self.has_correct_contract_been_deployed()
            payload = ValidateOraclePayload(self.context.agent_address, is_correct)

        with benchmark_tool.measure(self).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()

    def has_correct_contract_been_deployed(self) -> Generator[None, None, bool]:
        """Contract deployment verification.

        Obtain a contract safe transaction hash (contract api response) from
        the shared period state to verify that the correct oracle contract has
        been replayed

        :yields: None
        :return: bool
        """
        contract_api_response = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_STATE,  # type: ignore
            contract_address=self.period_state.oracle_contract_address,
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
