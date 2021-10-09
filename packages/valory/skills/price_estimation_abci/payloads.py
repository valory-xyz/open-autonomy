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
from abc import ABC
from enum import Enum
from typing import Dict

from packages.valory.skills.abstract_round_abci.base import BaseTxPayload


class TransactionType(Enum):
    """Enumeration of transaction types."""

    REGISTRATION = "registration"
    SELECT_KEEPER = "select_keeper"
    DEPLOY_SAFE = "deploy_safe"
    VALIDATE = "validate"
    OBSERVATION = "observation"
    ESTIMATE = "estimate"
    TX_HASH = "tx_hash"
    SIGNATURE = "signature"
    FINALIZATION = "finalization"

    def __str__(self) -> str:
        """Get the string value of the transaction type."""
        return self.value


class BasePriceEstimationPayload(BaseTxPayload, ABC):
    """Base class for the price estimation demo."""


class RegistrationPayload(BasePriceEstimationPayload):
    """Represent a transaction payload of type 'registration'."""

    transaction_type = TransactionType.REGISTRATION


class SelectKeeperPayload(BasePriceEstimationPayload):
    """Represent a transaction payload of type 'select_keeper'."""

    transaction_type = TransactionType.SELECT_KEEPER

    def __init__(self, sender: str, keeper: str) -> None:
        """Initialize an 'select_keeper' transaction payload.

        :param sender: the sender (Ethereum) address
        :param keeper: the keeper selection
        """
        super().__init__(sender)
        self._keeper = keeper

    @property
    def keeper(self) -> str:
        """Get the keeper."""
        return self._keeper

    @property
    def data(self) -> Dict:
        """Get the data."""
        return dict(keeper=self.keeper)


class DeploySafePayload(BasePriceEstimationPayload):
    """Represent a transaction payload of type 'deploy_safe'."""

    transaction_type = TransactionType.DEPLOY_SAFE

    def __init__(self, sender: str, safe_contract_address: str) -> None:
        """Initialize a 'deploy_safe' transaction payload.

        :param sender: the sender (Ethereum) address
        :param safe_contract_address: the Safe contract address
        """
        super().__init__(sender)
        self._safe_contract_address = safe_contract_address

    @property
    def safe_contract_address(self) -> str:
        """Get the Safe contract address."""
        return self._safe_contract_address

    @property
    def data(self) -> Dict:
        """Get the data."""
        return dict(safe_contract_address=self.safe_contract_address)


class ValidatePayload(BasePriceEstimationPayload):
    """Represent a transaction payload of type 'validate'."""

    transaction_type = TransactionType.VALIDATE

    def __init__(self, sender: str, vote: bool) -> None:
        """Initialize an 'validate' transaction payload.

        :param sender: the sender (Ethereum) address
        :param vote: the vote
        """
        super().__init__(sender)
        self._vote = vote

    @property
    def vote(self) -> bool:
        """Get the vote."""
        return self._vote

    @property
    def data(self) -> Dict:
        """Get the data."""
        return dict(vote=self.vote)


class ObservationPayload(BasePriceEstimationPayload):
    """Represent a transaction payload of type 'observation'."""

    transaction_type = TransactionType.OBSERVATION

    def __init__(self, sender: str, observation: float) -> None:
        """Initialize an 'observation' transaction payload.

        :param sender: the sender (Ethereum) address
        :param observation: the observation
        """
        super().__init__(sender)
        self._observation = observation

    @property
    def observation(self) -> float:
        """Get the observation."""
        return self._observation

    @property
    def data(self) -> Dict:
        """Get the data."""
        return dict(observation=self.observation)


class EstimatePayload(BasePriceEstimationPayload):
    """Represent a transaction payload of type 'estimate'."""

    transaction_type = TransactionType.ESTIMATE

    def __init__(self, sender: str, estimate: float) -> None:
        """Initialize an 'estimate' transaction payload.

        :param sender: the sender (Ethereum) address
        :param estimate: the estimate
        """
        super().__init__(sender)
        self._estimate = estimate

    @property
    def estimate(self) -> float:
        """Get the estimate."""
        return self._estimate

    @property
    def data(self) -> Dict:
        """Get the data."""
        return dict(estimate=self.estimate)


class SignaturePayload(BasePriceEstimationPayload):
    """Represent a transaction payload of type 'signature'."""

    transaction_type = TransactionType.SIGNATURE

    def __init__(self, sender: str, signature: str) -> None:
        """Initialize an 'signature' transaction payload.

        :param sender: the sender (Ethereum) address
        :param signature: the signature
        """
        super().__init__(sender)
        self._signature = signature

    @property
    def signature(self) -> str:
        """Get the signature."""
        return self._signature

    @property
    def data(self) -> Dict:
        """Get the data."""
        return dict(signature=self.signature)


class TransactionHashPayload(BasePriceEstimationPayload):
    """Represent a transaction payload of type 'tx_hash'."""

    transaction_type = TransactionType.TX_HASH

    def __init__(self, sender: str, tx_hash: str) -> None:
        """Initialize an 'tx_hash' transaction payload.

        :param sender: the sender (Ethereum) address
        :param tx_hash: the tx_hash
        """
        super().__init__(sender)
        self._tx_hash = tx_hash

    @property
    def tx_hash(self) -> str:
        """Get the tx_hash."""
        return self._tx_hash

    @property
    def data(self) -> Dict:
        """Get the data."""
        return dict(tx_hash=self.tx_hash)


class FinalizationTxPayload(BasePriceEstimationPayload):
    """Represent a transaction payload of type 'finalization'."""

    transaction_type = TransactionType.FINALIZATION

    def __init__(self, sender: str, tx_hash: str) -> None:
        """Initialize an 'finalization' transaction payload.

        :param sender: the sender (Ethereum) address
        :param tx_hash: the 'safe' transaction hash
        """
        super().__init__(sender)
        self._tx_hash = tx_hash

    @property
    def tx_hash(self) -> str:
        """Get the signature."""
        return self._tx_hash

    @property
    def data(self) -> Dict:
        """Get the data."""
        return dict(tx_hash=self.tx_hash)
