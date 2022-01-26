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

"""Test the utils.py module of the skill."""
import os
import tempfile
from unittest import mock

import pytest
from aea.skills.base import SkillContext, AgentContext

from packages.valory.protocols.abci import AbciMessage
from packages.valory.skills.abstract_round_abci.utils import (
    BenchmarkBehaviour,
    BenchmarkBlock,
    BenchmarkBlockTypes,
    BenchmarkTool,
    VerifyDrand,
    locate,
)

from tests.helpers.base import cd
from tests.helpers.constants import ROOT_DIR


DRAND_PUBLIC_KEY: str = "868f005eb8e6e4ca0a47c8a77ceaa5309a47978a7c71bc5cce96366b5d7a569937c529eeda66c7293784a9402801af31"

DRAND_VALUE = {
    "round": 1416669,
    "randomness": "f6be4bf1fa229f22340c1a5b258f809ac4af558200775a67dacb05f0cb258a11",
    "signature": (
        "b44d00516f46da3a503f9559a634869b6dc2e5d839e46ec61a090e3032172954929a5"
        "d9bd7197d7739fe55db770543c71182562bd0ad20922eb4fe6b8a1062ed21df3b68de"
        "44694eb4f20b35262fa9d63aa80ad3f6172dd4d33a663f21179604"
    ),
    "previous_signature": (
        "903c60a4b937a804001032499a855025573040cb86017c38e2b1c3725286756ce8f33"
        "61188789c17336beaf3f9dbf84b0ad3c86add187987a9a0685bc5a303e37b008fba8c"
        "44f02a416480dd117a3ff8b8075b1b7362c58af195573623187463"
    ),
}


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


def setup_mock_context() -> SkillContext:
    """Setup mock skill context"""

    agent_context = AgentContext(*(mock.Mock() for _ in range(13)))
    agent_context._data_dir = os.getcwd()  # pylint: disable=W0212

    skill_context = SkillContext()
    skill_context.set_agent_context(agent_context)

    return skill_context


def setup_benchmark_tool() -> BenchmarkTool:
    """Setup benchmark tool"""

    tool = BenchmarkTool()
    tool._context = setup_mock_context()

    for state_id in "ab":
        benchmark = BenchmarkBehaviour(mock.Mock())
        block_type = BenchmarkBlockTypes.LOCAL
        block = BenchmarkBlock(block_type)
        block.start, block.total_time = 0.0, 1.0
        benchmark.local_data[block_type] = block
        tool.benchmark_data[state_id] = benchmark

    return tool


def test_data() -> None:
    """Test data format benchmark tool"""

    expected = [
        {"behaviour": "a", "data": {"local": 1.0, "total": 1.0}},
        {"behaviour": "b", "data": {"local": 1.0, "total": 1.0}},
    ]

    tool = setup_benchmark_tool()
    assert tool.data == expected


class TestBenchmark:
    """Test the benchmark class."""

    def test_end_2_end(self) -> None:
        """Test end 2 end of the tool."""
        benchmark = BenchmarkTool()

        with pytest.raises(AttributeError):
            benchmark.save()

        benchmark._context = setup_mock_context()
        agent_dir = os.path.join(benchmark.context._get_agent_context().data_dir)  # pylint: disable=W0212
        data_dir = os.path.join(agent_dir, "logs")
        filepath = os.path.join(data_dir, "benchmark.json")

        benchmark.save()

        assert os.path.isdir(data_dir)
        assert os.path.isfile(filepath)
        os.remove(filepath)
        os.rmdir(data_dir)


class TestVerifyDrand:
    """Test DrandVerify."""

    drand_check: VerifyDrand

    def setup(
        self,
    ) -> None:
        """Setup test."""
        self.drand_check = VerifyDrand()

    def test_verify(
        self,
    ) -> None:
        """Test verify method."""

        result, error = self.drand_check.verify(DRAND_VALUE, DRAND_PUBLIC_KEY)
        assert result
        assert error is None

    def test_verify_fails(
        self,
    ) -> None:
        """Test verify method."""

        drand_value = DRAND_VALUE.copy()
        del drand_value["randomness"]
        result, error = self.drand_check.verify(drand_value, DRAND_PUBLIC_KEY)
        assert not result
        assert error == "DRAND dict is missing value for 'randomness'"

        drand_value = DRAND_VALUE.copy()
        drand_value["randomness"] = "".join(
            list(drand_value["randomness"])[:-1] + ["0"]  # type: ignore
        )
        result, error = self.drand_check.verify(drand_value, DRAND_PUBLIC_KEY)
        assert not result
        assert error == "Failed randomness hash check."

        drand_value = DRAND_VALUE.copy()
        with mock.patch.object(
            self.drand_check, "_verify_signature", return_value=False
        ):
            result, error = self.drand_check.verify(drand_value, DRAND_PUBLIC_KEY)

        assert not result
        assert error == "Failed bls.Verify check."
