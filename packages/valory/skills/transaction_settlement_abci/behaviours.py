# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2024 Valory AG
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
import re
from abc import ABC
from collections import deque
from typing import (
    Any,
    Deque,
    Dict,
    Generator,
    Iterator,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    Union,
    cast,
)

from aea.protocols.base import Message
from web3.types import Nonce, TxData, Wei

from packages.valory.contracts.gnosis_safe.contract import GnosisSafeContract
from packages.valory.protocols.contract_api.message import ContractApiMessage
from packages.valory.skills.abstract_round_abci.behaviour_utils import RPCResponseStatus
from packages.valory.skills.abstract_round_abci.behaviours import (
    AbstractRoundBehaviour,
    BaseBehaviour,
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
    RandomnessTransactionSubmissionRound,
    ResetRound,
    SelectKeeperTransactionSubmissionARound,
    SelectKeeperTransactionSubmissionBAfterTimeoutRound,
    SelectKeeperTransactionSubmissionBRound,
    SynchronizeLateMessagesRound,
    SynchronizedData,
    TransactionSubmissionAbciApp,
    ValidateTransactionRound,
)


TxDataType = Dict[str, Union[VerificationStatus, Deque[str], int, Set[str], str]]

drand_check = VerifyDrand()

REVERT_CODE_RE = r"\s(GS\d{3})[^\d]"

# This mapping was copied from:
# https://github.com/safe-global/safe-contracts/blob/ce5cbd256bf7a8a34538c7e5f1f2366a9d685f34/docs/error_codes.md
REVERT_CODES_TO_REASONS: Dict[str, str] = {
    "GS000": "Could not finish initialization",
    "GS001": "Threshold needs to be defined",
    "GS010": "Not enough gas to execute Safe transaction",
    "GS011": "Could not pay gas costs with ether",
    "GS012": "Could not pay gas costs with token",
    "GS013": "Safe transaction failed when gasPrice and safeTxGas were 0",
    "GS020": "Signatures data too short",
    "GS021": "Invalid contract signature location: inside static part",
    "GS022": "Invalid contract signature location: length not present",
    "GS023": "Invalid contract signature location: data not complete",
    "GS024": "Invalid contract signature provided",
    "GS025": "Hash has not been approved",
    "GS026": "Invalid owner provided",
    "GS030": "Only owners can approve a hash",
    "GS031": "Method can only be called from this contract",
    "GS100": "Modules have already been initialized",
    "GS101": "Invalid module address provided",
    "GS102": "Module has already been added",
    "GS103": "Invalid prevModule, module pair provided",
    "GS104": "Method can only be called from an enabled module",
    "GS200": "Owners have already been setup",
    "GS201": "Threshold cannot exceed owner count",
    "GS202": "Threshold needs to be greater than 0",
    "GS203": "Invalid owner address provided",
    "GS204": "Address is already an owner",
    "GS205": "Invalid prevOwner, owner pair provided",
    "GS300": "Guard does not implement IERC165",
}


class TransactionSettlementBaseBehaviour(BaseBehaviour, ABC):
    """Base behaviour for the common apps' skill."""

    @property
    def synchronized_data(self) -> SynchronizedData:
        """Return the synchronized data."""
        return cast(SynchronizedData, super().synchronized_data)

    @property
    def params(self) -> TransactionParams:
        """Return the params."""
        return cast(TransactionParams, super().params)

    @staticmethod
    def serialized_keepers(keepers: Deque[str], keeper_retries: int) -> str:
        """Get the keepers serialized."""
        if len(keepers) == 0:
            return ""
        keepers_ = "".join(keepers)
        keeper_retries_ = keeper_retries.to_bytes(32, "big").hex()
        concatenated = keeper_retries_ + keepers_

        return concatenated

    def get_gas_price_params(self, tx_body: dict) -> List[str]:
        """Guess the gas strategy from the transaction params"""
        strategy_to_params: Dict[str, List[str]] = {
            "eip": ["maxPriorityFeePerGas", "maxFeePerGas"],
            "gas_station": ["gasPrice"],
        }

        for strategy, params in strategy_to_params.items():
            if all(param in tx_body for param in params):
                self.context.logger.info(f"Detected gas strategy: {strategy}")
                return params

        return []

    def _get_tx_data(
        self,
        message: ContractApiMessage,
        use_flashbots: bool,
        manual_gas_limit: int = 0,
        raise_on_failed_simulation: bool = False,
        chain_id: Optional[str] = None,
    ) -> Generator[None, None, TxDataType]:
        """Get the transaction data from a `ContractApiMessage`."""
        tx_data: TxDataType = {
            "status": VerificationStatus.PENDING,
            "keepers": self.synchronized_data.keepers,
            "keeper_retries": self.synchronized_data.keeper_retries,
            "blacklisted_keepers": self.synchronized_data.blacklisted_keepers,
            "tx_digest": "",
        }

        # Check for errors in the transaction preparation
        if (
            message.performative == ContractApiMessage.Performative.ERROR
            and message.message is not None
        ):
            if self._safe_nonce_reused(message.message):
                tx_data["status"] = VerificationStatus.VERIFIED
            else:
                tx_data["status"] = VerificationStatus.ERROR
            self.context.logger.warning(self._parse_revert_reason(message))
            return tx_data

        # Check that we have a RAW_TRANSACTION response
        if message.performative != ContractApiMessage.Performative.RAW_TRANSACTION:
            self.context.logger.warning(
                f"get_raw_safe_transaction unsuccessful! Received: {message}"
            )
            return tx_data

        if manual_gas_limit > 0:
            message.raw_transaction.body["gas"] = manual_gas_limit

        # Send transaction
        tx_digest, rpc_status = yield from self.send_raw_transaction(
            message.raw_transaction,
            use_flashbots,
            raise_on_failed_simulation=raise_on_failed_simulation,
            chain_id=chain_id,
        )

        # Handle transaction results
        if rpc_status == RPCResponseStatus.ALREADY_KNOWN:
            self.context.logger.warning(
                "send_raw_transaction unsuccessful! Transaction is already in the mempool! Will attempt to verify it."
            )

        if rpc_status == RPCResponseStatus.INCORRECT_NONCE:
            tx_data["status"] = VerificationStatus.ERROR
            self.context.logger.warning(
                "send_raw_transaction unsuccessful! Incorrect nonce."
            )

        if rpc_status == RPCResponseStatus.INSUFFICIENT_FUNDS:
            # blacklist self.
            tx_data["status"] = VerificationStatus.INSUFFICIENT_FUNDS
            blacklisted = cast(Deque[str], tx_data["keepers"]).popleft()
            tx_data["keeper_retries"] = 1
            cast(Set[str], tx_data["blacklisted_keepers"]).add(blacklisted)
            self.context.logger.warning(
                "send_raw_transaction unsuccessful! Insufficient funds."
            )

        if rpc_status not in {
            RPCResponseStatus.SUCCESS,
            RPCResponseStatus.ALREADY_KNOWN,
        }:
            self.context.logger.warning(
                f"send_raw_transaction unsuccessful! Received: {rpc_status}"
            )
            return tx_data

        tx_data["tx_digest"] = cast(str, tx_digest)

        nonce = Nonce(int(cast(str, message.raw_transaction.body["nonce"])))
        fallback_gas = message.raw_transaction.body["gas"]

        # Get the gas params
        gas_price_params = self.get_gas_price_params(message.raw_transaction.body)

        gas_price = {
            gas_price_param: Wei(
                int(
                    cast(
                        str,
                        message.raw_transaction.body[gas_price_param],
                    )
                )
            )
            for gas_price_param in gas_price_params
        }

        # Set hash, nonce and tip.
        self.params.mutable_params.tx_hash = cast(str, tx_data["tx_digest"])
        if nonce == self.params.mutable_params.nonce:
            self.context.logger.info(
                "Attempting to replace transaction "
                f"with old gas price parameters {self.params.mutable_params.gas_price}, using new gas price parameters {gas_price}"
            )
        else:
            self.context.logger.info(
                f"Sent transaction for mining with gas parameters {gas_price}"
            )
            self.params.mutable_params.nonce = nonce
        self.params.mutable_params.gas_price = gas_price
        self.params.mutable_params.fallback_gas = fallback_gas

        return tx_data

    def _verify_tx(self, tx_hash: str) -> Generator[None, None, ContractApiMessage]:
        """Verify a transaction."""
        tx_params = skill_input_hex_to_payload(
            self.synchronized_data.most_voted_tx_hash
        )
        chain_id = self.synchronized_data.get_chain_id(self.params.default_chain_id)
        contract_api_msg = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_STATE,  # type: ignore
            contract_address=self.synchronized_data.safe_contract_address,
            contract_id=str(GnosisSafeContract.contract_id),
            contract_callable="verify_tx",
            tx_hash=tx_hash,
            owners=tuple(self.synchronized_data.participants),
            to_address=tx_params["to_address"],
            value=tx_params["ether_value"],
            data=tx_params["data"],
            safe_tx_gas=tx_params["safe_tx_gas"],
            signatures_by_owner={
                key: payload.signature
                for key, payload in self.synchronized_data.participant_to_signature.items()
            },
            operation=tx_params["operation"],
            chain_id=chain_id,
        )
        return contract_api_msg

    @staticmethod
    def _safe_nonce_reused(revert_reason: str) -> bool:
        """Check for GS026."""
        return "GS026" in revert_reason

    @staticmethod
    def _parse_revert_reason(message: ContractApiMessage) -> str:
        """Parse a revert reason and log a relevant message."""
        default_message = f"get_raw_safe_transaction unsuccessful! Received: {message}"

        revert_reason = message.message
        if not revert_reason:
            return default_message

        revert_match = re.findall(REVERT_CODE_RE, revert_reason)
        if revert_match is None or len(revert_match) != 1:
            return default_message

        revert_code = revert_match.pop()
        revert_explanation = REVERT_CODES_TO_REASONS.get(revert_code, None)
        if revert_explanation is None:
            return default_message

        return f"Received a {revert_code} revert error: {revert_explanation}."

    def _get_safe_nonce(self) -> Generator[None, None, ContractApiMessage]:
        """Get the safe nonce."""
        chain_id = self.synchronized_data.get_chain_id(self.params.default_chain_id)
        contract_api_msg = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_STATE,  # type: ignore
            contract_address=self.synchronized_data.safe_contract_address,
            contract_id=str(GnosisSafeContract.contract_id),
            contract_callable="get_safe_nonce",
            chain_id=chain_id,
        )
        return contract_api_msg


class RandomnessTransactionSubmissionBehaviour(RandomnessBehaviour):
    """Retrieve randomness."""

    matching_round = RandomnessTransactionSubmissionRound
    payload_class = RandomnessPayload


class SelectKeeperTransactionSubmissionBehaviourA(  # pylint: disable=too-many-ancestors
    SelectKeeperBehaviour, TransactionSettlementBaseBehaviour
):
    """Select the keeper agent."""

    matching_round = SelectKeeperTransactionSubmissionARound
    payload_class = SelectKeeperPayload

    def async_act(self) -> Generator:
        """Do the action."""

        with self.context.benchmark_tool.measure(self.behaviour_id).local():
            keepers = deque((self._select_keeper(),))
            payload = self.payload_class(
                self.context.agent_address, self.serialized_keepers(keepers, 1)
            )

        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class SelectKeeperTransactionSubmissionBehaviourB(  # pylint: disable=too-many-ancestors
    SelectKeeperTransactionSubmissionBehaviourA
):
    """Select the keeper b agent."""

    matching_round = SelectKeeperTransactionSubmissionBRound

    def async_act(self) -> Generator:
        """
        Do the action.

        Steps:
            - If we have not selected enough keepers for the period,
                select a keeper randomly and add it to the keepers' queue, with top priority.
            - Otherwise, cycle through the keepers' subset, using the following logic:
                A `PENDING` verification status means that we have not received any errors,
                therefore, all we know is that the tx has not been mined yet due to low pricing.
                Consequently, we are going to retry with the same keeper in order to replace the transaction.
                However, if we receive a status other than `PENDING`, we need to cycle through the keepers' subset.
                Moreover, if the current keeper has reached the allowed number of retries, then we cycle anyway.
            - Send the transaction with the keepers and wait for it to be mined.
            - Wait until ABCI application transitions to the next round.
            - Go to the next behaviour (set done event).
        """

        with self.context.benchmark_tool.measure(self.behaviour_id).local():
            keepers = self.synchronized_data.keepers
            keeper_retries = 1

            if self.synchronized_data.keepers_threshold_exceeded:
                keepers.rotate(-1)
                self.context.logger.info(f"Rotated keepers to: {keepers}.")
            elif (
                self.synchronized_data.keeper_retries
                != self.params.keeper_allowed_retries
                and self.synchronized_data.final_verification_status
                == VerificationStatus.PENDING
            ):
                keeper_retries += self.synchronized_data.keeper_retries
                self.context.logger.info(
                    f"Kept keepers and incremented retries: {keepers}."
                )
            else:
                keepers.appendleft(self._select_keeper())

            payload = self.payload_class(
                self.context.agent_address,
                self.serialized_keepers(keepers, keeper_retries),
            )

        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class SelectKeeperTransactionSubmissionBehaviourBAfterTimeout(  # pylint: disable=too-many-ancestors
    SelectKeeperTransactionSubmissionBehaviourB
):
    """Select the keeper b agent after a timeout."""

    matching_round = SelectKeeperTransactionSubmissionBAfterTimeoutRound


class ValidateTransactionBehaviour(TransactionSettlementBaseBehaviour):
    """Validate a transaction."""

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
        - Go to the next behaviour (set done event).
        """

        with self.context.benchmark_tool.measure(self.behaviour_id).local():
            is_correct = yield from self.has_transaction_been_sent()
            if is_correct:
                self.context.logger.info(
                    f"Finalized with transaction hash: {self.synchronized_data.to_be_validated_tx_hash}"
                )
            payload = ValidatePayload(self.context.agent_address, is_correct)

        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()

    def has_transaction_been_sent(self) -> Generator[None, None, Optional[bool]]:
        """Transaction verification."""

        to_be_validated_tx_hash = self.synchronized_data.to_be_validated_tx_hash

        response = yield from self.get_transaction_receipt(
            to_be_validated_tx_hash,
            self.params.retry_timeout,
            self.params.retry_attempts,
            chain_id=self.synchronized_data.get_chain_id(self.params.default_chain_id),
        )
        if response is None:  # pragma: nocover
            self.context.logger.error(
                f"tx {to_be_validated_tx_hash} receipt check timed out!"
            )
            return None

        contract_api_msg = yield from self._verify_tx(to_be_validated_tx_hash)
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


class CheckTransactionHistoryBehaviour(TransactionSettlementBaseBehaviour):
    """Check the transaction history."""

    matching_round = CheckTransactionHistoryRound
    check_expected_to_be_verified = "The next tx check"

    @property
    def history(self) -> List[str]:
        """Get the history of hashes."""
        return self.synchronized_data.tx_hashes_history

    def async_act(self) -> Generator:
        """Do the action."""

        with self.context.benchmark_tool.measure(self.behaviour_id).local():
            verification_status, tx_hash = yield from self._check_tx_history()
            if verification_status == VerificationStatus.VERIFIED:
                msg = f"A previous transaction {tx_hash} has already been verified "
                msg += (
                    f"for {self.synchronized_data.to_be_validated_tx_hash}."
                    if self.synchronized_data.tx_hashes_history
                    else "and was synced after the finalization round timed out."
                )
                self.context.logger.info(msg)
            elif verification_status == VerificationStatus.NOT_VERIFIED:
                self.context.logger.info(
                    f"No previous transaction has been verified for "
                    f"{self.synchronized_data.to_be_validated_tx_hash}."
                )

            verified_res = tx_hist_payload_to_hex(verification_status, tx_hash)
            payload = CheckTransactionHistoryPayload(
                self.context.agent_address, verified_res
            )

        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()

    def _check_tx_history(  # pylint: disable=too-many-return-statements
        self,
    ) -> Generator[None, None, Tuple[VerificationStatus, Optional[str]]]:
        """Check the transaction history."""
        if not self.history:
            self.context.logger.error(
                "An unexpected error occurred! The synchronized data do not contain any transaction hashes, "
                f"but entered the `{self.behaviour_id}` behaviour."
            )
            return VerificationStatus.ERROR, None

        contract_api_msg = yield from self._get_safe_nonce()
        if (
            contract_api_msg.performative != ContractApiMessage.Performative.STATE
        ):  # pragma: nocover
            self.context.logger.error(
                f"get_safe_nonce unsuccessful! Received: {contract_api_msg}"
            )
            return VerificationStatus.ERROR, None

        safe_nonce = cast(int, contract_api_msg.state.body["safe_nonce"])
        if safe_nonce == self.params.mutable_params.nonce:
            # if we have reached this state it means that the transaction didn't go through in the expected time
            # as such we assume it is not verified
            self.context.logger.info(
                f"Safe nonce is the same as the nonce used in the transaction: {safe_nonce}. "
                f"No transaction has gone through yet."
            )
            return VerificationStatus.NOT_VERIFIED, None

        self.context.logger.info(
            f"A transaction with nonce {safe_nonce} has already been sent. "
        )
        self.context.logger.info(
            f"Starting check for the transaction history: {self.history}. "
        )
        was_nonce_reused = False
        for tx_hash in self.history[::-1]:
            self.context.logger.info(f"Checking hash {tx_hash}...")
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

            status = cast(int, contract_api_msg.state.body["status"])
            if status == -1:
                self.context.logger.info(f"Tx hash {tx_hash} has no receipt!")
                # this loop might take a long time
                # we do not want to starve the rest of the behaviour
                # we yield which freezes this loop here until the
                # AbstractRoundBehaviour it belongs to, sends a tick to it
                yield
                continue

            tx_data = cast(TxData, contract_api_msg.state.body["transaction"])
            revert_reason = yield from self._get_revert_reason(tx_data)

            if revert_reason is not None:
                if self._safe_nonce_reused(revert_reason):
                    self.context.logger.info(
                        f"The safe's nonce has been reused for {tx_hash}. "
                        f"{self.check_expected_to_be_verified} is expected to be verified!"
                    )
                    was_nonce_reused = True
                    # this loop might take a long time
                    # we do not want to starve the rest of the behaviour
                    # we yield which freezes this loop here until the
                    # AbstractRoundBehaviour it belongs to, sends a tick to it
                    yield
                    continue

                self.context.logger.warning(
                    f"Payload is invalid for {tx_hash}! Cannot continue. Received: {revert_reason}"
                )

            return VerificationStatus.INVALID_PAYLOAD, tx_hash

        if was_nonce_reused:
            self.context.logger.info(
                f"Safe nonce {safe_nonce} was used, but no valid transaction was found. "
                f"We cannot resend the transaction with the same nonce."
            )
            return VerificationStatus.BAD_SAFE_NONCE, None

        return VerificationStatus.NOT_VERIFIED, None

    def _get_revert_reason(self, tx: TxData) -> Generator[None, None, Optional[str]]:
        """Get the revert reason of the given transaction."""
        chain_id = self.synchronized_data.get_chain_id(self.params.default_chain_id)
        contract_api_msg = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_STATE,  # type: ignore
            contract_address=self.synchronized_data.safe_contract_address,
            contract_id=str(GnosisSafeContract.contract_id),
            contract_callable="revert_reason",
            tx=tx,
            chain_id=chain_id,
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

    matching_round = CheckLateTxHashesRound
    check_expected_to_be_verified = "One of the next tx checks"

    @property
    def history(self) -> List[str]:
        """Get the history of hashes."""
        return [
            hash_
            for hashes in self.synchronized_data.late_arriving_tx_hashes.values()
            for hash_ in hashes
        ]


class SynchronizeLateMessagesBehaviour(TransactionSettlementBaseBehaviour):
    """Synchronize late-arriving messages behaviour."""

    matching_round = SynchronizeLateMessagesRound

    def __init__(self, **kwargs: Any):
        """Initialize a `SynchronizeLateMessagesBehaviour`"""
        super().__init__(**kwargs)
        # if we timed out during finalization, but we managed to receive a tx hash,
        # then we sync it here by initializing the `_tx_hashes` with the unsynced hash.
        self._tx_hashes: str = self.params.mutable_params.tx_hash
        self._messages_iterator: Iterator[ContractApiMessage] = iter(
            self.params.mutable_params.late_messages
        )
        self.use_flashbots = False

    def setup(self) -> None:
        """Setup the `SynchronizeLateMessagesBehaviour`."""
        tx_params = skill_input_hex_to_payload(
            self.synchronized_data.most_voted_tx_hash
        )
        self.use_flashbots = tx_params["use_flashbots"]

    def async_act(self) -> Generator:
        """Do the action."""

        with self.context.benchmark_tool.measure(self.behaviour_id).local():
            current_message = next(self._messages_iterator, None)
            if current_message is not None:
                chain_id = self.synchronized_data.get_chain_id(
                    self.params.default_chain_id
                )
                tx_data = yield from self._get_tx_data(
                    current_message,
                    self.use_flashbots,
                    chain_id=chain_id,
                )
                self.context.logger.info(
                    f"Found a late arriving message {current_message}. Result data: {tx_data}"
                )
                # here, we concatenate the tx_hashes of all the late-arriving messages. Later, we will parse them.
                self._tx_hashes += cast(str, tx_data["tx_digest"])
                return

            payload = SynchronizeLateMessagesPayload(
                self.context.agent_address, self._tx_hashes
            )

        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            # reset the local parameters if we were able to send them.
            self.params.mutable_params.tx_hash = ""
            self.params.mutable_params.late_messages = []
            yield from self.wait_until_round_end()

        self.set_done()


class SignatureBehaviour(TransactionSettlementBaseBehaviour):
    """Signature behaviour."""

    matching_round = CollectSignatureRound

    def async_act(self) -> Generator:
        """
        Do the action.

        Steps:
        - Request the signature of the transaction hash.
        - Send the signature as a transaction and wait for it to be mined.
        - Wait until ABCI application transitions to the next round.
        - Go to the next behaviour (set done event).
        """

        with self.context.benchmark_tool.measure(self.behaviour_id).local():
            self.context.logger.info(
                f"Agreement reached on tx data: {self.synchronized_data.most_voted_tx_hash}"
            )
            signature_hex = yield from self._get_safe_tx_signature()
            payload = SignaturePayload(self.context.agent_address, signature_hex)

        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()

    def _get_safe_tx_signature(self) -> Generator[None, None, str]:
        """Get signature of safe transaction hash."""
        tx_params = skill_input_hex_to_payload(
            self.synchronized_data.most_voted_tx_hash
        )
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


class FinalizeBehaviour(TransactionSettlementBaseBehaviour):
    """Finalize behaviour."""

    matching_round = FinalizationRound

    def _i_am_not_sending(self) -> bool:
        """Indicates if the current agent is the sender or not."""
        return (
            self.context.agent_address
            != self.synchronized_data.most_voted_keeper_address
        )

    def async_act(self) -> Generator[None, None, None]:
        """
        Do the action.

        Steps:
        - If the agent is the keeper, then prepare the transaction and send it.
        - Otherwise, wait until the next round.
        - If a timeout is hit, set exit A event, otherwise set done event.
        """
        if self._i_am_not_sending():
            yield from self._not_sender_act()
        else:
            yield from self._sender_act()

    def _not_sender_act(self) -> Generator:
        """Do the non-sender action."""
        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            self.context.logger.info(
                f"Waiting for the keeper to do its keeping: {self.synchronized_data.most_voted_keeper_address}"
            )
            yield from self.wait_until_round_end()
        self.set_done()

    def _sender_act(self) -> Generator[None, None, None]:
        """Do the sender action."""

        with self.context.benchmark_tool.measure(self.behaviour_id).local():
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
            else:  # pragma: no cover
                self.context.logger.info(
                    f"Finalization tx digest: {cast(str, tx_data['tx_digest'])}"
                )
                self.context.logger.debug(
                    f"Signatures: {pprint.pformat(self.synchronized_data.participant_to_signature)}"
                )

            tx_hashes_history = self.synchronized_data.tx_hashes_history

            if tx_data["tx_digest"] != "":
                tx_hashes_history.append(cast(str, tx_data["tx_digest"]))

            tx_data_serialized = {
                "status_value": cast(VerificationStatus, tx_data["status"]).value,
                "serialized_keepers": self.serialized_keepers(
                    cast(Deque[str], tx_data["keepers"]),
                    cast(int, tx_data["keeper_retries"]),
                ),
                "blacklisted_keepers": "".join(
                    cast(Set[str], tx_data["blacklisted_keepers"])
                ),
                "tx_hashes_history": "".join(tx_hashes_history),
                "received_hash": bool(tx_data["tx_digest"]),
            }

            payload = FinalizationTxPayload(
                self.context.agent_address,
                cast(Dict[str, Union[str, int, bool]], tx_data_serialized),
            )

        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            # reset the local tx hash parameter if we were able to send it
            self.params.mutable_params.tx_hash = ""
            yield from self.wait_until_round_end()

        self.set_done()

    def _send_safe_transaction(
        self,
    ) -> Generator[None, None, TxDataType]:
        """Send a Safe transaction using the participants' signatures."""
        tx_params = skill_input_hex_to_payload(
            self.synchronized_data.most_voted_tx_hash
        )
        chain_id = self.synchronized_data.get_chain_id(self.params.default_chain_id)
        contract_api_msg = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
            contract_address=self.synchronized_data.safe_contract_address,
            contract_id=str(GnosisSafeContract.contract_id),
            contract_callable="get_raw_safe_transaction",
            sender_address=self.context.agent_address,
            owners=tuple(self.synchronized_data.participants),
            to_address=tx_params["to_address"],
            value=tx_params["ether_value"],
            data=tx_params["data"],
            safe_tx_gas=tx_params["safe_tx_gas"],
            signatures_by_owner={
                key: payload.signature
                for key, payload in self.synchronized_data.participant_to_signature.items()
            },
            nonce=self.params.mutable_params.nonce,
            old_price=self.params.mutable_params.gas_price,
            operation=tx_params["operation"],
            fallback_gas=self.params.mutable_params.fallback_gas,
            gas_price=self.params.gas_params.gas_price,
            max_fee_per_gas=self.params.gas_params.max_fee_per_gas,
            max_priority_fee_per_gas=self.params.gas_params.max_priority_fee_per_gas,
            chain_id=chain_id,
        )

        tx_data = yield from self._get_tx_data(
            contract_api_msg,
            tx_params["use_flashbots"],
            tx_params["gas_limit"],
            tx_params["raise_on_failed_simulation"],
            chain_id,
        )
        return tx_data

    def handle_late_messages(self, behaviour_id: str, message: Message) -> None:
        """Store a potentially late-arriving message locally.

        :param behaviour_id: the id of the behaviour in which the message belongs to.
        :param message: the late arriving message to handle.
        """
        if (
            isinstance(message, ContractApiMessage)
            and behaviour_id == self.behaviour_id
        ):
            self.context.logger.info(f"Late message arrived: {message}")
            self.params.mutable_params.late_messages.append(message)
        else:
            super().handle_late_messages(behaviour_id, message)


class ResetBehaviour(TransactionSettlementBaseBehaviour):
    """Reset behaviour."""

    matching_round = ResetRound

    def async_act(self) -> Generator:
        """Do the action."""
        self.context.logger.info(
            f"Period {self.synchronized_data.period_count} was not finished. Resetting!"
        )
        payload = ResetPayload(
            self.context.agent_address, self.synchronized_data.period_count
        )
        yield from self.send_a2a_transaction(payload)
        yield from self.wait_until_round_end()
        self.set_done()


class TransactionSettlementRoundBehaviour(AbstractRoundBehaviour):
    """This behaviour manages the consensus stages for the basic transaction settlement."""

    initial_behaviour_cls = RandomnessTransactionSubmissionBehaviour
    abci_app_cls = TransactionSubmissionAbciApp
    behaviours: Set[Type[BaseBehaviour]] = {
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
