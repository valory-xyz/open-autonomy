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

from abc import ABC
from decimal import Decimal
from typing import Generator, Optional, Set, Type, cast

from packages.valory.contracts.gnosis_safe.contract import GnosisSafeContract
from packages.valory.contracts.offchain_aggregator.contract import (
    OffchainAggregatorContract,
)
from packages.valory.protocols.contract_api import ContractApiMessage
from packages.valory.skills.abstract_round_abci.behaviours import (
    AbstractRoundBehaviour,
    BaseState,
)
from packages.valory.skills.abstract_round_abci.utils import BenchmarkTool
from packages.valory.skills.oracle_deployment_abci.behaviours import (
    DeployOracleBehaviour,
    RandomnessOracleBehaviour,
    SelectKeeperOracleBehaviour,
    ValidateOracleBehaviour,
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
    RegistrationBehaviour,
    RegistrationStartupBehaviour,
    TendermintHealthcheckBehaviour,
)
from packages.valory.skills.safe_deployment_abci.behaviours import (
    DeploySafeBehaviour,
    RandomnessSafeBehaviour,
    SelectKeeperSafeBehaviour,
    ValidateSafeBehaviour,
)
from packages.valory.skills.transaction_settlement_abci.behaviours import (
    FinalizeBehaviour,
    RandomnessTransactionSubmissionBehaviour,
    ResetAndPauseBehaviour,
    ResetBehaviour,
    SelectKeeperTransactionSubmissionBehaviourA,
    SelectKeeperTransactionSubmissionBehaviourB,
    SignatureBehaviour,
    ValidateTransactionBehaviour,
)


benchmark_tool = BenchmarkTool()


SAFE_TX_GAS = 4000000  # TOFIX
ETHER_VALUE = 0


def to_int(most_voted_estimate: float, decimals: int) -> int:
    """Convert to int."""
    most_voted_estimate_ = str(most_voted_estimate)
    decimal_places = most_voted_estimate_[::-1].find(".")
    if decimal_places > decimals:
        most_voted_estimate_ = most_voted_estimate_[: -(decimal_places - decimals)]
    most_voted_estimate_decimal = Decimal(most_voted_estimate_)
    int_value = int(most_voted_estimate_decimal * (10 ** decimals))
    return int_value


def payload_to_hex(
    tx_hash: str, ether_value: int, safe_tx_gas: int, to_address: str, data: bytes
) -> str:
    """Serialise to a hex string."""
    if len(tx_hash) != 64:  # should be exactly 32 bytes!
        raise ValueError("cannot encode tx_hash of non-32 bytes")  # pragma: nocover
    ether_value_ = ether_value.to_bytes(32, "big").hex()
    safe_tx_gas_ = safe_tx_gas.to_bytes(32, "big").hex()
    if len(to_address) != 42:
        raise ValueError("cannot encode to_address of non 42 length")  # pragma: nocover
    concatenated = tx_hash + ether_value_ + safe_tx_gas_ + to_address + data.hex()
    return concatenated


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

        with benchmark_tool.measure(
            self,
        ).local():

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

        with benchmark_tool.measure(
            self,
        ).consensus():
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
        - Request the transaction hash for the safe transaction. This is the
          hash that needs to be signed by a threshold of agents.
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
        data = cast(bytes, contract_api_msg.raw_transaction.body["data"])
        to_address = self.period_state.oracle_contract_address
        ether_value = ETHER_VALUE
        safe_tx_gas = SAFE_TX_GAS
        contract_api_msg = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
            contract_address=self.period_state.safe_contract_address,
            contract_id=str(GnosisSafeContract.contract_id),
            contract_callable="get_raw_safe_transaction_hash",
            to_address=to_address,
            value=ether_value,
            data=data,
            safe_tx_gas=safe_tx_gas,
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
        payload_string = payload_to_hex(
            safe_tx_hash, ether_value, safe_tx_gas, to_address, data
        )
        return payload_string


class ObserverBehaviour(AbstractRoundBehaviour):
    """This behaviour manages the consensus stages for the observer behaviour."""

    initial_state_cls = TendermintHealthcheckBehaviour
    abci_app_cls = PriceAggregationAbciApp  # type: ignore
    behaviour_states: Set[Type[BaseState]] = {  # type: ignore
        TendermintHealthcheckBehaviour,  # type: ignore
        ObserveBehaviour,  # type: ignore
        EstimateBehaviour,  # type: ignore
        TransactionHashBehaviour,  # type: ignore
    }

    def setup(self) -> None:
        """Set up the behaviour."""
        super().setup()
        benchmark_tool.logger = self.context.logger


class PriceEstimationConsensusBehaviour(AbstractRoundBehaviour):
    """This behaviour manages the consensus stages for the price estimation."""

    initial_state_cls = TendermintHealthcheckBehaviour
    abci_app_cls = PriceEstimationAbciApp  # type: ignore
    behaviour_states: Set[Type[BaseState]] = {  # type: ignore
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
        RandomnessTransactionSubmissionBehaviour,  # type: ignore
        ObserveBehaviour,  # type: ignore
        EstimateBehaviour,  # type: ignore
        TransactionHashBehaviour,  # type: ignore
        SignatureBehaviour,  # type: ignore
        FinalizeBehaviour,  # type: ignore
        ValidateTransactionBehaviour,  # type: ignore
        SelectKeeperTransactionSubmissionBehaviourA,  # type: ignore
        SelectKeeperTransactionSubmissionBehaviourB,  # type: ignore
        ResetBehaviour,  # type: ignore
        ResetAndPauseBehaviour,  # type: ignore
    }

    def setup(self) -> None:
        """Set up the behaviour."""
        super().setup()
        benchmark_tool.logger = self.context.logger
