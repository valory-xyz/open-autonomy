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
import json
from typing import Generator, Optional, Set, Type, cast

from packages.valory.contracts.gnosis_safe.contract import GnosisSafeContract
from packages.valory.contracts.offchain_aggregator.contract import (
    OffchainAggregatorContract,
)
from packages.valory.protocols.contract_api import ContractApiMessage
from packages.valory.skills.abstract_round_abci.behaviours import AbstractRoundBehaviour
from packages.valory.skills.abstract_round_abci.utils import BenchmarkTool
from packages.valory.skills.common_apps.behaviours import (
    CommonAppsBaseState,
    FinalizeBehaviour,
    RandomnessInOperationBehaviour,
    RegistrationBehaviour,
    RegistrationStartupBehaviour,
    SelectKeeperABehaviour,
    SelectKeeperBBehaviour,
    SignatureBehaviour,
    TendermintHealthcheckBehaviour,
    ValidateTransactionBehaviour,
)
from packages.valory.skills.common_apps.payloads import (
    EstimatePayload,
    ObservationPayload,
    ResetPayload,
    TransactionHashPayload,
)
from packages.valory.skills.common_apps.rounds import ResetAndPauseRound, ResetRound
from packages.valory.skills.common_apps.tools import payload_to_hex, to_int
from packages.valory.skills.oracle_deployment_abci.behaviours import (
    DeployOracleBehaviour,
    RandomnessOracleBehaviour,
    SelectKeeperOracleBehaviour,
    ValidateOracleBehaviour,
)
from packages.valory.skills.price_estimation_abci.rounds import (
    CollectObservationRound,
    EstimateConsensusRound,
    PriceEstimationAbciApp,
    TxHashRound,
)
from packages.valory.skills.safe_deployment_abci.behaviours import (
    DeploySafeBehaviour,
    RandomnessSafeBehaviour,
    SelectKeeperSafeBehaviour,
    ValidateSafeBehaviour,
)


benchmark_tool = BenchmarkTool()


SAFE_TX_GAS = 4000000  # TOFIX
ETHER_VALUE = 0  # TOFIX


class ObserveBehaviour(CommonAppsBaseState):
    """Observe price estimate."""

    state_id = "observe"
    matching_round = CollectObservationRound

    def async_act(self) -> Generator:
        """
        Do the action.

        Steps:
        - Ask the configured API the price of a currency.
        - If the request fails, retry until max retries are exceeded.
        - Send an observation transaction and wait for it to be mined.
        - Wait until ABCI application transitions to the next round.
        - Go to the next behaviour state (set done event).
        """
        if self.context.price_api.is_retries_exceeded():
            # now we need to wait and see if the other agents progress the round, otherwise we should restart?
            with benchmark_tool.measure(
                self,
            ).consensus():
                yield from self.wait_until_round_end()
            self.set_done()
            return

        with benchmark_tool.measure(
            self,
        ).local():
            api_specs = self.context.price_api.get_spec()
            response = yield from self.get_http_response(
                method=api_specs["method"],
                url=api_specs["url"],
                headers=api_specs["headers"],
                parameters=api_specs["parameters"],
            )
            observation = self.context.price_api.process_response(response)

        if observation:
            self.context.logger.info(
                f"Got observation of {self.context.price_api.currency_id} price in "
                + f"{self.context.price_api.convert_id} from {self.context.price_api.api_id}: "
                + f"{observation}"
            )
            payload = ObservationPayload(self.context.agent_address, observation)
            with benchmark_tool.measure(
                self,
            ).consensus():
                yield from self.send_a2a_transaction(payload)
                yield from self.wait_until_round_end()
            self.set_done()
        else:
            self.context.logger.info(
                f"Could not get price from {self.context.price_api.api_id}"
            )
            yield from self.sleep(self.params.sleep_time)
            self.context.price_api.increment_retries()

    def clean_up(self) -> None:
        """
        Clean up the resources due to a 'stop' event.

        It can be optionally implemented by the concrete classes.
        """
        self.context.price_api.reset_retries()


class EstimateBehaviour(CommonAppsBaseState):
    """Estimate price."""

    state_id = "estimate"
    matching_round = EstimateConsensusRound

    def async_act(self) -> Generator:
        """
        Do the action.

        Steps:
        - Run the script to compute the estimate starting from the shared observations.
        - Build an estimate transaction and send the transaction and wait for it to be mined.
        - Wait until ABCI application transitions to the next round.
        - Go to the next behaviour state (set done event).
        """

        with benchmark_tool.measure(
            self,
        ).local():
            self.context.logger.info(
                "Got estimate of %s price in %s: %s",
                self.context.price_api.currency_id,
                self.context.price_api.convert_id,
                self.period_state.estimate,
            )
            payload = EstimatePayload(
                self.context.agent_address, self.period_state.estimate
            )

        with benchmark_tool.measure(
            self,
        ).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class TransactionHashBehaviour(CommonAppsBaseState):
    """Share the transaction hash for the signature round."""

    state_id = "tx_hash"
    matching_round = TxHashRound

    def async_act(self) -> Generator:
        """
        Do the action.

        Steps:
        - Request the transaction hash for the safe transaction. This is the hash that needs to be signed by a threshold of agents.
        - Send the transaction hash as a transaction and wait for it to be mined.
        - Wait until ABCI application transitions to the next round.
        - Go to the next behaviour state (set done event).
        """

        with benchmark_tool.measure(
            self,
        ).local():
            payload_string = yield from self._get_safe_tx_hash()
            payload = TransactionHashPayload(self.context.agent_address, payload_string)

        with benchmark_tool.measure(
            self,
        ).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()

    def _get_safe_tx_hash(self) -> Generator[None, None, Optional[str]]:
        """Get the transaction hash of the Safe tx."""
        contract_api_msg = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
            contract_address=self.period_state.oracle_contract_address,
            contract_id=str(OffchainAggregatorContract.contract_id),
            contract_callable="get_latest_transmission_details",
        )
        if (
            contract_api_msg.performative
            != ContractApiMessage.Performative.RAW_TRANSACTION
        ):  # pragma: nocover
            self.context.logger.warning("get_latest_transmission_details unsuccessful!")
            return None
        epoch_ = cast(int, contract_api_msg.raw_transaction.body["epoch_"]) + 1
        round_ = cast(int, contract_api_msg.raw_transaction.body["round_"])
        decimals = self.params.oracle_params["decimals"]
        amount = self.period_state.most_voted_estimate
        amount_ = to_int(amount, decimals)
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
            contract_callable="get_raw_safe_transaction_hash",
            to_address=self.period_state.oracle_contract_address,
            value=ETHER_VALUE,
            data=data,
            safe_tx_gas=SAFE_TX_GAS,
        )
        if (
            contract_api_msg.performative
            != ContractApiMessage.Performative.RAW_TRANSACTION
        ):  # pragma: nocover
            self.context.logger.warning("get_raw_safe_transaction_hash unsuccessful!")
            return None
        safe_tx_hash = cast(str, contract_api_msg.raw_transaction.body["tx_hash"])
        safe_tx_hash = safe_tx_hash[2:]
        self.context.logger.info(f"Hash of the Safe transaction: {safe_tx_hash}")
        # temp hack:
        payload_string = payload_to_hex(safe_tx_hash, epoch_, round_, amount_)
        return payload_string


class BaseResetBehaviour(CommonAppsBaseState):
    """Reset state."""

    pause = True

    _check_started: Optional[datetime.datetime] = None
    _timeout: float
    _is_healthy: bool = False

    def start_reset(self) -> None:
        """Start tendermint reset."""
        if self._check_started is None and not self._is_healthy:
            self._check_started = datetime.datetime.now()
            self._timeout = self.params.max_healthcheck
            self._is_healthy = False

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
            self.period_state.period_count + 1
        ) % self.context.params.reset_tendermint_after == 0:
            self.start_reset()
            if self._is_timeout_expired():
                raise RuntimeError("Error resetting tendermint node.")

            if not self._is_healthy:
                self.context.logger.info("Resetting tendermint node.")
                request_message, http_dialogue = self._build_http_request_message(
                    "GET",
                    self.context.params.tendermint_com_url + "/hard_reset",
                )
                result = yield from self._do_request(request_message, http_dialogue)
                try:
                    response = json.loads(result.body.decode())
                    if response.get("status"):
                        self.context.logger.info(response.get("message"))
                        self.context.state.period.reset_blockchain()
                        self.end_reset()
                    else:
                        self.context.logger.error(response.get("message"))
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

            remote_height = int(json_body["result"]["sync_info"]["latest_block_height"])
            local_height = self.context.state.period.height
            self.context.logger.info(
                "local-height = %s, remote-height=%s", local_height, remote_height
            )
            if local_height != remote_height:
                self.context.logger.info("local height != remote height; retrying...")
                yield from self.sleep(self.params.sleep_time)
                return  # pragma: nocover

        if self.pause:
            if (
                self.period_state.is_most_voted_estimate_set
                and self.period_state.is_final_tx_hash_set
            ):
                self.context.logger.info(
                    f"Finalized estimate: {self.period_state.most_voted_estimate} with transaction hash: {self.period_state.final_tx_hash}"
                )
            else:
                self.context.logger.info("Finalized estimate not available.")
            self.context.logger.info("Period end.")
            benchmark_tool.save()
            yield from self.wait_from_last_timestamp(self.params.observation_interval)
        else:
            self.context.logger.info(
                f"Period {self.period_state.period_count} was not finished. Resetting!"
            )

        self.end_reset()
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


class PriceEstimationConsensusBehaviour(AbstractRoundBehaviour):
    """This behaviour manages the consensus stages for the price estimation."""

    initial_state_cls = TendermintHealthcheckBehaviour
    abci_app_cls = PriceEstimationAbciApp  # type: ignore
    behaviour_states: Set[Type[CommonAppsBaseState]] = {  # type: ignore
        TendermintHealthcheckBehaviour,  # type: ignore
        RegistrationBehaviour,  # type: ignore
        RegistrationStartupBehaviour,  # type: ignore
        RandomnessSafeBehaviour,  # type: ignore
        RandomnessOracleBehaviour,  # type: ignore
        SelectKeeperSafeBehaviour,  # type: ignore
        DeploySafeBehaviour,  # type: ignore
        ValidateSafeBehaviour,  # type: ignore
        SelectKeeperOracleBehaviour,  # type: ignore
        DeployOracleBehaviour,  # type: ignore
        ValidateOracleBehaviour,  # type: ignore
        RandomnessInOperationBehaviour,  # type: ignore
        SelectKeeperABehaviour,  # type: ignore
        ObserveBehaviour,  # type: ignore
        EstimateBehaviour,  # type: ignore
        TransactionHashBehaviour,  # type: ignore
        SignatureBehaviour,  # type: ignore
        FinalizeBehaviour,  # type: ignore
        ValidateTransactionBehaviour,  # type: ignore
        SelectKeeperBBehaviour,  # type: ignore
        ResetBehaviour,  # type: ignore
        ResetAndPauseBehaviour,  # type: ignore
    }

    def setup(self) -> None:
        """Set up the behaviour."""
        super().setup()
        benchmark_tool.logger = self.context.logger
