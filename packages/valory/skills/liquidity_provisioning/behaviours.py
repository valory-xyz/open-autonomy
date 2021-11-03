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
    SelectKeeperMainRound,
    SelectKeeperDeployRound,
    SelectKeeperSwapRound,
    SelectKeeperAddAllowanceRound,
    SelectKeeperAddLiquidityRound,
    SelectKeeperRemoveLiquidityRound,
    SelectKeeperRemoveAllowanceRound,
    SelectKeeperSwapBackRound,
    StrategyEvaluationRound,
    WaitRound,
    SwapRound,
    ValidateSwapRound,
    AllowanceCheckRound,
    AddAllowanceRound,
    ValidateAddAllowanceRound,
    AddLiquidityRound,
    ValidateAddLiquidityRound,
    RemoveLiquidityRound,
    ValidateRemoveLiquidityRound,
    RemoveAllowanceRound,
    ValidateRemoveAllowanceRound,
    SwapBackRound,
    ValidateSwapBackRound
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
    SelectKeeperBehaviour,
    DeploySafeBehaviour,
    ValidateSafeBehaviour,
    SignatureBehaviour,
    EndBehaviour
)


class LiquidityProvisionBaseState(PriceEstimationBaseState):
    """Base state behaviour for the liquidity provision skill."""
    pass


class DeploySafeBehaviour(LiquidityProvisionBaseState):
    def async_act(self) -> Generator[None, None, None]:
        if self.context.agent_address != self.period_state.most_voted_keeper_address:
            yield from self._not_sender_act()
        else:
            yield from self._sender_act()

    def _not_sender_act(self) -> Generator:
        """Do the non-sender action."""

    def _sender_act(self) -> Generator[None, None, None]:
        """Do the sender action."""


class ValidateSafeBehaviour(LiquidityProvisionBaseState):
    def async_act(self) -> Generator[None, None, None]:
        pass


class StrategyEvaluationBehaviour(LiquidityProvisionBaseState):
    def async_act(self) -> Generator[None, None, None]:
        pass


class WaitBehaviour(LiquidityProvisionBaseState):
    def async_act(self) -> Generator[None, None, None]:
        pass


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


class ValidateSwapBehaviour(LiquidityProvisionBaseState):
    def async_act(self) -> Generator[None, None, None]:
        pass


class AllowanceCheckBehaviour(LiquidityProvisionBaseState):
    def async_act(self) -> Generator[None, None, None]:
        pass


class AddAllowanceBehaviour(LiquidityProvisionBaseState):
    def async_act(self) -> Generator[None, None, None]:
        if self.context.agent_address != self.period_state.most_voted_keeper_address:
            yield from self._not_sender_act()
        else:
            yield from self._sender_act()

    def _not_sender_act(self) -> Generator:
        """Do the non-sender action."""

    def _sender_act(self) -> Generator[None, None, None]:
        """Do the sender action."""


class ValidateAddAllowanceBehaviour(LiquidityProvisionBaseState):
    def async_act(self) -> Generator[None, None, None]:
        pass


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


class ValidateAddLiquidityBehaviour(LiquidityProvisionBaseState):
    def async_act(self) -> Generator[None, None, None]:
        pass


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


class ValidateRemoveLiquidityBehaviour(LiquidityProvisionBaseState):
    def async_act(self) -> Generator[None, None, None]:
        pass


class RemoveAllowanceBehaviour(LiquidityProvisionBaseState):
    def async_act(self) -> Generator[None, None, None]:
        if self.context.agent_address != self.period_state.most_voted_keeper_address:
            yield from self._not_sender_act()
        else:
            yield from self._sender_act()

    def _not_sender_act(self) -> Generator:
        """Do the non-sender action."""

    def _sender_act(self) -> Generator[None, None, None]:
        """Do the sender action."""


class ValidateRemoveAllowanceBehaviour(LiquidityProvisionBaseState):
    def async_act(self) -> Generator[None, None, None]:
        pass


class SwapBackBehaviour(LiquidityProvisionBaseState):
    def async_act(self) -> Generator[None, None, None]:
        if self.context.agent_address != self.period_state.most_voted_keeper_address:
            yield from self._not_sender_act()
        else:
            yield from self._sender_act()

    def _not_sender_act(self) -> Generator:
        """Do the non-sender action."""

    def _sender_act(self) -> Generator[None, None, None]:
        """Do the sender action."""


class ValidateSwapBackBehaviour(LiquidityProvisionBaseState):
    def async_act(self) -> Generator[None, None, None]:
        pass


class SelectKeeperMainBehaviour(SelectKeeperBehaviour):
    """Select the keeper agent."""

    state_id = "select_keeper_main"
    matching_round = SelectKeeperMainRound

class SelectKeeperDeployBehaviour(SelectKeeperBehaviour):
    """Select the keeper agent."""

    state_id = "select_keeper_deploy"
    matching_round = SelectKeeperDeployRound

class SelectKeeperSwapBehaviour(SelectKeeperBehaviour):
    """Select the keeper agent."""

    state_id = "select_keeper_swap"
    matching_round = SelectKeeperSwapRound

class SelectKeeperAddAllowanceBehaviour(SelectKeeperBehaviour):
    """Select the keeper agent."""

    state_id = "select_keeper_approve"
    matching_round = SelectKeeperAddAllowanceRound

class SelectKeeperAddLiquidityBehaviour(SelectKeeperBehaviour):
    """Select the keeper agent."""

    state_id = "select_keeper_add_liquidity"
    matching_round = SelectKeeperAddLiquidityRound

class SelectKeeperRemoveLiquidityBehaviour(SelectKeeperBehaviour):
    """Select the keeper agent."""

    state_id = "select_keeper_remove_liquidity"
    matching_round = SelectKeeperRemoveLiquidityRound

class SelectKeeperRemoveAllowanceBehaviour(SelectKeeperBehaviour):
    """Select the keeper agent."""

    state_id = "select_keeper_remove_allowance"
    matching_round = SelectKeeperRemoveAllowanceRound

class SelectKeeperSwapBackBehaviour(SelectKeeperBehaviour):
    """Select the keeper agent."""

    state_id = "select_keeper_swap_back"
    matching_round = SelectKeeperSwapBackRound


class LiquidityProvisionConsensusBehaviour(AbstractRoundBehaviour):
    """This behaviour manages the consensus stages for the price estimation."""

    initial_state_cls = TendermintHealthcheckBehaviour
    abci_app_cls: LiquidityProvisionAbciApp  # type: ignore
    behaviour_states: Set[Type[PriceEstimationBaseState]] = {  # type: ignore
        TendermintHealthcheckBehaviour,  # type: ignore
        RegistrationBehaviour,  # type: ignore
        RandomnessBehaviour,  # type: ignore
        SelectKeeperMainBehaviour,  # type: ignore
        DeploySafeBehaviour,  # type: ignore
        ValidateSafeBehaviour,  # type: ignore
        StrategyEvaluationBehaviour,
        SwapBehaviour,  # type: ignore
        ValidateSwapBehaviour,  # type: ignore
        AllowanceCheckBehaviour, # type: ignore
        AddAllowanceBehaviour,  # type: ignore
        ValidateAddAllowanceBehaviour,
        AddLiquidityBehaviour,  # type: ignore
        ValidateAddLiquidityBehaviour,
        RemoveLiquidityBehaviour,  # type: ignore
        ValidateRemoveLiquidityBehaviour,  # type: ignore
        RemoveAllowanceBehaviour,  # type: ignore
        ValidateRemoveAllowanceBehaviour,  # type: ignore
        SwapBackBehaviour,  # type: ignore
        ValidateSwapBackBehaviour,
        EndBehaviour,  # type: ignore
    }
