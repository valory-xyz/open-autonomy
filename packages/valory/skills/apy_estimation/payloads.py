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

"""This module contains the transaction payloads for the APY estimation app."""
from abc import ABC
from enum import Enum
from typing import Dict, Optional, Any, Union, List

from packages.valory.skills.abstract_round_abci.base import BaseTxPayload


class TransactionType(Enum):
    """Enumeration of transaction types."""

    REGISTRATION = "registration"
    RANDOMNESS = "randomness"
    SELECT_KEEPER = "select_keeper"
    RESET = "reset"
    FETCHING = "fetching"
    TRANSFORMATION = "transformation"
    PREPROCESS = "preprocess"
    OPTIMIZATION = "optimization"
    TRAINING = "training"
    TESTING = "testing"
    ESTIMATION = "estimation"

    def __str__(self) -> str:
        """Get the string value of the transaction type."""
        return self.value


class BaseAPYPayload(BaseTxPayload, ABC):
    """Base class for the simple abci demo."""

    def __hash__(self) -> int:
        """Hash the payload."""
        return hash(tuple(sorted(self.data.items())))


class RegistrationPayload(BaseAPYPayload):
    """Represent a transaction payload of type 'registration'."""

    transaction_type = TransactionType.REGISTRATION


class FetchingPayload(BaseAPYPayload):
    """Represent a transaction payload of type 'fetching'."""

    transaction_type = TransactionType.FETCHING

    def __init__(self, sender: str, history_hash: str, id_: Optional[str] = None) -> None:
        """Initialize a 'fetching' transaction payload.

        :param sender: the sender (Ethereum) address
        :param history_hash: the fetched history's hash.
        :param id_: the id of the transaction
        """
        super().__init__(sender, id_)
        self._history = history_hash

    @property
    def history(self) -> str:
        """Get the history's hash."""
        return self._history

    @property
    def data(self) -> Dict[str, str]:
        """Get the data."""
        return {"history": self._history}


class TransformationPayload(BaseAPYPayload):
    """Represent a transaction payload of type 'transformation'."""

    transaction_type = TransactionType.TRANSFORMATION

    def __init__(
            self, sender: str, transformation_hash: str, id_: Optional[str] = None
    ) -> None:
        """Initialize a 'transformation' transaction payload.

        :param sender: the sender (Ethereum) address
        :param transformation_hash: the transformation's hash.
        :param id_: the id of the transaction
        """
        super().__init__(sender, id_)
        self._transformation_hash = transformation_hash

    @property
    def transformation(self) -> str:
        """Get the transformation's hash."""
        return self._transformation_hash

    @property
    def data(self) -> Dict[str, str]:
        """Get the data."""
        return {"transformation": self._transformation_hash}


class PreprocessPayload(BaseAPYPayload):
    """Represent a transaction payload of type 'preprocess'."""

    transaction_type = TransactionType.PREPROCESS

    def __init__(
            self, sender: str, train_hash: str, test_hash: str, pair_name: str, id_: Optional[str] = None
    ) -> None:
        """Initialize a 'preprocess' transaction payload.

        :param sender: the sender (Ethereum) address
        :param train_hash: the train data hash.
        :param test_hash: the test data hash.
        :param pair_name: the name of the pool for which the preprocessed data are for.
        :param id_: the id of the transaction
        """
        super().__init__(sender, id_)
        self._train_hash = train_hash
        self._test_hash = test_hash
        self._pair_name = pair_name

    @property
    def train_test_hash(self) -> str:
        """Get the training and testing hash concatenation."""
        return self._train_hash + self._test_hash

    @property
    def pair_name(self) -> str:
        """Get the pool pair's name."""
        return self._pair_name

    @property
    def data(self) -> Dict[str, str]:
        """Get the data."""
        return {"train_test": self.train_test_hash, "pair_name": self._pair_name}


class OptimizationPayload(BaseAPYPayload):
    """Represent a transaction payload of type 'optimization'."""

    transaction_type = TransactionType.OPTIMIZATION

    def __init__(self, sender: str, study_hash: str, best_params: Dict[str, Any], id_: Optional[str] = None) -> None:
        """Initialize an 'optimization' transaction payload.

        :param sender: the sender (Ethereum) address
        :param study_hash: the optimization study's hash.
        :param best_params: the best params of the study.
        :param id_: the id of the transaction
        """
        super().__init__(sender, id_)
        self._study_hash = study_hash
        self._best_params = best_params

    @property
    def study(self) -> str:
        """Get the optimization study's hash."""
        return self._study_hash

    @property
    def best_params(self) -> Dict[str, Any]:
        """Get the best params of the optimization's study."""
        return self._best_params

    @property
    def data(self) -> Dict[str, Union[str, Dict[str, Any]]]:
        """Get the data."""
        return {"study_hash": self._study_hash, "best_params": self._best_params}


class TrainingPayload(BaseAPYPayload):
    """Represent a transaction payload of type 'training'."""

    transaction_type = TransactionType.TRAINING

    def __init__(self, sender: str, model_hash: str, id_: Optional[str] = None) -> None:
        """Initialize a 'training' transaction payload.

        :param sender: the sender (Ethereum) address
        :param model_hash: the model's hash.
        :param id_: the id of the transaction
        """
        super().__init__(sender, id_)
        self._model_hash = model_hash

    @property
    def model(self) -> str:
        """Get the model's hash."""
        return self._model_hash

    @property
    def data(self) -> Dict[str, str]:
        """Get the data."""
        return {"model": self._model_hash}


class TestingPayload(BaseAPYPayload):
    """Represent a transaction payload of type 'testing'."""

    transaction_type = TransactionType.TESTING

    def __init__(self, sender: str, report_hash: str, id_: Optional[str] = None) -> None:
        """Initialize a 'testing' transaction payload.

        :param sender: the sender (Ethereum) address
        :param report_hash: the test's report hash.
        :param id_: the id of the transaction
        """
        super().__init__(sender, id_)
        self._report_hash = report_hash

    @property
    def report_hash(self) -> str:
        """Get the test's report hash."""
        return self._report_hash

    @property
    def data(self) -> Dict[str, str]:
        """Get the data."""
        return {"report_hash": self._report_hash}


class EstimatePayload(BaseAPYPayload):
    """Represent a transaction payload of type 'estimate'."""

    transaction_type = TransactionType.ESTIMATION

    def __init__(self, sender: str, estimation: List[float], id_: Optional[str] = None) -> None:
        """Initialize an 'estimate' transaction payload.

        :param sender: the sender (Ethereum) address
        :param estimation: the estimation.
        :param id_: the id of the transaction
        """
        super().__init__(sender, id_)
        self._estimation = estimation

    @property
    def estimation(self) -> List[float]:
        """Get the estimation."""
        return self._estimation

    @property
    def data(self) -> Dict[str, List[float]]:
        """Get the data."""
        return {"estimation": self._estimation}


class ResetPayload(BaseAPYPayload):
    """Represent a transaction payload of type 'reset'."""

    transaction_type = TransactionType.RESET

    def __init__(
            self, sender: str, period_count: int, id_: Optional[str] = None
    ) -> None:
        """Initialize an 'reset' transaction payload.

        :param sender: the sender (Ethereum) address
        :param period_count: the period count id
        :param id_: the id of the transaction
        """
        super().__init__(sender, id_)
        self._period_count = period_count

    @property
    def period_count(self) -> int:
        """Get the period_count."""
        return self._period_count

    @property
    def data(self) -> Dict:
        """Get the data."""
        return dict(period_count=self.period_count)
