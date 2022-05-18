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

from aea_swarm.analyse.abci.docstrings import process_module
from aea_swarm.analyse.abci.logs import parse_file
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

    needs_update = set()
    abci_compositions = packages_dir.glob("*/skills/*/rounds.py")

    for path in sorted(abci_compositions):
        click.echo(f"Processing: {path}")
        if process_module(path, check=check):
            needs_update.add(str(path))

    if len(needs_update) > 0:
        file_string = "\n".join(sorted(needs_update))
        if check:
            raise click.ClickException(
                f"Following files needs updating.\n\n{file_string}"
            )
        click.echo(f"\nUpdated following files.\n\n{file_string}")
    else:
        click.echo("No update needed.")


@abci_group.command(name="logs")
@click.argument("file", type=click.Path(file_okay=True, dir_okay=False, exists=True))
def parse_logs(file: Path) -> None:
    """Parse logs."""

    try:
        parse_file(str(file))
    except Exception as e:  # pylint: disable=broad-except
        raise click.ClickException(str(e)) from e


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
