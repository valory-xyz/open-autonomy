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
import binascii
import json
import pprint
from abc import ABC
from datetime import datetime
from typing import Generator, cast

from packages.fetchai.connections.ledger.base import (
    CONNECTION_ID as LEDGER_CONNECTION_PUBLIC_ID,
)
from packages.fetchai.protocols.signing import SigningMessage
from packages.valory.contracts.gnosis_safe.contract import GnosisSafeContract
from packages.valory.skills.abstract_round_abci.behaviour_utils import (
    BaseState,
    DONE_EVENT,
)
from packages.valory.skills.abstract_round_abci.behaviours import (
    AbstractRoundBehaviour,
    TransitionFunction,
)
from packages.valory.skills.price_estimation_abci.models.payloads import (
    DeploySafePayload,
    EstimatePayload,
    FinalizationTxPayload,
    ObservationPayload,
    RegistrationPayload,
    SignaturePayload,
    TransactionHashPayload,
)
from packages.valory.skills.price_estimation_abci.models.rounds import (
    CollectObservationRound,
    CollectSignatureRound,
    DeploySafeRound,
    EstimateConsensusRound,
    FinalizationRound,
    PeriodState,
    RegistrationRound,
    TxHashRound,
)


SIGNATURE_LENGTH = 65
LEDGER_API_ADDRESS = str(LEDGER_CONNECTION_PUBLIC_ID)


class PriceEstimationBaseState(BaseState, ABC):  # pylint: disable=too-many-ancestors
    """Base state behaviour for the price estimation skill."""

    @property
    def period_state(self) -> PeriodState:
        """Return the period state."""
        return cast(PeriodState, self.context.state.period_state)


class TendermintHealthcheck(
    PriceEstimationBaseState
):  # pylint: disable=too-many-ancestors
    """Check whether Tendermint nodes are running."""

    state_id = "tendermint_healthcheck"

    def async_act(self) -> None:  # type: ignore
        """Check whether tendermint is running or not."""
        request_message, http_dialogue = self._build_http_request_message(
            "GET",
            self.context.params.tendermint_url + "/health",
        )
        result = yield from self._do_request(request_message, http_dialogue)
        try:
            json.loads(result.body.decode())
            self.context.logger.info("Tendermint running.")
            self.set_done()
        except json.JSONDecodeError:
            self.context.logger.error("Tendermint not running, trying again!")
            yield from self.sleep(1)


class RegistrationBehaviour(  # pylint: disable=too-many-ancestors
    PriceEstimationBaseState
):
    """Register to the next round."""

    state_id = "register"
    matching_round = RegistrationRound

    def async_act(self) -> None:  # type: ignore
        """
        Do the action.

        Steps:
        - Build a registration transaction
        - Send the transaction and wait for it to be mined.
        - Wait until ABCI application transitions to the next round.
        - Go to the next behaviour state.
        """
        payload = RegistrationPayload(self.context.agent_address)
        yield from self.send_a2a_transaction(payload)
        yield from self.wait_until_round_end()
        self.set_done()


class DeploySafeBehaviour(  # pylint: disable=too-many-ancestors
    PriceEstimationBaseState
):
    """Deploy Safe."""

    state_id = "deploy_safe"
    matching_round = DeploySafeRound
    _deploy_start_time = datetime.now()

    def async_act(self) -> Generator:
        """
        Do the action.

        If the agent is the designated deployer, then prepare the
        deployment transaction and send it.
        Otherwise, wait until the next round.
        """
        if self.context.agent_address != self.period_state.safe_sender_address:
            self._not_deployer_act()
        else:
            yield from self._deployer_act()
        yield from self.wait_until_round_end()
        self.context.logger.info(
            f"Safe contract address: {self.period_state.safe_contract_address}"
        )
        self.set_done()

    def _not_deployer_act(self) -> None:
        """Do the non-deployer action."""
        # Skip keeper every 5 seconds
        if (datetime.now() - self._deploy_start_time).seconds >= 5.0:
            self.period_state._skipped_keepers += 1
            self._deploy_start_time = datetime.now()

        self.context.logger.info(
            "I am not the designated sender, waiting until next round..."
        )

    def _deployer_act(self) -> Generator:
        """Do the deployer action."""
        self.context.logger.info(
            "I am the designated sender, deploying the safe contract..."
        )
        contract_address = yield from self._send_deploy_transaction()
        payload = DeploySafePayload(self.context.agent_address, contract_address)
        yield from self.send_a2a_transaction(payload)

    def _send_deploy_transaction(self) -> Generator[None, None, str]:
        owners = list(self.period_state.participants)
        threshold = self.context.params.consensus_params.two_thirds_threshold
        contract_api_response = yield from self.get_contract_api_response(
            contract_address=None,
            contract_id=str(GnosisSafeContract.contract_id),
            contract_callable="get_deploy_transaction",
            owners=owners,
            threshold=threshold,
            deployer_address=self.context.agent_address,
        )
        contract_address = cast(
            str, contract_api_response.raw_transaction.body.pop("contract_address")
        )
        tx_hash = yield from self.send_raw_transaction(
            contract_api_response.raw_transaction
        )
        self.context.logger.info(f"Deployment tx hash: {tx_hash}")
        return contract_address


class ObserveBehaviour(PriceEstimationBaseState):  # pylint: disable=too-many-ancestors
    """Observe price estimate."""

    state_id = "observe"
    matching_round = CollectObservationRound

    _number_of_retries = 0
    _retries = 0

    def async_act(self) -> Generator:
        """
        Do the action.

        Steps:
        - Ask the configured API the price of a currency
        - Build an observation transaction
        - Wait until ABCI application transitions to the next round.
        - Go to the next behaviour state.
        """
        currency_id = self.context.params.currency_id
        convert_id = self.context.params.convert_id

        if not self._number_of_retries:
            self._number_of_retries = self.context.price_api.retries
            self._retries = 0

        api_specs = self.context.price_api.get_spec(currency_id, convert_id)
        http_message, http_dialogue = self._build_http_request_message(
            method="GET",
            url=api_specs["url"],
            headers=api_specs["headers"],
            parameters=api_specs["parameters"],
        )
        response = yield from self._do_request(http_message, http_dialogue)
        observation = self.context.price_api.post_request_process(response)

        if observation:
            self.context.logger.info(
                f"Got observation of {currency_id} price in "
                + f"{convert_id} from {self.context.price_api.api_id}: "
                + f"{observation}"
            )
            payload = ObservationPayload(self.context.agent_address, observation)
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()
            self.set_done()
        else:
            self.context.logger.info(
                f"Could not get price from {self.context.price_api.api_id} "
                + "Trying Again"
            )

            self._retries += 1
            if self._retries > self._number_of_retries:
                raise RuntimeError("Max retries reached.")


class EstimateBehaviour(PriceEstimationBaseState):  # pylint: disable=too-many-ancestors
    """Estimate price."""

    state_id = "estimate"
    matching_round = EstimateConsensusRound

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
        yield from self.send_a2a_transaction(payload)
        yield from self.wait_until_round_end()
        self.set_done()


class TransactionHashBehaviour(  # pylint: disable=too-many-ancestors
    PriceEstimationBaseState
):
    """Share the transaction hash for the signature round."""

    state_id = "tx_hash"
    matching_round = TxHashRound

    def async_act(self) -> Generator:
        """
        Do the action.

        Steps:
        - TODO
        """
        data = self.period_state.encoded_estimate
        contract_api_msg = yield from self.get_contract_api_response(
            contract_address=self.period_state.safe_contract_address,
            contract_id=str(GnosisSafeContract.contract_id),
            contract_callable="get_raw_safe_transaction_hash",
            to_address=self.period_state.safe_sender_address,  # keeper address
            value=0,
            data=data,
        )
        safe_tx_hash = cast(str, contract_api_msg.raw_transaction.body["tx_hash"])
        safe_tx_hash = safe_tx_hash[2:]
        self.context.logger.info(f"Hash of the Safe transaction: {safe_tx_hash}")
        payload = TransactionHashPayload(self.context.agent_address, safe_tx_hash)
        yield from self.send_a2a_transaction(payload)
        yield from self.wait_until_round_end()
        self.set_done()


class SignatureBehaviour(  # pylint: disable=too-many-ancestors
    PriceEstimationBaseState
):
    """Signature state."""

    state_id = "sign"
    matching_round = CollectSignatureRound

    def async_act(self) -> Generator:
        """Do the act."""
        self.context.logger.info(
            f"Consensus reached on tx hash: {self.period_state.most_voted_tx_hash}"
        )
        signature_hex = yield from self._get_safe_tx_signature()
        payload = SignaturePayload(self.context.agent_address, signature_hex)
        yield from self.send_a2a_transaction(payload)
        yield from self.wait_until_round_end()
        self.set_done()

    def _get_safe_tx_signature(self) -> Generator[None, None, str]:
        # is_deprecated_mode=True because we want to call Account.signHash,
        # which is the same used by gnosis-py
        safe_tx_hash_bytes = binascii.unhexlify(self.period_state.most_voted_tx_hash)
        self._send_signing_request(safe_tx_hash_bytes, is_deprecated_mode=True)
        signature_response = yield from self.wait_for_message()
        signature_hex = cast(SigningMessage, signature_response).signed_message.body
        # remove the leading '0x'
        signature_hex = signature_hex[2:]
        self.context.logger.info(f"Signature: {signature_hex}")
        return signature_hex


class FinalizeBehaviour(PriceEstimationBaseState):  # pylint: disable=too-many-ancestors
    """Finalize state."""

    state_id = "finalize"
    matching_round = FinalizationRound
    _finalization_start_time = datetime.now()

    def async_act(self) -> Generator[None, None, None]:
        """Do the act."""
        if self.context.agent_address != self.period_state.safe_sender_address:
            self._not_sender_act()
        else:
            yield from self._sender_act()
        yield from self.wait_until_round_end()
        self.set_done()

    def _not_sender_act(self) -> None:
        """Do the non-sender action."""
        # Skip keeper every 5 seconds
        if (datetime.now() - self._finalization_start_time).seconds >= 5.0:
            self.period_state._skipped_keepers += 1
            self._finalization_start_time = datetime.now()

        self.context.logger.info(
            "I am not the designated sender, waiting until next round..."
        )

    def _sender_act(self) -> Generator[None, None, None]:
        """Do the sender action."""
        self.context.logger.info(
            "I am the designated sender, sending the safe transaction..."
        )
        tx_hash = yield from self._send_safe_transaction()
        self.context.logger.info(
            f"Transaction hash of the final transaction: {tx_hash}"
        )
        self.context.logger.info(
            f"Signatures: {pprint.pformat(self.context.state.period_state.participant_to_signature)}"
        )
        payload = FinalizationTxPayload(self.context.agent_address, tx_hash)
        yield from self.send_a2a_transaction(payload)

    def _send_safe_transaction(self) -> Generator[None, None, str]:
        """Send a Safe transaction using the participants' signatures."""
        contract_api_msg = yield from self.get_contract_api_response(
            contract_address=self.period_state.safe_contract_address,
            contract_id=str(GnosisSafeContract.contract_id),
            contract_callable="get_raw_safe_transaction",
            sender_address=self.context.agent_address,
            owners=tuple(self.period_state.participants),
            to_address=self.context.agent_address,
            value=0,
            data=self.period_state.encoded_estimate,
            signatures_by_owner=dict(self.period_state.participant_to_signature),
        )
        tx_hash = yield from self.send_raw_transaction(contract_api_msg.raw_transaction)
        self.context.logger.info(f"Finalization tx hash: {tx_hash}")
        return tx_hash


class EndBehaviour(PriceEstimationBaseState):  # pylint: disable=too-many-ancestors
    """Final state."""

    state_id = "end"

    def async_act(self) -> Generator:
        """Do the act."""
        self.context.logger.info(
            f"Finalized estimate: {self.period_state.most_voted_estimate} with transaction hash: {self.period_state.final_tx_hash}"
        )
        self.context.logger.info("Period end.")
        # dummy 'yield' to return a generator
        yield
        self.set_done()


class PriceEstimationConsensusBehaviour(AbstractRoundBehaviour):
    """This behaviour manages the consensus stages for the price estimation."""

    initial_state_cls = TendermintHealthcheck
    transition_function: TransitionFunction = {
        TendermintHealthcheck: {DONE_EVENT: RegistrationBehaviour},
        RegistrationBehaviour: {DONE_EVENT: DeploySafeBehaviour},
        DeploySafeBehaviour: {DONE_EVENT: ObserveBehaviour},
        ObserveBehaviour: {DONE_EVENT: EstimateBehaviour},
        EstimateBehaviour: {DONE_EVENT: TransactionHashBehaviour},
        TransactionHashBehaviour: {DONE_EVENT: SignatureBehaviour},
        SignatureBehaviour: {DONE_EVENT: FinalizeBehaviour},
        FinalizeBehaviour: {DONE_EVENT: EndBehaviour},
        EndBehaviour: {},
    }
