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

"""Tools for aggregating benchmark results."""

import json
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from autonomy.analyse.benchmark.html import HTML_TEMPLATE, TABLE_TEMPLATE


class BlockTypes:  # pylint: disable=too-few-public-methods
    """Block types."""

    ALL = "all"
    LOCAL = "local"
    CONSENSUS = "consensus"
    TOTAL = "total"

    types = ("local", "consensus", "total")


def read_benchmark_data(path: Path) -> List[Dict]:
    """Returns logs."""
    benchmark_data = []
    for agent_dir in path.iterdir():
        agent_benchmark_data: Dict[str, Any] = {}
        agent_benchmark_data["name"] = agent_dir.name
        agent_benchmark_data["data"] = dict(
            map(
                lambda path: (
                    int(path.name.replace(".json", "")),
                    json.loads(path.read_text()),
                ),
                agent_dir.glob("*.json"),
            )
        )
        benchmark_data.append(agent_benchmark_data)
    return benchmark_data


def create_dataframe(data: List[Dict]) -> pd.DataFrame:
    """Create pandas.DataFrame object from benchmark data."""

    rows = []
    behaviours = [behaviour_data["behaviour"] for behaviour_data in data[0]["data"][0]]
    cols = ["agent", "period", "block_type", *behaviours]

    for agent in data:
        for period_n, period_data in agent["data"].items():
            for block_t in BlockTypes.types:
                rows.append(
                    {
                        "agent": agent["name"],
                        "period": period_n,
                        "block_type": block_t,
                        **{
                            behaviour_data["behaviour"]: behaviour_data["data"].get(
                                block_t, 0.0
                            )
                            for behaviour_data in period_data
                        },
                    }
                )

    return pd.DataFrame(
        data=rows,
    )[cols]


def format_output(df: pd.DataFrame, period: int, block_type: str) -> str:
    """Format output from given dataframe and parameters"""

    df = df.copy(deep=True).fillna(value=0.0)
    df = df[df["period"] == period]
    df = df[df["block_type"] == block_type]

    del df["period"]
    del df["block_type"]

    time_df = df[df.columns[1:]]
    stats_df = pd.DataFrame(
        data=[
            ["mean", *time_df.mean().values],
            ["median", *time_df.median().values],
            ["std_dev", *time_df.std().values],
        ],
        columns=df.columns,
    )

    output_df = pd.concat((df, stats_df))
    return output_df.to_html(index=False, justify="left")


def aggregate(path: Path, block_type: str, period: int, output: Path) -> None:
    """Benchmark Aggregator."""

    path = Path(path)
    benchmark_data = read_benchmark_data(path)
    dataframe = create_dataframe(benchmark_data)

    periods = range(dataframe.period.max()) if period == -1 else (period,)
    blocks = BlockTypes.types if block_type == BlockTypes.ALL else (block_type,)

    tables = ""
    for period_n in periods:
        for block_t in blocks:
            tables += TABLE_TEMPLATE.format(
                table=format_output(dataframe, period_n, block_t),
                period=period_n,
                block=block_t,
            )

    output.write_text(HTML_TEMPLATE.format(tables=tables), encoding="utf-8")
