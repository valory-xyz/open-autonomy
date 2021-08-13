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

"""This module contains the transaction payloads for the price_estimation app."""
from enum import Enum

from packages.valory.skills.abstract_round_abci.base_models import BaseTxPayload


class TransactionType(Enum):
    """Enumeration of transaction types."""

    REGISTRATION = "registration"
    OBSERVATION = "observation"
    ESTIMATE = "estimate"


class RegistrationPayload(BaseTxPayload):
    """Represent a transaction payload of type 'registration'."""

    def __init__(self, sender: str) -> None:
        """
        Initialize a 'registration' transaction payload.

        :param sender: the sender (Ethereum) address
        """
        super().__init__(TransactionType.REGISTRATION, sender)


class ObservationPayload(BaseTxPayload):
    """Represent a transaction payload of type 'observation'."""

    def __init__(self, sender: str, observation: float) -> None:
        """Initialize an 'observation' transaction payload.

        :param sender: the sender (Ethereum) address
        :param observation: the observation
        """
        super().__init__(TransactionType.OBSERVATION, sender)
        self._observation = observation

    @property
    def observation(self) -> float:
        """Get the observation."""
        return self._observation


class EstimatePayload(BaseTxPayload):
    """Represent a transaction payload of type 'estimate'."""

    def __init__(self, sender: str, estimate: float) -> None:
        """Initialize an 'estimate' transaction payload.

        :param sender: the sender (Ethereum) address
        :param estimate: the estimate
        """
        super().__init__(TransactionType.ESTIMATE, sender)
        self._estimate = estimate

    @property
    def estimate(self) -> float:
        """Get the estimate."""
        return self._estimate
