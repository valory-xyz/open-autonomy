# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2026 Valory AG
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

"""Tests for ACN node Docker image helper."""

from unittest.mock import MagicMock, patch

from aea_test_autonomy.docker.acn_node import ACNNodeDockerImage


class TestACNNodeWait:  # pylint: disable=too-few-public-methods
    """Test ACNNodeDockerImage.wait() does not mutate set during iteration."""

    def test_wait_no_set_mutation_during_iteration(self) -> None:
        """Test that wait() does not modify the set while iterating over it."""
        config = {
            "AEA_P2P_URI_PUBLIC": "0.0.0.0:5000",
            "AEA_P2P_URI": "0.0.0.0:5000",
            "AEA_P2P_DELEGATE_URI": "0.0.0.0:11000",
            "AEA_P2P_URI_MONITORING": "0.0.0.0:8081",
        }
        image = ACNNodeDockerImage(client=MagicMock(), config=config)

        # Mock socket to simulate all ports are open (connect_ex returns 0)
        mock_sock = MagicMock()
        mock_sock.connect_ex.return_value = 0

        with patch(
            "aea_test_autonomy.docker.acn_node.socket.socket", return_value=mock_sock
        ):
            # This should not raise RuntimeError: Set changed size during iteration
            result = image.wait(max_attempts=5, sleep_rate=0.01)

        assert result is True
