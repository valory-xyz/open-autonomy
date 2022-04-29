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

"""Analyse CLI module."""
from pathlib import Path
from typing import Optional
from warnings import filterwarnings

import click

from aea_swarm.analyse.abci.docstrings import (
    check_working_tree_is_dirty,
    process_module,
)
from aea_swarm.analyse.benchmark.aggregate import BlockTypes, aggregate


filterwarnings("ignore")


@click.group(name="analyse")
def analyse_group() -> None:
    """Analyse an AEA project."""


@analyse_group.group(name="abci")
def abci_group() -> None:
    """Analyse ABCI apps."""


@abci_group.command(name="docstrings")
@click.argument(
    "packages_dir",
    type=click.Path(dir_okay=True, file_okay=False, exists=True),
    default=Path("packages/"),
)
@click.option("--check", is_flag=True, default=False)
def docstrings(packages_dir: Path, check: bool) -> None:
    """Analyse ABCI docstring definitions."""

    no_update = set()
    abci_compositions = packages_dir.glob("*/skills/*/rounds.py")
    for path in sorted(abci_compositions):
        click.echo(f"Processing: {path}")
        file = process_module(path)
        if file is not None:
            no_update.add(file)

    if check:
        check_working_tree_is_dirty()
    else:
        if len(no_update) > 0:
            click.echo("\nFollowing files doesn't need to be updated.\n")
            click.echo("\n".join(sorted(no_update)))


@analyse_group.command(name="benchmarks")
@click.argument(
    "path",
    type=click.types.Path(exists=True, dir_okay=True, resolve_path=True),
    required=True,
)
@click.option(
    "--block-type",
    "-b",
    type=click.Choice(choices=(*BlockTypes.types, BlockTypes.ALL), case_sensitive=True),
    default=BlockTypes.ALL,
    required=False,
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
def benchmark(path: Path, block_type: str, period: int, output: Optional[Path]) -> None:
    """Benchmark Aggregator."""

    output = Path("./benchmarks.html" if output is None else output).resolve()

    try:
        aggregate(path=path, block_type=block_type, period=period, output=output)
    except Exception as e:  # pylint: disable=broad-except
        raise click.ClickException(str(e)) from e
