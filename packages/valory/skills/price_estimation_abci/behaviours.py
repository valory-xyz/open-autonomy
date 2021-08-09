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
from abc import ABC
from functools import partial
from typing import Any, Callable, Generator, cast

from aea.skills.behaviours import FSMBehaviour, State
from aea_ledger_ethereum import EthereumCrypto

from packages.fetchai.protocols.http import HttpMessage
from packages.fetchai.protocols.signing import SigningMessage
from packages.fetchai.protocols.signing.custom_types import RawMessage, Terms
from packages.valory.skills.price_estimation_abci.behaviours_utils import (
    AsyncBehaviour,
    DONE_EVENT,
    WaitForConditionBehaviour,
)
from packages.valory.skills.price_estimation_abci.dialogues import SigningDialogues
from packages.valory.skills.price_estimation_abci.models import (
    BaseTxPayload,
    EstimatePayload,
    ObservationPayload,
    RegistrationPayload,
    Transaction,
)
from packages.valory.skills.price_estimation_abci.tendermint_rpc import BehaviourUtils


class PriceEstimationConsensusBehaviour(FSMBehaviour):
    """This behaviour manages the consensus stages for the price estimation."""

    def setup(self) -> None:
        """Set up the behaviour."""
        # initial delay to wait synchronization with Tendermint
        self.register_state(
            "wait_tendermint",
            WaitForConditionBehaviour(
                condition=self.get_wait_tendermint_rpc_is_ready(),
                name="wait_tendermint",
                skill_context=self.context,
            ),
            initial=True,
        )
        self.register_state(
            "register",
            RegistrationBehaviour(name="register", skill_context=self.context),
        )
        self.register_state(
            "wait_registration_threshold",
            WaitForConditionBehaviour(
                condition=self.wait_registration_threshold,
                name="wait_registration_threshold",
                skill_context=self.context,
            ),
        )
        self.register_state(
            "observe",
            ObserveBehaviour(name="observe", skill_context=self.context),
        )
        self.register_state(
            "wait_observation_threshold",
            WaitForConditionBehaviour(
                condition=self.wait_observation_threshold,
                name="wait_observation_threshold",
                skill_context=self.context,
            ),
        )
        self.register_state(
            "estimate",
            EstimateBehaviour(name="estimate", skill_context=self.context),
        )

        self.register_state(
            "wait_estimate_threshold",
            WaitForConditionBehaviour(
                condition=self.wait_estimate_threshold,
                name="wait_estimate_threshold",
                skill_context=self.context,
            ),
        )

        self.register_state(
            "end",
            EndBehaviour(name="end", skill_context=self.context),
        )

        self.register_transition("wait_tendermint", "register", DONE_EVENT)
        self.register_transition("register", "wait_registration_threshold", DONE_EVENT)
        self.register_transition("wait_registration_threshold", "observe", DONE_EVENT)
        self.register_transition("observe", "wait_observation_threshold", DONE_EVENT)
        self.register_transition("wait_observation_threshold", "estimate", DONE_EVENT)
        self.register_transition("estimate", "wait_estimate_threshold", DONE_EVENT)
        self.register_transition("wait_estimate_threshold", "end", DONE_EVENT)

    def teardown(self) -> None:
        """Tear down the behaviour"""

    def get_wait_tendermint_rpc_is_ready(self) -> Callable:
        """
        Wait Tendermint RPC server is up.

        This method will return a function that returns
        False until 'initial_delay' seconds (a skill parameter)
        have elapsed since the call of the method.

        :return: the function used to wait.
        """

        def _check_time(expected_time: datetime.datetime) -> bool:
            return datetime.datetime.now() > expected_time

        initial_delay = self.context.params.initial_delay
        date = datetime.datetime.now() + datetime.timedelta(0, initial_delay)
        return partial(_check_time, date)

    def wait_registration_threshold(self) -> bool:
        """Wait registration threshold is reached."""
        return self.context.state.current_round.registration_threshold_reached

    def wait_observation_threshold(self) -> bool:
        """Wait observation threshold is reached."""
        return self.context.state.current_round.observation_threshold_reached

    def wait_estimate_threshold(self) -> bool:
        """Wait estimate threshold is reached."""
        return self.context.state.current_round.estimate_threshold_reached


class BaseState(
    AsyncBehaviour, State, BehaviourUtils, ABC
):  # pylint: disable=too-many-ancestors
    """Base class for FSM states."""

    is_programmatically_defined = True

    def __init__(self, **kwargs: Any):  # pylint: disable=super-init-not-called
        """Initialize a base state behaviour."""
        AsyncBehaviour.__init__(self)
        State.__init__(self, **kwargs)

    def handle_signing_failure(self) -> None:
        """Handle signing failure."""
        self.context.logger.error("the transaction could not be signed.")

    def _send_transaction(self, payload: BaseTxPayload) -> Generator:
        """
        Send transaction and wait for the response.

        Steps:
        - Request the signature of the payload to the Decision Maker
        - Send the transaction to the 'price-estimation' app via the Tendermint node,
          and wait/repeat until the transaction is not mined.

        :param: payload: the payload to send
        :yield: the responses
        """
        self._send_signing_request(payload.encode())
        signature = yield from self.wait_for_message()
        if signature is None:
            self.handle_signing_failure()
            return
        signature_bytes = signature.body
        transaction = Transaction(payload, signature_bytes)
        while True:
            response = yield from self.broadcast_tx_commit(transaction.encode())
            response = cast(HttpMessage, response)
            if self._check_transaction_delivered(response):
                # done
                break
            # otherwise, repeat until done

    def _send_signing_request(self, raw_message: bytes) -> None:
        """Send a signing request."""
        signing_dialogues = cast(SigningDialogues, self.context.signing_dialogues)
        signing_msg, _ = signing_dialogues.create(
            counterparty=self.context.decision_maker_address,
            performative=SigningMessage.Performative.SIGN_MESSAGE,
            raw_message=RawMessage(EthereumCrypto.identifier, raw_message),
            terms=Terms(
                ledger_id=EthereumCrypto.identifier,
                sender_address="",
                counterparty_address="",
                amount_by_currency_id={},
                quantities_by_good_id={},
                nonce="",
            ),
        )
        self.context.decision_maker_message_queue.put_nowait(signing_msg)


class RegistrationBehaviour(BaseState):  # pylint: disable=too-many-ancestors
    """Register to the next round."""

    is_programmatically_defined = True

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the behaviour."""
        super().__init__(**kwargs)
        self._is_done: bool = False

    def is_done(self) -> bool:
        """Check whether the state is done."""
        return self._is_done

    def async_act(self) -> None:  # type: ignore
        """
        Do the action.

        Steps:
        - Build a registration transaction
        - Send the transaction and wait for it to be mined
        - Go to the next state.
        """
        self.context.logger.info("Entered in the 'registration' behaviour state")
        payload = RegistrationPayload(self.context.agent_address)
        yield from self._send_transaction(payload)
        self.context.logger.info("'registration' behaviour state is done")
        # set flag 'done' and event to "done"
        self._is_done = True
        self._event = DONE_EVENT


class ObserveBehaviour(BaseState):  # pylint: disable=too-many-ancestors
    """Observe price estimate."""

    is_programmatically_defined = True

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the behaviour."""
        super().__init__(**kwargs)
        self._is_done: bool = False

    def is_done(self) -> bool:
        """Check whether the state is done."""
        return self._is_done

    def async_act(self) -> Generator:
        """
        Do the action.

        Steps:
        - Ask the configured API the price of a currency
        - Build an observation transaction
        - Send the transaction and wait for it to be mined
        - Go to the next state.
        """
        self.context.logger.info("Entered in the 'observation' behaviour state")
        currency_id = self.context.params.currency_id
        convert_id = self.context.params.convert_id
        observation = self.context.price_api.get_price(currency_id, convert_id)
        self.context.logger.info(
            f"Got observation of {currency_id} price in {convert_id} from {self.context.price_api}: {observation}"
        )
        payload = ObservationPayload(self.context.agent_address, observation)
        yield from self._send_transaction(payload)
        self.context.logger.info("'observation' behaviour state is done")
        # set flag 'done' and event to "done"
        self._is_done = True
        self._event = DONE_EVENT


class EstimateBehaviour(BaseState):  # pylint: disable=too-many-ancestors
    """Estimate price."""

    is_programmatically_defined = True

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the behaviour."""
        super().__init__(**kwargs)
        self._is_done: bool = False

    def is_done(self) -> bool:
        """Check whether the state is done."""
        return self._is_done

    def async_act(self) -> Generator:
        """
        Do the action.

        Steps:
        - Run the script to compute the estimate starting from the shared observations
        - Build an estimate transaction
        - Send the transaction and wait for it to be mined
        - Go to the next state.
        """
        self.context.logger.info("Entered in the 'estimate' behaviour state")
        currency_id = self.context.params.currency_id
        convert_id = self.context.params.convert_id
        observation_payloads = self.context.state.current_round.observations
        observations = [obs_payload.observation for obs_payload in observation_payloads]
        self.context.logger.info(
            f"Using observations {observations} to compute the estimate."
        )
        estimate = self.context.estimator.aggregate(observations)
        self.context.logger.info(
            f"Got estimate of {currency_id} price in {convert_id}: {estimate}"
        )
        payload = EstimatePayload(self.context.agent_address, estimate)
        yield from self._send_transaction(payload)
        self.context.logger.info("'estimate' behaviour state is done")
        # set flag 'done' and event to "done"
        self._is_done = True
        self._event = DONE_EVENT


class EndBehaviour(State):
    """Final state."""

    is_programmatically_defined = True

    def is_done(self) -> bool:
        """Check if the behaviour is done."""
        return True

    def act(self) -> None:
        """Do the act."""
        final_estimate = self.context.state.current_round.most_voted_estimate
        self.context.logger.info(f"Consensus reached on estimate: {final_estimate}")
