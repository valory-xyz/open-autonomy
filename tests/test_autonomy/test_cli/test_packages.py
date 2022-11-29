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

from tests.test_autonomy.test_cli.base import BaseCliTest


class TestPackages(BaseCliTest):
    """Test packages command"""

    cli_options = ("packages", "lock")

    def test_lock(self) -> None:
        """Test lock"""

        result = self.run_cli()
        assert result.exit_code == 0
        assert "Updating hashes..." in result.stdout
        assert "Done" in result.stdout

    def test_lock_check(self) -> None:
        """Test lock --check"""

        result = self.run_cli(("--check", ))
        assert result.exit_code == 0
        assert "Verifying packages.json" in result.stdout
        assert "Verification successful" in result.stdout
