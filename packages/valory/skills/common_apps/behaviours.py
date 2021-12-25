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
import json
import pprint
from abc import ABC
from typing import Generator, Optional, cast

from aea_ledger_ethereum import EthereumApi

from packages.valory.contracts.gnosis_safe.contract import GnosisSafeContract
from packages.valory.contracts.offchain_aggregator.contract import (
    OffchainAggregatorContract,
)
from packages.valory.protocols.contract_api.message import ContractApiMessage
from packages.valory.skills.abstract_round_abci.behaviours import BaseState
from packages.valory.skills.abstract_round_abci.models import (
    SharedState as BaseSharedState,
)
from packages.valory.skills.abstract_round_abci.utils import BenchmarkTool, VerifyDrand
from packages.valory.skills.common_apps.models import Params
from packages.valory.skills.common_apps.payloads import (
    FinalizationTxPayload,
    RandomnessPayload,
    RegistrationPayload,
    ResetPayload,
    SelectKeeperPayload,
    SignaturePayload,
    ValidatePayload,
)
from packages.valory.skills.common_apps.rounds import (
    CollectSignatureRound,
    FinalizationRound,
    PeriodState,
    RandomnessTransactionSubmissionRound,
    RegistrationRound,
    RegistrationStartupRound,
    ResetAndPauseRound,
    ResetRound,
    SelectKeeperTransactionSubmissionRoundA,
    SelectKeeperTransactionSubmissionRoundB,
    ValidateTransactionRound,
)
from packages.valory.skills.common_apps.tools import hex_to_payload, random_selection


SAFE_TX_GAS = 4000000  # TOFIX
ETHER_VALUE = 0  # TOFIX

benchmark_tool = BenchmarkTool()
drand_check = VerifyDrand()


class CommonAppsBaseState(BaseState, ABC):
    """Base state behaviour for the common apps skill."""

    @property
    def period_state(self) -> PeriodState:
        """Return the period state."""
        return cast(PeriodState, cast(BaseSharedState, self.context.state).period_state)

    @property
    def params(self) -> Params:
        """Return the params."""
        return cast(Params, self.context.params)


class TendermintHealthcheckBehaviour(CommonAppsBaseState):
    """Check whether Tendermint nodes are running."""

    state_id = "tendermint_healthcheck"
    matching_round = None

    _check_started: Optional[datetime.datetime] = None
    _timeout: float
    _is_healthy: bool

    def start(self) -> None:
        """Set up the behaviour."""
        if self._check_started is None:
            self._check_started = datetime.datetime.now()
            self._timeout = self.params.max_healthcheck
            self._is_healthy = False

    def _is_timeout_expired(self) -> bool:
        """Check if the timeout expired."""
        if self._check_started is None or self._is_healthy:
            return False  # pragma: no cover
        return datetime.datetime.now() > self._check_started + datetime.timedelta(
            0, self._timeout
        )

    def async_act(self) -> Generator:
        """Do the action."""

        self.start()
        if self._is_timeout_expired():
            # if the Tendermint node cannot update the app then the app cannot work
            raise RuntimeError("Tendermint node did not come live!")
        if not self._is_healthy:
            health = yield from self._get_health()
            try:
                json_body = json.loads(health.body.decode())
            except json.JSONDecodeError:
                self.context.logger.error("Tendermint not running yet, trying again!")
                yield from self.sleep(self.params.sleep_time)
                return
            self._is_healthy = True
        status = yield from self._get_status()
        try:
            json_body = json.loads(status.body.decode())
        except json.JSONDecodeError:
            self.context.logger.error(
                "Tendermint not accepting transactions yet, trying again!"
            )
            yield from self.sleep(self.params.sleep_time)
            return

        remote_height = int(json_body["result"]["sync_info"]["latest_block_height"])
        local_height = self.context.state.period.height
        self.context.logger.info(
            "local-height = %s, remote-height=%s", local_height, remote_height
        )
        if local_height != remote_height:
            self.context.logger.info("local height != remote height; retrying...")
            yield from self.sleep(self.params.sleep_time)
            return
        self.context.logger.info("local height == remote height; done")
        self.set_done()


class RegistrationBaseBehaviour(CommonAppsBaseState):
    """Register to the next periods."""

    def async_act(self) -> Generator:
        """
        Do the action.

        Steps:
        - Build a registration transaction.
        - Send the transaction and wait for it to be mined.
        - Wait until ABCI application transitions to the next round.
        - Go to the next behaviour state (set done event).
        """

        with benchmark_tool.measure(
            self,
        ).local():
            payload = RegistrationPayload(self.context.agent_address)

        with benchmark_tool.measure(
            self,
        ).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class RegistrationStartupBehaviour(RegistrationBaseBehaviour):
    """Register to the next periods."""

    state_id = "registration_startup"
    matching_round = RegistrationStartupRound


class RegistrationBehaviour(RegistrationBaseBehaviour):
    """Register to the next periods."""

    state_id = "registration"
    matching_round = RegistrationRound


class RandomnessBehaviour(CommonAppsBaseState):
    """Check whether Tendermint nodes are running."""

    def async_act(self) -> Generator:
        """
        Check whether tendermint is running or not.

        Steps:
        - Do a http request to the tendermint health check endpoint
        - Retry until healthcheck passes or timeout is hit.
        - If healthcheck passes set done event.
        """
        if self.context.randomness_api.is_retries_exceeded():
            # now we need to wait and see if the other agents progress the round
            with benchmark_tool.measure(
                self,
            ).consensus():
                yield from self.wait_until_round_end()
            self.set_done()
            return

        with benchmark_tool.measure(
            self,
        ).local():
            api_specs = self.context.randomness_api.get_spec()
            response = yield from self.get_http_response(
                method=api_specs["method"],
                url=api_specs["url"],
            )
            observation = self.context.randomness_api.process_response(response)

        if observation:
            self.context.logger.info(f"Retrieved DRAND values: {observation}.")
            self.context.logger.info("Verifying DRAND values.")
            check, error = drand_check.verify(observation, self.params.drand_public_key)
            if check:
                self.context.logger.info("DRAND check successful.")
            else:
                self.context.logger.info(f"DRAND check failed, {error}.")
                observation["randomness"] = ""
                observation["round"] = ""

            payload = RandomnessPayload(
                self.context.agent_address,
                observation["round"],
                observation["randomness"],
            )
            with benchmark_tool.measure(
                self,
            ).consensus():
                yield from self.send_a2a_transaction(payload)
                yield from self.wait_until_round_end()

            self.set_done()
        else:
            self.context.logger.error(
                f"Could not get randomness from {self.context.randomness_api.api_id}"
            )
            yield from self.sleep(self.params.sleep_time)
            self.context.randomness_api.increment_retries()

    def clean_up(self) -> None:
        """
        Clean up the resources due to a 'stop' event.

        It can be optionally implemented by the concrete classes.
        """
        self.context.randomness_api.reset_retries()


class RandomnessTransactionSubmissionBehaviour(RandomnessBehaviour):
    """Retrieve randomness."""

    state_id = "randomness_transaction_submission"
    matching_round = RandomnessTransactionSubmissionRound


class SelectKeeperBehaviour(CommonAppsBaseState, ABC):
    """Select the keeper agent."""

    def async_act(self) -> Generator:
        """
        Do the action.

        Steps:
        - Select a keeper randomly.
        - Send the transaction with the keeper and wait for it to be mined.
        - Wait until ABCI application transitions to the next round.
        - Go to the next behaviour state (set done event).
        """

        with benchmark_tool.measure(
            self,
        ).local():
            if (
                self.period_state.is_keeper_set
                and len(self.period_state.participants) > 1
            ):
                # if a keeper is already set we remove it from the potential selection.
                potential_keepers = list(self.period_state.participants)
                potential_keepers.remove(self.period_state.most_voted_keeper_address)
                relevant_set = sorted(potential_keepers)
            else:
                relevant_set = sorted(self.period_state.participants)
            keeper_address = random_selection(
                relevant_set,
                self.period_state.keeper_randomness,
            )

            self.context.logger.info(f"Selected a new keeper: {keeper_address}.")
            payload = SelectKeeperPayload(self.context.agent_address, keeper_address)

        with benchmark_tool.measure(
            self,
        ).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class SelectKeeperTransactionSubmissionBehaviourA(SelectKeeperBehaviour):
    """Select the keeper agent."""

    state_id = "select_keeper_transaction_submission_a"
    matching_round = SelectKeeperTransactionSubmissionRoundA


class SelectKeeperTransactionSubmissionBehaviourB(SelectKeeperBehaviour):
    """Select the keeper agent."""

    state_id = "select_keeper_transaction_submission_b"
    matching_round = SelectKeeperTransactionSubmissionRoundB


class ValidateTransactionBehaviour(CommonAppsBaseState):
    """ValidateTransaction."""

    state_id = "validate_transaction"
    matching_round = ValidateTransactionRound

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
        _, epoch_, round_, amount_ = hex_to_payload(
            self.period_state.most_voted_tx_hash
        )
        contract_api_msg = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
            contract_address=self.period_state.oracle_contract_address,
            contract_id=str(OffchainAggregatorContract.contract_id),
            contract_callable="get_transmit_data",
            epoch_=epoch_,
            round_=round_,
            amount_=amount_,
        )
        if (
            contract_api_msg.performative
            != ContractApiMessage.Performative.RAW_TRANSACTION
        ):  # pragma: nocover
            self.context.logger.error(
                f"get_transmit_data unsuccessful! Received: {contract_api_msg}"
            )
            return False
        data = contract_api_msg.raw_transaction.body["data"]
        contract_api_msg = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_STATE,  # type: ignore
            contract_address=self.period_state.safe_contract_address,
            contract_id=str(GnosisSafeContract.contract_id),
            contract_callable="verify_tx",
            tx_hash=self.period_state.final_tx_hash,
            owners=tuple(self.period_state.participants),
            to_address=self.period_state.oracle_contract_address,
            value=ETHER_VALUE,
            data=data,
            safe_tx_gas=SAFE_TX_GAS,
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


class SignatureBehaviour(CommonAppsBaseState):
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
        # is_deprecated_mode=True because we want to call Account.signHash,
        # which is the same used by gnosis-py
        safe_tx_hash_bytes = binascii.unhexlify(
            self.period_state.most_voted_tx_hash[:64]
        )
        signature_hex = yield from self.get_signature(
            safe_tx_hash_bytes, is_deprecated_mode=True
        )
        # remove the leading '0x'
        signature_hex = signature_hex[2:]
        self.context.logger.info(f"Signature: {signature_hex}")
        return signature_hex


class FinalizeBehaviour(CommonAppsBaseState):
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
            tx_digest = yield from self._send_safe_transaction()
            if tx_digest is None:
                self.context.logger.error(  # pragma: nocover
                    "Did not succeed with finalising the transaction!"
                )
            else:
                self.context.logger.info(f"Finalization tx digest: {tx_digest}")
                self.context.logger.debug(
                    f"Signatures: {pprint.pformat(self.period_state.participant_to_signature)}"
                )
            payload = FinalizationTxPayload(self.context.agent_address, tx_digest)

        with benchmark_tool.measure(
            self,
        ).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()

    def _send_safe_transaction(self) -> Generator[None, None, Optional[str]]:
        """Send a Safe transaction using the participants' signatures."""
        _, epoch_, round_, amount_ = hex_to_payload(
            self.period_state.most_voted_tx_hash
        )
        contract_api_msg = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
            contract_address=self.period_state.oracle_contract_address,
            contract_id=str(OffchainAggregatorContract.contract_id),
            contract_callable="get_transmit_data",
            epoch_=epoch_,
            round_=round_,
            amount_=amount_,
        )
        if (
            contract_api_msg.performative
            != ContractApiMessage.Performative.RAW_TRANSACTION
        ):  # pragma: nocover
            self.context.logger.warning("get_transmit_data unsuccessful!")
            return None
        data = contract_api_msg.raw_transaction.body["data"]
        contract_api_msg = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
            contract_address=self.period_state.safe_contract_address,
            contract_id=str(GnosisSafeContract.contract_id),
            contract_callable="get_raw_safe_transaction",
            sender_address=self.context.agent_address,
            owners=tuple(self.period_state.participants),
            to_address=self.period_state.oracle_contract_address,
            value=ETHER_VALUE,
            data=data,
            safe_tx_gas=SAFE_TX_GAS,
            signatures_by_owner={
                key: payload.signature
                for key, payload in self.period_state.participant_to_signature.items()
            },
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
        return tx_digest


class BaseResetBehaviour(CommonAppsBaseState):
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
                    raise RuntimeError("Error resetting tendermint node.")

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
                            return
                    except json.JSONDecodeError:
                        self.context.logger.error(
                            "Error communicating with tendermint com server."
                        )
                        yield from self.sleep(self.params.sleep_time)
                        return

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
    """Reset state."""

    matching_round = ResetAndPauseRound
    state_id = "reset_and_pause"
    pause = True
