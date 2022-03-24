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
from typing import Any, Callable

from _pytest.monkeypatch import MonkeyPatch

from packages.valory.skills.apy_estimation_abci.tasks import OptimizeTask
from packages.valory.skills.apy_estimation_abci.tasks import TestTask as _TestTask
from packages.valory.skills.apy_estimation_abci.tasks import TrainTask, TransformTask


class TestTransformTask:
    """Tests for the `TransformTask`."""

    @staticmethod
    def test_execute(
        monkeypatch: MonkeyPatch, no_action: Callable[[Any], None]
    ) -> None:
        """Test the execute method."""
        monkeypatch.setattr(
            "packages.valory.skills.apy_estimation_abci.tasks.transform_hist_data",
            no_action,
        )
        TransformTask().execute()


class TestOptimizeTask:
    """Tests for the `OptimizeTask`."""

    @staticmethod
    def test_execute(
        monkeypatch: MonkeyPatch, no_action: Callable[[Any], None]
    ) -> None:
        """Test the execute method."""
        monkeypatch.setattr(
            "packages.valory.skills.apy_estimation_abci.tasks.optimize", no_action
        )
        OptimizeTask().execute()


class TestTrainTask:
    """Tests for the `TrainTask`."""

    @staticmethod
    def test_execute(
        monkeypatch: MonkeyPatch, no_action: Callable[[Any], None]
    ) -> None:
        """Test the execute method."""
        monkeypatch.setattr(
            "packages.valory.skills.apy_estimation_abci.tasks.train_forecaster",
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
            "packages.valory.skills.apy_estimation_abci.tasks.test_forecaster",
            no_action,
        )
        _TestTask().execute()
