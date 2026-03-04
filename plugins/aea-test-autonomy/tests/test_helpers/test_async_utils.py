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

"""Tests for async_utils helpers."""

from unittest.mock import patch

from aea_test_autonomy.helpers.async_utils import BaseThreadedAsyncLoop


class TestBaseThreadedAsyncLoopTeardown:  # pylint: disable=too-few-public-methods
    """Test that BaseThreadedAsyncLoop teardown stops the loop."""

    def test_teardown_calls_stop_not_start(self) -> None:
        """Test that teardown_method calls stop() on the loop, not start()."""
        instance = BaseThreadedAsyncLoop()
        instance.setup_method()
        assert instance.loop.is_alive()

        with patch.object(instance.loop, "stop", wraps=instance.loop.stop) as mock_stop:
            instance.teardown_method()
            mock_stop.assert_called_once()

        assert not instance.loop.is_alive()
