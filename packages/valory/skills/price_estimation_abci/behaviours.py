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
from typing import Generator, cast

from aea_ledger_ethereum import EthereumApi

from packages.fetchai.connections.ledger.base import (
    CONNECTION_ID as LEDGER_CONNECTION_PUBLIC_ID,
)
from packages.fetchai.protocols.contract_api import ContractApiMessage
from packages.fetchai.protocols.signing import SigningMessage
from packages.valory.contracts.gnosis_safe.contract import GnosisSafeContract
from packages.valory.skills.abstract_round_abci.behaviour_utils import (
    BaseState,
    DONE_EVENT,
    EXIT_A_EVENT,
    EXIT_B_EVENT,
    FAIL_EVENT,
    TimeoutException,
)
from packages.valory.skills.abstract_round_abci.behaviours import (
    AbstractRoundBehaviour,
    TransitionFunction,
)
from packages.valory.skills.price_estimation_abci.models import Params, SharedState
from packages.valory.skills.price_estimation_abci.payloads import (
    DeploySafePayload,
    EstimatePayload,
    FinalizationTxPayload,
    ObservationPayload,
    RegistrationPayload,
    SelectKeeperPayload,
    SignaturePayload,
    TransactionHashPayload,
    ValidatePayload,
)
from packages.valory.skills.price_estimation_abci.rounds import (
    CollectObservationRound,
    CollectSignatureRound,
    ConsensusReachedRound,
    DeploySafeRound,
    EstimateConsensusRound,
    FinalizationRound,
    PeriodState,
    RegistrationRound,
    SelectKeeperARound,
    SelectKeeperBRound,
    TxHashRound,
    ValidateSafeRound,
    ValidateTransactionRound,
)
from packages.valory.skills.price_estimation_abci.tools import random_selection


SIGNATURE_LENGTH = 65
LEDGER_API_ADDRESS = str(LEDGER_CONNECTION_PUBLIC_ID)


class PriceEstimationBaseState(BaseState, ABC):
    """Base state behaviour for the price estimation skill."""

    @property
    def period_state(self) -> PeriodState:
        """Return the period state."""
        return cast(PeriodState, cast(SharedState, self.context.state).period_state)

    @property
    def params(self) -> Params:
        """Return the params."""
        return cast(Params, self.context.params)

    @property
    def shared_state(self) -> SharedState:
        """Return the shared state."""
        return cast(SharedState, self.context.state)


class TendermintHealthcheckBehaviour(PriceEstimationBaseState):
    """Check whether Tendermint nodes are running."""

    state_id = "tendermint_healthcheck"

    def async_act(self) -> None:  # type: ignore
        """Check whether tendermint is running or not."""
        if self.params.is_health_check_timed_out():
            # if the tendermint node cannot start then the app cannot work
            raise RuntimeError("Tendermint node did not come live!")
        request_message, http_dialogue = self._build_http_request_message(
            "GET",
            self.params.tendermint_url + "/health",
        )
        result = yield from self._do_request(request_message, http_dialogue)
        try:
            json.loads(result.body.decode())
            self.context.logger.info("Tendermint running.")
            self.set_done()
        except json.JSONDecodeError:
            self.context.logger.error("Tendermint not running, trying again!")
            yield from self.sleep(1)
            self.params.increment_retries()


class RegistrationBehaviour(PriceEstimationBaseState):
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


class SelectKeeperBehaviour(PriceEstimationBaseState, ABC):
    """Select the keeper agent."""

    def async_act(self) -> None:  # type: ignore
        """
        Do the action.

        Steps:
        - Select a new random keeper
        - Send the transaction and wait for it to be mined.
        - Wait until ABCI application transitions to the next round.
        - Go to the next behaviour state.
        """
        keeper_address = random_selection(
            sorted(self.period_state.participants),
            self.period_state.keeper_randomness,
        )

        self.context.logger.info(f"Selected a new keeper: {keeper_address}.")
        payload = SelectKeeperPayload(self.context.agent_address, keeper_address)
        yield from self.send_a2a_transaction(payload)
        yield from self.wait_until_round_end()
        self.set_done()


class SelectKeeperABehaviour(SelectKeeperBehaviour):
    """Select the keeper agent."""

    state_id = "select_keeper_a"
    matching_round = SelectKeeperARound


class SelectKeeperBBehaviour(SelectKeeperBehaviour):
    """Select the keeper agent."""

    state_id = "select_keeper_b"
    matching_round = SelectKeeperBRound


class DeploySafeBehaviour(PriceEstimationBaseState):
    """Deploy Safe."""

    state_id = "deploy_safe"
    matching_round = DeploySafeRound

    def async_act(self) -> Generator:
        """
        Do the action.

        If the agent is the designated deployer, then prepare the
        deployment transaction and send it.
        Otherwise, wait until the next round.
        """
        if self.context.agent_address != self.period_state.most_voted_keeper_address:
            yield from self._not_deployer_act()
        else:
            yield from self._deployer_act()

    def _not_deployer_act(self) -> Generator:
        """Do the non-deployer action."""
        try:
            yield from self.wait_until_round_end(
                timeout=self.context.params.keeper_timeout_seconds
            )
            self.set_done()
        except TimeoutException:
            self.set_exit_a()

    def _deployer_act(self) -> Generator:
        """Do the deployer action."""
        self.context.logger.info(
            "I am the designated sender, deploying the safe contract..."
        )
        try:
            # TOFIX: here the deploy needs to time out and raise TimeoutException; timeout=self.context.params.keeper_timeout_seconds
            contract_address = yield from self._send_deploy_transaction()
        except TimeoutException:
            self.set_exit_a()
            return
        payload = DeploySafePayload(self.context.agent_address, contract_address)
        yield from self.send_a2a_transaction(payload)
        self.context.logger.info(f"Safe contract address: {contract_address}")
        yield from self.wait_until_round_end()
        self.set_done()

    def _send_deploy_transaction(self) -> Generator[None, None, str]:
        owners = sorted(self.period_state.participants)
        threshold = self.params.consensus_params.consensus_threshold
        contract_api_response = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_DEPLOY_TRANSACTION,
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
        tx_hash, tx_receipt = yield from self.send_raw_transaction(
            contract_api_response.raw_transaction
        )
        _ = EthereumApi.get_contract_address(
            tx_receipt
        )  # returns None as the contract is created via a proxy
        self.context.logger.info(f"Deployment tx hash: {tx_hash}")
        return contract_address


class ValidateSafeBehaviour(PriceEstimationBaseState):
    """ValidateSafe."""

    state_id = "validate_safe"
    matching_round = ValidateSafeRound

    def async_act(self) -> Generator:
        """
        Do the action.

        If the agent is the designated deployer, then prepare the
        deployment transaction and send it.
        Otherwise, wait until the next round.
        """
        is_correct = yield from self.has_correct_contract_been_deployed()
        payload = ValidatePayload(self.context.agent_address, is_correct)
        yield from self.send_a2a_transaction(payload)
        yield from self.wait_until_round_end()
        self.set_done()

    def has_correct_contract_been_deployed(self) -> Generator[None, None, bool]:
        """Contract deployment verification."""
        contract_api_response = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_STATE,
            contract_address=self.period_state.safe_contract_address,
            contract_id=str(GnosisSafeContract.contract_id),
            contract_callable="verify_contract",
        )
        verified = cast(bool, contract_api_response.state.body["verified"])
        return verified


class ObserveBehaviour(PriceEstimationBaseState):
    """Observe price estimate."""

    state_id = "observe"
    matching_round = CollectObservationRound

    def async_act(self) -> Generator:
        """
        Do the action.

        Steps:
        - Ask the configured API the price of a currency
        - Build an observation transaction
        - Wait until ABCI application transitions to the next round.
        - Go to the next behaviour state.
        """
        if self.context.price_api.is_retries_exceeded():
            # now we need to wait and see if the other agents progress the round, otherwise we should restart?
            self.set_fail()

        currency_id = self.params.currency_id
        convert_id = self.params.convert_id
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
                f"Could not get price from {self.context.price_api.api_id}"
            )
            self.context.price_api.increment_retries()


class WaitBehaviour(PriceEstimationBaseState):
    """
    Wait behaviour.

    This behaviour is used to regroup the agents after a failure.
    """

    state_id = "wait"

    def async_act(self) -> Generator:
        """Do the action."""
        raise NotImplementedError


class EstimateBehaviour(PriceEstimationBaseState):
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

        currency_id = self.params.currency_id
        convert_id = self.params.convert_id
        self.context.logger.info(
            "Got estimate of %s price in %s: %s",
            currency_id,
            convert_id,
            self.period_state.estimate,
        )
        payload = EstimatePayload(
            self.context.agent_address, self.period_state.estimate
        )
        yield from self.send_a2a_transaction(payload)
        yield from self.wait_until_round_end()
        self.set_done()


class TransactionHashBehaviour(PriceEstimationBaseState):
    """Share the transaction hash for the signature round."""

    state_id = "tx_hash"
    matching_round = TxHashRound

    def async_act(self) -> Generator:
        """
        Do the action.

        Steps:
        - TODO
        """
        data = self.period_state.encoded_most_voted_estimate
        contract_api_msg = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,
            contract_address=self.period_state.safe_contract_address,
            contract_id=str(GnosisSafeContract.contract_id),
            contract_callable="get_raw_safe_transaction_hash",
            to_address=self.period_state.most_voted_keeper_address,
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


class SignatureBehaviour(PriceEstimationBaseState):
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


class FinalizeBehaviour(PriceEstimationBaseState):
    """Finalize state."""

    state_id = "finalize"
    matching_round = FinalizationRound

    def async_act(self) -> Generator[None, None, None]:
        """Do the act."""
        self.shared_state.set_state_time(self.state_id)
        if self.context.agent_address != self.period_state.most_voted_keeper_address:
            yield from self._not_sender_act()
        else:
            yield from self._sender_act()

    def _not_sender_act(self) -> Generator:
        """Do the non-sender action."""
        try:
            yield from self.wait_until_round_end(
                timeout=self.context.params.keeper_timeout_seconds
            )
            self.set_done()
        except TimeoutException:
            self.set_exit_b()

    def _sender_act(self) -> Generator[None, None, None]:
        """Do the sender action."""
        self.context.logger.info(
            "I am the designated sender, sending the safe transaction..."
        )
        try:
            # TOFIX: here the deploy needs to time out and raise TimeoutException; timeout=self.context.params.keeper_timeout_seconds
            tx_hash = yield from self._send_safe_transaction()
        except TimeoutException:
            self.set_exit_b()
            return
        self.context.logger.info(
            f"Transaction hash of the final transaction: {tx_hash}"
        )
        self.context.logger.info(
            f"Signatures: {pprint.pformat(self.period_state.participant_to_signature)}"
        )
        payload = FinalizationTxPayload(self.context.agent_address, tx_hash)
        yield from self.send_a2a_transaction(payload)
        yield from self.wait_until_round_end()
        self.set_done()

    def _send_safe_transaction(self) -> Generator[None, None, str]:
        """Send a Safe transaction using the participants' signatures."""
        contract_api_msg = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,
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
        tx_hash, _ = yield from self.send_raw_transaction(
            contract_api_msg.raw_transaction
        )
        self.context.logger.info(f"Finalization tx hash: {tx_hash}")
        return tx_hash


class ValidateTransactionBehaviour(PriceEstimationBaseState):
    """ValidateTransaction."""

    state_id = "validate_transaction"
    matching_round = ValidateTransactionRound

    def async_act(self) -> Generator:
        """
        Do the action.

        If the agent is the designated deployer, then prepare the
        deployment transaction and send it.
        Otherwise, wait until the next round.
        """
        is_correct = yield from self.has_transaction_been_sent()
        payload = ValidatePayload(self.context.agent_address, is_correct)
        yield from self.send_a2a_transaction(payload)
        yield from self.wait_until_round_end()
        self.set_done()

    def has_transaction_been_sent(self) -> Generator[None, None, bool]:
        """Contract deployment verification."""
        contract_api_msg = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_STATE,
            contract_address=self.period_state.safe_contract_address,
            contract_id=str(GnosisSafeContract.contract_id),
            contract_callable="verify_tx",
            tx_hash=self.period_state.final_tx_hash,
        )
        verified = cast(bool, contract_api_msg.state.body["verified"])
        return verified


class EndBehaviour(PriceEstimationBaseState):
    """Final state."""

    state_id = "end"
    matching_round = ConsensusReachedRound

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

    initial_state_cls = TendermintHealthcheckBehaviour
    transition_function: TransitionFunction = {
        TendermintHealthcheckBehaviour: {DONE_EVENT: RegistrationBehaviour},
        RegistrationBehaviour: {DONE_EVENT: SelectKeeperABehaviour},
        SelectKeeperABehaviour: {DONE_EVENT: DeploySafeBehaviour},
        DeploySafeBehaviour: {
            DONE_EVENT: ValidateSafeBehaviour,
            EXIT_A_EVENT: SelectKeeperABehaviour,
        },
        ValidateSafeBehaviour: {DONE_EVENT: ObserveBehaviour},
        ObserveBehaviour: {DONE_EVENT: EstimateBehaviour, FAIL_EVENT: WaitBehaviour},
        EstimateBehaviour: {DONE_EVENT: TransactionHashBehaviour},
        TransactionHashBehaviour: {DONE_EVENT: SignatureBehaviour},
        SignatureBehaviour: {DONE_EVENT: FinalizeBehaviour},
        FinalizeBehaviour: {
            DONE_EVENT: ValidateTransactionBehaviour,
            EXIT_B_EVENT: SelectKeeperBBehaviour,
        },
        ValidateTransactionBehaviour: {DONE_EVENT: EndBehaviour},
        SelectKeeperBBehaviour: {DONE_EVENT: FinalizeBehaviour},
        EndBehaviour: {},
    }
