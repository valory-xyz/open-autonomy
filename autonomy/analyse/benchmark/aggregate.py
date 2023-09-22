# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2023 Valory AG
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
import statistics
from pathlib import Path
from typing import Callable, Dict, List, Tuple, cast

from autonomy.analyse.benchmark.html import (
    BLOCK_TEMPLATE,
    HTML_TEMPLATE,
    TABLE_TEMPLATE,
    TD_TEMPLATE,
    TH_TEMPLATE,
    TROW_TEMPLATE,
)


STATISTICS = {
    "Mean": statistics.mean,
    "Maximum": max,
    "Minimum": min,
}


class BlockTypes:  # pylint: disable=too-few-public-methods
    """Block types."""

    ALL = "all"
    LOCAL = "local"
    CONSENSUS = "consensus"
    TOTAL = "total"

    types = (LOCAL, CONSENSUS, TOTAL)


def read_benchmark_data(
    path: Path,
    block_type: str = BlockTypes.ALL,
    period: int = -1,
) -> Dict[str, Dict[str, List[Dict]]]:
    """Returns logs."""
    benchmark_data: Dict[str, Dict[str, List[Dict]]] = {}
    for agent_dir in path.iterdir():
        benchmark_data[agent_dir.name] = {}
        benchmark_data_files = list(agent_dir.glob("*.json"))
        periods = sorted(
            tuple(map(lambda x: x.name, benchmark_data_files))
            if period == -1
            else (f"{period}.json",)
        )
        for _period in periods:
            period_name, _ = _period.split(".")
            period_data = json.loads((agent_dir / _period).read_text())
            if block_type == BlockTypes.ALL:
                benchmark_data[agent_dir.name][period_name] = period_data
                continue

            benchmark_data[agent_dir.name][period_name] = [
                {
                    "behaviour": behaviour["behaviour"],
                    "data": {block_type: behaviour["data"][block_type]},
                }
                for behaviour in period_data
            ]

    return benchmark_data


def add_statistic(
    name: str,
    aggregator: Callable,
    behaviours: List[str],
    behaviour_history: Dict[str, List[float]],
) -> str:
    """Add a stastic column."""
    rows = TD_TEMPLATE.format(name)
    for behaviour in behaviours:
        rows += TD_TEMPLATE.format(aggregator(behaviour_history[behaviour]))
    return TROW_TEMPLATE.format(rows)


def add_statistics(
    behaviours: List[str],
    behaviour_history: Dict[str, List[float]],
) -> str:
    """Add statistics."""
    tbody = TROW_TEMPLATE.format(
        f"""<td style="text-align: center;" colspan="{len(behaviours)}">Statistics</td>"""
    )
    for name, aggregator in STATISTICS.items():
        tbody += add_statistic(
            name=name,
            aggregator=cast(Callable, aggregator),
            behaviour_history=behaviour_history,
            behaviours=behaviours,
        )
    return tbody


def create_table_data(
    data: Dict[str, List[Dict]],
    blocks: Tuple[str, ...],
) -> Tuple[List[str], List[str], Dict[str, Dict]]:
    """Create table data."""
    periods: List[str] = []
    header_columns: List[str] = ["Period"]
    tables_data: Dict[str, Dict] = {}
    for block in blocks:
        if block not in tables_data:
            tables_data[block] = {}
        for period, behaviours in data.items():
            for behaviour in behaviours:
                if period not in tables_data[block]:
                    tables_data[block][period] = {}
                tables_data[block][period][behaviour["behaviour"]] = behaviour["data"][
                    block
                ]
                if behaviour["behaviour"] not in header_columns:
                    header_columns.append(behaviour["behaviour"])
            if period not in periods:
                periods.append(period)
    return periods, header_columns, tables_data


def create_agent_table(
    agent: str, data: Dict[str, List[Dict]], blocks: Tuple[str, ...]
) -> str:
    """Create agent table."""
    tables = f"""<div style="width: 100%; text-align: center"> Benchmark data for agent {agent}</div>\n"""
    periods, header_columns, tables_data = create_table_data(
        data=data,
        blocks=blocks,
    )
    behaviour_history: Dict[str, List[float]] = {
        behaviour: [] for behaviour in header_columns[1:]
    }
    for block, block_data in tables_data.items():
        thead = "".join(map(TH_TEMPLATE.format, header_columns))
        tbody = ""
        for period in sorted(periods):
            rows = TD_TEMPLATE.format(period)
            for behaviour_name in header_columns[1:]:
                behaviour_history[behaviour_name].append(
                    block_data[period][behaviour_name]
                )
                rows += TD_TEMPLATE.format(block_data[period][behaviour_name])
            tbody += TROW_TEMPLATE.format(rows)
        tbody += add_statistics(
            behaviours=header_columns[1:], behaviour_history=behaviour_history
        )
        tables += BLOCK_TEMPLATE.format(
            table=TABLE_TEMPLATE.format(
                colspan=len(header_columns),
                block_type=block,
                thead=thead,
                tbody=tbody,
            ),
        )
    return tables


def aggregate(path: Path, block_type: str, period: int, output: Path) -> None:
    """Benchmark Aggregator."""
    path = Path(path)
    benchmark_data = read_benchmark_data(
        path,
        block_type=block_type,
        period=period,
    )
    tables = [
        create_agent_table(
            agent=agent,
            data=data,
            blocks=(
                BlockTypes.types if block_type == BlockTypes.ALL else (block_type,)
            ),
        )
        for agent, data in benchmark_data.items()
    ]

    output.write_text(HTML_TEMPLATE.format(tables="".join(tables)), encoding="utf-8")
