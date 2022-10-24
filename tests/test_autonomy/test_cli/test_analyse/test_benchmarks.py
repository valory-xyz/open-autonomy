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

"""Test `benchmarks` command"""

import json
import os
from contextlib import suppress
from pathlib import Path
from typing import Dict, List, Tuple

from autonomy.analyse.benchmark.aggregate import BlockTypes
from autonomy.deploy.constants import BENCHMARKS_DIR

from tests.test_autonomy.test_cli.base import BaseCliTest


NUMBER_OF_AGENTS = 4
NUMBER_OF_PERIODS = 3
NUMBER_OF_BEHAVIOURS = 3


def generate_benchmark_data(
    number_or_behaviours: int = NUMBER_OF_BEHAVIOURS,
) -> List[Dict]:
    """Generate dummy benchmark data."""

    return [
        {
            "behaviour": f"behaviour_{behaviour}",
            "data": {
                "local": 7.033348083496094e-05,
                "consensus": 3.771540880203247,
                "total": 3.771611213684082,
            },
        }
        for behaviour in range(number_or_behaviours)
    ]


class TestBenchmarks(BaseCliTest):
    """Test benchmarks tool."""

    cli_options: Tuple[str, ...] = ("analyse", "benchmarks")

    benchmarks_dir: Path
    output_file: Path

    def setup(self) -> None:
        """Setup test method."""

        super().setup()

        self.benchmarks_dir = self.t / BENCHMARKS_DIR
        self.benchmarks_dir.mkdir()
        self.output_file = self.t / "benchmarks.html"

        for agent in range(NUMBER_OF_AGENTS):
            agent_dir = self.benchmarks_dir / f"agent_{agent}"
            agent_dir.mkdir()
            for i in range(NUMBER_OF_PERIODS):
                period_file = agent_dir / f"{i}.json"
                period_file.write_text(json.dumps(generate_benchmark_data()))

        os.chdir(self.t)

    def teardown(self) -> None:
        """Teardown test method."""

        super().teardown()

        with suppress(FileNotFoundError):
            os.remove(self.output_file)

    def _run_test(self, block_type: str) -> None:
        """Test run."""

        result = self.run_cli(
            (
                str(self.benchmarks_dir),
                "--output",
                str(self.output_file),
                f"--block-type={block_type}",
            ),
        )

        assert result.exit_code == 0
        assert self.output_file.exists()

        file_content = self.output_file.read_text()
        block_types = [BlockTypes.LOCAL, BlockTypes.CONSENSUS, BlockTypes.TOTAL]

        if block_type == BlockTypes.ALL:
            assert any([f"Block: {b}" in file_content for b in block_types])
        else:
            block_types.remove(block_type)
            assert f"Block: {block_type}" in file_content
            assert any([f"Block: {b}" not in file_content for b in block_types])

    def test_all_blocks(
        self,
    ) -> None:
        """Test with only local blocks."""

        self._run_test(BlockTypes.ALL)

    def test_only_local_blocks(
        self,
    ) -> None:
        """Test with all blocks."""

        self._run_test(BlockTypes.LOCAL)

    def test_only_consensus_blocks(
        self,
    ) -> None:
        """Test with only consensus blocks."""

        self._run_test(BlockTypes.CONSENSUS)

    def test_only_total_blocks(
        self,
    ) -> None:
        """Test with only total blocks."""

        self._run_test(BlockTypes.TOTAL)
