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

"""This module contains the transaction payloads for common apps."""
from enum import Enum
from typing import Any, Dict, Optional

from packages.valory.skills.abstract_round_abci.base import BaseTxPayload


class TransactionType(Enum):
    """Enumeration of transaction types."""

    OBSERVATION = "observation"
    ESTIMATE = "estimate"
    TX_HASH = "tx_hash"

    def __str__(self) -> str:
        """Get the string value of the transaction type."""
        return self.value


class TransactionHashPayload(BaseTxPayload):
    """Represent a transaction payload of type 'tx_hash'."""

    transaction_type = TransactionType.TX_HASH

    def __init__(
        self, sender: str, tx_hash: Optional[str] = None, **kwargs: Any
    ) -> None:
        """Initialize an 'tx_hash' transaction payload.

        :param sender: the sender (Ethereum) address
        :param tx_hash: the tx_hash
        :param kwargs: the keyword arguments
        """
        super().__init__(sender, **kwargs)
        self._tx_hash = tx_hash

    @property
    def tx_hash(self) -> Optional[str]:
        """Get the tx_hash."""
        return self._tx_hash

    @property
    def data(self) -> Dict:
        """Get the data."""
        return dict(tx_hash=self.tx_hash) if self.tx_hash is not None else {}


class ObservationPayload(BaseTxPayload):
    """Represent a transaction payload of type 'observation'."""

    transaction_type = TransactionType.OBSERVATION

    def __init__(self, sender: str, observation: float, **kwargs: Any) -> None:
        """Initialize an 'observation' transaction payload.

        :param sender: the sender (Ethereum) address
        :param observation: the observation
        :param kwargs: the keyword arguments
        """
        super().__init__(sender, **kwargs)
        self._observation = observation

    @property
    def observation(self) -> float:
        """Get the observation."""
        return self._observation

    @property
    def data(self) -> Dict:
        """Get the data."""
        return dict(observation=self.observation)


class EstimatePayload(BaseTxPayload):
    """Represent a transaction payload of type 'estimate'."""

    transaction_type = TransactionType.ESTIMATE

    def __init__(self, sender: str, estimate: float, **kwargs: Any) -> None:
        """Initialize an 'estimate' transaction payload.

        :param sender: the sender (Ethereum) address
        :param estimate: the estimate
        :param kwargs: the keyword arguments
        """
        super().__init__(sender, **kwargs)
        self._estimate = estimate

    @property
    def estimate(self) -> float:
        """Get the estimate."""
        return self._estimate

    @property
    def data(self) -> Dict:
        """Get the data."""
        return dict(estimate=self.estimate)
