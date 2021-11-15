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
from abc import ABC
from enum import Enum
from types import MappingProxyType
from typing import AbstractSet, Dict, Mapping, Optional, Tuple, Type, cast

from aea.exceptions import enforce

from packages.valory.skills.abstract_round_abci.base import (
    AbciApp,
    AbciAppTransitionFunction,
    AbstractRound,
    BasePeriodState,
    OnlyKeeperSendsRound,
    VotingRound,
)
from packages.valory.skills.liquidity_provision.payloads import (
    AllowanceCheckPayload,
    StrategyEvaluationPayload,
    StrategyType,
)
from packages.valory.skills.price_estimation_abci.payloads import (
    FinalizationTxPayload,
    SignaturePayload,
    TransactionHashPayload,
    TransactionType,
    ValidatePayload,
)
from packages.valory.skills.price_estimation_abci.rounds import (
    CollectDifferentUntilAllRound,
    CollectDifferentUntilThresholdRound,
    CollectSameUntilThresholdRound,
    DeploySafeRound,
    RandomnessRound,
    RegistrationRound,
    ResetRound,
)
from packages.valory.skills.price_estimation_abci.rounds import (
    ValidateSafeRound as DeploySafeValidationRound,
)


class Event(Enum):
    """Event enumeration for the liquidity provision demo."""

    DONE = "done"
    EXIT = "exit"
    ROUND_TIMEOUT = "round_timeout"
    NO_MAJORITY = "no_majority"
    WAIT = "wait"
    NO_ALLOWANCE = "no_allowance"


class PeriodState(
    BasePeriodState
):  # pylint: disable=too-many-instance-attributes,too-many-statements,too-many-public-methods
    """
    Class to represent a period state.

    This state is replicated by the tendermint application.
    """

    def __init__(  # pylint: disable=too-many-arguments,too-many-locals,too-many-statements
        self,
        participants: Optional[AbstractSet[str]] = None,
        participant_to_strategy: Optional[
            Mapping[str, StrategyEvaluationPayload]
        ] = None,
        most_voted_strategy: Optional[dict] = None,
        participant_to_allowance_check: Optional[
            Mapping[str, StrategyEvaluationPayload]
        ] = None,
        most_voted_allowance_check: Optional[int] = None,
        most_voted_keeper_address: Optional[str] = None,
        safe_contract_address: Optional[str] = None,
        participant_to_swap_tx_hash: Optional[
            Mapping[str, StrategyEvaluationPayload]
        ] = None,
        most_voted_swap_tx_hash: Optional[str] = None,
        participant_to_add_allowance_tx_hash: Optional[
            Mapping[str, StrategyEvaluationPayload]
        ] = None,
        most_voted_add_allowance_tx_hash: Optional[str] = None,
        participant_to_add_liquidity_tx_hash: Optional[
            Mapping[str, StrategyEvaluationPayload]
        ] = None,
        most_voted_add_liquidity_tx_hash: Optional[str] = None,
        participant_to_remove_liquidity_tx_hash: Optional[
            Mapping[str, StrategyEvaluationPayload]
        ] = None,
        most_voted_remove_liquidity_tx_hash: Optional[str] = None,
        participant_to_remove_allowance_tx_hash: Optional[
            Mapping[str, StrategyEvaluationPayload]
        ] = None,
        most_voted_remove_allowance_tx_hash: Optional[str] = None,
        participant_to_swap_back_tx_hash: Optional[
            Mapping[str, StrategyEvaluationPayload]
        ] = None,
        most_voted_swap_back_tx_hash: Optional[str] = None,
        participant_to_swap_signature: Optional[Mapping[str, SignaturePayload]] = None,
        most_voted_swap_signature: Optional[str] = None,
        participant_to_add_allowance_signature: Optional[
            Mapping[str, StrategyEvaluationPayload]
        ] = None,
        most_voted_add_allowance_signature: Optional[str] = None,
        participant_to_add_liquidity_signature: Optional[
            Mapping[str, StrategyEvaluationPayload]
        ] = None,
        most_voted_add_liquidity_signature: Optional[str] = None,
        participant_to_remove_liquidity_signature: Optional[
            Mapping[str, StrategyEvaluationPayload]
        ] = None,
        most_voted_remove_liquidity_signature: Optional[str] = None,
        participant_to_remove_allowance_signature: Optional[
            Mapping[str, StrategyEvaluationPayload]
        ] = None,
        most_voted_remove_allowance_signature: Optional[str] = None,
        participant_to_swap_back_signature: Optional[
            Mapping[str, StrategyEvaluationPayload]
        ] = None,
        most_voted_swap_back_signature: Optional[str] = None,
        participant_to_swap_send: Optional[
            Mapping[str, StrategyEvaluationPayload]
        ] = None,
        most_voted_swap_send: Optional[str] = None,
        participant_to_add_allowance_send: Optional[
            Mapping[str, StrategyEvaluationPayload]
        ] = None,
        most_voted_add_allowance_send: Optional[str] = None,
        participant_to_add_liquidity_send: Optional[
            Mapping[str, StrategyEvaluationPayload]
        ] = None,
        most_voted_add_liquidity_send: Optional[str] = None,
        participant_to_remove_liquidity_send: Optional[
            Mapping[str, StrategyEvaluationPayload]
        ] = None,
        most_voted_remove_liquidity_send: Optional[str] = None,
        participant_to_remove_allowance_send: Optional[
            Mapping[str, StrategyEvaluationPayload]
        ] = None,
        most_voted_remove_allowance_send: Optional[str] = None,
        participant_to_swap_back_send: Optional[
            Mapping[str, StrategyEvaluationPayload]
        ] = None,
        most_voted_swap_back_send: Optional[str] = None,
        participant_to_swap_validation: Optional[
            Mapping[str, StrategyEvaluationPayload]
        ] = None,
        most_voted_swap_validation: Optional[str] = None,
        participant_to_add_allowance_validation: Optional[
            Mapping[str, SignaturePayload]
        ] = None,
        most_voted_add_allowance_validation: Optional[str] = None,
        participant_to_add_liquidity_validation: Optional[
            Mapping[str, SignaturePayload]
        ] = None,
        most_voted_add_liquidity_validation: Optional[str] = None,
        participant_to_remove_liquidity_validation: Optional[
            Mapping[str, SignaturePayload]
        ] = None,
        most_voted_remove_liquidity_validation: Optional[str] = None,
        participant_to_remove_allowance_validation: Optional[
            Mapping[str, SignaturePayload]
        ] = None,
        most_voted_remove_allowance_validation: Optional[str] = None,
        participant_to_swap_back_validation: Optional[
            Mapping[str, SignaturePayload]
        ] = None,
        most_voted_swap_back_validation: Optional[str] = None,
        final_swap_tx_hash: Optional[str] = None,
        final_add_allowance_tx_hash: Optional[str] = None,
        final_add_liquidity_tx_hash: Optional[str] = None,
        final_remove_liquidity_tx_hash: Optional[str] = None,
        final_remove_allowance_tx_hash: Optional[str] = None,
        final_swap_back_tx_hash: Optional[str] = None,
    ) -> None:
        """Initialize a period state."""
        super().__init__(participants=participants)
        self._participant_to_strategy = participant_to_strategy
        self._most_voted_strategy = most_voted_strategy
        self._most_voted_keeper_address = most_voted_keeper_address
        self._safe_contract_address = safe_contract_address
        self._participant_to_allowance_check = participant_to_allowance_check
        self._most_voted_allowance_check = most_voted_allowance_check

        self._participant_to_swap_tx_hash = participant_to_swap_tx_hash
        self._most_voted_swap_tx_hash = most_voted_swap_tx_hash

        self._participant_to_add_allowance_tx_hash = (
            participant_to_add_allowance_tx_hash
        )
        self._most_voted_add_allowance_tx_hash = most_voted_add_allowance_tx_hash

        self._participant_to_add_liquidity_tx_hash = (
            participant_to_add_liquidity_tx_hash
        )
        self._most_voted_add_liquidity_tx_hash = most_voted_add_liquidity_tx_hash

        self._participant_to_remove_liquidity_tx_hash = (
            participant_to_remove_liquidity_tx_hash
        )
        self._most_voted_remove_liquidity_tx_hash = most_voted_remove_liquidity_tx_hash

        self._participant_to_remove_allowance_tx_hash = (
            participant_to_remove_allowance_tx_hash
        )
        self._most_voted_remove_allowance_tx_hash = most_voted_remove_allowance_tx_hash

        self._participant_to_swap_back_tx_hash = participant_to_swap_back_tx_hash
        self._most_voted_swap_back_tx_hash = most_voted_swap_back_tx_hash

        self._participant_to_swap_signature = participant_to_swap_signature
        self._most_voted_swap_signature = most_voted_swap_signature

        self._participant_to_add_allowance_signature = (
            participant_to_add_allowance_signature
        )
        self._most_voted_add_allowance_signature = most_voted_add_allowance_signature

        self._participant_to_add_liquidity_signature = (
            participant_to_add_liquidity_signature
        )
        self._most_voted_add_liquidity_signature = most_voted_add_liquidity_signature

        self._participant_to_remove_liquidity_signature = (
            participant_to_remove_liquidity_signature
        )
        self._most_voted_remove_liquidity_signature = (
            most_voted_remove_liquidity_signature
        )

        self._participant_to_remove_allowance_signature = (
            participant_to_remove_allowance_signature
        )
        self._most_voted_remove_allowance_signature = (
            most_voted_remove_allowance_signature
        )

        self._participant_to_swap_back_signature = participant_to_swap_back_signature
        self._most_voted_swap_back_signature = most_voted_swap_back_signature

        self._participant_to_swap_send = participant_to_swap_send
        self._most_voted_swap_send = most_voted_swap_send

        self._participant_to_add_allowance_send = participant_to_add_allowance_send
        self._most_voted_add_allowance_send = most_voted_add_allowance_send

        self._participant_to_add_liquidity_send = participant_to_add_liquidity_send
        self._most_voted_add_liquidity_send = most_voted_add_liquidity_send

        self._participant_to_remove_liquidity_send = (
            participant_to_remove_liquidity_send
        )
        self._most_voted_remove_liquidity_send = most_voted_remove_liquidity_send

        self._participant_to_remove_allowance_send = (
            participant_to_remove_allowance_send
        )
        self._most_voted_remove_allowance_send = most_voted_remove_allowance_send

        self._participant_to_swap_back_send = participant_to_swap_back_send
        self._most_voted_swap_back_send = most_voted_swap_back_send

        self._participant_to_swap_validation = participant_to_swap_validation
        self._most_voted_swap_validation = most_voted_swap_validation

        self._participant_to_add_allowance_validation = (
            participant_to_add_allowance_validation
        )
        self._most_voted_add_allowance_validation = most_voted_add_allowance_validation

        self._participant_to_add_liquidity_validation = (
            participant_to_add_liquidity_validation
        )
        self._most_voted_add_liquidity_validation = most_voted_add_liquidity_validation

        self._participant_to_remove_liquidity_validation = (
            participant_to_remove_liquidity_validation
        )
        self._most_voted_remove_liquidity_validation = (
            most_voted_remove_liquidity_validation
        )

        self._participant_to_remove_allowance_validation = (
            participant_to_remove_allowance_validation
        )
        self._most_voted_remove_allowance_validation = (
            most_voted_remove_allowance_validation
        )

        self._participant_to_swap_back_validation = participant_to_swap_back_validation
        self._most_voted_swap_back_validation = most_voted_swap_back_validation

        self._final_swap_tx_hash = final_swap_tx_hash
        self._final_add_allowance_tx_hash = final_add_allowance_tx_hash
        self._final_add_liquidity_tx_hash = final_add_liquidity_tx_hash
        self._final_remove_liquidity_tx_hash = final_remove_liquidity_tx_hash
        self._final_remove_allowance_tx_hash = final_remove_allowance_tx_hash
        self._final_swap_back_tx_hash = final_swap_back_tx_hash

    @property
    def most_voted_strategy(self) -> dict:
        """Get the most_voted_strategy."""
        enforce(
            self._most_voted_strategy is not None,
            "'most_voted_strategy' field is None",
        )
        return cast(dict, self._most_voted_strategy)

    @property
    def encoded_most_voted_strategy(self) -> bytes:
        """Get the encoded (most voted) strategy."""
        return bytes()

    @property
    def most_voted_keeper_address(self) -> str:
        """Get the most_voted_keeper_address."""
        enforce(
            self._most_voted_keeper_address is not None,
            "'most_voted_keeper_address' field is None",
        )
        return cast(str, self._most_voted_keeper_address)

    @property
    def safe_contract_address(self) -> str:
        """Get the safe contract address."""
        enforce(
            self._safe_contract_address is not None,
            "'safe_contract_address' field is None",
        )
        return cast(str, self._safe_contract_address)

    def reset(self) -> "PeriodState":
        """Return the initial period state."""
        return PeriodState(self.participants)

    @property
    def most_voted_swap_tx_hash(self) -> str:
        """Get the most_voted_swap_tx_hash."""
        enforce(
            self._most_voted_swap_tx_hash is not None,
            "'most_voted_swap_tx_hash' field is None",
        )
        return cast(str, self._most_voted_swap_tx_hash)

    @property
    def encoded_most_voted_swap_tx_hash(self) -> bytes:
        """Get the encoded (most voted) swap tx hash."""
        return bytes()

    @property
    def most_voted_add_allowance_tx_hash(self) -> str:
        """Get the most_voted_add_allowance_tx_hash."""
        enforce(
            self._most_voted_add_allowance_tx_hash is not None,
            "'most_voted_add_allowance_tx_hash' field is None",
        )
        return cast(str, self._most_voted_add_allowance_tx_hash)

    @property
    def encoded_most_voted_add_allowance_tx_hash(self) -> bytes:
        """Get the encoded (most voted) add_allowance tx hash."""
        return bytes()

    @property
    def most_voted_add_liquidity_tx_hash(self) -> str:
        """Get the most_voted_add_liquidity_tx_hash."""
        enforce(
            self._most_voted_add_liquidity_tx_hash is not None,
            "'most_voted_add_liquidity_tx_hash' field is None",
        )
        return cast(str, self._most_voted_add_liquidity_tx_hash)

    @property
    def encoded_most_voted_add_liquidity_tx_hash(self) -> bytes:
        """Get the encoded (most voted) add_liquidity tx hash."""
        return bytes()

    @property
    def most_voted_remove_liquidity_tx_hash(self) -> str:
        """Get the most_voted_remove_liquidity_tx_hash."""
        enforce(
            self._most_voted_remove_liquidity_tx_hash is not None,
            "'most_voted_remove_liquidity_tx_hash' field is None",
        )
        return cast(str, self._most_voted_remove_liquidity_tx_hash)

    @property
    def encoded_most_voted_remove_liquidity_tx_hash(self) -> bytes:
        """Get the encoded (most voted) remove_liquidity tx hash."""
        return bytes()

    @property
    def most_voted_remove_allowance_tx_hash(self) -> str:
        """Get the most_voted_remove_allowance_tx_hash."""
        enforce(
            self._most_voted_remove_allowance_tx_hash is not None,
            "'most_voted_remove_allowance_tx_hash' field is None",
        )
        return cast(str, self._most_voted_remove_allowance_tx_hash)

    @property
    def encoded_most_voted_remove_allowance_tx_hash(self) -> bytes:
        """Get the encoded (most voted) remove_allowance tx hash."""
        return bytes()

    @property
    def most_voted_swap_back_tx_hash(self) -> str:
        """Get the most_voted_swap_back_tx_hash."""
        enforce(
            self._most_voted_swap_back_tx_hash is not None,
            "'most_voted_swap_back_tx_hash' field is None",
        )
        return cast(str, self._most_voted_swap_back_tx_hash)

    @property
    def encoded_most_voted_swap_back_tx_hash(self) -> bytes:
        """Get the encoded (most voted) swap_back tx hash."""
        return bytes()

    @property
    def most_voted_swap_signature(self) -> str:
        """Get the most_voted_swap_signature."""
        enforce(
            self._most_voted_swap_signature is not None,
            "'most_voted_swap_signature' field is None",
        )
        return cast(str, self._most_voted_swap_signature)

    @property
    def encoded_most_voted_swap_signature(self) -> bytes:
        """Get the encoded (most voted) swap tx hash."""
        return bytes()

    @property
    def most_voted_add_allowance_signature(self) -> str:
        """Get the most_voted_add_allowance_signature."""
        enforce(
            self._most_voted_add_allowance_signature is not None,
            "'most_voted_add_allowance_signature' field is None",
        )
        return cast(str, self._most_voted_add_allowance_signature)

    @property
    def encoded_most_voted_add_allowance_signature(self) -> bytes:
        """Get the encoded (most voted) add_allowance tx hash."""
        return bytes()

    @property
    def most_voted_add_liquidity_signature(self) -> str:
        """Get the most_voted_add_liquidity_signature."""
        enforce(
            self._most_voted_add_liquidity_signature is not None,
            "'most_voted_add_liquidity_signature' field is None",
        )
        return cast(str, self._most_voted_add_liquidity_signature)

    @property
    def encoded_most_voted_add_liquidity_signature(self) -> bytes:
        """Get the encoded (most voted) add_liquidity tx hash."""
        return bytes()

    @property
    def most_voted_remove_liquidity_signature(self) -> str:
        """Get the most_voted_remove_liquidity_signature."""
        enforce(
            self._most_voted_remove_liquidity_signature is not None,
            "'most_voted_remove_liquidity_signature' field is None",
        )
        return cast(str, self._most_voted_remove_liquidity_signature)

    @property
    def encoded_most_voted_remove_liquidity_signature(self) -> bytes:
        """Get the encoded (most voted) remove_liquidity tx hash."""
        return bytes()

    @property
    def most_voted_remove_allowance_signature(self) -> str:
        """Get the most_voted_remove_allowance_signature."""
        enforce(
            self._most_voted_remove_allowance_signature is not None,
            "'most_voted_remove_allowance_signature' field is None",
        )
        return cast(str, self._most_voted_remove_allowance_signature)

    @property
    def encoded_most_voted_remove_allowance_signature(self) -> bytes:
        """Get the encoded (most voted) remove_allowance tx hash."""
        return bytes()

    @property
    def most_voted_swap_back_signature(self) -> str:
        """Get the most_voted_swap_back_signature."""
        enforce(
            self._most_voted_swap_back_signature is not None,
            "'most_voted_swap_back_signature' field is None",
        )
        return cast(str, self._most_voted_swap_back_signature)

    @property
    def encoded_most_voted_swap_back_signature(self) -> bytes:
        """Get the encoded (most voted) swap_back tx hash."""
        return bytes()

    @property
    def most_voted_swap_send(self) -> str:
        """Get the most_voted_swap_send."""
        enforce(
            self._most_voted_swap_send is not None,
            "'most_voted_swap_send' field is None",
        )
        return cast(str, self._most_voted_swap_send)

    @property
    def encoded_most_voted_swap_send(self) -> bytes:
        """Get the encoded (most voted) swap tx hash."""
        return bytes()

    @property
    def most_voted_add_allowance_send(self) -> str:
        """Get the most_voted_add_allowance_send."""
        enforce(
            self._most_voted_add_allowance_send is not None,
            "'most_voted_add_allowance_send' field is None",
        )
        return cast(str, self._most_voted_add_allowance_send)

    @property
    def encoded_most_voted_add_allowance_send(self) -> bytes:
        """Get the encoded (most voted) add_allowance tx hash."""
        return bytes()

    @property
    def most_voted_add_liquidity_send(self) -> str:
        """Get the most_voted_add_liquidity_send."""
        enforce(
            self._most_voted_add_liquidity_send is not None,
            "'most_voted_add_liquidity_send' field is None",
        )
        return cast(str, self._most_voted_add_liquidity_send)

    @property
    def encoded_most_voted_add_liquidity_send(self) -> bytes:
        """Get the encoded (most voted) add_liquidity tx hash."""
        return bytes()

    @property
    def most_voted_remove_liquidity_send(self) -> str:
        """Get the most_voted_remove_liquidity_send."""
        enforce(
            self._most_voted_remove_liquidity_send is not None,
            "'most_voted_remove_liquidity_send' field is None",
        )
        return cast(str, self._most_voted_remove_liquidity_send)

    @property
    def encoded_most_voted_remove_liquidity_send(self) -> bytes:
        """Get the encoded (most voted) remove_liquidity tx hash."""
        return bytes()

    @property
    def most_voted_remove_allowance_send(self) -> str:
        """Get the most_voted_remove_allowance_send."""
        enforce(
            self._most_voted_remove_allowance_send is not None,
            "'most_voted_remove_allowance_send' field is None",
        )
        return cast(str, self._most_voted_remove_allowance_send)

    @property
    def encoded_most_voted_remove_allowance_send(self) -> bytes:
        """Get the encoded (most voted) remove_allowance tx hash."""
        return bytes()

    @property
    def most_voted_swap_back_send(self) -> str:
        """Get the most_voted_swap_back_send."""
        enforce(
            self._most_voted_swap_back_send is not None,
            "'most_voted_swap_back_send' field is None",
        )
        return cast(str, self._most_voted_swap_back_send)

    @property
    def encoded_most_voted_swap_back_send(self) -> bytes:
        """Get the encoded (most voted) swap_back tx hash."""
        return bytes()

    @property
    def most_voted_swap_validation(self) -> str:
        """Get the most_voted_swap_validation."""
        enforce(
            self._most_voted_swap_validation is not None,
            "'most_voted_swap_validation' field is None",
        )
        return cast(str, self._most_voted_swap_validation)

    @property
    def encoded_most_voted_swap_validation(self) -> bytes:
        """Get the encoded (most voted) swap tx hash."""
        return bytes()

    @property
    def most_voted_add_allowance_validation(self) -> str:
        """Get the most_voted_add_allowance_validation."""
        enforce(
            self._most_voted_add_allowance_validation is not None,
            "'most_voted_add_allowance_validation' field is None",
        )
        return cast(str, self._most_voted_add_allowance_validation)

    @property
    def encoded_most_voted_add_allowance_validation(self) -> bytes:
        """Get the encoded (most voted) add_allowance tx hash."""
        return bytes()

    @property
    def most_voted_add_liquidity_validation(self) -> str:
        """Get the most_voted_add_liquidity_validation."""
        enforce(
            self._most_voted_add_liquidity_validation is not None,
            "'most_voted_add_liquidity_validation' field is None",
        )
        return cast(str, self._most_voted_add_liquidity_validation)

    @property
    def encoded_most_voted_add_liquidity_validation(self) -> bytes:
        """Get the encoded (most voted) add_liquidity tx hash."""
        return bytes()

    @property
    def most_voted_remove_liquidity_validation(self) -> str:
        """Get the most_voted_remove_liquidity_validation."""
        enforce(
            self._most_voted_remove_liquidity_validation is not None,
            "'most_voted_remove_liquidity_validation' field is None",
        )
        return cast(str, self._most_voted_remove_liquidity_validation)

    @property
    def encoded_most_voted_remove_liquidity_validation(self) -> bytes:
        """Get the encoded (most voted) remove_liquidity tx hash."""
        return bytes()

    @property
    def most_voted_remove_allowance_validation(self) -> str:
        """Get the most_voted_remove_allowance_validation."""
        enforce(
            self._most_voted_remove_allowance_validation is not None,
            "'most_voted_remove_allowance_validation' field is None",
        )
        return cast(str, self._most_voted_remove_allowance_validation)

    @property
    def encoded_most_voted_remove_allowance_validation(self) -> bytes:
        """Get the encoded (most voted) remove_allowance tx hash."""
        return bytes()

    @property
    def most_voted_swap_back_validation(self) -> str:
        """Get the most_voted_swap_back_validation."""
        enforce(
            self._most_voted_swap_back_validation is not None,
            "'most_voted_swap_back_validation' field is None",
        )
        return cast(str, self._most_voted_swap_back_validation)

    @property
    def encoded_most_voted_swap_back_validation(self) -> bytes:
        """Get the encoded (most voted) swap_back tx hash."""
        return bytes()

    @property
    def final_swap_tx_hash(self) -> str:
        """Get the final_tx_hash."""
        enforce(
            self._final_swap_tx_hash is not None,
            "'final_tx_hash' field is None",
        )
        return cast(str, self._final_swap_tx_hash)

    @property
    def final_add_allowance_tx_hash(self) -> str:
        """Get the final_tx_hash."""
        enforce(
            self._final_add_allowance_tx_hash is not None,
            "'final_tx_hash' field is None",
        )
        return cast(str, self._final_add_allowance_tx_hash)

    @property
    def final_add_liquidity_tx_hash(self) -> str:
        """Get the final_tx_hash."""
        enforce(
            self._final_add_liquidity_tx_hash is not None,
            "'final_tx_hash' field is None",
        )
        return cast(str, self._final_add_liquidity_tx_hash)

    @property
    def final_remove_liquidity_tx_hash(self) -> str:
        """Get the final_tx_hash."""
        enforce(
            self._final_remove_liquidity_tx_hash is not None,
            "'final_tx_hash' field is None",
        )
        return cast(str, self._final_remove_liquidity_tx_hash)

    @property
    def final_remove_allowance_tx_hash(self) -> str:
        """Get the final_tx_hash."""
        enforce(
            self._final_remove_allowance_tx_hash is not None,
            "'final_tx_hash' field is None",
        )
        return cast(str, self._final_remove_allowance_tx_hash)

    @property
    def final_swap_back_tx_hash(self) -> str:
        """Get the final_tx_hash."""
        enforce(
            self._final_swap_back_tx_hash is not None,
            "'final_tx_hash' field is None",
        )
        return cast(str, self._final_swap_back_tx_hash)

    @property
    def participant_to_swap_signature(self) -> Mapping[str, SignaturePayload]:
        """Get the participant_to_swap_signature."""
        enforce(
            self._participant_to_swap_signature is not None,
            "'participant_to_swap_signature' field is None",
        )
        return cast(Mapping[str, SignaturePayload], self._participant_to_swap_signature)

    @property
    def participant_to_add_allowance_validation(self) -> Mapping[str, SignaturePayload]:
        """Get the participant_to_add_allowance_validation."""
        enforce(
            self._participant_to_add_allowance_validation is not None,
            "'participant_to_add_allowance_validation' field is None",
        )
        return cast(
            Mapping[str, SignaturePayload],
            self._participant_to_add_allowance_validation,
        )

    @property
    def participant_to_add_liquidity_validation(self) -> Mapping[str, SignaturePayload]:
        """Get the participant_to_add_liquidity_validation."""
        enforce(
            self._participant_to_add_liquidity_validation is not None,
            "'participant_to_add_liquidity_validation' field is None",
        )
        return cast(
            Mapping[str, SignaturePayload],
            self._participant_to_add_liquidity_validation,
        )

    @property
    def participant_to_remove_liquidity_validation(
        self,
    ) -> Mapping[str, SignaturePayload]:
        """Get the participant_to_remove_liquidity_validation."""
        enforce(
            self._participant_to_remove_liquidity_validation is not None,
            "'participant_to_remove_liquidity_validation' field is None",
        )
        return cast(
            Mapping[str, SignaturePayload],
            self._participant_to_remove_liquidity_validation,
        )

    @property
    def participant_to_remove_allowance_validation(
        self,
    ) -> Mapping[str, SignaturePayload]:
        """Get the participant_to_remove_allowance_validation."""
        enforce(
            self._participant_to_remove_allowance_validation is not None,
            "'participant_to_remove_allowance_validation' field is None",
        )
        return cast(
            Mapping[str, SignaturePayload],
            self._participant_to_remove_allowance_validation,
        )

    @property
    def participant_to_swap_back_validation(self) -> Mapping[str, SignaturePayload]:
        """Get the participant_to_swap_back_validation."""
        enforce(
            self._participant_to_swap_back_validation is not None,
            "'participant_to_swap_back_validation' field is None",
        )
        return cast(
            Mapping[str, SignaturePayload], self._participant_to_swap_back_validation
        )


class LiquidityProvisionAbstractRound(AbstractRound[Event, TransactionType], ABC):
    """Abstract round for the liquidity provision skill."""

    @property
    def period_state(self) -> PeriodState:
        """Return the period state."""
        return cast(PeriodState, self._state)

    def _return_no_majority_event(self) -> Tuple[PeriodState, Event]:
        """
        Trigger the NO_MAJORITY event.

        :return: a new period state and a NO_MAJORITY event
        """
        return self.period_state.reset(), Event.NO_MAJORITY


class TransactionHashBaseRound(
    CollectSameUntilThresholdRound, LiquidityProvisionAbstractRound
):
    """
    This class represents the 'tx-hash' round.

    Input: a period state with the prior round data
    Ouptut: a new period state with the prior round data and the votes for each tx hash

    It schedules the CollectSignatureRound.
    """

    round_id = "tx_hash"
    allowed_tx_type = TransactionHashPayload.transaction_type
    payload_attribute = "tx_hash"

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            state = self.period_state.update(
                participant_to_tx_hash=MappingProxyType(self.collection),
                most_voted_tx_hash=self.most_voted_payload,
            )
            return state, Event.DONE
        if not self.is_majority_possible(
            self.collection, self.period_state.nb_participants
        ):
            return self._return_no_majority_event()
        return None


class TransactionSignatureBaseRound(
    CollectDifferentUntilThresholdRound, LiquidityProvisionAbstractRound
):
    """This class represents the 'abstract_signature' round."""

    round_id = "abstract_signature"
    allowed_tx_type = SignaturePayload.transaction_type
    payload_attribute = "signature"

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        if self.collection_threshold_reached:
            state = self.period_state.update(
                participant_to_signature=MappingProxyType(self.collection),
            )
            return state, Event.DONE
        if not self.is_majority_possible(
            self.collection, self.period_state.nb_participants
        ):
            return self._return_no_majority_event()
        return None


class TransactionSendBaseRound(OnlyKeeperSendsRound, LiquidityProvisionAbstractRound):
    """
    This class represents the finalization Safe round.

    Input: a period state with the prior round data
    Output: a new period state with the prior round data and the hash of the Safe transaction

    It schedules the ValidateTransactionRound.
    """

    round_id = "finalization"
    allowed_tx_type = FinalizationTxPayload.transaction_type
    payload_attribute = "tx_hash"

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        # if reached participant threshold, set the result
        if self.has_keeper_sent_payload:
            state = self.period_state.update(final_tx_hash=self.keeper_payload)
            return state, Event.DONE
        return None


class TransactionValidationBaseRound(VotingRound, LiquidityProvisionAbstractRound):
    """
    This class represents the validate round.

    Input: a period state with the set of participants, the keeper and the Safe contract address.
    Output: a period state with the set of participants, the keeper, the Safe contract address and a validation of the Safe contract address.
    """

    allowed_tx_type = ValidatePayload.transaction_type
    exit_event: Event
    payload_attribute = "vote"

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        # if reached participant threshold, set the result
        if self.positive_vote_threshold_reached:
            state = self.period_state.update(
                participant_to_votes=MappingProxyType(self.collection)
            )
            return state, Event.DONE
        if self.negative_vote_threshold_reached:
            state = self.period_state.update()
            return state, self.exit_event
        if not self.is_majority_possible(
            self.collection, self.period_state.nb_participants
        ):
            return self._return_no_majority_event()
        return None


class SelectKeeperMainRound(
    CollectDifferentUntilAllRound, LiquidityProvisionAbstractRound
):
    """This class represents the select keeper main round."""

    round_id = "select_keeper_main"


class StrategyEvaluationRound(
    CollectSameUntilThresholdRound, LiquidityProvisionAbstractRound
):
    """This class represents the strategy evaluation round.

    Input: a set of participants (addresses)
    Output: a set of participants (addresses) and the strategy

    It schedules the WaitRound or the SwapRound.
    """

    round_id = "strategy_evaluation"
    allowed_tx_type = StrategyEvaluationPayload.transaction_type
    payload_attribute = "strategy"

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            state = self.period_state.update(
                participant_to_strategy=MappingProxyType(self.collection),
                most_voted_strategy=self.most_voted_payload,
            )
            event = (
                Event.DONE
                if self.period_state.most_voted_strategy["action"] == StrategyType.GO
                else Event.WAIT
            )
            return state, event
        if not self.is_majority_possible(
            self.collection, self.period_state.nb_participants
        ):
            return self._return_no_majority_event()
        return None


class WaitRound(LiquidityProvisionAbstractRound):
    """This class represents the wait round."""


class SwapSelectKeeperRound(
    CollectSameUntilThresholdRound, LiquidityProvisionAbstractRound
):
    """This class represents the swap select keeper round."""

    round_id = "swap_select_keeper"


class SwapTransactionHashRound(TransactionHashBaseRound):
    """This class represents the swap transaction hash round."""

    round_id = "swap_tx_hash"


class SwapSignatureRound(TransactionSignatureBaseRound):
    """This class represents the Swap signature round."""

    round_id = "swap_signature"


class SwapSendRound(TransactionSendBaseRound):
    """This class represents the swap send round."""

    round_id = "swap_send"


class SwapValidationRound(TransactionValidationBaseRound):
    """This class represents the swap validation round."""

    round_id = "swap_validation"


class AllowanceCheckRound(
    CollectSameUntilThresholdRound, LiquidityProvisionAbstractRound
):
    """This class represents the AllowanceCheck round."""

    round_id = "allowance_check"
    allowed_tx_type = AllowanceCheckPayload.transaction_type
    payload_attribute = "allowance"

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        # if reached observation threshold, set the result
        if self.threshold_reached:
            state = self.period_state.update(
                participant_to_allowance_check=MappingProxyType(self.collection),
                most_voted_allowance_check=self.most_voted_payload,
            )
            return state, Event.DONE
        return None


class AddAllowanceSelectKeeperRound(
    CollectSameUntilThresholdRound, LiquidityProvisionAbstractRound
):
    """This class represents the AddAllowance select keeper round."""

    round_id = "add_allowance_select_keeper"


class AddAllowanceTransactionHashRound(TransactionHashBaseRound):
    """This class represents the AddAllowance transaction hash round."""

    round_id = "add_allowance_tx_hash"


class AddAllowanceSignatureRound(TransactionSignatureBaseRound):
    """This class represents the AddLiquidity signature round."""

    round_id = "add_allowance_signature"


class AddAllowanceSendRound(TransactionSendBaseRound):
    """This class represents the AddAllowance send round."""

    round_id = "add_allowance_send"


class AddAllowanceValidationRound(TransactionValidationBaseRound):
    """This class represents the AddAllowance validation round."""

    round_id = "add_allowance_validation"


class AddLiquiditySelectKeeperRound(
    CollectSameUntilThresholdRound, LiquidityProvisionAbstractRound
):
    """This class represents the AddLiquidity select keeper round."""

    round_id = "add_liquidity_select_keeper"


class AddLiquidityTransactionHashRound(TransactionHashBaseRound):
    """This class represents the AddLiquidity transaction hash round."""

    round_id = "add_liquidity_tx_hash"


class AddLiquiditySignatureRound(TransactionSignatureBaseRound):
    """This class represents the AddLiquidity signature round."""

    round_id = "add_liquidity_signature"


class AddLiquiditySendRound(TransactionSendBaseRound):
    """This class represents the AddLiquidity send round."""

    round_id = "add_liquidity_send"


class AddLiquidityValidationRound(TransactionValidationBaseRound):
    """This class represents the AddLiquidity validation round."""

    round_id = "add_liquidity_validation"


class RemoveLiquiditySelectKeeperRound(
    CollectSameUntilThresholdRound, LiquidityProvisionAbstractRound
):
    """This class represents the RemoveLiquidity select keeper round."""

    round_id = "remove_liquidity_select_keeper"


class RemoveLiquidityTransactionHashRound(TransactionHashBaseRound):
    """This class represents the RemoveLiquidity transaction hash round."""

    round_id = "remove_liquidity_tx_hash"


class RemoveLiquiditySignatureRound(TransactionSignatureBaseRound):
    """This class represents the RemoveLiquidity signature round."""

    round_id = "remove_liquidity_signature"


class RemoveLiquiditySendRound(TransactionSendBaseRound):
    """This class represents the RemoveLiquidity send round."""

    round_id = "remove_liquidity_send"


class RemoveLiquidityValidationRound(TransactionValidationBaseRound):
    """This class represents the RemoveLiquidity validation round."""

    round_id = "remove_liquidity_validation"


class RemoveAllowanceSelectKeeperRound(
    CollectSameUntilThresholdRound, LiquidityProvisionAbstractRound
):
    """This class represents the RemoveAllowance select keeper round."""

    round_id = "remove_allowance_select_keeper"


class RemoveAllowanceTransactionHashRound(TransactionHashBaseRound):
    """This class represents the RemoveAllowance transaction hash round."""

    round_id = "remove_allowance_tx_hash"


class RemoveAllowanceSignatureRound(TransactionSignatureBaseRound):
    """This class represents the RemoveAllowance signature round."""

    round_id = "remove_allowance_signature"


class RemoveAllowanceSendRound(TransactionSendBaseRound):
    """This class represents the RemoveAllowance send round."""

    round_id = "remove_allowance_send"


class RemoveAllowanceValidationRound(TransactionValidationBaseRound):
    """This class represents the RemoveAllowance validation round."""

    round_id = "remove_allowance_validation"


class SwapBackSelectKeeperRound(
    CollectSameUntilThresholdRound, LiquidityProvisionAbstractRound
):
    """This class represents the SwapBack select keeper round."""

    round_id = "swap_back_select_keeper"


class SwapBackTransactionHashRound(TransactionHashBaseRound):
    """This class represents the SwapBack transaction hash round."""

    round_id = "swap_back_tx_hash"


class SwapBackSignatureRound(TransactionSignatureBaseRound):
    """This class represents the SwapBack signature round."""

    round_id = "swap_back_signature"


class SwapBackSendRound(TransactionSendBaseRound):
    """This class represents the SwapBack send round."""

    round_id = "swap_back_send"


class SwapBackValidationRound(TransactionValidationBaseRound):
    """This class represents the SwapBack validation round."""

    round_id = "swap_back_validation"


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
            Event.DONE: DeploySafeValidationRound,
            Event.EXIT: RandomnessRound,
        },
        DeploySafeValidationRound: {
            Event.DONE: StrategyEvaluationRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
        StrategyEvaluationRound: {
            Event.DONE: SwapTransactionHashRound,
            Event.WAIT: WaitRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
        WaitRound: {
            Event.DONE: StrategyEvaluationRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
        SwapSelectKeeperRound: {
            Event.DONE: SwapTransactionHashRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
        SwapTransactionHashRound: {
            Event.DONE: SwapSignatureRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
            Event.EXIT: SwapSelectKeeperRound,
        },
        SwapSignatureRound: {
            Event.DONE: SwapSendRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
            Event.EXIT: SwapSelectKeeperRound,
        },
        SwapSendRound: {
            Event.DONE: SwapValidationRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
            Event.EXIT: SwapSelectKeeperRound,
        },
        SwapValidationRound: {
            Event.DONE: AllowanceCheckRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
        AllowanceCheckRound: {
            Event.NO_ALLOWANCE: AddAllowanceTransactionHashRound,
            Event.DONE: AddLiquidityTransactionHashRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
        AddAllowanceSelectKeeperRound: {
            Event.DONE: AddAllowanceTransactionHashRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
        AddAllowanceTransactionHashRound: {
            Event.DONE: AddAllowanceSignatureRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
            Event.EXIT: AddAllowanceSelectKeeperRound,
        },
        AddAllowanceSignatureRound: {
            Event.DONE: AddAllowanceSendRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
            Event.EXIT: AddAllowanceSelectKeeperRound,
        },
        AddAllowanceSendRound: {
            Event.DONE: AddAllowanceValidationRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
            Event.EXIT: AddAllowanceSelectKeeperRound,
        },
        AddAllowanceValidationRound: {
            Event.DONE: AddLiquidityTransactionHashRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
        AddLiquiditySelectKeeperRound: {
            Event.DONE: AddLiquidityTransactionHashRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
        AddLiquidityTransactionHashRound: {
            Event.DONE: AddLiquiditySignatureRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
            Event.EXIT: AddLiquiditySelectKeeperRound,
        },
        AddLiquiditySignatureRound: {
            Event.DONE: AddLiquiditySendRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
            Event.EXIT: AddLiquiditySelectKeeperRound,
        },
        AddLiquiditySendRound: {
            Event.DONE: AddLiquidityValidationRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
            Event.EXIT: AddLiquiditySelectKeeperRound,
        },
        AddLiquidityValidationRound: {
            Event.DONE: RemoveLiquidityTransactionHashRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
        RemoveLiquiditySelectKeeperRound: {
            Event.DONE: RemoveLiquidityTransactionHashRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
        RemoveLiquidityTransactionHashRound: {
            Event.DONE: RemoveLiquiditySignatureRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
            Event.EXIT: RemoveLiquiditySelectKeeperRound,
        },
        RemoveLiquiditySignatureRound: {
            Event.DONE: RemoveLiquiditySendRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
            Event.EXIT: RemoveLiquiditySelectKeeperRound,
        },
        RemoveLiquiditySendRound: {
            Event.DONE: RemoveLiquidityValidationRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
            Event.EXIT: RemoveLiquiditySelectKeeperRound,
        },
        RemoveLiquidityValidationRound: {
            Event.DONE: RemoveAllowanceTransactionHashRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
        RemoveAllowanceSelectKeeperRound: {
            Event.DONE: RemoveAllowanceTransactionHashRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
        RemoveAllowanceTransactionHashRound: {
            Event.DONE: RemoveAllowanceSignatureRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
            Event.EXIT: RemoveAllowanceSelectKeeperRound,
        },
        RemoveAllowanceSignatureRound: {
            Event.DONE: RemoveAllowanceSendRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
            Event.EXIT: RemoveAllowanceSelectKeeperRound,
        },
        RemoveAllowanceSendRound: {
            Event.DONE: RemoveAllowanceValidationRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
            Event.EXIT: RemoveAllowanceSelectKeeperRound,
        },
        RemoveAllowanceValidationRound: {
            Event.DONE: SwapBackTransactionHashRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
        SwapBackSelectKeeperRound: {
            Event.DONE: SwapBackTransactionHashRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
        SwapBackTransactionHashRound: {
            Event.DONE: SwapBackSignatureRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
            Event.EXIT: SwapBackSelectKeeperRound,
        },
        SwapBackSignatureRound: {
            Event.DONE: SwapBackSendRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
            Event.EXIT: SwapBackSelectKeeperRound,
        },
        SwapBackSendRound: {
            Event.DONE: SwapBackValidationRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
            Event.EXIT: SwapBackSelectKeeperRound,
        },
        SwapBackValidationRound: {
            Event.DONE: ResetRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
        ResetRound: {
            Event.DONE: RandomnessRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
    }
    event_to_timeout: Dict[Event, float] = {
        Event.EXIT: 5.0,
        Event.ROUND_TIMEOUT: 30.0,
    }
