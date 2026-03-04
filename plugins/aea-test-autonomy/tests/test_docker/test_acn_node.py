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


class TestACNNodeWait:
    """Test ACNNodeDockerImage.wait() behaviour."""

    @staticmethod
    def _make_image() -> ACNNodeDockerImage:
        """Create an ACNNodeDockerImage with default config."""
        config = {
            "AEA_P2P_URI_PUBLIC": "0.0.0.0:5000",
            "AEA_P2P_URI": "0.0.0.0:5000",
            "AEA_P2P_DELEGATE_URI": "0.0.0.0:11000",
            "AEA_P2P_URI_MONITORING": "0.0.0.0:8081",
        }
        return ACNNodeDockerImage(client=MagicMock(), config=config)

    def test_wait_connects_all_uris(self) -> None:
        """Test that wait() successfully connects all URIs."""
        image = self._make_image()
        mock_sock = MagicMock()
        mock_sock.__enter__ = MagicMock(return_value=mock_sock)
        mock_sock.__exit__ = MagicMock(return_value=False)
        mock_sock.connect_ex.return_value = 0

        with patch(
            "aea_test_autonomy.docker.acn_node.socket.socket",
            return_value=mock_sock,
        ):
            result = image.wait(max_attempts=5, sleep_rate=0.01)

        assert result is True

    def test_wait_closes_socket_on_connect_exception(self) -> None:
        """Test that socket is closed even when connect_ex raises."""
        image = self._make_image()
        mock_sock = MagicMock()
        mock_sock.__enter__ = MagicMock(return_value=mock_sock)
        mock_sock.__exit__ = MagicMock(return_value=False)
        mock_sock.connect_ex.side_effect = OSError("connection error")

        with patch(
            "aea_test_autonomy.docker.acn_node.socket.socket",
            return_value=mock_sock,
        ):
            image.wait(max_attempts=1, sleep_rate=0.01)

        # Context manager __exit__ must be called (ensures socket cleanup)
        mock_sock.__exit__.assert_called()
