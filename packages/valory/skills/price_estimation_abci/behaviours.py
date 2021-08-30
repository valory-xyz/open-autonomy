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
import datetime
import pprint
from abc import ABC
from functools import partial
from typing import Any, Callable, Dict, Generator, List, Tuple, Type, cast

from aea.exceptions import enforce
from aea.helpers.transaction.base import RawTransaction, Terms
from aea.skills.behaviours import FSMBehaviour
from aea_ledger_ethereum import EthereumCrypto

from packages.fetchai.connections.ledger.base import (
    CONNECTION_ID as LEDGER_CONNECTION_PUBLIC_ID,
)
from packages.fetchai.protocols.contract_api import ContractApiMessage
from packages.fetchai.protocols.signing import SigningMessage
from packages.valory.contracts.gnosis_safe.contract import GnosisSafeContract
from packages.valory.skills.abstract_round_abci.behaviour_utils import (
    BaseState,
    DONE_EVENT,
)
from packages.valory.skills.price_estimation_abci.dialogues import (
    ContractApiDialogue,
    ContractApiDialogues,
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
    ConsensusReachedRound,
    DeploySafeRound,
    EstimateConsensusRound,
    FinalizationRound,
    PeriodState,
    RegistrationRound,
    TxHashRound,
)


SIGNATURE_LENGTH = 65
LEDGER_API_ADDRESS = str(LEDGER_CONNECTION_PUBLIC_ID)


class PriceEstimationConsensusBehaviour(FSMBehaviour):
    """This behaviour manages the consensus stages for the price estimation."""

    def setup(self) -> None:
        """Set up the behaviour."""
        self._register_states(
            [
                InitialDelayState,  # type: ignore
                RegistrationBehaviour,  # type: ignore
                DeploySafeBehaviour,  # type: ignore
                ObserveBehaviour,  # type: ignore
                EstimateBehaviour,  # type: ignore
                TransactionHashBehaviour,  # type: ignore
                SignatureBehaviour,  # type: ignore
                FinalizeBehaviour,  # type: ignore
                EndBehaviour,  # type: ignore
            ]
        )

    def teardown(self) -> None:
        """Tear down the behaviour"""

    def _register_states(self, state_classes: List[Type[BaseState]]) -> None:
        """Register a list of states."""
        enforce(
            len(state_classes) != 0,
            "empty list of state classes",
            exception_class=ValueError,
        )
        self._register_state(state_classes[0], initial=True)
        for state_cls in state_classes[1:]:
            self._register_state(state_cls)

        for index in range(len(state_classes) - 1):
            before, after = state_classes[index], state_classes[index + 1]
            self.register_transition(before.state_id, after.state_id, DONE_EVENT)

    def _register_state(
        self, state_cls: Type[BaseState], initial: bool = False
    ) -> None:
        """Register state."""
        name = state_cls.state_id
        return super().register_state(
            state_cls.state_id,
            state_cls(name=name, skill_context=self.context),
            initial=initial,
        )

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


class PriceEstimationBaseState(BaseState, ABC):  # pylint: disable=too-many-ancestors
    """Base state behaviour for the price estimation skill."""

    @property
    def period_state(self) -> PeriodState:
        """Return the period state."""
        return cast(PeriodState, self.context.state.period_state)

    def get_default_terms(self) -> Terms:
        """
        Get default transaction terms.

        :return: terms
        """
        terms = Terms(
            ledger_id=EthereumCrypto.identifier,
            sender_address=self.context.agent_address,
            counterparty_address=self.context.agent_address,
            amount_by_currency_id={},
            quantities_by_good_id={},
            nonce="",
        )
        return terms


class InitialDelayState(PriceEstimationBaseState):  # pylint: disable=too-many-ancestors
    """Wait for some seconds until Tendermint nodes are running."""

    state_id = "initial_delay"

    def async_act(self) -> None:  # type: ignore
        """Do the action."""
        delay = self.context.params.initial_delay
        yield from self.sleep(delay)
        self.set_done()


class RegistrationBehaviour(  # pylint: disable=too-many-ancestors
    PriceEstimationBaseState
):
    """Register to the next round."""

    state_id = "register"

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


class DeploySafeBehaviour(  # pylint: disable=too-many-ancestors
    PriceEstimationBaseState
):
    """Deploy Safe."""

    state_id = "deploy_safe"

    def async_act(self) -> Generator:
        """
        Do the action.

        If the agent is the designated deployer, then prepare the
        deployment transaction and send it.
        Otherwise, wait until the next round.
        """
        self._log_start()
        if self.context.agent_address != self.period_state.safe_sender_address:
            self.not_deployer_act()
        else:
            yield from self.deployer_act()
        yield from self.wait_until_round_end(DeploySafeRound.round_id)
        self.context.logger.info(
            f"Safe contract address: {self.period_state.safe_contract_address}"
        )
        self._log_end()
        self.set_done()

    def not_deployer_act(self) -> None:
        """Do the non-deployer action."""
        self.context.logger.info(
            "I am not the designated sender, waiting until next round..."
        )

    def deployer_act(self) -> Generator:
        """Do the deployer action."""
        stop_condition = self.is_round_ended(DeploySafeRound.round_id)
        if stop_condition():
            self.context.logger.info("contract already deployed, skipping...")
            return
        self.context.logger.info(
            "I am the designated sender, deploying the safe contract..."
        )
        contract_address = yield from self._send_deploy_transaction()
        payload = DeploySafePayload(self.context.agent_address, contract_address)
        yield from self._send_transaction(payload, stop_condition=stop_condition)

    def _send_deploy_transaction(self) -> Generator[None, None, str]:
        owners = list(self.period_state.participants)
        threshold = self.context.params.consensus_params.two_thirds_threshold
        contract_api_response = yield from self._get_contract_deploy_transaction(
            owners=owners, threshold=threshold
        )
        raw_transaction = cast(
            ContractApiMessage, contract_api_response
        ).raw_transaction
        contract_address = raw_transaction.body.pop("contract_address")
        tx_hash = yield from self._send_raw_transaction(raw_transaction)
        self.context.logger.info(f"Deployment tx hash: {tx_hash}")
        return contract_address

    def _get_contract_deploy_transaction(self, **kwargs: Any) -> ContractApiMessage:
        """
        Request contract deploy transaction

        :param: kwargs: keyword argument for the contract api request
        :return: the contract api response
        :yields: the contract api response
        """
        contract_api_dialogues = cast(
            ContractApiDialogues, self.context.contract_api_dialogues
        )
        contract_api_msg, contract_api_dialogue = contract_api_dialogues.create(
            counterparty=LEDGER_API_ADDRESS,
            performative=ContractApiMessage.Performative.GET_DEPLOY_TRANSACTION,
            ledger_id=EthereumCrypto.identifier,
            contract_id=str(GnosisSafeContract.contract_id),
            callable="get_deploy_transaction",
            kwargs=ContractApiMessage.Kwargs(
                dict(deployer_address=self.context.agent_address, **kwargs)
            ),
        )
        contract_api_dialogue = cast(
            ContractApiDialogue,
            contract_api_dialogue,
        )
        contract_api_dialogue.terms = self.get_default_terms()
        request_nonce = self._get_request_nonce_from_dialogue(contract_api_dialogue)
        self.context.requests.request_id_to_callback[
            request_nonce
        ] = self.default_callback_request
        self.context.outbox.put_message(message=contract_api_msg)
        response = yield from self.wait_for_message()
        return response


class ObserveBehaviour(PriceEstimationBaseState):  # pylint: disable=too-many-ancestors
    """Observe price estimate."""

    state_id = "observe"

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


class EstimateBehaviour(PriceEstimationBaseState):  # pylint: disable=too-many-ancestors
    """Estimate price."""

    state_id = "estimate"

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


class TransactionHashBehaviour(  # pylint: disable=too-many-ancestors
    PriceEstimationBaseState
):
    """Share the transaction hash for the signature round."""

    state_id = "tx_hash"

    def async_act(self) -> None:  # type: ignore
        """
        Do the action.

        Steps:
        - TODO
        """
        self._log_start()
        if self.context.agent_address != self.period_state.safe_sender_address:
            self.not_sender_act()
        else:
            yield from self.sender_act()
        yield from self.wait_until_round_end(TxHashRound.round_id)
        self._log_end()
        self.set_done()

    def not_sender_act(self) -> None:
        """Do the non-deployer action."""
        self.context.logger.info(
            "I am not the designated sender, waiting until next round..."
        )

    def sender_act(self) -> Generator[None, None, None]:
        """Do the deployer action."""
        self.context.logger.info(
            "I am the designated sender, committing the transaction hash..."
        )
        self.context.logger.info(
            f"Consensus reached on estimate: {self.period_state.most_voted_estimate}"
        )
        data = self.period_state.encoded_estimate
        safe_tx_hash = yield from self._get_safe_transaction_hash(
            self.period_state.safe_contract_address,
            to_address=self.context.agent_address,
            value=0,
            data=data,
        )
        safe_tx_hash = safe_tx_hash[2:]
        self.context.logger.info(f"Hash of the Safe transaction: {safe_tx_hash}")
        payload = TransactionHashPayload(self.context.agent_address, safe_tx_hash)
        stop_condition = self.is_round_ended(TxHashRound.round_id)
        yield from self._send_transaction(payload, stop_condition=stop_condition)

    def _get_safe_transaction_hash(
        self, contract_address: str, **kwargs: Any
    ) -> ContractApiMessage:
        """
        Request contract safe transaction hash

        :param: contract_address: the contract address
        :param: kwargs: keyword argument for the contract api request
        :return: the contract api response
        :yields: the contract api response
        """
        contract_api_dialogues = cast(
            ContractApiDialogues, self.context.contract_api_dialogues
        )
        contract_api_msg, contract_api_dialogue = contract_api_dialogues.create(
            counterparty=LEDGER_API_ADDRESS,
            performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,
            ledger_id=EthereumCrypto.identifier,
            contract_id=str(GnosisSafeContract.contract_id),
            contract_address=contract_address,
            callable="get_raw_safe_transaction_hash",
            kwargs=ContractApiMessage.Kwargs(kwargs),
        )
        contract_api_dialogue = cast(
            ContractApiDialogue,
            contract_api_dialogue,
        )
        contract_api_dialogue.terms = self.get_default_terms()
        request_nonce = self._get_request_nonce_from_dialogue(contract_api_dialogue)
        self.context.requests.request_id_to_callback[
            request_nonce
        ] = self.default_callback_request
        self.context.outbox.put_message(message=contract_api_msg)
        response = yield from self.wait_for_message()
        tx_hash = cast(ContractApiMessage, response).raw_transaction.body["tx_hash"]
        return cast(str, tx_hash)


class SignatureBehaviour(  # pylint: disable=too-many-ancestors
    PriceEstimationBaseState
):
    """Signature state."""

    state_id = "sign"

    def async_act(self) -> Generator:
        """Do the act."""
        self._log_start()
        signature_hex = yield from self._get_safe_tx_signature()
        payload = SignaturePayload(self.context.agent_address, signature_hex)
        stop_condition = self.is_round_ended(CollectSignatureRound.round_id)
        yield from self._send_transaction(payload, stop_condition=stop_condition)
        yield from self.wait_until_round_end(CollectSignatureRound.round_id)
        self._log_end()
        self.set_done()

    def _get_safe_tx_signature(self) -> Generator[None, None, str]:
        # is_deprecated_mode=True because we want to call Account.signHash,
        # which is the same used by gnosis-py
        safe_tx_hash_bytes = binascii.unhexlify(self.period_state.safe_tx_hash)
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

    def async_act(self) -> Generator[None, None, None]:
        """Do the act."""
        self._log_start()
        if self.context.agent_address != self.period_state.safe_sender_address:
            self.not_sender_act()
        else:
            yield from self.sender_act()
        yield from self.wait_until_round_end(FinalizationRound.round_id)
        self._log_end()
        self.set_done()

    def not_sender_act(self) -> None:
        """Do the non-sender action."""
        self.context.logger.info(
            "I am not the designated sender, waiting until next round..."
        )

    def sender_act(self) -> Generator[None, None, None]:
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
        stop_condition = self.is_round_ended(FinalizationRound.round_id)
        yield from self._send_transaction(payload, stop_condition=stop_condition)

    def _send_safe_transaction(self) -> Generator[None, None, str]:
        """Send a Safe transaction using the participants' signatures."""
        data = self.period_state.encoded_estimate

        # compose final signature (need to be sorted!)
        final_signature = b""
        for signer in self.period_state.sorted_addresses:
            if signer not in self.period_state.participant_to_signature:
                continue
            signature = self.period_state.participant_to_signature[signer]
            signature_bytes = binascii.unhexlify(signature)
            final_signature += signature_bytes

        transaction = yield from self._get_safe_transaction(
            contract_address=self.period_state.safe_contract_address,
            owners=tuple(self.period_state.participants),
            sender_address=self.context.agent_address,
            to_address=self.context.agent_address,
            value=0,
            data=data,
            signatures_by_owner=dict(self.period_state.participant_to_signature),
        )
        tx_hash = yield from self._send_raw_transaction(transaction)
        self.context.logger.info(f"Finalization tx hash: {tx_hash}")
        return tx_hash

    def _get_safe_transaction(  # pylint: disable=too-many-arguments
        self,
        contract_address: str,
        sender_address: str,
        owners: Tuple[str, ...],
        to_address: str,
        value: int,
        data: bytes,
        signatures_by_owner: Dict[str, str],
    ) -> Generator[None, None, RawTransaction]:
        """
        Request contract safe transaction hash

        :param: contract_address: the contract address
        :param sender_address: the address of the sender
        :param owners: the sequence of owners
        :param to_address: the tx recipient address
        :param value: the ETH value of the transaction
        :param data: the data of the transaction
        :param signatures_by_owner: mapping from owners to signatures
        :return: the raw transaction
        :yields: the raw transaction
        """
        contract_api_dialogues = cast(
            ContractApiDialogues, self.context.contract_api_dialogues
        )
        contract_api_msg, contract_api_dialogue = contract_api_dialogues.create(
            counterparty=LEDGER_API_ADDRESS,
            performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,
            ledger_id=EthereumCrypto.identifier,
            contract_id=str(GnosisSafeContract.contract_id),
            contract_address=contract_address,
            callable="get_raw_safe_transaction",
            kwargs=ContractApiMessage.Kwargs(
                dict(
                    sender_address=sender_address,
                    owners=owners,
                    to_address=to_address,
                    value=value,
                    data=data,
                    signatures_by_owner=signatures_by_owner,
                )
            ),
        )
        contract_api_dialogue = cast(
            ContractApiDialogue,
            contract_api_dialogue,
        )
        contract_api_dialogue.terms = self.get_default_terms()
        request_nonce = self._get_request_nonce_from_dialogue(contract_api_dialogue)
        self.context.requests.request_id_to_callback[
            request_nonce
        ] = self.default_callback_request
        self.context.outbox.put_message(message=contract_api_msg)
        response = yield from self.wait_for_message()
        return cast(ContractApiMessage, response).raw_transaction


class EndBehaviour(PriceEstimationBaseState):  # pylint: disable=too-many-ancestors
    """Final state."""

    state_id = "end"

    def async_act(self) -> Generator:
        """Do the act."""
        self.context.logger.info(
            f"Finalized estimate: {self.period_state.most_voted_estimate} with transaction hash: {self.period_state.final_tx_hash}"
        )
        self.context.logger.info("Period end.")
        self.set_done()
        # dummy 'yield' to return a generator
        yield
