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

"""Test IO operations."""
import os.path
from pathlib import PosixPath

import joblib
import numpy as np
import pytest
from aea.helpers.ipfs.base import IPFSHashOnly

from packages.valory.skills.apy_estimation_abci.ml.forecasting import (
    init_forecaster,
    train_forecaster,
)
from packages.valory.skills.apy_estimation_abci.ml.io import (
    load_forecaster,
    save_forecaster,
)


class TestIO:
    """Tests for ML io operations."""

    @staticmethod
    def test_save_forecaster(tmp_path: PosixPath) -> None:
        """Test `save_forecaster`."""
        to_save = init_forecaster(0, 0, 0, 0, 0)

        # Test with non-existing path.
        filepath = os.path.join("non-existing", "test.joblib")
        with pytest.raises((NotADirectoryError, FileNotFoundError)):  # type: ignore
            save_forecaster(filepath, to_save)

        # Test with normal path by comparing the hash of the saved file.
        actual_filepath = os.path.join(tmp_path, "actual.joblib")
        save_forecaster(actual_filepath, to_save)
        expected_filepath = actual_filepath.replace("actual", "expected")
        joblib.dump(to_save, expected_filepath)

        hasher = IPFSHashOnly()
        actual_hash = hasher.get(actual_filepath)
        expected_hash = hasher.get(expected_filepath)
        assert actual_hash == expected_hash

    @staticmethod
    def test_hashes_of_saved_forecasters(tmp_path: PosixPath) -> None:
        """Test hashes of `save_forecaster`'s generated files."""
        # has to be > 1
        n_hashes_to_compare = 5
        hashes = []
        dummy_training_data = np.asarray([i for i in range(30)])
        filepath = os.path.join(tmp_path, "forecaster.joblib")

        for _ in range(n_hashes_to_compare):
            # Train & save the forecaster.
            forecaster = train_forecaster(dummy_training_data, 2, 2, 2, 20, 1)
            save_forecaster(filepath, forecaster)
            # Hash the forecaster's file.
            hasher = IPFSHashOnly()
            hashes.append(hasher.get(filepath))

        # See if all the hashes are the same.
        assert all(x == hashes[0] for x in hashes[1:])

    @staticmethod
    def test_load_forecaster(tmp_path: PosixPath, observations: np.ndarray) -> None:
        """Test `load_forecaster`."""
        hyperparameters = 1, 1, 1, 3, 1
        expected = init_forecaster(*hyperparameters)

        # Test with non-existing path.
        filepath = os.path.join("non-existing", "test.joblib")
        with pytest.raises((NotADirectoryError, FileNotFoundError)):  # type: ignore
            load_forecaster(filepath)

        # Test with normal path, by comparing the models' predictions.
        filepath = os.path.join(tmp_path, "test.joblib")
        joblib.dump(expected, filepath)
        actual = load_forecaster(filepath)
        assert expected._get_tags() == actual._get_tags()

        actual_trained = actual.fit(observations)
        expected_trained = expected.fit(observations)
        n_periods = 5
        predictions = []
        for model in (actual_trained, expected_trained):
            predictions.append(model.predict(n_periods))

        np.allclose(*predictions)
