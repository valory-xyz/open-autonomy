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

"""This module contains the behaviours for the 'abci' skill."""
import binascii
import pprint
from abc import ABC
from typing import Any, Dict, Generator, Optional, Set, Tuple, Type, Union, cast

from aea.protocols.base import Message
from web3.types import Nonce, TxData

from packages.valory.contracts.gnosis_safe.contract import GnosisSafeContract
from packages.valory.protocols.contract_api.message import ContractApiMessage
from packages.valory.skills.abstract_round_abci.behaviour_utils import RPCResponseStatus
from packages.valory.skills.abstract_round_abci.behaviours import (
    AbstractRoundBehaviour,
    BaseState,
)
from packages.valory.skills.abstract_round_abci.common import (
    RandomnessBehaviour,
    SelectKeeperBehaviour,
)
from packages.valory.skills.abstract_round_abci.utils import VerifyDrand
from packages.valory.skills.transaction_settlement_abci.models import TransactionParams
from packages.valory.skills.transaction_settlement_abci.payload_tools import (
    VerificationStatus,
    skill_input_hex_to_payload,
    tx_hist_payload_to_hex,
)
from packages.valory.skills.transaction_settlement_abci.payloads import (
    CheckTransactionHistoryPayload,
    FinalizationTxPayload,
    RandomnessPayload,
    ResetPayload,
    SelectKeeperPayload,
    SignaturePayload,
    SynchronizeLateMessagesPayload,
    ValidatePayload,
)
from packages.valory.skills.transaction_settlement_abci.rounds import (
    CheckLateTxHashesRound,
    CheckTransactionHistoryRound,
    CollectSignatureRound,
    FinalizationRound,
    PeriodState,
    RandomnessTransactionSubmissionRound,
    ResetRound,
    SelectKeeperTransactionSubmissionRoundA,
    SelectKeeperTransactionSubmissionRoundB,
    SelectKeeperTransactionSubmissionRoundBAfterTimeout,
    SynchronizeLateMessagesRound,
    TransactionSubmissionAbciApp,
    ValidateTransactionRound,
)


TxDataType = Dict[str, Union[VerificationStatus, str, int]]


drand_check = VerifyDrand()


class TransactionSettlementBaseState(BaseState, ABC):
    """Base state behaviour for the common apps' skill."""

    @property
    def period_state(self) -> PeriodState:
        """Return the period state."""
        return cast(PeriodState, super().period_state)

    @property
    def params(self) -> TransactionParams:
        """Return the params."""
        return cast(TransactionParams, super().params)

    def _get_tx_data(
        self, message: ContractApiMessage
    ) -> Generator[None, None, TxDataType]:
        """Get the transaction data from a `ContractApiMessage`."""
        tx_data: TxDataType = {
            "status": VerificationStatus.PENDING,
            "tx_digest": "",
            "nonce": "",
            "max_priority_fee_per_gas": "",
        }

        if (
            message.performative == ContractApiMessage.Performative.ERROR
            and message.message is not None
        ):
            if self._safe_nonce_reused(message.message):
                tx_data["status"] = VerificationStatus.VERIFIED
            else:
                tx_data["status"] = VerificationStatus.ERROR
            self.context.logger.warning(
                f"get_raw_safe_transaction unsuccessful! Received: {message}"
            )
            return tx_data

        if (
            message.performative != ContractApiMessage.Performative.RAW_TRANSACTION
        ):  # pragma: nocover
            self.context.logger.warning(
                f"get_raw_safe_transaction unsuccessful! Received: {message}"
            )
            return tx_data

        tx_digest, rpc_status = yield from self.send_raw_transaction(
            message.raw_transaction
        )

        if rpc_status == RPCResponseStatus.INCORRECT_NONCE:
            self.context.logger.warning(
                f"send_raw_transaction unsuccessful! Received: {rpc_status}"
            )
            tx_data["status"] = VerificationStatus.ERROR
            return tx_data

        if rpc_status != RPCResponseStatus.SUCCESS:
            self.context.logger.warning(
                f"send_raw_transaction unsuccessful! Received: {rpc_status}"
            )
            return tx_data

        tx_data["tx_digest"] = cast(str, tx_digest)
        tx_data["nonce"] = int(cast(str, message.raw_transaction.body["nonce"]))
        tx_data["max_priority_fee_per_gas"] = int(
            cast(
                str,
                message.raw_transaction.body["maxPriorityFeePerGas"],
            )
        )
        # Set nonce and tip.
        self.params.nonce = Nonce(int(cast(str, tx_data["nonce"])))
        self.params.tip = int(cast(str, tx_data["max_priority_fee_per_gas"]))

        return tx_data

    def _verify_tx(self, tx_hash: str) -> Generator[None, None, ContractApiMessage]:
        """Verify a transaction."""
        tx_params = skill_input_hex_to_payload(self.period_state.most_voted_tx_hash)

        contract_api_msg = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_STATE,  # type: ignore
            contract_address=self.period_state.safe_contract_address,
            contract_id=str(GnosisSafeContract.contract_id),
            contract_callable="verify_tx",
            tx_hash=tx_hash,
            owners=tuple(self.period_state.participants),
            to_address=tx_params["to_address"],
            value=tx_params["ether_value"],
            data=tx_params["data"],
            safe_tx_gas=tx_params["safe_tx_gas"],
            signatures_by_owner={
                key: payload.signature
                for key, payload in self.period_state.participant_to_signature.items()
            },
            operation=tx_params["operation"],
        )

        return contract_api_msg

    @staticmethod
    def _safe_nonce_reused(revert_reason: str) -> bool:
        """Check for GS026."""
        return "GS026" in revert_reason

    def _reset_params_if_flag_set(self) -> None:
        """Reset tx parameters."""
        if self.period_state.is_reset_params_set:
            self.params.reset_tx_params()


class RandomnessTransactionSubmissionBehaviour(RandomnessBehaviour):
    """Retrieve randomness."""

    state_id = "randomness_transaction_submission"
    matching_round = RandomnessTransactionSubmissionRound
    payload_class = RandomnessPayload


class SelectKeeperTransactionSubmissionBehaviourA(  # pylint: disable=too-many-ancestors
    SelectKeeperBehaviour, TransactionSettlementBaseState
):
    """Select the keeper agent."""

    state_id = "select_keeper_transaction_submission_a"
    matching_round = SelectKeeperTransactionSubmissionRoundA
    payload_class = SelectKeeperPayload


class SelectKeeperTransactionSubmissionBehaviourB(  # pylint: disable=too-many-ancestors
    SelectKeeperBehaviour, TransactionSettlementBaseState
):
    """Select the keeper b agent."""

    state_id = "select_keeper_transaction_submission_b"
    matching_round = SelectKeeperTransactionSubmissionRoundB
    payload_class = SelectKeeperPayload


class SelectKeeperTransactionSubmissionBehaviourBAfterTimeout(  # pylint: disable=too-many-ancestors
    SelectKeeperBehaviour, TransactionSettlementBaseState
):
    """Select the keeper b agent after a timeout."""

    state_id = "select_keeper_transaction_submission_b_after_timeout"
    matching_round = SelectKeeperTransactionSubmissionRoundBAfterTimeout
    payload_class = SelectKeeperPayload


class ValidateTransactionBehaviour(TransactionSettlementBaseState):
    """Validate a transaction."""

    state_id = "validate_transaction"
    matching_round = ValidateTransactionRound

    def async_act(self) -> Generator:
        """
        Do the action.

        Steps:
        - Validate that the transaction hash provided by the keeper points to a
          valid transaction.
        - Send the transaction with the validation result and wait for it to be
          mined.
        - Wait until ABCI application transitions to the next round.
        - Go to the next behaviour state (set done event).
        """

        with self.context.benchmark_tool.measure(self.state_id).local():
            is_correct = yield from self.has_transaction_been_sent()
            if is_correct:
                self.context.logger.info(
                    f"Finalized with transaction hash: {self.period_state.to_be_validated_tx_hash}"
                )
            payload = ValidatePayload(self.context.agent_address, is_correct)

        with self.context.benchmark_tool.measure(self.state_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()

    def has_transaction_been_sent(self) -> Generator[None, None, Optional[bool]]:
        """Transaction verification."""
        response = yield from self.get_transaction_receipt(
            self.period_state.to_be_validated_tx_hash,
            self.params.retry_timeout,
            self.params.retry_attempts,
        )
        if response is None:  # pragma: nocover
            self.context.logger.error(
                f"tx {self.period_state.to_be_validated_tx_hash} receipt check timed out!"
            )
            return None

        # Reset tx parameters.
        self.params.reset_tx_params()

        contract_api_msg = yield from self._verify_tx(
            self.period_state.to_be_validated_tx_hash
        )
        if (
            contract_api_msg.performative != ContractApiMessage.Performative.STATE
        ):  # pragma: nocover
            self.context.logger.error(
                f"verify_tx unsuccessful! Received: {contract_api_msg}"
            )
            return False
        verified = cast(bool, contract_api_msg.state.body["verified"])
        verified_log = (
            f"Verified result: {verified}"
            if verified
            else f"Verified result: {verified}, all: {contract_api_msg.state.body}"
        )
        self.context.logger.info(verified_log)
        return verified


class CheckTransactionHistoryBehaviour(TransactionSettlementBaseState):
    """Check the transaction history."""

    state_id = "check_transaction_history"
    matching_round = CheckTransactionHistoryRound

    def async_act(self) -> Generator:
        """Do the action."""

        with self.context.benchmark_tool.measure(self.state_id).local():
            verification_status, tx_hash = yield from self._check_tx_history()

            if verification_status == VerificationStatus.VERIFIED:
                self.context.logger.info(
                    f"A previous transaction {tx_hash} has already been verified for "
                    f"{self.period_state.to_be_validated_tx_hash}."
                )
            elif verification_status == VerificationStatus.NOT_VERIFIED:
                self.context.logger.info(
                    f"No previous transaction has been verified for "
                    f"{self.period_state.to_be_validated_tx_hash}."
                )

            verified_res = tx_hist_payload_to_hex(verification_status, tx_hash)
            payload = CheckTransactionHistoryPayload(
                self.context.agent_address, verified_res
            )

        with self.context.benchmark_tool.measure(self.state_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()

    def _check_tx_history(
        self,
    ) -> Generator[None, None, Tuple[VerificationStatus, Optional[str]]]:
        """Check the transaction history."""
        history = (
            self.period_state.tx_hashes_history
            if self.state_id == "check_transaction_history"
            else self.period_state.late_arriving_tx_hashes
        )

        if history is None:
            self.context.logger.error(
                "An unexpected error occurred! The state's history does not contain any transaction hashes, "
                f"but entered the `{self.state_id}` state."
            )
            return VerificationStatus.ERROR, None

        for tx_hash in history[::-1]:
            contract_api_msg = yield from self._verify_tx(tx_hash)

            if (
                contract_api_msg.performative != ContractApiMessage.Performative.STATE
            ):  # pragma: nocover
                self.context.logger.error(
                    f"verify_tx unsuccessful for {tx_hash}! Received: {contract_api_msg}"
                )
                return VerificationStatus.ERROR, tx_hash

            verified = cast(bool, contract_api_msg.state.body["verified"])
            verified_log = f"Verified result for {tx_hash}: {verified}"

            if verified:
                self.context.logger.info(verified_log)
                return VerificationStatus.VERIFIED, tx_hash

            self.context.logger.info(
                verified_log + f", all: {contract_api_msg.state.body}"
            )

            tx_data = cast(TxData, contract_api_msg.state.body["transaction"])
            revert_reason = yield from self._get_revert_reason(tx_data)

            if revert_reason is not None:
                if self._safe_nonce_reused(revert_reason):
                    check_expected_to_be_verified = (
                        "The next tx check"
                        if self.state_id == "check_transaction_history"
                        else "One of the next tx checks"
                    )
                    self.context.logger.info(
                        f"The safe's nonce has been reused for {tx_hash}. "
                        f"{check_expected_to_be_verified} is expected to be verified!"
                    )
                    continue

                self.context.logger.warning(
                    f"Payload is invalid for {tx_hash}! Cannot continue. Received: {revert_reason}"
                )

            return VerificationStatus.INVALID_PAYLOAD, tx_hash

        return VerificationStatus.NOT_VERIFIED, None

    def _get_revert_reason(self, tx: TxData) -> Generator[None, None, Optional[str]]:
        """Get the revert reason of the given transaction."""
        contract_api_msg = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_STATE,  # type: ignore
            contract_address=self.period_state.safe_contract_address,
            contract_id=str(GnosisSafeContract.contract_id),
            contract_callable="revert_reason",
            tx=tx,
        )

        if (
            contract_api_msg.performative != ContractApiMessage.Performative.STATE
        ):  # pragma: nocover
            self.context.logger.error(
                f"An unexpected error occurred while checking {tx['hash'].hex()}: {contract_api_msg}"
            )
            return None

        return cast(str, contract_api_msg.state.body["revert_reason"])


class CheckLateTxHashesBehaviour(  # pylint: disable=too-many-ancestors
    CheckTransactionHistoryBehaviour
):
    """Check the late-arriving transaction hashes."""

    state_id = "check_late_tx_hashes"
    matching_round = CheckLateTxHashesRound


class SynchronizeLateMessagesBehaviour(TransactionSettlementBaseState):
    """Synchronize late-arriving messages state."""

    state_id = "sync_late_messages"
    matching_round = SynchronizeLateMessagesRound

    def __init__(self, **kwargs: Any):
        """Initialize a `SynchronizeLateMessagesBehaviour`"""
        super().__init__(**kwargs)
        self._tx_hashes: str = ""

    def async_act(self) -> Generator:
        """Do the action."""

        with self.context.benchmark_tool.measure(self.state_id).local():
            if len(self.params.late_messages) > 0:
                current_message = self.params.late_messages.pop()
                tx_data = yield from self._get_tx_data(current_message)
                # here, we concatenate the tx_hashes of all the late-arriving messages. Later, we will parse them.
                self._tx_hashes += cast(str, tx_data["tx_digest"])
                return

            payload = SynchronizeLateMessagesPayload(
                self.context.agent_address, self._tx_hashes
            )

        with self.context.benchmark_tool.measure(self.state_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()

    def set_done(self) -> None:
        """Set the behaviour to done and clean the local late message parameter."""
        super().set_done()
        self.params.late_messages = []


class SignatureBehaviour(TransactionSettlementBaseState):
    """Signature state."""

    state_id = "sign"
    matching_round = CollectSignatureRound

    def async_act(self) -> Generator:
        """
        Do the action.

        Steps:
        - Request the signature of the transaction hash.
        - Send the signature as a transaction and wait for it to be mined.
        - Wait until ABCI application transitions to the next round.
        - Go to the next behaviour state (set done event).
        """

        with self.context.benchmark_tool.measure(self.state_id).local():
            self.context.logger.info(
                f"Consensus reached on tx hash: {self.period_state.most_voted_tx_hash}"
            )
            signature_hex = yield from self._get_safe_tx_signature()
            payload = SignaturePayload(self.context.agent_address, signature_hex)

        with self.context.benchmark_tool.measure(self.state_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()

    def _get_safe_tx_signature(self) -> Generator[None, None, str]:
        """Get signature of safe transaction hash."""
        tx_params = skill_input_hex_to_payload(self.period_state.most_voted_tx_hash)
        # is_deprecated_mode=True because we want to call Account.signHash,
        # which is the same used by gnosis-py
        safe_tx_hash_bytes = binascii.unhexlify(tx_params["safe_tx_hash"])
        signature_hex = yield from self.get_signature(
            safe_tx_hash_bytes, is_deprecated_mode=True
        )
        # remove the leading '0x'
        signature_hex = signature_hex[2:]
        self.context.logger.info(f"Signature: {signature_hex}")
        return signature_hex


class FinalizeBehaviour(TransactionSettlementBaseState):
    """Finalize state."""

    state_id = "finalize"
    matching_round = FinalizationRound

    def async_act(self) -> Generator[None, None, None]:
        """
        Do the action.

        Steps:
        - If the agent is the keeper, then prepare the transaction and send it.
        - Otherwise, wait until the next round.
        - If a timeout is hit, set exit A event, otherwise set done event.
        """

        # Reset tx params if the flag has been set
        self._reset_params_if_flag_set()

        if self.context.agent_address != self.period_state.most_voted_keeper_address:
            yield from self._not_sender_act()
        else:
            yield from self._sender_act()

    def _not_sender_act(self) -> Generator:
        """Do the non-sender action."""
        with self.context.benchmark_tool.measure(self.state_id).consensus():
            yield from self.wait_until_round_end()
        self.set_done()

    def _sender_act(self) -> Generator[None, None, None]:
        """Do the sender action."""

        with self.context.benchmark_tool.measure(self.state_id).local():
            self.context.logger.info(
                "I am the designated sender, attempting to send the safe transaction..."
            )
            tx_data = yield from self._send_safe_transaction()
            if (
                tx_data["tx_digest"] == ""
                and tx_data["status"] == VerificationStatus.PENDING
            ) or tx_data["status"] == VerificationStatus.ERROR:
                self.context.logger.error(
                    "Did not succeed with finalising the transaction!"
                )
            elif tx_data["status"] == VerificationStatus.VERIFIED:
                self.context.logger.error(
                    "Trying to finalize a transaction which has been verified already!"
                )
            else:
                self.context.logger.info(
                    f"Finalization tx digest: {cast(str, tx_data['tx_digest'])}"
                )
                self.context.logger.debug(
                    f"Signatures: {pprint.pformat(self.period_state.participant_to_signature)}"
                )
            tx_data["status"] = cast(VerificationStatus, tx_data["status"]).value
            payload = FinalizationTxPayload(
                self.context.agent_address,
                cast(Dict[str, Union[str, int]], tx_data),
            )

        with self.context.benchmark_tool.measure(self.state_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()

    def _send_safe_transaction(
        self,
    ) -> Generator[None, None, Dict[str, Union[VerificationStatus, str, int]]]:
        """Send a Safe transaction using the participants' signatures."""
        tx_params = skill_input_hex_to_payload(self.period_state.most_voted_tx_hash)

        contract_api_msg = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
            contract_address=self.period_state.safe_contract_address,
            contract_id=str(GnosisSafeContract.contract_id),
            contract_callable="get_raw_safe_transaction",
            sender_address=self.context.agent_address,
            owners=tuple(self.period_state.participants),
            to_address=tx_params["to_address"],
            value=tx_params["ether_value"],
            data=tx_params["data"],
            safe_tx_gas=tx_params["safe_tx_gas"],
            signatures_by_owner={
                key: payload.signature
                for key, payload in self.period_state.participant_to_signature.items()
            },
            nonce=self.params.nonce,
            old_tip=self.params.tip,
            operation=tx_params["operation"],
        )

        tx_data = yield from self._get_tx_data(contract_api_msg)
        return tx_data

    def handle_late_messages(self, message: Message) -> None:
        """Store a potentially late-arriving message locally.

        :param message: the late arriving message to handle.
        """
        if isinstance(message, ContractApiMessage):
            self.params.late_messages.append(message)
        else:
            super().handle_late_messages(message)


class ResetBehaviour(TransactionSettlementBaseState):
    """Reset state."""

    matching_round = ResetRound
    state_id = "reset"

    def async_act(self) -> Generator:
        """Do the action."""
        self.context.logger.info(
            f"Period {self.period_state.period_count} was not finished. Resetting!"
        )
        self.params.reset_tx_params()
        payload = ResetPayload(
            self.context.agent_address, self.period_state.period_count + 1
        )
        yield from self.send_a2a_transaction(payload)
        yield from self.wait_until_round_end()
        self.set_done()


class TransactionSettlementRoundBehaviour(AbstractRoundBehaviour):
    """This behaviour manages the consensus stages for the basic transaction settlement."""

    initial_state_cls = RandomnessTransactionSubmissionBehaviour
    abci_app_cls = TransactionSubmissionAbciApp  # type: ignore
    behaviour_states: Set[Type[BaseState]] = {
        RandomnessTransactionSubmissionBehaviour,  # type: ignore
        SelectKeeperTransactionSubmissionBehaviourA,  # type: ignore
        SelectKeeperTransactionSubmissionBehaviourB,  # type: ignore
        SelectKeeperTransactionSubmissionBehaviourBAfterTimeout,  # type: ignore
        ValidateTransactionBehaviour,  # type: ignore
        CheckTransactionHistoryBehaviour,  # type: ignore
        SignatureBehaviour,  # type: ignore
        FinalizeBehaviour,  # type: ignore
        SynchronizeLateMessagesBehaviour,  # type: ignore
        CheckLateTxHashesBehaviour,  # type: ignore
        ResetBehaviour,  # type: ignore
    }
