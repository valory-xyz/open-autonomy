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
import json
from abc import ABC
from decimal import Decimal
from typing import Dict, Generator, Optional, Sequence, Set, Type, cast

from aea.exceptions import enforce

from packages.valory.contracts.gnosis_safe.contract import GnosisSafeContract
from packages.valory.contracts.offchain_aggregator.contract import (
    OffchainAggregatorContract,
)
from packages.valory.protocols.contract_api import ContractApiMessage
from packages.valory.skills.abstract_round_abci.behaviours import (
    AbstractRoundBehaviour,
    BaseState,
)
from packages.valory.skills.oracle_deployment_abci.behaviours import (
    OracleDeploymentRoundBehaviour,
)
from packages.valory.skills.price_estimation_abci.composition import (
    PriceEstimationAbciApp,
)
from packages.valory.skills.price_estimation_abci.models import Params
from packages.valory.skills.price_estimation_abci.payloads import (
    EstimatePayload,
    ObservationPayload,
    TransactionHashPayload,
)
from packages.valory.skills.price_estimation_abci.rounds import (
    CollectObservationRound,
    EstimateConsensusRound,
    PeriodState,
    PriceAggregationAbciApp,
    TxHashRound,
)
from packages.valory.skills.registration_abci.behaviours import (
    AgentRegistrationRoundBehaviour,
    RegistrationStartupBehaviour,
)
from packages.valory.skills.reset_pause_abci.behaviours import (
    ResetPauseABCIConsensusBehaviour,
)
from packages.valory.skills.safe_deployment_abci.behaviours import (
    SafeDeploymentRoundBehaviour,
)
from packages.valory.skills.transaction_settlement_abci.behaviours import (
    TransactionSettlementRoundBehaviour,
)
from packages.valory.skills.transaction_settlement_abci.payload_tools import (
    hash_payload_to_hex,
)


# This safeTxGas value is calculated from experimental values plus
# a 10% buffer and rounded up. The Gnosis safe default value is 0 (max gas)
# https://help.gnosis-safe.io/en/articles/4738445-advanced-transaction-parameters
# More on gas estimation: https://help.gnosis-safe.io/en/articles/4933491-gas-estimation
SAFE_TX_GAS = 120000
ETHER_VALUE = 0

NO_OBSERVATION = 0.0


def to_int(most_voted_estimate: float, decimals: int) -> int:
    """Convert to int."""
    most_voted_estimate_ = str(most_voted_estimate)
    decimal_places = most_voted_estimate_[::-1].find(".")
    if decimal_places > decimals:
        most_voted_estimate_ = most_voted_estimate_[: -(decimal_places - decimals)]
    most_voted_estimate_decimal = Decimal(most_voted_estimate_)
    int_value = int(most_voted_estimate_decimal * (10 ** decimals))
    return int_value


class PriceEstimationBaseState(BaseState, ABC):
    """Base state behaviour for the common apps' skill."""

    @property
    def period_state(self) -> PeriodState:
        """Return the period state."""
        return cast(PeriodState, super().period_state)

    @property
    def params(self) -> Params:
        """Return the params."""
        return cast(Params, super().params)


class ObserveBehaviour(PriceEstimationBaseState):
    """Observe price estimate."""

    state_id = "collect_observation"
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
            with self.context.benchmark_tool.measure(self.state_id).consensus():
                yield from self.wait_until_round_end()
            self.set_done()
            return

        with self.context.benchmark_tool.measure(self.state_id).local():
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
            with self.context.benchmark_tool.measure(self.state_id).consensus():
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


class EstimateBehaviour(PriceEstimationBaseState):
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

        with self.context.benchmark_tool.measure(self.state_id).local():

            self.period_state.set_aggregator_method(
                self.params.observation_aggregator_function
            )
            self.context.logger.info(
                "Got estimate of %s price in %s: %s, Using aggregator method: %s",
                self.context.price_api.currency_id,
                self.context.price_api.convert_id,
                self.period_state.estimate,
                self.params.observation_aggregator_function,
            )
            payload = EstimatePayload(
                self.context.agent_address, self.period_state.estimate
            )

        with self.context.benchmark_tool.measure(self.state_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


def pack_for_server(  # pylint: disable-msg=too-many-arguments
    participants: Sequence[str],
    decimals: int,
    period_count: int,
    estimate: float,
    observations: Dict[str, float],
    data_source: str,
    unit: str,
    **_: Dict[str, str],
) -> bytes:
    """Package server data for signing"""
    enforce(len(str(estimate)) <= 32, "'estimate' too large")
    enforce(len(data_source) <= 32, "'data_source' too large")
    enforce(len(unit) <= 32, "'unit' too large")
    enforce(
        all(len(str(value)) <= 32 for value in observations.values()),
        "'observation' values too large",
    )
    observed = (
        to_int(observations.get(p, NO_OBSERVATION), decimals) for p in participants
    )
    return b"".join(
        [
            period_count.to_bytes(32, "big"),
            to_int(estimate, decimals).to_bytes(32, "big"),
            *map(lambda n: n.to_bytes(32, "big"), observed),
            str(data_source).zfill(32).encode("utf-8"),
            str(unit).zfill(32).encode("utf-8"),
        ]
    )


class TransactionHashBehaviour(PriceEstimationBaseState):
    """Share the transaction hash for the signature round."""

    state_id = "tx_hash"
    matching_round = TxHashRound

    def async_act(self) -> Generator:
        """
        Do the action.

        Steps:
        - Request the transaction hash for the safe transaction. This is the
          hash that needs to be signed by a threshold of agents.
        - Send the transaction hash as a transaction and wait for it to be mined.
        - Wait until ABCI application transitions to the next round.
        - Go to the next behaviour state (set done event).
        """

        with self.context.benchmark_tool.measure(self.state_id).local():
            payload_string = yield from self._get_safe_tx_hash()
            payload = TransactionHashPayload(self.context.agent_address, payload_string)

        with self.context.benchmark_tool.measure(self.state_id).consensus():
            if self.params.is_broadcasting_to_server:
                yield from self.send_to_server()
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()

    def send_to_server(self) -> Generator:  # pylint: disable-msg=too-many-locals
        """
        Send data to server.

        We send current period state data of the agents and the previous
        cycle's on-chain settlement tx hash. The current cycle's tx hash
        is not available at this stage yet, and the first iteration will
        contain no tx hash since there has not been on-chain transaction
        settlement yet.

        :yield: the http response
        """

        period_count = self.period_state.period_count

        self.context.logger.info("Attempting broadcast")

        prev_tx_hash = ""
        if period_count != 0:
            # grab tx_hash from previous cycle
            prev_period_count = period_count - 1
            previous_data = (
                self.period_state.db._data[  # pylint: disable=protected-access
                    prev_period_count
                ]
            )

            prev_tx_hash = previous_data.get("final_tx_hash", "")

        # select relevant data
        agents = self.period_state.db.get_strict("participants")
        payloads = self.period_state.db.get_strict("participant_to_observations")
        estimate = self.period_state.db.get_strict("most_voted_estimate")

        observations = {
            agent: getattr(payloads.get(agent), "observation", NO_OBSERVATION)
            for agent in agents
        }

        price_api = self.context.price_api

        # adding timestamp on server side when received
        # period and agent_address are used as `primary key`
        data_for_server = {
            "period_count": period_count,
            "agent_address": self.context.agent_address,
            "estimate": estimate,
            "prev_tx_hash": prev_tx_hash,
            "observations": observations,
            "data_source": price_api.api_id,
            "unit": f"{price_api.currency_id}:{price_api.convert_id}",
        }

        # pack data
        participants = self.period_state.sorted_participants
        decimals = self.params.oracle_params["decimals"]
        package = pack_for_server(participants, decimals, **data_for_server)
        data_for_server["package"] = package.hex()

        # get signature
        signature = yield from self.get_signature(package, is_deprecated_mode=True)
        data_for_server["signature"] = signature
        self.context.logger.info(f"Signature: {signature}")

        message = str(data_for_server).encode("utf-8")
        server_api_specs = self.context.server_api.get_spec()
        raw_response = yield from self.get_http_response(
            method=server_api_specs["method"],
            url=server_api_specs["url"],
            content=message,
        )

        response = self.context.server_api.process_response(raw_response)
        self.context.logger.info(f"Broadcast response: {response}")

    def _get_safe_tx_hash(self) -> Generator[None, None, Optional[str]]:
        """Get the transaction hash of the Safe tx."""
        contract_callable = "get_latest_transmission_details"
        contract_api_msg = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
            contract_address=self.period_state.oracle_contract_address,
            contract_id=str(OffchainAggregatorContract.contract_id),
            contract_callable=contract_callable,
        )
        if (
            contract_api_msg.performative
            != ContractApiMessage.Performative.RAW_TRANSACTION
        ):  # pragma: nocover
            yield from self.__handle_potential_rate_limiting(
                contract_api_msg, contract_callable
            )
            return None
        epoch_ = cast(int, contract_api_msg.raw_transaction.body["epoch_"]) + 1
        round_ = cast(int, contract_api_msg.raw_transaction.body["round_"])
        decimals = self.params.oracle_params["decimals"]
        amount = self.period_state.most_voted_estimate
        amount_ = to_int(amount, decimals)
        contract_callable = "get_transmit_data"
        contract_api_msg = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
            contract_address=self.period_state.oracle_contract_address,
            contract_id=str(OffchainAggregatorContract.contract_id),
            contract_callable=contract_callable,
            epoch_=epoch_,
            round_=round_,
            amount_=amount_,
        )
        if (
            contract_api_msg.performative
            != ContractApiMessage.Performative.RAW_TRANSACTION
        ):  # pragma: nocover
            yield from self.__handle_potential_rate_limiting(
                contract_api_msg, contract_callable
            )
            return None
        data = cast(bytes, contract_api_msg.raw_transaction.body["data"])
        to_address = self.period_state.oracle_contract_address
        ether_value = ETHER_VALUE
        safe_tx_gas = SAFE_TX_GAS
        contract_callable = "get_raw_safe_transaction_hash"
        contract_api_msg = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
            contract_address=self.period_state.safe_contract_address,
            contract_id=str(GnosisSafeContract.contract_id),
            contract_callable=contract_callable,
            to_address=to_address,
            value=ether_value,
            data=data,
            safe_tx_gas=safe_tx_gas,
        )
        if (
            contract_api_msg.performative
            != ContractApiMessage.Performative.RAW_TRANSACTION
        ):  # pragma: nocover
            yield from self.__handle_potential_rate_limiting(
                contract_api_msg, contract_callable
            )
            return None
        safe_tx_hash = cast(str, contract_api_msg.raw_transaction.body["tx_hash"])
        safe_tx_hash = safe_tx_hash[2:]
        self.context.logger.info(f"Hash of the Safe transaction: {safe_tx_hash}")
        # temp hack:
        payload_string = hash_payload_to_hex(
            safe_tx_hash, ether_value, safe_tx_gas, to_address, data
        )
        return payload_string

    def __handle_potential_rate_limiting(
        self, contract_api_msg: ContractApiMessage, contract_callable: str
    ) -> Generator[None, None, None]:
        """Check if we have been rate limited and cool down if needed."""
        if contract_api_msg.code == 429:
            message = json.loads(cast(str, contract_api_msg.message))
            if message["error"]["code"] == "-32005":
                backoff = message["data"]["backoff_seconds"]
                self.context.logger.warning(
                    f"We have been rate-limited! Sleeping for {backoff} seconds..."
                )
                yield from self.sleep(backoff)
                return

        self.context.logger.warning(
            f"{contract_callable} unsuccessful! Response: {contract_api_msg}"
        )


class ObserverRoundBehaviour(AbstractRoundBehaviour):
    """This behaviour manages the consensus stages for the observer behaviour."""

    initial_state_cls = ObserveBehaviour
    abci_app_cls = PriceAggregationAbciApp  # type: ignore
    behaviour_states: Set[Type[BaseState]] = {  # type: ignore
        ObserveBehaviour,  # type: ignore
        EstimateBehaviour,  # type: ignore
        TransactionHashBehaviour,  # type: ignore
    }


class PriceEstimationConsensusBehaviour(AbstractRoundBehaviour):
    """This behaviour manages the consensus stages for the price estimation."""

    initial_state_cls = RegistrationStartupBehaviour
    abci_app_cls = PriceEstimationAbciApp  # type: ignore
    behaviour_states: Set[Type[BaseState]] = {
        *OracleDeploymentRoundBehaviour.behaviour_states,
        *AgentRegistrationRoundBehaviour.behaviour_states,
        *SafeDeploymentRoundBehaviour.behaviour_states,
        *TransactionSettlementRoundBehaviour.behaviour_states,
        *ResetPauseABCIConsensusBehaviour.behaviour_states,
        *ObserverRoundBehaviour.behaviour_states,
    }
