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


class RandomnessPayload(BaseAPYPayload):
    """Represent a transaction payload of type 'randomness'."""

    transaction_type = TransactionType.RANDOMNESS

    def __init__(
        self, sender: str, round_id: int, randomness: str, **kwargs: Any
    ) -> None:
        """Initialize an 'select_keeper' transaction payload.

        :param sender: the sender (Ethereum) address
        :param round_id: the round id
        :param randomness: the randomness
        :param kwargs: the keyword arguments
        """
        super().__init__(sender, **kwargs)
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

    def __init__(self, sender: str, history: Optional[str], **kwargs: Any) -> None:
        """Initialize a 'fetching' transaction payload.

        :param sender: the sender (Ethereum) address
        :param history: the fetched history's hash.
        :param kwargs: the keyword arguments
        """
        super().__init__(sender, **kwargs)
        self._history = history

    @property
    def history(self) -> Optional[str]:
        """Get the history's hash."""
        return self._history

    @property
    def data(self) -> Dict[str, Union[None, str, int]]:
        """Get the data."""
        return {"history": self.history if self.history is not None else ""}


class TransformationPayload(BaseAPYPayload):
    """Represent a transaction payload of type 'transformation'."""

    transaction_type = TransactionType.TRANSFORMATION

    def __init__(
        self,
        sender: str,
        transformed_history_hash: Optional[str],
        latest_observation_hist_hash: Optional[str],
        **kwargs: Any
    ) -> None:
        """Initialize a 'transformation' transaction payload.

        :param sender: the sender (Ethereum) address
        :param transformed_history_hash: the transformation's history hash.
        :param latest_observation_hist_hash: the latest observation's history hash.
        :param kwargs: the keyword arguments
        """
        super().__init__(sender, **kwargs)
        self._transformed_history_hash = transformed_history_hash
        self._latest_observation_hist_hash = latest_observation_hist_hash

    @property
    def transformed_history_hash(self) -> Optional[str]:
        """Get the transformation's history hash."""
        return self._transformed_history_hash

    @property
    def latest_observation_hist_hash(self) -> Optional[str]:
        """Get the latest observation's history hash."""
        return self._latest_observation_hist_hash

    @property
    def data(self) -> Dict[str, Optional[str]]:
        """Get the data."""
        return {
            "transformed_history_hash": self.transformed_history_hash
            if self.transformed_history_hash is not None
            else "",
            "latest_observation_hist_hash": self.latest_observation_hist_hash
            if self.latest_observation_hist_hash is not None
            else "",
        }


class PreprocessPayload(BaseAPYPayload):
    """Represent a transaction payload of type 'preprocess'."""

    transaction_type = TransactionType.PREPROCESS

    def __init__(  # pylint: disable=too-many-arguments
        self,
        sender: str,
        train_hash: Optional[str] = None,
        test_hash: Optional[str] = None,
        train_test: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        """Initialize a 'preprocess' transaction payload.

        :param sender: the sender (Ethereum) address
        :param train_hash: the train data hash.
        :param test_hash: the test data hash.
        :param train_test: the train-test concatenated hash.
        :param kwargs: the keyword arguments
        """
        super().__init__(sender, **kwargs)
        self._train_hash = train_hash
        self._test_hash = test_hash
        self._train_test = train_test

        if self._train_test is not None:
            self._train_hash = self._test_hash = None

    @property
    def train_test_hash(self) -> Optional[str]:
        """Get the training and testing hash concatenation."""
        if self._train_test is None and not any(
            hash_ is None for hash_ in (self._train_hash, self._test_hash)
        ):
            return cast(str, self._train_hash) + cast(str, self._test_hash)
        return self._train_test

    @property
    def data(self) -> Dict[str, Optional[str]]:
        """Get the data."""
        return {
            "train_test": self.train_test_hash
            if self.train_test_hash is not None
            else "",
        }


class BatchPreparationPayload(BaseAPYPayload):
    """Represent a transaction payload of type 'batch_preparation'."""

    transaction_type = TransactionType.BATCH_PREPARATION

    def __init__(
        self, sender: str, prepared_batch: Optional[str], **kwargs: Any
    ) -> None:
        """Initialize a 'batch_preparation' transaction payload.

        :param sender: the sender (Ethereum) address
        :param prepared_batch: the transformation's hash.
        :param kwargs: the keyword arguments
        """
        super().__init__(sender, **kwargs)
        self._prepared_batch = prepared_batch

    @property
    def prepared_batch(self) -> Optional[str]:
        """Get the prepared batch's hash."""
        return self._prepared_batch

    @property
    def data(self) -> Dict[str, Optional[str]]:
        """Get the data."""
        return (
            {"prepared_batch": self.prepared_batch}
            if self.prepared_batch is not None
            else {}
        )


class OptimizationPayload(BaseAPYPayload):
    """Represent a transaction payload of type 'optimization'."""

    transaction_type = TransactionType.OPTIMIZATION

    def __init__(self, sender: str, best_params: Optional[str], **kwargs: Any) -> None:
        """Initialize an 'optimization' transaction payload.

        :param sender: the sender (Ethereum) address
        :param best_params: the best params of the study.
        :param kwargs: the keyword arguments
        """
        super().__init__(sender, **kwargs)
        self._best_params = best_params

    @property
    def best_params(self) -> Optional[str]:
        """Get the best params of the optimization's study."""
        return self._best_params

    @property
    def data(self) -> Dict[str, Optional[str]]:
        """Get the data."""
        return {"best_params": self.best_params} if self.best_params is not None else {}


class TrainingPayload(BaseAPYPayload):
    """Represent a transaction payload of type 'training'."""

    transaction_type = TransactionType.TRAINING

    def __init__(self, sender: str, models_hash: Optional[str], **kwargs: Any) -> None:
        """Initialize a 'training' transaction payload.

        :param sender: the sender (Ethereum) address
        :param models_hash: the model's hash.
        :param kwargs: the keyword arguments
        """
        super().__init__(sender, **kwargs)
        self._models_hash = models_hash

    @property
    def models_hash(self) -> Optional[str]:
        """Get the models' hash."""
        return self._models_hash

    @property
    def data(self) -> Dict[str, Optional[str]]:
        """Get the data."""
        return {"models_hash": self.models_hash} if self.models_hash is not None else {}


class TestingPayload(BaseAPYPayload):
    """Represent a transaction payload of type 'testing'."""

    transaction_type = TransactionType.TESTING

    def __init__(self, sender: str, report_hash: Optional[str], **kwargs: Any) -> None:
        """Initialize a 'testing' transaction payload.

        :param sender: the sender (Ethereum) address
        :param report_hash: the test's report hash.
        :param kwargs: the keyword arguments
        """
        super().__init__(sender, **kwargs)
        self._report_hash = report_hash

    @property
    def report_hash(self) -> Optional[str]:
        """Get the test's report hash."""
        return self._report_hash

    @property
    def data(self) -> Dict[str, Optional[str]]:
        """Get the data."""
        return {"report_hash": self.report_hash} if self.report_hash is not None else {}


class UpdatePayload(BaseAPYPayload):
    """Represent a transaction payload of type 'update'."""

    transaction_type = TransactionType.UPDATE

    def __init__(
        self, sender: str, updated_models_hash: Optional[str], **kwargs: Any
    ) -> None:
        """Initialize an 'update' transaction payload.

        :param sender: the sender (Ethereum) address
        :param updated_models_hash: the updated model's hash.
        :param kwargs: the keyword arguments
        """
        super().__init__(sender, **kwargs)
        self._updated_model_hash = updated_models_hash

    @property
    def updated_models_hash(self) -> Optional[str]:
        """Get the updated model's hash."""
        return self._updated_model_hash

    @property
    def data(self) -> Dict[str, Optional[str]]:
        """Get the data."""
        return (
            {"updated_models_hash": self.updated_models_hash}
            if self.updated_models_hash is not None
            else {}
        )


class EstimatePayload(BaseAPYPayload):
    """Represent a transaction payload of type 'estimate'."""

    transaction_type = TransactionType.ESTIMATION

    def __init__(
        self, sender: str, estimations_hash: Optional[str], **kwargs: Any
    ) -> None:
        """Initialize an 'estimate' transaction payload.

        :param sender: the sender (Ethereum) address
        :param estimations_hash: the hash of the estimations.
        :param kwargs: the keyword arguments
        """
        super().__init__(sender, **kwargs)
        self._estimations_hash = estimations_hash

    @property
    def estimations_hash(self) -> Optional[str]:
        """Get the estimations' hash."""
        return self._estimations_hash

    @property
    def data(self) -> Dict[str, Optional[str]]:
        """Get the data."""
        return (
            {"estimations_hash": self.estimations_hash}
            if self.estimations_hash is not None
            else {}
        )


class ResetPayload(BaseAPYPayload):
    """Represent a transaction payload of type 'reset'."""

    transaction_type = TransactionType.RESET

    def __init__(self, sender: str, period_count: int, **kwargs: Any) -> None:
        """Initialize an 'reset' transaction payload.

        :param sender: the sender (Ethereum) address
        :param period_count: the period count id
        :param kwargs: the keyword arguments
        """
        super().__init__(sender, **kwargs)
        self._period_count = period_count

    @property
    def period_count(self) -> int:
        """Get the period_count."""
        return self._period_count

    @property
    def data(self) -> Dict:
        """Get the data."""
        return dict(period_count=self.period_count)
