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
from typing import Callable, Dict, List


MAX_COL_LENGTH = 7


def get_file_list() -> List[str]:
    """Returns file list."""
    return glob("./logs/*.json")


def read_benchmarks() -> List[Dict]:
    """Returns logs."""
    return [json.load(open(file, "r", encoding="utf-8")) for file in get_file_list()]


def aggregate_round(round_id: str, benchmarks: List[Dict], aggregate_method: Callable) -> float:
    """Aggregate value for round_id over agents."""
    round_data = map(lambda x: x["data"][round_id], benchmarks)
    return aggregate_method(list(round_data))


def main() -> None:
    """Run main function."""

    print ("\nConsensus Benchmark\n")

    benchmarks = read_benchmarks()
    benchmark = benchmarks[0]
    rounds = benchmark["rounds"]
    columns = ["agent  "] + rounds + ["total"]

    separator = "-|-".join(["-" * len(col) for col in columns])
    header = " | ".join(columns)

    benchmarks += [
        {
            "agent": "separator"
        },
        {
            "agent_address": "average",
            "agent": benchmark["agent"],
            "data":dict([
                (round_id, aggregate_round(round_id, benchmarks, mean))
                for round_id in benchmark["rounds"]
            ])
        },
        {
            "agent": "separator"
        },
        {
            "agent_address": "std_dev",
            "agent": benchmark["agent"],
            "data":dict([
                (round_id, aggregate_round(round_id, benchmarks, stdev))
                for round_id in benchmark["rounds"]
            ])
        }
    ]

    print(header + "\n" + separator)
    for benchmark in benchmarks:
        if benchmark["agent"] == "separator":
            print(separator)
        else:
            benchmark["data"]["total"] = sum(benchmark["data"].values())
            row = " | ".join(
                [benchmark["agent_address"][:MAX_COL_LENGTH]] + [f"{str(benchmark['data'][round_id])[:MAX_COL_LENGTH]}{' '*(len(round_id)-MAX_COL_LENGTH)}" for round_id in columns[1:]])
            print(row)
    print()

if __name__ == "__main__":
    main()
