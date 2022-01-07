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
from typing import Any, Dict, Optional, Union, cast

from packages.valory.skills.abstract_round_abci.base import BaseTxPayload


class TransactionType(Enum):
    """Enumeration of transaction types."""

    REGISTRATION = "registration"
    RANDOMNESS = "randomness"
    SELECT_KEEPER = "select_keeper"
    RESET = "reset"
    FETCHING = "fetching"
    TRANSFORMATION = "transformation"
    BATCH_PREPARATION = "batch_preparation"
    PREPROCESS = "preprocess"
    OPTIMIZATION = "optimization"
    TRAINING = "training"
    TESTING = "testing"
    UPDATE = "update"
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


class RandomnessPayload(BaseAPYPayload):
    """Represent a transaction payload of type 'randomness'."""

    transaction_type = TransactionType.RANDOMNESS

    def __init__(
        self, sender: str, round_id: int, randomness: str, id_: Optional[str] = None
    ) -> None:
        """Initialize an 'select_keeper' transaction payload.

        :param sender: the sender (Ethereum) address
        :param round_id: the round id
        :param randomness: the randomness
        :param id_: the id of the transaction
        """
        super().__init__(sender, id_)
        self._round_id = round_id
        self._randomness = randomness

    @property
    def round_id(self) -> int:
        """Get the round id."""
        return self._round_id

    @property
    def randomness(self) -> str:
        """Get the randomness."""
        return self._randomness

    @property
    def data(self) -> Dict:
        """Get the data."""
        return dict(round_id=self._round_id, randomness=self._randomness)


class FetchingPayload(BaseAPYPayload):
    """Represent a transaction payload of type 'fetching'."""

    transaction_type = TransactionType.FETCHING

    def __init__(
        self,
        sender: str,
        history: str,
        latest_observation_timestamp: int,
        id_: Optional[str] = None,
    ) -> None:
        """Initialize a 'fetching' transaction payload.

        :param sender: the sender (Ethereum) address
        :param history: the fetched history's hash.
        :param latest_observation_timestamp: the latest observation's timestamp.
        :param id_: the id of the transaction
        """
        super().__init__(sender, id_)
        self._history = history
        self._latest_observation_timestamp = latest_observation_timestamp

    @property
    def history(self) -> str:
        """Get the history's hash."""
        return self._history

    @property
    def latest_observation_timestamp(self) -> int:
        """Get the latest observation's timestamp."""
        return self._latest_observation_timestamp

    @property
    def data(self) -> Dict[str, Union[str, int]]:
        """Get the data."""
        return {
            "history": self._history,
            "latest_observation_timestamp": self._latest_observation_timestamp,
        }


class TransformationPayload(BaseAPYPayload):
    """Represent a transaction payload of type 'transformation'."""

    transaction_type = TransactionType.TRANSFORMATION

    def __init__(
        self, sender: str, transformation: str, id_: Optional[str] = None
    ) -> None:
        """Initialize a 'transformation' transaction payload.

        :param sender: the sender (Ethereum) address
        :param transformation: the transformation's hash.
        :param id_: the id of the transaction
        """
        super().__init__(sender, id_)
        self._transformation_hash = transformation

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

    def __init__(  # pylint: disable=too-many-arguments
        self,
        sender: str,
        pair_name: str,
        train_hash: Optional[str] = None,
        test_hash: Optional[str] = None,
        train_test: Optional[str] = None,
        id_: Optional[str] = None,
    ) -> None:
        """Initialize a 'preprocess' transaction payload.

        :param sender: the sender (Ethereum) address
        :param train_hash: the train data hash.
        :param test_hash: the test data hash.
        :param pair_name: the name of the pool for which the preprocessed data are for.
        :param train_test: the train-test concatenated hash.
        :param id_: the id of the transaction
        """
        super().__init__(sender, id_)
        self._pair_name = pair_name
        self._train_hash = train_hash
        self._test_hash = test_hash
        self._train_test = train_test

        if self._train_test is None:
            if all(var is None for var in (self._train_hash, self._test_hash)):
                raise ValueError(
                    "Either `train_hash` and `test_hash` or `train_test` "
                    "should be given for the `PreprocessPayload`!"
                )
        else:
            self._train_hash = self._test_hash = None

    @property
    def train_test_hash(self) -> str:
        """Get the training and testing hash concatenation."""
        if self._train_test is None:
            hash_ = cast(str, self._train_hash) + cast(str, self._test_hash)
        else:
            hash_ = self._train_test

        return hash_

    @property
    def pair_name(self) -> str:
        """Get the pool pair's name."""
        return self._pair_name

    @property
    def data(self) -> Dict[str, str]:
        """Get the data."""
        return {"train_test": self.train_test_hash, "pair_name": self._pair_name}


class BatchPreparationPayload(BaseAPYPayload):
    """Represent a transaction payload of type 'batch_preparation'."""

    transaction_type = TransactionType.BATCH_PREPARATION

    def __init__(
        self, sender: str, prepared_batch: str, id_: Optional[str] = None
    ) -> None:
        """Initialize a 'batch_preparation' transaction payload.

        :param sender: the sender (Ethereum) address
        :param prepared_batch: the transformation's hash.
        :param id_: the id of the transaction
        """
        super().__init__(sender, id_)
        self._prepared_batch = prepared_batch

    @property
    def prepared_batch(self) -> str:
        """Get the prepared batch's hash."""
        return self._prepared_batch

    @property
    def data(self) -> Dict[str, str]:
        """Get the data."""
        return {"prepared_batch": self._prepared_batch}


class OptimizationPayload(BaseAPYPayload):
    """Represent a transaction payload of type 'optimization'."""

    transaction_type = TransactionType.OPTIMIZATION

    def __init__(
        self,
        sender: str,
        best_params: str,
        id_: Optional[str] = None,
    ) -> None:
        """Initialize an 'optimization' transaction payload.

        :param sender: the sender (Ethereum) address
        :param best_params: the best params of the study.
        :param id_: the id of the transaction
        """
        super().__init__(sender, id_)
        self._best_params = best_params

    @property
    def best_params(self) -> str:
        """Get the best params of the optimization's study."""
        return self._best_params

    @property
    def data(self) -> Dict[str, Union[str, Dict[str, Any]]]:
        """Get the data."""
        return {"best_params": self._best_params}


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
        return {"model_hash": self._model_hash}


class TestingPayload(BaseAPYPayload):
    """Represent a transaction payload of type 'testing'."""

    transaction_type = TransactionType.TESTING

    def __init__(
        self, sender: str, report_hash: str, id_: Optional[str] = None
    ) -> None:
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


class UpdatePayload(BaseAPYPayload):
    """Represent a transaction payload of type 'update'."""

    transaction_type = TransactionType.UPDATE

    def __init__(
        self, sender: str, updated_model_hash: str, id_: Optional[str] = None
    ) -> None:
        """Initialize an 'update' transaction payload.

        :param sender: the sender (Ethereum) address
        :param updated_model_hash: the updated model's hash.
        :param id_: the id of the transaction
        """
        super().__init__(sender, id_)
        self._updated_model_hash = updated_model_hash

    @property
    def updated_model_hash(self) -> str:
        """Get the updated model's hash."""
        return self._updated_model_hash

    @property
    def data(self) -> Dict[str, str]:
        """Get the data."""
        return {"updated_model_hash": self._updated_model_hash}


class EstimatePayload(BaseAPYPayload):
    """Represent a transaction payload of type 'estimate'."""

    transaction_type = TransactionType.ESTIMATION

    def __init__(
        self, sender: str, estimation: float, id_: Optional[str] = None
    ) -> None:
        """Initialize an 'estimate' transaction payload.

        :param sender: the sender (Ethereum) address
        :param estimation: the estimation.
        :param id_: the id of the transaction
        """
        super().__init__(sender, id_)
        self._estimation = estimation

    @property
    def estimation(self) -> float:
        """Get the estimation."""
        return self._estimation

    @property
    def data(self) -> Dict[str, float]:
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
