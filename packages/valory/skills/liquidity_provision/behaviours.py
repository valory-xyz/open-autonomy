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

"""This module contains the behaviours for the 'liquidity_provision' skill."""
import binascii
import pprint
from abc import ABC
from typing import Generator, Mapping, Optional, Set, Type, cast

from aea_ledger_ethereum import EthereumApi

from packages.open_aea.protocols.signing import SigningMessage
from packages.valory.contracts.gnosis_safe.contract import GnosisSafeContract
from packages.valory.contracts.gnosis_safe.contract import (
    PUBLIC_ID as GNOSIS_SAFE_CONTRACT_ID,
)
from packages.valory.protocols.contract_api import ContractApiMessage
from packages.valory.skills.abstract_round_abci.behaviours import (
    AbstractRoundBehaviour,
    BaseState,
)
from packages.valory.skills.abstract_round_abci.utils import BenchmarkTool
from packages.valory.skills.liquidity_provision.models import Params, SharedState
from packages.valory.skills.liquidity_provision.payloads import (
    StrategyEvaluationPayload,
    StrategyType,
)
from packages.valory.skills.liquidity_provision.rounds import (
    EnterPoolSelectKeeperRound,
    EnterPoolTransactionHashRound,
    EnterPoolTransactionSendRound,
    EnterPoolTransactionSignatureRound,
    EnterPoolTransactionValidationRound,
    ExitPoolSelectKeeperRound,
    ExitPoolTransactionHashRound,
    ExitPoolTransactionSendRound,
    ExitPoolTransactionSignatureRound,
    ExitPoolTransactionValidationRound,
    LiquidityProvisionAbciApp,
    PeriodState,
    StrategyEvaluationRound,
    DeploySafeRandomnessRound,
    DeploySafeSelectKeeperRound,
    EnterPoolRandomnessRound,
    ExitPoolRandomnessRound,
)
from packages.valory.skills.price_estimation_abci.behaviours import (
    DeploySafeBehaviour as DeploySafeSendBehaviour,
)
from packages.valory.skills.price_estimation_abci.behaviours import (
    RandomnessBehaviour as RandomnessBehaviourPriceEstimation,
)
from packages.valory.skills.price_estimation_abci.behaviours import (
    RegistrationBehaviour,
    ResetAndPauseBehaviour,
    ResetBehaviour,
    SelectKeeperBehaviour,
    TendermintHealthcheckBehaviour,
)
from packages.valory.skills.price_estimation_abci.behaviours import (
    ValidateSafeBehaviour as DeploySafeValidationBehaviour,
)
from packages.valory.skills.price_estimation_abci.payloads import (
    FinalizationTxPayload,
    SignaturePayload,
    TransactionHashPayload,
    ValidatePayload,
)
from packages.valory.skills.price_estimation_abci.rounds import RandomnessRound


benchmark_tool = BenchmarkTool()


class LiquidityProvisionBaseBehaviour(BaseState, ABC):
    """Base state behaviour for the liquidity provision skill."""

    @property
    def period_state(self) -> PeriodState:
        """Return the period state."""
        return cast(PeriodState, cast(SharedState, self.context.state).period_state)

    @property
    def params(self) -> Params:
        """Return the params."""
        return cast(Params, self.context.params)


class TransactionHashBaseBehaviour(LiquidityProvisionBaseBehaviour):
    """Prepare transaction hash."""

    def async_act(self) -> Generator:
        """
        Do the action.

        Steps:
        - Request the transaction hash for the transaction. This is the hash that needs to be signed by a threshold of agents.
        - Send the transaction hash as a transaction and wait for it to be mined.
        - Wait until ABCI application transitions to the next round.
        - Go to the next behaviour state (set done event).
        """

        with benchmark_tool.measure(
            self,
        ).local():
            contract_api_msg = yield from self.get_contract_api_response(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address="",
                contract_id=str(GNOSIS_SAFE_CONTRACT_ID),
                contract_callable="get_raw_safe_transaction_hash",
                to_address="",
                value=0,
            )
            safe_tx_hash = cast(str, contract_api_msg.raw_transaction.body["tx_hash"])
            safe_tx_hash = safe_tx_hash[2:]
            self.context.logger.info(f"Hash of the Swap transaction: {safe_tx_hash}")
            payload = TransactionHashPayload(self.context.agent_address, safe_tx_hash)

        with benchmark_tool.measure(
            self,
        ).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class TransactionSignatureBaseBehaviour(LiquidityProvisionBaseBehaviour):
    """Signature base behaviour."""

    def async_act(self) -> Generator:
        """
        Do the action.

        Steps:
        - Request the signature of the transaction hash.
        - Send the signature as a transaction and wait for it to be mined.
        - Wait until ABCI application transitions to the next round.
        - Go to the next behaviour state (set done event).
        """

        with benchmark_tool.measure(
            self,
        ).local():
            self.context.logger.info(
                f"Consensus reached on {self.state_id} tx hash: {self.period_state.most_voted_tx_hash}"
            )
            signature_hex = yield from self._get_safe_tx_signature()
            payload = SignaturePayload(self.context.agent_address, signature_hex)

        with benchmark_tool.measure(
            self,
        ).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()

    def _get_safe_tx_signature(self) -> Generator[None, None, str]:
        # is_deprecated_mode=True because we want to call Account.signHash,
        # which is the same used by gnosis-py
        safe_tx_hash_bytes = binascii.unhexlify(
            self.period_state.most_voted_tx_hash[:64]
        )
        self._send_signing_request(safe_tx_hash_bytes, is_deprecated_mode=True)
        signature_response = yield from self.wait_for_message()
        signature_hex = cast(SigningMessage, signature_response).signed_message.body
        # remove the leading '0x'
        signature_hex = signature_hex[2:]
        self.context.logger.info(f"Signature: {signature_hex}")
        return signature_hex


class TransactionSendBaseBehaviour(LiquidityProvisionBaseBehaviour):
    """Finalize state."""

    def async_act(self) -> Generator[None, None, None]:
        """
        Do the action.

        Steps:
        - If the agent is the keeper, then prepare the transaction and send it.
        - Otherwise, wait until the next round.
        - If a timeout is hit, set exit A event, otherwise set done event.
        """
        if self.context.agent_address != self.period_state.most_voted_keeper_address:
            yield from self._not_sender_act()
        else:
            yield from self._sender_act()

    def _not_sender_act(self) -> Generator:
        """Do the non-sender action."""
        with benchmark_tool.measure(
            self,
        ).consensus():
            yield from self.wait_until_round_end()
        self.set_done()

    def _sender_act(self) -> Generator[None, None, None]:
        """Do the sender action."""

        with benchmark_tool.measure(
            self,
        ).local():
            self.context.logger.info(
                "I am the designated sender, sending the safe transaction..."
            )
            tx_hash = yield from self._send_safe_transaction()
            self.context.logger.info(
                f"Transaction hash of the final transaction: {tx_hash}"
            )
            self.context.logger.info(f"Signatures: {pprint.pformat(self.period_state.participants)}")
            payload = FinalizationTxPayload(self.context.agent_address, tx_hash)

        with benchmark_tool.measure(
            self,
        ).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()

    def _send_safe_transaction(self) -> Generator[None, None, str]:
        """Send a Safe transaction using the participants' signatures."""
        contract_api_msg = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
            contract_address=self.period_state.safe_contract_address,
            contract_id=str(GnosisSafeContract.contract_id),
            contract_callable="get_raw_safe_transaction",
            sender_address=self.context.agent_address,
            owners=tuple(self.period_state.participants),
            to_address=self.context.agent_address,
            signatures_by_owner={
                key: payload.signature for key, payload in self.period_state.participant_to_signature.items()
            },
        )
        tx_hash = yield from self.send_raw_transaction(contract_api_msg.raw_transaction)
        self.context.logger.info(f"Finalization tx hash: {tx_hash}")
        return tx_hash


class TransactionValidationBaseBehaviour(LiquidityProvisionBaseBehaviour):
    """ValidateTransaction."""

    def async_act(self) -> Generator:
        """
        Do the action.

        Steps:
        - Validate that the transaction hash provided by the keeper points to a valid transaction.
        - Send the transaction with the validation result and wait for it to be mined.
        - Wait until ABCI application transitions to the next round.
        - Go to the next behaviour state (set done event).
        """

        with benchmark_tool.measure(
            self,
        ).local():
            is_correct = yield from self.has_transaction_been_sent()
            payload = ValidatePayload(self.context.agent_address, is_correct)

        with benchmark_tool.measure(
            self,
        ).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()

    def has_transaction_been_sent(self) -> Generator[None, None, Optional[bool]]:
        """Contract deployment verification."""
        response = yield from self.get_transaction_receipt(
            self.period_state.final_tx_hash,
            self.params.retry_timeout,
            self.params.retry_attempts,
        )
        if response is None:  # pragma: nocover
            self.context.logger.info(
                f"tx {self.period_state.final_tx_hash} receipt check timed out!"
            )
            return None
        is_settled = EthereumApi.is_transaction_settled(response)
        if not is_settled:  # pragma: nocover
            self.context.logger.info(
                f"tx {self.period_state.final_tx_hash} not settled!"
            )
            return False
        contract_api_msg = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_STATE,  # type: ignore
            contract_address=self.period_state.safe_contract_address,
            contract_id=str(GnosisSafeContract.contract_id),
            contract_callable="verify_tx",
            tx_hash=self.period_state.final_tx_hash,
            owners=tuple(self.period_state.participants),
            to_address=self.context.agent_address,
            signatures_by_owner={
                key: payload.signature
                for key, payload in self.period_state.participant_to_signature.items()
            },
        )
        if contract_api_msg.performative != ContractApiMessage.Performative.STATE:
            return False  # pragma: nocover
        verified = cast(bool, contract_api_msg.state.body["verified"])
        verified_log = (
            f"Verified result: {verified}"
            if verified
            else f"Verified result: {verified}, all: {contract_api_msg.state.body}"
        )
        self.context.logger.info(verified_log)
        return verified


class DeploySafeRandomnessBehaviour(RandomnessBehaviourPriceEstimation):
    """Get randomness."""

    state_id = "deploy_safe_randomness"
    matching_round = DeploySafeRandomnessRound

class DeploySafeSelectKeeperBehaviour(SelectKeeperBehaviour):
    """Select the keeper agent."""

    state_id = "deploy_safe_select_keeper"
    matching_round = DeploySafeSelectKeeperRound


def get_strategy_update() -> dict:
    """Get a strategy update."""
    strategy = {
        "action": StrategyType.GO,
        "pair": ["FTM", "BOO"],
        "pool": "0x0000000000000000000000000000",
        "amountETH": 0.1,  # Be careful with floats and determinism here
    }
    return strategy


class StrategyEvaluationBehaviour(LiquidityProvisionBaseBehaviour):
    """Evaluate the financial strategy."""

    state_id = "strategy_evaluation"
    matching_round = StrategyEvaluationRound

    def async_act(self) -> Generator:
        """Do the action."""

        with benchmark_tool.measure(
            self,
        ).local():

            strategy = get_strategy_update()
            payload = StrategyEvaluationPayload(self.context.agent_address, strategy)

            if strategy["action"] == StrategyType.WAIT:
                self.context.logger.info("Current strategy is still optimal. Waiting.")

            if strategy["action"] == StrategyType.GO:
                self.context.logger.info(
                    f"Performing strategy update: moving {strategy['amountETH']} into "
                    "{strategy['pair'][0]}-{strategy['pair'][1]} (pool {strategy['pool']})"
                )

        with benchmark_tool.measure(
            self,
        ).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class EnterPoolTransactionHashBehaviour(TransactionHashBaseBehaviour):
    """Prepare the 'enter pool' multisend tx."""

    # swap + add allowance + add liquidity

    state_id = "enter_pool_tx_hash"
    matching_round = EnterPoolTransactionHashRound


class EnterPoolTransactionSignatureBehaviour(TransactionSignatureBaseBehaviour):
    """Sign the 'enter pool' multisend tx."""

    state_id = "enter_pool_tx_signature"
    matching_round = EnterPoolTransactionSignatureRound


class EnterPoolTransactionSendBehaviour(TransactionSendBaseBehaviour):
    """Send the 'enter pool' multisend tx."""

    state_id = "enter_pool_tx_send"
    matching_round = EnterPoolTransactionSendRound


class EnterPoolTransactionValidationBehaviour(TransactionValidationBaseBehaviour):
    """Validate the 'enter pool' multisend tx."""

    state_id = "enter_pool_tx_validation"
    matching_round = EnterPoolTransactionValidationRound


class EnterPoolRandomnessBehaviour(RandomnessBehaviourPriceEstimation):
    """Get randomness."""

    state_id = "enter_pool_randomness"
    matching_round = EnterPoolRandomnessRound


class EnterPoolSelectKeeperBehaviour(SelectKeeperBehaviour):
    """'exit pool' select keeper."""

    state_id = "enter_pool_select_keeper"
    matching_round = EnterPoolSelectKeeperRound


class ExitPoolTransactionHashBehaviour(TransactionHashBaseBehaviour):
    """Prepare the 'exit pool' multisend tx."""

    # remove liquidity + remove allowance + swap back

    state_id = "exit_pool_tx_hash"
    matching_round = ExitPoolTransactionHashRound


class ExitPoolTransactionSignatureBehaviour(TransactionSignatureBaseBehaviour):
    """Prepare the 'exit pool' multisend tx."""

    state_id = "exit_pool_tx_signature"
    matching_round = ExitPoolTransactionSignatureRound


class ExitPoolTransactionSendBehaviour(TransactionSendBaseBehaviour):
    """Prepare the 'exit pool' multisend tx."""

    state_id = "exit_pool_tx_send"
    matching_round = ExitPoolTransactionSendRound


class ExitPoolTransactionValidationBehaviour(TransactionValidationBaseBehaviour):
    """Prepare the 'exit pool' multisend tx."""

    state_id = "exit_pool_tx_validation"
    matching_round = ExitPoolTransactionValidationRound


class ExitPoolRandomnessBehaviour(RandomnessBehaviourPriceEstimation):
    """Get randomness."""

    state_id = "exit_pool_randomness"
    matching_round = ExitPoolRandomnessRound


class ExitPoolSelectKeeperBehaviour(SelectKeeperBehaviour):
    """'exit pool' select keeper."""

    state_id = "exit_pool_select_keeper"
    matching_round = ExitPoolSelectKeeperRound


class LiquidityProvisionConsensusBehaviour(AbstractRoundBehaviour):
    """This behaviour manages the consensus stages for the liquidity provision."""

    initial_state_cls = TendermintHealthcheckBehaviour
    abci_app_cls = LiquidityProvisionAbciApp  # type: ignore
    behaviour_states: Set[Type[LiquidityProvisionBaseBehaviour]] = {  # type: ignore
        TendermintHealthcheckBehaviour,  # type: ignore
        RegistrationBehaviour,  # type: ignore
        DeploySafeRandomnessBehaviour,  # type: ignore
        DeploySafeSelectKeeperBehaviour,  # type: ignore
        DeploySafeSendBehaviour,  # type: ignore
        DeploySafeValidationBehaviour,  # type: ignore
        StrategyEvaluationBehaviour,  # type: ignore
        EnterPoolSelectKeeperBehaviour,  # type: ignore
        EnterPoolTransactionHashBehaviour,  # type: ignore
        EnterPoolTransactionSignatureBehaviour,  # type: ignore
        EnterPoolTransactionSendBehaviour,  # type: ignore
        EnterPoolTransactionValidationBehaviour,  # type: ignore
        EnterPoolRandomnessBehaviour,  # type: ignore
        EnterPoolSelectKeeperBehaviour,  # type: ignore
        ExitPoolSelectKeeperBehaviour,  # type: ignore
        ExitPoolTransactionHashBehaviour,  # type: ignore
        ExitPoolTransactionSignatureBehaviour,  # type: ignore
        ExitPoolTransactionSendBehaviour,  # type: ignore
        ExitPoolTransactionValidationBehaviour,  # type: ignore
        ExitPoolRandomnessBehaviour,  # type: ignore
        ExitPoolSelectKeeperBehaviour,  # type: ignore
        ResetBehaviour,  # type: ignore
        ResetAndPauseBehaviour,  # type: ignore
    }

    def setup(self) -> None:
        """Set up the behaviour."""
        super().setup()
        benchmark_tool.logger = self.context.logger
