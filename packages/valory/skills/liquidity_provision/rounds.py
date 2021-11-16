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
    BaseRandomnessRound,
    CollectDifferentUntilAllRound,
    CollectDifferentUntilThresholdRound,
    CollectSameUntilThresholdRound,
    DeploySafeRound,
    RandomnessRound,
    RegistrationRound,
    ResetAndPauseRound,
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
    RESET_TIMEOUT = "reset_timeout"
    WAIT = "wait"


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
        period_count: Optional[int] = None,
        period_setup_params: Optional[Dict] = None,
        most_voted_strategy: Optional[dict] = None,
        most_voted_keeper_address: Optional[str] = None,
        safe_contract_address: Optional[str] = None,
        multisend_contract_address: Optional[str] = None,
        most_voted_tx_hash: Optional[str] = None,
        final_tx_hash: Optional[str] = None,
        participant_to_signature: Optional[Mapping[str, SignaturePayload]] = None,
    ) -> None:
        """Initialize a period state."""
        super().__init__(participants=participants)
        self._period_count = period_count if period_count is not None else 0
        self._period_setup_params = (
            period_setup_params if period_setup_params is not None else {}
        )

        self._most_voted_keeper_address = most_voted_keeper_address
        self._safe_contract_address = safe_contract_address
        self._multisend_contract_address = multisend_contract_address
        self._participant_to_signature = participant_to_signature
        self._most_voted_strategy = most_voted_strategy
        self._most_voted_tx_hash = most_voted_tx_hash
        self._final_tx_hash = final_tx_hash

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

    @property
    def multisend_contract_address(self) -> str:
        """Get the multisend contract address."""
        enforce(
            self._multisend_contract_address is not None,
            "'multisend_contract_address' field is None",
        )
        return cast(str, self._safe_contract_address)

    @property
    def participant_to_signature(self) -> Mapping[str, SignaturePayload]:
        """Get the participant_to_signature."""
        enforce(
            self._participant_to_signature is not None,
            "'participant_to_signature' field is None",
        )
        return cast(
            Mapping[str, SignaturePayload],
            self._participant_to_signature,
        )

    @property
    def most_voted_strategy(self) -> dict:
        """Get the most_voted_strategy."""
        enforce(
            self._most_voted_strategy is not None,
            "'most_voted_strategy' field is None",
        )
        return cast(dict, self._most_voted_strategy)

    def reset(self) -> "PeriodState":
        """Return the initial period state."""
        return PeriodState(self.participants)

    @property
    def most_voted_tx_hash(self) -> str:
        """Get the most_voted_enter_pool_tx_hash."""
        enforce(
            self._most_voted_tx_hash is not None,
            "'most_voted_enter_pool_tx_hash' field is None",
        )
        return cast(str, self._most_voted_tx_hash)

    @property
    def final_tx_hash(self) -> str:
        """Get the final_enter_pool_tx_hash."""
        enforce(
            self._final_tx_hash is not None,
            "'final_enter_pool_tx_hash' field is None",
        )
        return cast(str, self._final_tx_hash)


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

    round_id = "transaction_valid_round"
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


class DeploySafeRandomnessRound(BaseRandomnessRound):
    """Deploy safe randomness round."""

    round_id = "deploy_safe_randomness"


class DeploySafeSelectKeeperRound(
    CollectDifferentUntilAllRound, LiquidityProvisionAbstractRound
):
    """This class represents the select keeper main round."""

    round_id = "deploy_safe_randomness"


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
                else Event.RESET_TIMEOUT
            )
            return state, event
        if not self.is_majority_possible(
            self.collection, self.period_state.nb_participants
        ):
            return self._return_no_majority_event()
        return None


class EnterPoolTransactionHashRound(TransactionHashBaseRound):
    """This class represents the SwapBack transaction hash round."""

    round_id = "enter_pool_tx_hash"


class EnterPoolTransactionSignatureRound(TransactionSignatureBaseRound):
    """This class represents the SwapBack signature round."""

    round_id = "enter_pool_tx_signature"


class EnterPoolTransactionSendRound(TransactionSendBaseRound):
    """This class represents the SwapBack send round."""

    round_id = "enter_pool_tx_send"


class EnterPoolTransactionValidationRound(TransactionValidationBaseRound):
    """This class represents the SwapBack validation round."""

    round_id = "enter_pool_tx_validation"


class EnterPoolRandomnessRound(BaseRandomnessRound):
    """Enter pool randomness round."""

    round_id = "enter_pool_randomness"


class EnterPoolSelectKeeperRound(
    CollectSameUntilThresholdRound, LiquidityProvisionAbstractRound
):
    """This class represents the SwapBack select keeper round."""

    round_id = "enter_pool_select_keeper"


class ExitPoolTransactionHashRound(TransactionHashBaseRound):
    """This class represents the SwapBack transaction hash round."""

    round_id = "exit_pool_tx_hash"


class ExitPoolTransactionSignatureRound(TransactionSignatureBaseRound):
    """This class represents the SwapBack signature round."""

    round_id = "exit_pool_tx_signature"


class ExitPoolTransactionSendRound(TransactionSendBaseRound):
    """This class represents the SwapBack send round."""

    round_id = "exit_pool_tx_send"


class ExitPoolTransactionValidationRound(TransactionValidationBaseRound):
    """This class represents the SwapBack validation round."""

    round_id = "exit_pool_tx_validation"


class ExitPoolRandomnessRound(BaseRandomnessRound):
    """Exit pool randomness round."""

    round_id = "exit_pool_randomness"


class ExitPoolSelectKeeperRound(
    CollectSameUntilThresholdRound, LiquidityProvisionAbstractRound
):
    """This class represents the SwapBack select keeper round."""

    round_id = "exit_pool_select_keeper"


class LiquidityProvisionAbciApp(AbciApp[Event]):
    """Liquidity Provision ABCI application."""

    initial_round_cls: Type[AbstractRound] = RegistrationRound
    transition_function: AbciAppTransitionFunction = {
        RegistrationRound: {Event.DONE: RandomnessRound},
        DeploySafeRandomnessRound: {
            Event.DONE: DeploySafeSelectKeeperRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
        DeploySafeSelectKeeperRound: {
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
            Event.DONE: EnterPoolTransactionHashRound,
            Event.WAIT: ResetAndPauseRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
        EnterPoolTransactionHashRound: {
            Event.DONE: EnterPoolTransactionSignatureRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
        EnterPoolTransactionSignatureRound: {
            Event.DONE: EnterPoolTransactionSendRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
        EnterPoolTransactionSendRound: {
            Event.DONE: EnterPoolTransactionValidationRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
        EnterPoolTransactionValidationRound: {
            Event.DONE: ExitPoolTransactionHashRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
            Event.ROUND_TIMEOUT: EnterPoolRandomnessRound,
        },
        EnterPoolRandomnessRound: {
            Event.DONE: EnterPoolSelectKeeperRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
        EnterPoolSelectKeeperRound: {
            Event.DONE: ExitPoolTransactionHashRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
        ExitPoolTransactionHashRound: {
            Event.DONE: ExitPoolTransactionSignatureRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
        ExitPoolTransactionSignatureRound: {
            Event.DONE: ExitPoolTransactionSendRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
        ExitPoolTransactionSendRound: {
            Event.DONE: ExitPoolTransactionValidationRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
        ExitPoolTransactionValidationRound: {
            Event.DONE: ResetRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
            Event.ROUND_TIMEOUT: ExitPoolRandomnessRound,
        },
        ExitPoolRandomnessRound: {
            Event.DONE: ExitPoolSelectKeeperRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
        ExitPoolSelectKeeperRound: {
            Event.DONE: ExitPoolTransactionHashRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
        ResetRound: {
            Event.DONE: RandomnessRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
        ResetAndPauseRound: {
            Event.DONE: RandomnessRound,
            Event.RESET_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
    }
    event_to_timeout: Dict[Event, float] = {
        Event.EXIT: 5.0,
        Event.ROUND_TIMEOUT: 30.0,
    }
