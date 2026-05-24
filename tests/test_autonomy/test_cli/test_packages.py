# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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

"""Test for packages command"""

from collections import namedtuple
from typing import Any
from unittest import mock

from autonomy.cli.packages import get_package_manager

from tests.test_autonomy.test_cli.base import BaseCliTest


class TestPackages(BaseCliTest):
    """Test packages command"""

    cli_options = ("packages", "lock")

    def test_lock(self) -> None:
        """Test lock"""

        target = "autonomy.cli.packages.get_package_manager"
        with mock.patch(target, return_value=mock.MagicMock()) as m:
            with mock.patch("sys.exit") as sys_exit_mock:
                result = self.run_cli()
                assert result.exit_code == 0
                assert "Updating hashes..." in result.stdout
                m.assert_called_once()
                assert "Done" in result.stdout
                sys_exit_mock.assert_called_with(0)

    def test_lock_check(self) -> None:
        """Test lock --check"""

        ctr = 0

        def side_effect(*args: Any, **kwargs: Any) -> Any:
            nonlocal ctr
            if ctr == 0:
                ctr += 1
                return get_package_manager(*args, **kwargs)
            return mock.MagicMock()

        target = "autonomy.cli.packages.get_package_manager"
        with mock.patch(target, side_effect=side_effect):
            with mock.patch("sys.exit") as sys_exit_mock:
                result = self.run_cli(("--check",))
                assert result.exit_code == 0
                assert "Verifying packages.json" in result.stdout
                assert "Verification successful" in result.stdout
                sys_exit_mock.assert_called_with(0)

    def test_lock_check_fail(self) -> None:
        """Test lock --check failure"""

        DummyPackageManager = namedtuple("DummyPackageManager", "verify")
        return_value = DummyPackageManager(lambda *_, **__: 1)
        target = "autonomy.cli.packages.get_package_manager"
        with mock.patch(target, return_value=return_value):
            result = self.run_cli(("--check",))
            assert result.exit_code == 1
            assert "Verification failed." in result.stdout
