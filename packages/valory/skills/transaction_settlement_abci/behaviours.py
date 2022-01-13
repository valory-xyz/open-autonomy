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
import datetime
import json
import pprint
from abc import ABC
from typing import Dict, Generator, Optional, Tuple, Union, cast

from aea_ledger_ethereum import EthereumApi

from packages.valory.contracts.gnosis_safe.contract import GnosisSafeContract
from packages.valory.protocols.contract_api.message import ContractApiMessage
from packages.valory.skills.abstract_round_abci.behaviours import BaseState
from packages.valory.skills.abstract_round_abci.common import (
    RandomnessBehaviour,
    SelectKeeperBehaviour,
)
from packages.valory.skills.abstract_round_abci.utils import BenchmarkTool, VerifyDrand
from packages.valory.skills.transaction_settlement_abci.payloads import (
    FinalizationTxPayload,
    RandomnessPayload,
    ResetPayload,
    SelectKeeperPayload,
    SignaturePayload,
    ValidatePayload,
)
from packages.valory.skills.transaction_settlement_abci.rounds import (
    CollectSignatureRound,
    FinalizationRound,
    PeriodState,
    RandomnessTransactionSubmissionRound,
    ResetAndPauseRound,
    ResetRound,
    SelectKeeperTransactionSubmissionRoundA,
    SelectKeeperTransactionSubmissionRoundB,
    ValidateTransactionRound,
)


benchmark_tool = BenchmarkTool()
drand_check = VerifyDrand()


def hex_to_payload(payload: str) -> Tuple[str, int, int, str, bytes]:
    """Decode payload."""
    if len(payload) < 234:
        raise ValueError("cannot decode provided payload")  # pragma: nocover
    tx_hash = payload[:64]
    ether_value = int.from_bytes(bytes.fromhex(payload[64:128]), "big")
    safe_tx_gas = int.from_bytes(bytes.fromhex(payload[128:192]), "big")
    to_address = payload[192:234]
    data = bytes.fromhex(payload[234:])
    return (tx_hash, ether_value, safe_tx_gas, to_address, data)


class TransactionSettlementBaseState(BaseState, ABC):
    """Base state behaviour for the common apps' skill."""

    @property
    def period_state(self) -> PeriodState:
        """Return the period state."""
        return cast(PeriodState, super().period_state)


class RandomnessTransactionSubmissionBehaviour(RandomnessBehaviour):
    """Retrieve randomness."""

    state_id = "randomness_transaction_submission"
    matching_round = RandomnessTransactionSubmissionRound
    payload_class = RandomnessPayload


class SelectKeeperTransactionSubmissionBehaviourA(SelectKeeperBehaviour):
    """Select the keeper agent."""

    state_id = "select_keeper_transaction_submission_a"
    matching_round = SelectKeeperTransactionSubmissionRoundA
    payload_class = SelectKeeperPayload


class SelectKeeperTransactionSubmissionBehaviourB(SelectKeeperBehaviour):
    """Select the keeper agent."""

    state_id = "select_keeper_transaction_submission_b"
    matching_round = SelectKeeperTransactionSubmissionRoundB
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
        """Transaction verification."""
        response = yield from self.get_transaction_receipt(
            self.period_state.final_tx_hash,
            self.params.retry_timeout,
            self.params.retry_attempts,
        )
        if response is None:  # pragma: nocover
            self.context.logger.error(
                f"tx {self.period_state.final_tx_hash} receipt check timed out!"
            )
            return None
        is_settled = EthereumApi.is_transaction_settled(response)
        if not is_settled:  # pragma: nocover
            self.context.logger.info(
                f"tx {self.period_state.final_tx_hash} not settled!"
            )
            return False
        _, ether_value, safe_tx_gas, to_address, data = hex_to_payload(
            self.period_state.most_voted_tx_hash
        )
        contract_api_msg = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_STATE,  # type: ignore
            contract_address=self.period_state.safe_contract_address,
            contract_id=str(GnosisSafeContract.contract_id),
            contract_callable="verify_tx",
            tx_hash=self.period_state.final_tx_hash,
            owners=tuple(self.period_state.participants),
            to_address=to_address,
            value=ether_value,
            data=data,
            safe_tx_gas=safe_tx_gas,
            signatures_by_owner={
                key: payload.signature
                for key, payload in self.period_state.participant_to_signature.items()
            },
        )
        if (
            contract_api_msg.performative != ContractApiMessage.Performative.STATE
        ):  # pragma: nocover
            self.context.logger.error(
                f"get_transmit_data unsuccessful! Received: {contract_api_msg}"
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

        with benchmark_tool.measure(
            self,
        ).local():
            self.context.logger.info(
                f"Consensus reached on tx hash: {self.period_state.most_voted_tx_hash}"
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
        """Get signature of safe transaction hash."""
        safe_tx_hash, _, _, _, _ = hex_to_payload(self.period_state.most_voted_tx_hash)
        # is_deprecated_mode=True because we want to call Account.signHash,
        # which is the same used by gnosis-py
        safe_tx_hash_bytes = binascii.unhexlify(safe_tx_hash)
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
                "I am the designated sender, attempting to send the safe transaction..."
            )
            tx_data = yield from self._send_safe_transaction()
            if tx_data is None or tx_data["tx_digest"] is None:
                # if we enter here, then the event.FAILED will be raised from the round, and we will select a new keeper
                self.context.logger.error(  # pragma: nocover
                    "Did not succeed with finalising the transaction!"
                )
            else:
                self.context.logger.info(
                    f"Finalization tx digest: {cast(Dict[str, Union[str, int]], tx_data['tx_digest'])}"
                )
                self.context.logger.debug(
                    f"Signatures: {pprint.pformat(self.period_state.participant_to_signature)}"
                )
            payload = FinalizationTxPayload(self.context.agent_address, tx_data)

        with benchmark_tool.measure(
            self,
        ).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()

    def _send_safe_transaction(
        self,
    ) -> Generator[None, None, Optional[Dict[str, Union[None, str, int]]]]:
        """Send a Safe transaction using the participants' signatures."""
        _, ether_value, safe_tx_gas, to_address, data = hex_to_payload(
            self.period_state.most_voted_tx_hash
        )

        gas_data = self._adjust_gas_data()

        contract_api_msg = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
            contract_address=self.period_state.safe_contract_address,
            contract_id=str(GnosisSafeContract.contract_id),
            contract_callable="get_raw_safe_transaction",
            sender_address=self.context.agent_address,
            owners=tuple(self.period_state.participants),
            to_address=to_address,
            value=ether_value,
            data=data,
            safe_tx_gas=safe_tx_gas,
            signatures_by_owner={
                key: payload.signature
                for key, payload in self.period_state.participant_to_signature.items()
            },
            nonce=self.period_state.nonce,
            max_fee_per_gas=gas_data["max_fee_per_gas"],
            max_priority_fee_per_gas=gas_data["max_priority_fee_per_gas"],
        )
        if (
            contract_api_msg.performative
            != ContractApiMessage.Performative.RAW_TRANSACTION
        ):  # pragma: nocover
            self.context.logger.warning("get_raw_safe_transaction unsuccessful!")
            return None
        tx_digest = yield from self.send_raw_transaction(
            contract_api_msg.raw_transaction
        )

        tx_data = {
            "tx_digest": tx_digest,
            "nonce": int(cast(str, contract_api_msg.raw_transaction.body["nonce"])),
            "max_fee_per_gas": int(
                cast(str, contract_api_msg.raw_transaction.body["maxFeePerGas"])
            ),
            "max_priority_fee_per_gas": int(
                cast(
                    str,
                    contract_api_msg.raw_transaction.body["maxPriorityFeePerGas"],
                )
            ),
        }

        return tx_data

    def _adjust_gas_data(self) -> Dict[str, int]:
        """Get the gas data and adjust properly if re-submitting."""
        # Get the gas data.
        gas_data = {
            "max_fee_per_gas": cast(int, self.period_state.gas_data["max_fee_per_gas"]),
            "max_priority_fee_per_gas": cast(
                int, self.period_state.gas_data["max_priority_fee_per_gas"]
            ),
        }

        # Recalculate the fees to use.
        if self.period_state.is_resubmitting:
            gas_data = EthereumApi.update_gas_pricing(gas_data)

        return gas_data


class BaseResetBehaviour(TransactionSettlementBaseState):
    """Reset state."""

    pause = True

    _check_started: Optional[datetime.datetime] = None
    _timeout: float
    _is_healthy: bool = False

    def start_reset(self) -> Generator:
        """Start tendermint reset."""
        if self._check_started is None and not self._is_healthy:
            # we do the reset in the middle of the pause as there are no immediate transactions on either side of the reset
            yield from self.wait_from_last_timestamp(
                self.params.observation_interval / 2
            )
            self._check_started = datetime.datetime.now()
            self._timeout = self.params.max_healthcheck
            self._is_healthy = False
        yield

    def end_reset(
        self,
    ) -> None:
        """End tendermint reset."""
        self._check_started = None
        self._timeout = -1.0
        self._is_healthy = True

    def _is_timeout_expired(self) -> bool:
        """Check if the timeout expired."""
        if self._check_started is None or self._is_healthy:
            return False  # pragma: no cover
        return datetime.datetime.now() > self._check_started + datetime.timedelta(
            0, self._timeout
        )

    def async_act(self) -> Generator:
        """
        Do the action.

        Steps:
        - Trivially log the state.
        - Sleep for configured interval.
        - Build a registration transaction.
        - Send the transaction and wait for it to be mined.
        - Wait until ABCI application transitions to the next round.
        - Go to the next behaviour state (set done event).
        """
        if (
            self.pause
            and self.period_state.is_most_voted_estimate_set
            and self.period_state.is_final_tx_hash_set
        ):
            if (
                self.period_state.period_count != 0
                and self.period_state.period_count
                % self.context.params.reset_tendermint_after
                == 0
            ):
                yield from self.start_reset()
                if self._is_timeout_expired():
                    # if the Tendermint node cannot update the app then the app cannot work
                    raise RuntimeError(  # pragma: no cover
                        "Error resetting tendermint node."
                    )

                if not self._is_healthy:
                    self.context.logger.info(
                        f"Resetting tendermint node at end of period={self.period_state.period_count}."
                    )
                    request_message, http_dialogue = self._build_http_request_message(
                        "GET",
                        self.context.params.tendermint_com_url + "/hard_reset",
                    )
                    result = yield from self._do_request(request_message, http_dialogue)
                    try:
                        response = json.loads(result.body.decode())
                        if response.get("status"):
                            self.context.logger.info(response.get("message"))
                            self.context.logger.info(
                                "Resetting tendermint node successful! Resetting local blockchain."
                            )
                            self.context.state.period.reset_blockchain()
                            self.end_reset()
                        else:
                            msg = response.get("message")
                            self.context.logger.error(f"Error resetting: {msg}")
                            yield from self.sleep(self.params.sleep_time)
                            return  # pragma: no cover
                    except json.JSONDecodeError:
                        self.context.logger.error(
                            "Error communicating with tendermint com server."
                        )
                        yield from self.sleep(self.params.sleep_time)
                        return  # pragma: no cover

                status = yield from self._get_status()
                try:
                    json_body = json.loads(status.body.decode())
                except json.JSONDecodeError:
                    self.context.logger.error(
                        "Tendermint not accepting transactions yet, trying again!"
                    )
                    yield from self.sleep(self.params.sleep_time)
                    return  # pragma: nocover

                remote_height = int(
                    json_body["result"]["sync_info"]["latest_block_height"]
                )
                local_height = self.context.state.period.height
                self.context.logger.info(
                    "local-height = %s, remote-height=%s", local_height, remote_height
                )
                if local_height != remote_height:
                    self.context.logger.info(
                        "local height != remote height; retrying..."
                    )
                    yield from self.sleep(self.params.sleep_time)
                    return  # pragma: nocover

                self.context.logger.info(
                    "local height == remote height; continuing execution..."
                )
            yield from self.wait_from_last_timestamp(
                self.params.observation_interval / 2
            )
            self.context.logger.info(
                f"Finalized estimate: {self.period_state.most_voted_estimate} with transaction hash: {self.period_state.final_tx_hash}"
            )
            self.context.logger.info("Period end.")
            benchmark_tool.save()
        else:
            self.context.logger.info(
                f"Period {self.period_state.period_count} was not finished. Resetting!"
            )

        payload = ResetPayload(
            self.context.agent_address, self.period_state.period_count + 1
        )
        yield from self.send_a2a_transaction(payload)
        yield from self.wait_until_round_end()
        self.set_done()


class ResetBehaviour(BaseResetBehaviour):
    """Reset state."""

    matching_round = ResetRound
    state_id = "reset"
    pause = False


class ResetAndPauseBehaviour(BaseResetBehaviour):
    """Reset and pause state."""

    matching_round = ResetAndPauseRound
    state_id = "reset_and_pause"
    pause = True
