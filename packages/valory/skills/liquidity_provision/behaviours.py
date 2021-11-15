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
from typing import Generator, Mapping, Set, Type, cast

from packages.open_aea.protocols.signing import SigningMessage
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
    AllowanceCheckPayload,
    StrategyEvaluationPayload,
    StrategyType,
)
from packages.valory.skills.liquidity_provision.rounds import (
    AddAllowanceSelectKeeperRound,
    AddAllowanceSendRound,
    AddAllowanceSignatureRound,
    AddAllowanceTransactionHashRound,
    AddAllowanceValidationRound,
    AddLiquiditySelectKeeperRound,
    AddLiquiditySendRound,
    AddLiquiditySignatureRound,
    AddLiquidityTransactionHashRound,
    AddLiquidityValidationRound,
    AllowanceCheckRound,
    LiquidityProvisionAbciApp,
    PeriodState,
    RemoveAllowanceSelectKeeperRound,
    RemoveAllowanceSendRound,
    RemoveAllowanceSignatureRound,
    RemoveAllowanceTransactionHashRound,
    RemoveAllowanceValidationRound,
    RemoveLiquiditySelectKeeperRound,
    RemoveLiquiditySendRound,
    RemoveLiquiditySignatureRound,
    RemoveLiquidityTransactionHashRound,
    RemoveLiquidityValidationRound,
    SelectKeeperMainRound,
    StrategyEvaluationRound,
    SwapBackSelectKeeperRound,
    SwapBackSendRound,
    SwapBackSignatureRound,
    SwapBackTransactionHashRound,
    SwapBackValidationRound,
    SwapSelectKeeperRound,
    SwapSendRound,
    SwapSignatureRound,
    SwapTransactionHashRound,
    SwapValidationRound,
    TransactionHashBaseRound,
    TransactionSendBaseRound,
    TransactionSignatureBaseRound,
    TransactionValidationBaseRound,
    WaitRound,
)
from packages.valory.skills.price_estimation_abci.behaviours import (
    DeploySafeBehaviour as DeploySafeSendBehaviour,
)
from packages.valory.skills.price_estimation_abci.behaviours import (
    RandomnessBehaviour as RandomnessBehaviourPriceEstimation,
)
from packages.valory.skills.price_estimation_abci.behaviours import (
    RegistrationBehaviour,
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


class RandomnessBehaviour(RandomnessBehaviourPriceEstimation):
    """Get randomness."""

    state_id = "randomness"
    matching_round = RandomnessRound


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

    state_id = "swap_tx_hash"
    matching_round = TransactionHashBaseRound

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
            data = self.period_state.encoded_most_voted_swap_tx_hash
            contract_api_msg = yield from self.get_contract_api_response(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address="",
                contract_id=str(GNOSIS_SAFE_CONTRACT_ID),
                contract_callable="get_raw_safe_transaction_hash",
                to_address="",
                value=0,
                data=data,
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

    state_id = "signature"
    matching_round = TransactionSignatureBaseRound

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
                f"Consensus reached on {self.state_id} tx hash: {self.period_state.most_voted_swap_tx_hash}"
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
            self.period_state.most_voted_swap_tx_hash[:64]
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

    state_id = "tx_send"
    matching_round = TransactionSendBaseRound
    participants = {}  # type: Mapping[str, SignaturePayload]

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
            self.context.logger.info(f"Signatures: {pprint.pformat(self.participants)}")
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
            contract_address="",
            contract_id="",
            contract_callable="get_raw_safe_transaction",
            sender_address=self.context.agent_address,
            owners=tuple(self.period_state.participants),
            to_address=self.context.agent_address,
            value=0,
            data="",
            signatures_by_owner={
                key: payload.signature for key, payload in self.participants.items()
            },
        )
        tx_hash = yield from self.send_raw_transaction(contract_api_msg.raw_transaction)
        self.context.logger.info(f"Finalization tx hash: {tx_hash}")
        return tx_hash


class TransactionValidationBaseBehaviour(LiquidityProvisionBaseBehaviour):
    """ValidateTransaction."""

    state_id = "validate_transaction"
    matching_round = TransactionValidationBaseRound
    final_tx_hash = ""
    data = {}  # type: dict
    participants = {}  # type: Mapping[str, SignaturePayload]

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

    def has_transaction_been_sent(self) -> Generator[None, None, bool]:
        """Contract deployment verification."""
        contract_api_msg = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_STATE,  # type: ignore
            contract_address="",
            contract_id="",
            contract_callable="verify_tx",
            tx_hash=self.final_tx_hash,
            owners=tuple(self.period_state.participants),
            to_address=self.period_state.most_voted_keeper_address,
            value=0,
            data=self.data,
            signatures_by_owner={
                key: payload.signature for key, payload in self.participants.items()
            },
        )
        if contract_api_msg.performative != ContractApiMessage.Performative.STATE:
            return False  # pragma: nocover
        verified = cast(bool, contract_api_msg.state.body["verified"])
        return verified


class SelectKeeperMainBehaviour(SelectKeeperBehaviour):
    """Select the keeper agent."""

    state_id = "select_keeper_main"
    matching_round = SelectKeeperMainRound


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


class WaitBehaviour(LiquidityProvisionBaseBehaviour):
    """Wait until next strategy evaluation."""

    state_id = "wait"
    matching_round = WaitRound


class SwapSelectKeeperBehaviour(SelectKeeperBehaviour):
    """Select the keeper agent."""

    state_id = "swap_select_keeper"
    matching_round = SwapSelectKeeperRound


class SwapTransactionHashBehaviour(TransactionHashBaseBehaviour):
    """Swap tokens: prepare transaction hash."""

    state_id = "swap_tx_hash"
    matching_round = SwapTransactionHashRound


class SwapSignatureBehaviour(TransactionSignatureBaseBehaviour):
    """Swap tokens: sign the transaction."""

    state_id = "swap_signature"
    matching_round = SwapSignatureRound


class SwapSendBehaviour(TransactionSendBaseBehaviour):
    """Swap tokens: send the transaction."""

    state_id = "swap_send"
    matching_round = SwapSendRound


class SwapValidationBehaviour(TransactionValidationBaseBehaviour):
    """Swap tokens: validate the tx."""

    state_id = "swap_validation"
    matching_round = SwapValidationRound


def get_allowance() -> int:
    """Get the allowance."""
    return 0


class AllowanceCheckBehaviour(LiquidityProvisionBaseBehaviour):
    """Check the current token allowance."""

    state_id = "allowance_check"
    matching_round = AllowanceCheckRound

    def async_act(self) -> Generator:
        """Do the action."""
        allowance = get_allowance()
        payload = AllowanceCheckPayload(self.context.agent_address, allowance)

        if allowance == self.period_state.most_voted_strategy["amountETH"]:
            self.context.logger.info(
                "Insufficient allowance. Transitioning to allowance increase."
            )
        else:
            self.context.logger.info(
                "Sufficient allowance. Transitioning to add liquidity."
            )

        with benchmark_tool.measure(
            self,
        ).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class AddAllowanceSelectKeeperBehaviour(SelectKeeperBehaviour):
    """Select the keeper agent."""

    state_id = "add_allowance_select_keeper"
    matching_round = AddAllowanceSelectKeeperRound


class AddAllowanceTransactionHashBehaviour(TransactionHashBaseBehaviour):
    """Approve token: prepare transaction hash."""

    state_id = "add_allowance_tx_hash"
    matching_round = AddAllowanceTransactionHashRound


class AddAllowanceSignatureBehaviour(TransactionSignatureBaseBehaviour):
    """Approve token: sign the transaction."""

    state_id = "add_allowance_signature"
    matching_round = AddAllowanceSignatureRound


class AddAllowanceSendBehaviour(TransactionSendBaseBehaviour):
    """Approve token: send the transaction."""

    state_id = "add_allowance_send"
    matching_round = AddAllowanceSendRound


class AddAllowanceValidationBehaviour(TransactionValidationBaseBehaviour):
    """Approve token: validate the tx."""

    state_id = "add_allowance_validation"
    matching_round = AddAllowanceValidationRound


class AddLiquiditySelectKeeperBehaviour(SelectKeeperBehaviour):
    """Select the keeper agent."""

    state_id = "add_liquidity_select_keeper"
    matching_round = AddLiquiditySelectKeeperRound


class AddLiquidityTransactionHashBehaviour(TransactionHashBaseBehaviour):
    """Enter liquidity pool: prepare transaction hash."""

    state_id = "add_liquidity_tx_hash"
    matching_round = AddLiquidityTransactionHashRound


class AddLiquiditySignatureBehaviour(TransactionSignatureBaseBehaviour):
    """Enter liquidity pool: sign the transaction."""

    state_id = "add_liquidity_signature"
    matching_round = AddLiquiditySignatureRound


class AddLiquiditySendBehaviour(TransactionSendBaseBehaviour):
    """Enter liquidity pool: send the transaction."""

    state_id = "add_liquidity_send"
    matching_round = AddLiquiditySendRound


class AddLiquidityValidationBehaviour(TransactionValidationBaseBehaviour):
    """Enter liquidity pool: validate the tx."""

    state_id = "add_liquidity_validation"
    matching_round = AddLiquidityValidationRound


class RemoveLiquiditySelectKeeperBehaviour(SelectKeeperBehaviour):
    """Select the keeper agent."""

    state_id = "remove_liquidity_select_keeper"
    matching_round = RemoveLiquiditySelectKeeperRound


class RemoveLiquidityTransactionHashBehaviour(TransactionHashBaseBehaviour):
    """Leave liquidity pool: prepare transaction hash."""

    state_id = "remove_liquidity_tx_hash"
    matching_round = RemoveLiquidityTransactionHashRound


class RemoveLiquiditySignatureBehaviour(TransactionSignatureBaseBehaviour):
    """Leave liquidity pool: sign the transaction."""

    state_id = "remove_liquidity_signature"
    matching_round = RemoveLiquiditySignatureRound


class RemoveLiquiditySendBehaviour(TransactionSendBaseBehaviour):
    """Leave liquidity pool: send the transaction."""

    state_id = "remove_liquidity_send"
    matching_round = RemoveLiquiditySendRound


class RemoveLiquidityValidationBehaviour(TransactionValidationBaseBehaviour):
    """Leave liquidity pool: validate the tx."""

    state_id = "remove_liquidity_validation"
    matching_round = RemoveLiquidityValidationRound


class RemoveAllowanceSelectKeeperBehaviour(SelectKeeperBehaviour):
    """Select the keeper agent."""

    state_id = "remove_allowance_select_keeper"
    matching_round = RemoveAllowanceSelectKeeperRound


class RemoveAllowanceTransactionHashBehaviour(TransactionHashBaseBehaviour):
    """Cancel token allowance: prepare transaction hash."""

    state_id = "remove_allowance_tx_hash"
    matching_round = RemoveAllowanceTransactionHashRound


class RemoveAllowanceSignatureBehaviour(TransactionSignatureBaseBehaviour):
    """Cancel token allowance: sign the transaction."""

    state_id = "remove_allowance_signature"
    matching_round = RemoveAllowanceSignatureRound


class RemoveAllowanceSendBehaviour(TransactionSendBaseBehaviour):
    """Cancel token allowance: send the transaction."""

    state_id = "remove_allowance_send"
    matching_round = RemoveAllowanceSendRound


class RemoveAllowanceValidationBehaviour(TransactionValidationBaseBehaviour):
    """Cancel token allowance: validate the tx."""

    state_id = "remove_allowance_validation"
    matching_round = RemoveAllowanceValidationRound


class SwapBackSelectKeeperBehaviour(SelectKeeperBehaviour):
    """Select the keeper agent."""

    state_id = "swap_back_select_keeper"
    matching_round = SwapBackSelectKeeperRound


class SwapBackTransactionHashBehaviour(TransactionHashBaseBehaviour):
    """Swap tokens back to original holdings: prepare transaction hash."""

    state_id = "swap_back_tx_hash"
    matching_round = SwapBackTransactionHashRound


class SwapBackSignatureBehaviour(TransactionSignatureBaseBehaviour):
    """Swap tokens back to original holdings: sign the transaction."""

    state_id = "swap_back_signature"
    matching_round = SwapBackSignatureRound


class SwapBackSendBehaviour(TransactionSendBaseBehaviour):
    """Swap tokens back to original holdings: send the transaction."""

    state_id = "swap_back_send"
    matching_round = SwapBackSendRound


class SwapBackValidationBehaviour(TransactionValidationBaseBehaviour):
    """Swap tokens back to original holdings: validate the tx."""

    state_id = "swap_back_validation"
    matching_round = SwapBackValidationRound


class LiquidityProvisionConsensusBehaviour(AbstractRoundBehaviour):
    """This behaviour manages the consensus stages for the liquidity provision."""

    initial_state_cls = TendermintHealthcheckBehaviour
    abci_app_cls = LiquidityProvisionAbciApp  # type: ignore
    behaviour_states: Set[Type[LiquidityProvisionBaseBehaviour]] = {  # type: ignore
        TendermintHealthcheckBehaviour,  # type: ignore
        RegistrationBehaviour,  # type: ignore
        RandomnessBehaviour,  # type: ignore
        SelectKeeperMainBehaviour,  # type: ignore
        DeploySafeSendBehaviour,  # type: ignore
        DeploySafeValidationBehaviour,  # type: ignore
        StrategyEvaluationBehaviour,  # type: ignore
        WaitBehaviour,  # type: ignore
        SwapSelectKeeperBehaviour,  # type: ignore
        SwapTransactionHashBehaviour,  # type: ignore
        SwapSignatureBehaviour,  # type: ignore
        SwapSendBehaviour,  # type: ignore
        SwapValidationBehaviour,  # type: ignore
        AllowanceCheckBehaviour,  # type: ignore
        AddAllowanceSelectKeeperBehaviour,  # type: ignore
        AddAllowanceTransactionHashBehaviour,  # type: ignore
        AddAllowanceSignatureBehaviour,  # type: ignore
        AddAllowanceSendBehaviour,  # type: ignore
        AddAllowanceValidationBehaviour,  # type: ignore
        AddLiquiditySelectKeeperBehaviour,  # type: ignore
        AddLiquidityTransactionHashBehaviour,  # type: ignore
        AddLiquiditySignatureBehaviour,  # type: ignore
        AddLiquiditySendBehaviour,  # type: ignore
        AddLiquidityValidationBehaviour,  # type: ignore
        RemoveLiquiditySelectKeeperBehaviour,  # type: ignore
        RemoveLiquidityTransactionHashBehaviour,  # type: ignore
        RemoveLiquiditySignatureBehaviour,  # type: ignore
        RemoveLiquiditySendBehaviour,  # type: ignore
        RemoveLiquidityValidationBehaviour,  # type: ignore
        RemoveAllowanceSelectKeeperBehaviour,  # type: ignore
        RemoveAllowanceTransactionHashBehaviour,  # type: ignore
        RemoveAllowanceSignatureBehaviour,  # type: ignore
        RemoveAllowanceSendBehaviour,  # type: ignore
        RemoveAllowanceValidationBehaviour,  # type: ignore
        SwapBackSelectKeeperBehaviour,  # type: ignore
        SwapBackTransactionHashBehaviour,  # type: ignore
        SwapBackSignatureBehaviour,  # type: ignore
        SwapBackSendBehaviour,  # type: ignore
        SwapBackValidationBehaviour,  # type: ignore
        ResetBehaviour,  # type: ignore
    }

    def setup(self) -> None:
        """Set up the behaviour."""
        super().setup()
        benchmark_tool.logger = self.context.logger
