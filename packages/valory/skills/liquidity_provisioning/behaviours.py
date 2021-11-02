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

"""This module contains the behaviours for the 'liquidity_provisioning' skill."""
import binascii
import json
import pprint
from abc import ABC
from typing import Generator, Set, Type, cast

from aea_ledger_ethereum import EthereumApi

from packages.open_aea.protocols.signing import SigningMessage
from packages.valory.connections.ledger.base import (
    CONNECTION_ID as LEDGER_CONNECTION_PUBLIC_ID,
)
from packages.valory.contracts.gnosis_safe.contract import GnosisSafeContract
from packages.valory.protocols.contract_api import ContractApiMessage
from packages.valory.skills.abstract_round_abci.behaviours import (
    AbstractRoundBehaviour,
    BaseState,
)
from packages.valory.skills.abstract_round_abci.utils import BenchmarkTool
from packages.valory.skills.price_estimation_abci.models import Params, SharedState
from packages.valory.skills.price_estimation_abci.payloads import (
    DeploySafePayload,
    EstimatePayload,
    FinalizationTxPayload,
    ObservationPayload,
    RandomnessPayload,
    RegistrationPayload,
    SelectKeeperPayload,
    SignaturePayload,
    TransactionHashPayload,
    ValidatePayload,
)
from packages.valory.skills.price_estimation_abci.rounds import (
    CollectObservationRound,
    CollectSignatureRound,
    ConsensusReachedRound,
    DeploySafeRound,
    EstimateConsensusRound,
    FinalizationRound,
    PeriodState,
    PriceEstimationAbciApp,
    RandomnessRound,
    RegistrationRound,
    SelectKeeperARound,
    SelectKeeperBRound,
    TxHashRound,
    ValidateSafeRound,
    ValidateTransactionRound,
)
from packages.valory.skills.liquidity_provisioning.rounds import (
    LiquidityProvisionAbciApp
)
from packages.valory.skills.price_estimation_abci.tools import random_selection
from packages.valory.skills.abstract_round_abci.behaviours import (
    PriceEstimationBaseState,
    TendermintHealthcheckBehaviour,
    RegistrationBehaviour,
    RandomnessBehaviour,
    SelectKeeperABehaviour,
    SelectKeeperBBehaviour,
    EndBehaviour
)


class LiquidityProvisionBaseState(PriceEstimationBaseState):
    """Base state behaviour for the price estimation skill."""
    def async_act(self) -> Generator[None, None, None]:
        if self.context.agent_address != self.period_state.most_voted_keeper_address:
            yield from self._not_sender_act()
        else:
            yield from self._sender_act()

    def _not_sender_act(self) -> Generator:
        """Do the non-sender action."""

    def _sender_act(self) -> Generator[None, None, None]:
        """Do the sender action."""

class AllowanceCheckBehaviour(LiquidityProvisionBaseState):
    def async_act(self) -> Generator[None, None, None]:
        if self.context.agent_address != self.period_state.most_voted_keeper_address:
            yield from self._not_sender_act()
        else:
            yield from self._sender_act()

    def _not_sender_act(self) -> Generator:
        """Do the non-sender action."""

    def _sender_act(self) -> Generator[None, None, None]:
        """Do the sender action."""

class ApproveBehaviour(LiquidityProvisionBaseState):
    def async_act(self) -> Generator[None, None, None]:
        if self.context.agent_address != self.period_state.most_voted_keeper_address:
            yield from self._not_sender_act()
        else:
            yield from self._sender_act()

    def _not_sender_act(self) -> Generator:
        """Do the non-sender action."""

    def _sender_act(self) -> Generator[None, None, None]:
        """Do the sender action."""

class AddLiquidityBehaviour(LiquidityProvisionBaseState):
    def async_act(self) -> Generator[None, None, None]:
        if self.context.agent_address != self.period_state.most_voted_keeper_address:
            yield from self._not_sender_act()
        else:
            yield from self._sender_act()

    def _not_sender_act(self) -> Generator:
        """Do the non-sender action."""

    def _sender_act(self) -> Generator[None, None, None]:
        """Do the sender action."""

class RemoveLiquidityBehaviour(LiquidityProvisionBaseState):
    def async_act(self) -> Generator[None, None, None]:
        if self.context.agent_address != self.period_state.most_voted_keeper_address:
            yield from self._not_sender_act()
        else:
            yield from self._sender_act()

    def _not_sender_act(self) -> Generator:
        """Do the non-sender action."""

    def _sender_act(self) -> Generator[None, None, None]:
        """Do the sender action."""

class SwapBehaviour(LiquidityProvisionBaseState):
    def async_act(self) -> Generator[None, None, None]:
        if self.context.agent_address != self.period_state.most_voted_keeper_address:
            yield from self._not_sender_act()
        else:
            yield from self._sender_act()

    def _not_sender_act(self) -> Generator:
        """Do the non-sender action."""

    def _sender_act(self) -> Generator[None, None, None]:
        """Do the sender action."""

class LiquidityProvisionConsensusBehaviour(AbstractRoundBehaviour):
    """This behaviour manages the consensus stages for the price estimation."""

    initial_state_cls = TendermintHealthcheckBehaviour
    abci_app_cls: LiquidityProvisionAbciApp  # type: ignore
    behaviour_states: Set[Type[PriceEstimationBaseState]] = {  # type: ignore
        TendermintHealthcheckBehaviour,  # type: ignore
        RegistrationBehaviour,  # type: ignore
        RandomnessBehaviour,  # type: ignore
        SelectKeeperABehaviour,  # type: ignore
        SwapBehaviour,  # type: ignore
        AllowanceCheckBehaviour, # type: ignore
        ApproveBehaviour,  # type: ignore
        AddLiquidityBehaviour,  # type: ignore
        RemoveLiquidityBehaviour,  # type: ignore
        SwapBehaviour,  # type: ignore
        EndBehaviour,  # type: ignore
    }
