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

"""This module contains the data classes for the liquidity provision ABCI application."""
import struct
from abc import ABC
from enum import Enum
from types import MappingProxyType
from typing import (
    AbstractSet,
    Dict,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Type,
    cast,
)

from aea.exceptions import enforce

from packages.valory.skills.abstract_round_abci.base import (
    ABCIAppInternalError,
    AbciApp,
    AbciAppTransitionFunction,
    AbstractRound,
    BasePeriodState,
    BaseTxPayload,
    CollectDifferentUntilAllRound,
    CollectDifferentUntilThresholdRound,
    CollectSameUntilThresholdRound,
    OnlyKeeperSendsRound,
    TransactionNotValidError,
    VotingRound,
)
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
    TransactionType,
    ValidatePayload,
)
from packages.valory.skills.price_estimation_abci.tools import aggregate

from packages.valory.skills.price_estimation_abci.rounds import (
    ConsensusReachedRound,
    RegistrationRound,
    RandomnessRound,
    DeploySafeRound,
    ValidateSafeRound
)

class Event(Enum):
    """Event enumeration for the liquidity provisioning demo."""

    DONE = "done"
    EXIT = "exit"
    ROUND_TIMEOUT = "round_timeout"
    NO_MAJORITY = "no_majority"
    WAIT = "wait"
    NO_ALLOWANCE = "no_allowance"


class SelectKeeperMainRound:
    """This class represents the select keeper A round."""

    round_id = "select_keeper_main"

class SelectKeeperDeployRound:
    """This class represents the select keeper A round."""

    round_id = "select_keeper_deploy"

class SelectKeeperSwapRound:
    """This class represents the select keeper A round."""

    round_id = "select_keeper_swap"

class SelectKeeperAddAllowanceRound:
    """This class represents the select keeper A round."""

    round_id = "select_keeper_approve"

class SelectKeeperAddLiquidityRound:
    """This class represents the select keeper A round."""

    round_id = "select_keeper_add_liquidity"

class SelectKeeperRemoveLiquidityRound:
    """This class represents the select keeper A round."""

    round_id = "select_keeper_remove_liquidity"

class SelectKeeperRemoveAllowanceRound:
    """This class represents the select keeper A round."""

    round_id = "select_keeper_remove_allowance"

class SelectKeeperSwapBackRound:
    """This class represents the select keeper A round."""

    round_id = "select_keeper_swap_back"


class StrategyEvaluationRound:
    pass

class WaitRound:
    pass

class SwapRound:
    pass

class ValidateSwapRound:
    pass

class AllowanceCheckRound:
    pass

class AddAllowanceRound:
    pass

class ValidateAddAllowanceRound:
    pass

class AddLiquidityRound:
    pass

class ValidateAddLiquidityRound:
    pass

class RemoveLiquidityRound:
    pass

class ValidateRemoveLiquidityRound:
    pass

class RemoveAllowanceRound:
    pass

class ValidateRemoveAllowanceRound:
    pass

class SwapBackRound:
    pass

class ValidateSwapBackRound:
    pass

class LiquidityProvisionAbciApp(AbciApp[Event]):
    """Liquidity Provision ABCI application."""

    initial_round_cls: Type[AbstractRound] = RegistrationRound
    transition_function: AbciAppTransitionFunction = {
        RegistrationRound: {Event.DONE: RandomnessRound},
        RandomnessRound: {
            Event.DONE: SelectKeeperMainRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
        SelectKeeperMainRound: {
            Event.DONE: DeploySafeRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
        DeploySafeRound: {
            Event.DONE: ValidateSafeRound,
            Event.EXIT: SelectKeeperDeployRound,
        },
        SelectKeeperDeployRound: {
            Event.DONE: DeploySafeRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
        ValidateSafeRound: {
            Event.DONE: StrategyEvaluationRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
        StrategyEvaluationRound: {
            Event.DONE: SwapRound,
            Event.WAIT: WaitRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
        WaitRound: {
            Event.DONE: StrategyEvaluationRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
        SwapRound: {
            Event.DONE: ValidateSwapRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
            Event.EXIT: SelectKeeperSwapRound,
        },
        SelectKeeperSwapRound: {
            Event.DONE: SwapRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
        ValidateSwapRound: {
            Event.DONE: AllowanceCheckRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
        AllowanceCheckRound: {
            Event.DONE: AddLiquidityRound,
            Event.NO_ALLOWANCE: AddAllowanceRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
        AddAllowanceRound: {
            Event.DONE: ValidateAddAllowanceRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
            Event.EXIT: SelectKeeperAddAllowanceRound,
        },
        SelectKeeperAddAllowanceRound: {
            Event.DONE: AddAllowanceRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
        ValidateAddAllowanceRound: {
            Event.DONE: AddLiquidityRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
        AddLiquidityRound: {
            Event.DONE: ValidateAddLiquidityRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
            Event.EXIT: SelectKeeperAddLiquidityRound,
        },
        SelectKeeperAddLiquidityRound: {
            Event.DONE: AddLiquidityRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
        ValidateAddLiquidityRound: {
            Event.DONE: RemoveLiquidityRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
        RemoveLiquidityRound: {
            Event.DONE: ValidateRemoveLiquidityRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
            Event.EXIT: SelectKeeperRemoveLiquidityRound,
        },
        SelectKeeperRemoveLiquidityRound: {
            Event.DONE: RemoveLiquidityRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
        ValidateRemoveLiquidityRound: {
            Event.DONE: RemoveAllowanceRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
        RemoveAllowanceRound: {
            Event.DONE: ValidateRemoveAllowanceRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
            Event.EXIT: SelectKeeperRemoveAllowanceRound,
        },
        SelectKeeperRemoveAllowanceRound: {
            Event.DONE: SwapRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
        ValidateRemoveAllowanceRound: {
            Event.DONE: SwapBackRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
        SwapBackRound: {
            Event.DONE: ValidateSwapBackRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
            Event.EXIT: SelectKeeperSwapBackRound,
        },
        SelectKeeperSwapBackRound: {
            Event.DONE: SwapBackRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
        ValidateSwapBackRound: {
            Event.DONE: ConsensusReachedRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
    }
    event_to_timeout: Dict[Event, float] = {
        Event.EXIT: 5.0,
        Event.ROUND_TIMEOUT: 30.0,
    }
