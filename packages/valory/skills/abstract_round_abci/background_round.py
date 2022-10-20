# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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

"""This module contains the background behaviour and round classes."""
from mailbox import Message
from typing import Generator, Callable

from packages.valory.skills.abstract_round_abci.base import BaseTxPayload
from packages.valory.skills.abstract_round_abci.behaviour_utils import BaseBehaviour, AsyncBehaviour


class TerminationPayload(BaseTxPayload):
    pass


class TerminationBehaviour(BaseBehaviour):
    """Defines the behaviour that is responsible for service termination, it runs concurrently with other behaviours."""

    behaviour_id = "termination_behaviour_background"

    _service_owner_address: str

    def async_act(self) -> Generator:
        """Performs the termination logic."""
        signal_present = yield from self.check_for_signal()
        if not signal_present:
            yield from self.sleep(self.params.sleep_time)
            return

        self.context.logger.info("Terminate signal was received, preparing termination transaction.")

        multisend_data = yield from self.get_multisend_payload()
        payload = TerminationPayload(self.context.agent_address, multisend_data)
        yield from self.send_a2a_transaction(payload)
        yield from self.wait_for_termination_majority()

    def check_for_signal(self) -> Generator[None, None, bool]:
        """
        This method checks for the termination signal.

        We check for the signal by looking at the "SafeReceived" events on the safe contract.
        https://github.com/safe-global/safe-contracts/blob/v1.3.0/contracts/common/EtherPaymentFallback.sol#L10
        In order for an SafeReceived event to qualify as a termination signal it has to fulfill the following:
            1. It MUST be sent by the service owner (self._service_owner).
            2. It MUST be 0 value tx.

        :returns: True if the termination signal is found, false otherwise
        """
        pass

    def get_service_owner(self) -> Generator[None, None, str]:
        """Method that returns the service owner."""
        pass

    def get_multisend_payload(self) -> Generator[None, None, str]:
        """Prepares and returns the multisend to hand over safe ownership to the service_owner."""
        pass

    def wait_for_termination_majority(self) -> Generator:
        """
        Wait until we reach majority on the termination transaction.
        :yield: None
        """
        yield from self.wait_for_condition(self._is_termination_majority)

    def _is_termination_majority(self) -> bool:
        """Rely on the round to decide when majority is reached."""
        return self.synchronized_data.db.get("most_voted_termination", None) is not None

    def get_callback_request(self) -> Callable[[Message, "BaseBehaviour"], None]:
        """Wrapper for callback_request(), overridden to avoid mix-ups with normal (non-background) behaviours."""

        def callback_request(
            message: Message, _current_behaviour: BaseBehaviour
        ) -> None:
            """
            This method gets called when a response for a prior request is received.

            Overridden to remove the check that checks whether the behaviour that made the request is still active.
            The received message gets passed to the behaviour that invoked it, in this case it's always the
            background behaviour.

            :param message: the response.
            :param _current_behaviour: not used, left in to satisfy the interface.
            :return: none
            """
            if self.is_stopped:
                self.context.logger.debug(
                    "dropping message as behaviour has stopped: %s", message
                )
                return

            if self.state != AsyncBehaviour.AsyncState.WAITING_MESSAGE:
                self.context.logger.warning(
                    f"could not send message {message} to {self.behaviour_id}"
                )
                return

            self.try_send(message)

        return callback_request

    def is_round_ended(self, round_id: str) -> Callable[[], bool]:
        """
        Get a callable to check whether the current round has ended.

        We consider the background round ended when we have majority on the termination transaction.
        Overriden to allow for the behaviour to send transactions at any time.

        :return: the termination majority callable
        """
        return self._is_termination_majority
