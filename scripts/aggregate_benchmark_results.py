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

"""
Script for aggregating results.

To use this script you'll need benchmark data generated from agent runtime. To
generate benchmark data run

make run-oracle
or
make run-oracle-dev

By default this will create a 4 agent runtime where you can wait until all 4 agents
are at the end of the first period (you can wait for more periods if you want) and
then you can stop the runtime. The data will be stored in deployments/build/logs
folder. You can use this script to aggregate this data.

python script/aggregate_benchmark_results.py -p deployments/build/logs

By default script will generate output for all periods but you can specify which
period to generate output for, same goes for block types as well.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
import pandas as pd


BLOCK_TYPES = ("local", "consensus", "total", "all")
HTML_TEMPLATE = """<html>
<head>
    <title>
        Benchmarks
    </title>
    <style>
        *{{
            padding: 0;
            margin: 0;
        }}
        body{{
            padding: 5;
        }}
        td{{
            height: 24px;
            min-width: 96px;
            max-width: fit-content;
            font-size: 14px;
            padding: 3px;
        }}

        th{{
            height: 24px;
            min-width: 96px;
            max-width: fit-content;
            font-size: 14px;
            padding: 3px;
        }}
    </style>
</head>
<body>
    {tables}
</body>
</hmtl>"""

TABLE_TEMPLATE = """
<div style="margin: 16px 8px;">
    <div style="height: 3vh; width: 100%; font-size: 14px;">
        Period: {period} | Block: {block}
    </div>
    {table}
</div>"""


def read_benchmark_data(path: Path) -> List[Dict]:
    """Returns logs."""
    benchmark_data = []
    for agent_dir in list(path.iterdir()):
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
            for block_t in BLOCK_TYPES[:-1]:
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


@click.command("Benchmark Aggregator")
@click.option(
    "--path",
    "-p",
    type=click.types.Path(exists=True, dir_okay=True, resolve_path=True),
    required=True,
)
@click.option(
    "--block-type",
    "-b",
    type=click.Choice(
        choices=("local", "consensus", "total", "all"), case_sensitive=True
    ),
    required=False,
    default="all",
)
@click.option(
    "--period",
    "-d",
    type=int,
    default=-1,
    required=False,
)
@click.option(
    "--output",
    "-o",
    type=click.types.Path(file_okay=True, dir_okay=False, resolve_path=True),
)
def main(path: Path, block_type: str, period: int, output: Optional[Path]) -> None:
    """Main function."""

    path = Path(path)
    benchmark_data = read_benchmark_data(path)
    dataframe = create_dataframe(benchmark_data)

    periods = range(dataframe.period.max()) if period == -1 else (period,)
    blocks = BLOCK_TYPES[:-1] if block_type == "all" else (block_type,)

    tables = ""
    for period_n in periods:
        for block_t in blocks:
            tables += TABLE_TEMPLATE.format(
                table=format_output(dataframe, period_n, block_t),
                period=period_n,
                block=block_t,
            )

    output = Path("./benchmarks.html" if output is None else output).resolve()
    output.write_text(HTML_TEMPLATE.format(tables=tables), encoding="utf-8")


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
