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

"""Test tasks for the skill."""

# pylint: skip-file

from typing import Any, Callable

import pytest
from _pytest.monkeypatch import MonkeyPatch

from packages.valory.skills.apy_estimation_abci import tasks
from packages.valory.skills.apy_estimation_abci.tasks import (
    EstimateTask,
    OptimizeTask,
    PrepareBatchTask,
    PreprocessTask,
)
from packages.valory.skills.apy_estimation_abci.tasks import TestTask as _TestTask
from packages.valory.skills.apy_estimation_abci.tasks import (
    TrainTask,
    TransformTask,
    UpdateTask,
)


@pytest.fixture
def no_action() -> Callable[[Any], None]:
    """Create a no-action function."""
    return lambda *_, **__: None


class TestTransformTask:
    """Tests for the `TransformTask`."""

    @staticmethod
    def test_execute(
        monkeypatch: MonkeyPatch, no_action: Callable[[Any], None]
    ) -> None:
        """Test the execute method."""
        monkeypatch.setattr(
            tasks,
            "transform_hist_data",
            no_action,
        )
        TransformTask().execute()


class TestPreprocessTask:
    """Tests for the `PreprocessTask`."""

    @staticmethod
    def test_execute(
        monkeypatch: MonkeyPatch, no_action: Callable[[Any], None]
    ) -> None:
        """Test the execute method."""
        monkeypatch.setattr(
            tasks,
            "prepare_pair_data",
            no_action,
        )
        PreprocessTask().execute()


class TestPrepareBatchTask:
    """Tests for the `PrepareBatchTask`."""

    @staticmethod
    def test_execute(
        monkeypatch: MonkeyPatch, no_action: Callable[[Any], None]
    ) -> None:
        """Test the execute method."""
        monkeypatch.setattr(tasks, "prepare_batch", no_action)
        PrepareBatchTask().execute()


class TestOptimizeTask:
    """Tests for the `OptimizeTask`."""

    @staticmethod
    def test_execute(
        monkeypatch: MonkeyPatch, no_action: Callable[[Any], None]
    ) -> None:
        """Test the execute method."""
        monkeypatch.setattr(tasks, "optimize", no_action)
        OptimizeTask().execute()


class TestTrainTask:
    """Tests for the `TrainTask`."""

    @staticmethod
    def test_execute(
        monkeypatch: MonkeyPatch, no_action: Callable[[Any], None]
    ) -> None:
        """Test the execute method."""
        monkeypatch.setattr(
            tasks,
            "train_forecaster_per_pool",
            no_action,
        )
        TrainTask().execute()


class TestTestTask:
    """Tests for the `TestTask`."""

    @staticmethod
    def test_execute(
        monkeypatch: MonkeyPatch, no_action: Callable[[Any], None]
    ) -> None:
        """Test the execute method."""
        monkeypatch.setattr(
            tasks,
            "test_forecaster_per_pool",
            no_action,
        )
        _TestTask().execute()


class TestUpdateTask:
    """Tests for the `UpdateTask`."""

    @staticmethod
    def test_execute(
        monkeypatch: MonkeyPatch, no_action: Callable[[Any], None]
    ) -> None:
        """Test the execute method."""
        monkeypatch.setattr(
            tasks,
            "update_forecaster_per_pool",
            no_action,
        )
        UpdateTask().execute()


class TestEstimateTask:
    """Tests for the `EstimateTask`."""

    @staticmethod
    def test_execute(
        monkeypatch: MonkeyPatch, no_action: Callable[[Any], None]
    ) -> None:
        """Test the execute method."""
        monkeypatch.setattr(
            tasks,
            "estimate_apy_per_pool",
            no_action,
        )
        EstimateTask().execute()
