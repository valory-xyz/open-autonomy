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

"""Script for aggregating results."""


import json
from glob import glob
from statistics import mean, stdev
from typing import Any, Callable, Dict, List
from decimal import Decimal

MAX_COL_LENGTH: int = 7
BENCHMARK_BLOCK_TYPES: List[str] = [
    "local",
    "consensus",
    "total"
]


def get_file_list() -> List[str]:
    """Returns file list."""
    return glob("./logs/*.json")


def read_benchmarks() -> List[Dict]:
    """Returns logs."""
    return [json.load(open(file, "r", encoding="utf-8")) for file in get_file_list()]


def aggregate_behaviour(benchmarks: List[Dict], aggregate_method: Callable) -> float:
    """Aggregate value for a behaviour over agents."""
    return {
        "behaviour": benchmarks[0].get("behaviour"),
        "data": dict([(block_type, aggregate_method([row["data"].get(block_type, 0) for row in benchmarks])) for block_type in BENCHMARK_BLOCK_TYPES])
    }


def pad_column(value: Any, column_name: str) -> str:
    """Pad value with whitespaces according to the `MAX_COL_LENGTH`"""

    if isinstance(value, float) and value <= 1e-4:
        value = 0

    value = str(value)
    if len(value) > MAX_COL_LENGTH:
        return value[:MAX_COL_LENGTH] + ' ' * (len(column_name) - MAX_COL_LENGTH)

    return value + ' ' * (len(column_name) - len(value))


def main() -> None:
    """Run main function."""

    print("\nAgent Benchmark Utility.\n")

    benchmarks = read_benchmarks()
    benchmark = benchmarks[0]
    columns = [behaviour_data["behaviour"] for behaviour_data in benchmark["data"]]
    columns = ["agent  "] + [col if len(col) > MAX_COL_LENGTH else col + ' ' * (
        MAX_COL_LENGTH - len(col)) for col in columns] + ["total"]
    separator = "-|-".join(["-" * len(col) for col in columns])
    header = " | ".join(columns)

    benchmarks += [
        {
            "agent_address": "separator"
        },
        {
            "agent_address": "average",
            "agent": "price_estimation",
            "data": [aggregate_behaviour(col, mean) for col in zip(*[benchmark["data"] for benchmark in benchmarks])]
        },
        {
            "agent_address": "separator"
        },
        {
            "agent_address": "std_dev",
            "agent": "price_estimation",
            "data": [aggregate_behaviour(col, stdev) for col in zip(*[benchmark["data"] for benchmark in benchmarks])]
        }
    ]

    def _display_results_by_block(block_type: str):
        print(f"Block type : {block_type}\n")
        print(header + "\n" + separator)

        for benchmark in benchmarks:
            if benchmark["agent_address"] == "separator":
                print(separator)
                continue

            block_data = [behaviour_data["data"].get(block_type, 0)
                          for behaviour_data in benchmark["data"]]
            block_data = [benchmark["agent_address"], *block_data, sum(block_data)]

            row = " | ".join([pad_column(data, col)
                             for col, data in zip(columns, block_data)])

            print(row)
        print()

    for block_type in BENCHMARK_BLOCK_TYPES:
        _display_results_by_block(block_type)


if __name__ == "__main__":
    main()
