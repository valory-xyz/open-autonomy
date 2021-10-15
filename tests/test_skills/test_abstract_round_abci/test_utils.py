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

"""Test the utils.py module of the skill."""

from packages.valory.protocols.abci import AbciMessage
from packages.valory.skills.abstract_round_abci.utils import locate

from tests.helpers.base import cd
from tests.helpers.constants import ROOT_DIR


class TestLocate:
    """Test the helper function "locate"."""

    def test_locate(self) -> None:
        """Test the locate function to locate modules."""
        with cd(ROOT_DIR):
            package = locate("packages.valory.protocols.abci.message")
            non_existing_package = locate("packages.valory.protocols.non_existing")
        assert package is not None
        assert non_existing_package is None

    def test_locate_class(self) -> None:
        """Test the locate function to locate classes."""
        with cd(ROOT_DIR):
            expected_class = AbciMessage
            actual_class = locate("packages.valory.protocols.abci.message.AbciMessage")
        # although they are the same class, they are different instances in memory
        # and the build-in default "__eq__" method does not compare the attributes.
        # so compare the names
        assert actual_class is not None
        assert expected_class.__name__ == actual_class.__name__

    def test_locate_with_builtins(self) -> None:
        """Test that locate function returns the built-in."""
        result = locate("int.bit_length")
        assert int.bit_length == result

    def test_locate_when_path_does_not_exist(self) -> None:
        """Test that locate function returns None when the dotted path does not exist."""
        result = locate("not.existing.path")
        assert result is None

        result = locate("ThisClassDoesNotExist")
        assert result is None
