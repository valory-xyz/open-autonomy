# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2024 Valory AG
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

"""This module contains the behaviours, round and payloads for the 'abstract_round_abci' skill."""

import hashlib
import random
from abc import ABC
from math import floor
from typing import Any, Dict, Generator, List, Optional, Type, Union, cast

from packages.valory.protocols.ledger_api.message import LedgerApiMessage
from packages.valory.skills.abstract_round_abci.base import BaseTxPayload
from packages.valory.skills.abstract_round_abci.behaviour_utils import BaseBehaviour
from packages.valory.skills.abstract_round_abci.utils import VerifyDrand


RandomnessObservation = Optional[Dict[str, Union[str, int]]]


drand_check = VerifyDrand()


def random_selection(elements: List[Any], randomness: float) -> str:
    """
    Select a random element from a list.

    :param: elements: a list of elements to choose among
    :param: randomness: a random number in the [0,1) interval
    :return: a randomly chosen element
    """
    if not elements:
        raise ValueError("No elements to randomly select among")
    if randomness < 0 or randomness >= 1:
        raise ValueError("Randomness should lie in the [0,1) interval")
    random_position = floor(randomness * len(elements))
    return elements[random_position]


class RandomnessBehaviour(BaseBehaviour, ABC):
    """Behaviour to collect randomness values from DRAND service for keeper agent selection."""

    payload_class: Type[BaseTxPayload]

    def failsafe_randomness(
        self,
    ) -> Generator[None, None, RandomnessObservation]:
        """
        This methods provides a failsafe for randomness retrieval.

        :return: derived randomness
        :yields: derived randomness
        """
        ledger_api_response = yield from self.get_ledger_api_response(
            performative=LedgerApiMessage.Performative.GET_STATE,  # type: ignore
            ledger_callable="get_block",
            block_identifier="latest",
        )

        if (
            ledger_api_response.performative == LedgerApiMessage.Performative.ERROR
            or "hash" not in ledger_api_response.state.body
        ):
            return None

        randomness = hashlib.sha256(
            cast(str, ledger_api_response.state.body.get("hash")).encode()
            + str(self.params.service_id).encode()
        ).hexdigest()
        return {"randomness": randomness, "round": 0}

    def get_randomness_from_api(
        self,
    ) -> Generator[None, None, RandomnessObservation]:
        """Retrieve randomness from given api specs."""
        api_specs = self.context.randomness_api.get_spec()
        response = yield from self.get_http_response(
            method=api_specs["method"],
            url=api_specs["url"],
        )
        observation = self.context.randomness_api.process_response(response)
        if observation is not None:
            self.context.logger.info("Verifying DRAND values...")
            check, error = drand_check.verify(observation, self.params.drand_public_key)
            if check:
                self.context.logger.info("DRAND check successful.")
            else:
                self.context.logger.error(f"DRAND check failed, {error}.")
                return None
        return observation

    def async_act(self) -> Generator:
        """
        Retrieve randomness from API.

        Steps:
        - Do a http request to the API.
        - Retry until receiving valid values for randomness or retries exceed.
        - If retrieved values are valid continue else generate randomness from chain.
        """
        with self.context.benchmark_tool.measure(self.behaviour_id).local():
            if self.context.randomness_api.is_retries_exceeded():
                self.context.logger.warning("Cannot retrieve randomness from api.")
                self.context.logger.info("Generating randomness from chain...")
                observation = yield from self.failsafe_randomness()
                if observation is None:
                    self.context.logger.error(
                        "Could not generate randomness from chain!"
                    )
                    return
            else:
                self.context.logger.info("Retrieving DRAND values from api...")
                observation = yield from self.get_randomness_from_api()
                self.context.logger.info(f"Retrieved DRAND values: {observation}.")

        if observation:
            payload = self.payload_class(  # type: ignore
                self.context.agent_address,
                round_id=observation["round"],
                randomness=observation["randomness"],
            )
            with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
                yield from self.send_a2a_transaction(payload)
                yield from self.wait_until_round_end()

            self.set_done()
        else:
            self.context.logger.error(
                f"Could not get randomness from {self.context.randomness_api.api_id}"
            )
            yield from self.sleep(
                self.context.randomness_api.retries_info.suggested_sleep_time
            )
            self.context.randomness_api.increment_retries()

    def clean_up(self) -> None:
        """
        Clean up the resources due to a 'stop' event.

        It can be optionally implemented by the concrete classes.
        """
        self.context.randomness_api.reset_retries()


class SelectKeeperBehaviour(BaseBehaviour, ABC):
    """Select the keeper agent."""

    payload_class: Type[BaseTxPayload]

    def _select_keeper(self) -> str:
        """
        Select a new keeper randomly.

        1. Sort the list of participants who are not blacklisted as keepers.
        2. Randomly shuffle it.
        3. Pick the first keeper in order.
        4. If he has already been selected, pick the next one.

        :return: the selected keeper's address.
        """
        # Get all the participants who have not been blacklisted as keepers
        non_blacklisted = (
            self.synchronized_data.participants
            - self.synchronized_data.blacklisted_keepers
        )
        if not non_blacklisted:
            raise RuntimeError(
                "Cannot continue if all the keepers have been blacklisted!"
            )

        # Sorted list of participants who are not blacklisted as keepers
        relevant_set = sorted(list(non_blacklisted))

        # Random seeding and shuffling of the set
        random.seed(self.synchronized_data.keeper_randomness)
        random.shuffle(relevant_set)

        # If the keeper is not set yet, pick the first address
        keeper_address = relevant_set[0]

        # If the keeper has been already set, select the next.
        if (
            self.synchronized_data.is_keeper_set
            and len(self.synchronized_data.participants) > 1
        ):
            old_keeper_index = relevant_set.index(
                self.synchronized_data.most_voted_keeper_address
            )
            keeper_address = relevant_set[(old_keeper_index + 1) % len(relevant_set)]

        self.context.logger.info(f"Selected a new keeper: {keeper_address}.")

        return keeper_address

    def async_act(self) -> Generator:
        """
        Do the action.

        Steps:
        - Select a keeper randomly.
        - Send the transaction with the keeper and wait for it to be mined.
        - Wait until ABCI application transitions to the next round.
        - Go to the next behaviour state (set done event).
        """

        with self.context.benchmark_tool.measure(self.behaviour_id).local():
            payload = self.payload_class(  # type: ignore
                self.context.agent_address, self._select_keeper()
            )

        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()
