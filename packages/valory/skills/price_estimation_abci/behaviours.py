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

"""This module contains the behaviours for the 'abci' skill."""
import datetime
from functools import partial
from typing import Callable, Generator, cast

from aea.skills.behaviours import FSMBehaviour
from web3.types import Wei

from packages.fetchai.protocols.signing import SigningMessage
from packages.valory.skills.abstract_round_abci.behaviour_utils import (
    BaseState,
    DONE_EVENT,
)
from packages.valory.skills.price_estimation_abci.helpers.gnosis_safe import (
    get_deploy_safe_tx,
)
from packages.valory.skills.price_estimation_abci.models.payloads import (
    DeploySafePayload,
    EstimatePayload,
    FinalizationTxPayload,
    ObservationPayload,
    RegistrationPayload,
    SignaturePayload,
)
from packages.valory.skills.price_estimation_abci.models.rounds import (
    CollectObservationRound,
    CollectSignatureRound,
    ConsensusReachedRound,
    DeploySafeRound,
    EstimateConsensusRound,
    FinalizationRound,
    RegistrationRound,
)


SIGNATURE_LENGTH = 65


class PriceEstimationConsensusBehaviour(FSMBehaviour):
    """This behaviour manages the consensus stages for the price estimation."""

    def setup(self) -> None:
        """Set up the behaviour."""
        # initial delay to wait synchronization with Tendermint
        self.register_state(
            "initial_delay",
            InitialDelayState(name="initial_delay", skill_context=self.context),
            initial=True,
        )
        self.register_state(
            "register",
            RegistrationBehaviour(name="register", skill_context=self.context),
        )
        self.register_state(
            "deploy_safe",
            DeploySafeBehaviour(name="deploy_safe", skill_context=self.context),
        )
        self.register_state(
            "observe",
            ObserveBehaviour(name="observe", skill_context=self.context),
        )
        self.register_state(
            "estimate",
            EstimateBehaviour(name="estimate", skill_context=self.context),
        )
        self.register_state(
            "signature",
            SignatureBehaviour(name="signature", skill_context=self.context),
        )
        self.register_state(
            "finalize",
            FinalizeBehaviour(name="finalize", skill_context=self.context),
        )
        self.register_state(
            "end",
            EndBehaviour(name="end", skill_context=self.context),
        )

        self.register_transition("initial_delay", "register", DONE_EVENT)
        self.register_transition("register", "deploy_safe", DONE_EVENT)
        self.register_transition("deploy_safe", "observe", DONE_EVENT)
        self.register_transition("observe", "estimate", DONE_EVENT)
        self.register_transition("estimate", "signature", DONE_EVENT)
        self.register_transition("signature", "finalize", DONE_EVENT)
        self.register_transition("finalize", "end", DONE_EVENT)

    def teardown(self) -> None:
        """Tear down the behaviour"""

    def get_wait_tendermint_rpc_is_ready(self) -> Callable:
        """
        Wait Tendermint RPC server is up.

        This method will return a function that returns
        False until 'initial_delay' seconds (a skill parameter)
        have elapsed since the call of the method.

        :return: the function used to wait.
        """

        def _check_time(expected_time: datetime.datetime) -> bool:
            return datetime.datetime.now() > expected_time

        initial_delay = self.context.params.initial_delay
        date = datetime.datetime.now() + datetime.timedelta(0, initial_delay)
        return partial(_check_time, date)

    def wait_observation_round(self) -> bool:
        """Wait registration threshold is reached."""
        return (
            self.context.state.period.current_round_id
            == CollectObservationRound.round_id
        )

    def wait_estimate_round(self) -> bool:
        """Wait observation threshold is reached."""
        return (
            self.context.state.period.current_round_id
            == EstimateConsensusRound.round_id
        )

    def wait_consensus_round(self) -> bool:
        """Wait estimate threshold is reached."""
        return (
            self.context.state.period.current_round_id == ConsensusReachedRound.round_id
        )


class InitialDelayState(BaseState):  # pylint: disable=too-many-ancestors
    """Wait for some seconds until Tendermint nodes are running."""

    def async_act(self) -> None:  # type: ignore
        """Do the action."""
        delay = self.context.params.initial_delay
        yield from self.sleep(delay)
        self.set_done()


class RegistrationBehaviour(BaseState):  # pylint: disable=too-many-ancestors
    """Register to the next round."""

    def async_act(self) -> None:  # type: ignore
        """
        Do the action.

        Steps:
        - Build a registration transaction
        - Send the transaction and wait for it to be mined
        - Wait until ABCI application transitions to the next round.
        - Go to the next behaviour state.
        """
        self._log_start()
        payload = RegistrationPayload(self.context.agent_address)
        stop_condition = self.is_round_ended(RegistrationRound.round_id)
        yield from self._send_transaction(payload, stop_condition=stop_condition)
        yield from self.wait_until_round_end(RegistrationRound.round_id)
        self._log_end()
        self.set_done()


class DeploySafeBehaviour(BaseState):  # pylint: disable=too-many-ancestors
    """Deploy Safe."""

    def async_act(self) -> None:  # type: ignore
        """
        Do the action.

        Steps:
        - TODO
        """
        self._log_start()
        if self.context.agent_address != self.period_state.safe_sender_address:
            self.not_deployer_act()
        else:
            yield from self.deployer_act()
        yield from self.wait_until_round_end(DeploySafeRound.round_id)
        self._log_end()
        self.set_done()

    def not_deployer_act(self) -> None:
        """Do the non-deployer action."""
        self.context.logger.info(
            "I am not the designated sender, waiting until next round..."
        )

    def deployer_act(self) -> None:
        """Do the deployer action."""
        self.context.logger.info(
            "I am the designated sender, deploying the safe contract..."
        )
        contract_address = yield from self._send_deploy_transaction()
        payload = DeploySafePayload(self.context.agent_address, contract_address)
        stop_condition = self.is_round_ended(DeploySafeRound.round_id)
        yield from self._send_transaction(payload, stop_condition=stop_condition)

    def _send_deploy_transaction(self):
        ethereum_node_url = self.context.params.ethereum_node_url
        owners = self.period_state.participants
        threshold = self.context.params.consensus_params.two_thirds_threshold
        tx_params, contract_address = get_deploy_safe_tx(
            ethereum_node_url, self.context.agent_address, list(owners), threshold
        )
        tx_hash = yield from self._send_raw_transaction(tx_params)
        self.context.logger.info(f"Tx hash: {tx_hash}")
        return contract_address


class ObserveBehaviour(BaseState):  # pylint: disable=too-many-ancestors
    """Observe price estimate."""

    def async_act(self) -> Generator:
        """
        Do the action.

        Steps:
        - Ask the configured API the price of a currency
        - Build an observation transaction
        - Wait until ABCI application transitions to the next round.
        - Go to the next behaviour state.
        """
        self._log_start()
        currency_id = self.context.params.currency_id
        convert_id = self.context.params.convert_id
        observation = self.context.price_api.get_price(currency_id, convert_id)
        self.context.logger.info(
            f"Got observation of {currency_id} price in {convert_id} from {self.context.price_api.api_id}: {observation}"
        )
        payload = ObservationPayload(self.context.agent_address, observation)
        stop_condition = self.is_round_ended(CollectObservationRound.round_id)
        yield from self._send_transaction(payload, stop_condition=stop_condition)
        yield from self.wait_until_round_end(CollectObservationRound.round_id)
        self._log_end()
        self.set_done()


class EstimateBehaviour(BaseState):  # pylint: disable=too-many-ancestors
    """Estimate price."""

    def async_act(self) -> Generator:
        """
        Do the action.

        Steps:
        - Run the script to compute the estimate starting from the shared observations
        - Build an estimate transaction
        - Send the transaction and wait for it to be mined
        - Wait until ABCI application transitions to the next round.
        - Go to the next behaviour state.
        """
        self._log_start()
        currency_id = self.context.params.currency_id
        convert_id = self.context.params.convert_id
        observation_payloads = self.period_state.observations
        observations = [obs_payload.observation for obs_payload in observation_payloads]
        self.context.logger.info(
            f"Using observations {observations} to compute the estimate."
        )
        estimate = self.context.estimator.aggregate(observations)
        self.context.logger.info(
            f"Got estimate of {currency_id} price in {convert_id}: {estimate}"
        )
        payload = EstimatePayload(self.context.agent_address, estimate)
        stop_condition = self.is_round_ended(EstimateConsensusRound.round_id)
        yield from self._send_transaction(payload, stop_condition=stop_condition)
        yield from self.wait_until_round_end(EstimateConsensusRound.round_id)
        self._log_end()
        self.set_done()


class SignatureBehaviour(BaseState):  # pylint: disable=too-many-ancestors
    """Signature state."""

    is_programmatically_defined = True

    def async_act(self) -> Generator:
        """Do the act."""
        self._log_start()
        final_estimate = self.period_state.most_voted_estimate
        self.context.logger.info(f"Consensus reached on estimate: {final_estimate}")
        encoded_estimate = self.period_state.encoded_estimate
        signature_hex = yield from self._get_safe_tx_signature(encoded_estimate)
        payload = SignaturePayload(self.context.agent_address, signature_hex)
        stop_condition = self.is_round_ended(CollectSignatureRound.round_id)
        yield from self._send_transaction(payload, stop_condition=stop_condition)
        yield from self.wait_until_round_end(CollectSignatureRound.round_id)
        self._log_end()
        self.set_done()

    def _get_safe_tx_signature(self, data: bytes):
        safe_tx = self._get_safe_tx(data)
        # is_deprecated_mode=True because we want to call Account.signHash,
        # which is the same used by gnosis-py
        self._send_signing_request(safe_tx.safe_tx_hash, is_deprecated_mode=True)
        signature_response = yield from self.wait_for_message()
        signature_hex = cast(SigningMessage, signature_response).signed_message.body
        # remove the leading '0x'
        signature_hex = signature_hex[2:]
        return signature_hex


class FinalizeBehaviour(BaseState):  # pylint: disable=too-many-ancestors
    """Finalize state."""

    is_programmatically_defined = True

    def async_act(self) -> None:
        """Do the act."""
        self._log_start()
        if self.context.agent_address != self.period_state.safe_sender_address:
            self.not_deployer_act()
        else:
            yield from self.deployer_act()
        yield from self.wait_until_round_end(FinalizationRound.round_id)
        self._log_end()
        self._log_end()
        self.set_done()

    def not_deployer_act(self) -> None:
        """Do the non-deployer action."""
        self.context.logger.info(
            "I am not the designated sender, waiting until next round..."
        )

    def deployer_act(self) -> None:
        """Do the deployer action."""
        self.context.logger.info(
            "I am the designated sender, sending the safe transaction..."
        )
        tx_hash = yield from self._send_safe_transaction()
        payload = FinalizationTxPayload(self.context.agent_address, tx_hash)
        stop_condition = self.is_round_ended(DeploySafeRound.round_id)
        yield from self._send_transaction(payload, stop_condition=stop_condition)

    def _send_safe_transaction(self) -> str:
        """Send a Safe transaction using the participants' signatures."""
        sorted_addresses = self.period_state.sorted_addresses
        data = self.period_state.encoded_estimate

        # compose final signature (need to be sorted!)
        final_signature = ""
        for signer, signature in self.period_state.participant_to_signature.items():
            signer_index = sorted_addresses.index(signer)
            final_signature = (
                final_signature[: 65 * signer_index]
                + signature
                + final_signature[65 * signer_index :]
            )

        safe_tx = self._get_safe_tx(data)
        safe_tx.signatures = final_signature
        safe_tx.call(self.context.agent_address)

        tx_gas_price = safe_tx.gas_price or safe_tx.w3.eth.gas_price
        tx_parameters = {
            "from": self.context.agent_address,
            "gasPrice": tx_gas_price,
        }
        tx = safe_tx.w3_tx.buildTransaction(tx_parameters)
        tx["gas"] = Wei(max(tx["gas"] + 75000, safe_tx.recommended_gas()))

        safe_tx.w3_tx.buildTransaction(tx_parameters)

        tx_hash = yield from self._send_raw_transaction(tx_parameters)
        return tx_hash


class EndBehaviour(BaseState):  # pylint: disable=too-many-ancestors
    """Final state."""

    is_programmatically_defined = True

    def async_act(self) -> None:
        """Do the act."""
        final_estimate = self.period_state.most_voted_estimate
        self.context.logger.info(f"Consensus reached on estimate: {final_estimate}")
        self.context.logger.info(
            f"Signatures: {self.context.state.period_state.participant_to_signature}"
        )
        self.set_done()
