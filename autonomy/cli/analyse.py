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
import importlib
import sys
from pathlib import Path
from typing import List
from warnings import filterwarnings

import click
from aea.cli.utils.context import Context
from aea.cli.utils.decorators import pass_ctx
from aea.configurations.constants import DEFAULT_SKILL_CONFIG_FILE

from autonomy.analyse.abci.app_spec import DFA, SpecCheck
from autonomy.analyse.abci.docstrings import process_module
from autonomy.analyse.abci.logs import parse_file
from autonomy.analyse.benchmark.aggregate import BlockTypes, aggregate
from autonomy.analyse.handlers import check_handlers
from autonomy.cli.utils.click_utils import abci_spec_format_flag


BENCHMARKS_DIR = Path("./benchmarks.html")

filterwarnings("ignore")


@click.group(name="analyse")
def analyse_group() -> None:
    """Analyse an agent service."""


@analyse_group.group(name="abci")
def abci_group() -> None:
    """Analyse ABCI apps of an agent service."""


@abci_group.command(name="generate-app-specs")
@click.argument("app_class", type=str)
@click.argument("output_file", type=click.Path())
@abci_spec_format_flag()
def generate_abci_app_specs(
    app_class: str, output_file: Path, spec_format: str
) -> None:
    """Generate ABCI app specs."""

    module_name, class_name = app_class.rsplit(".", 1)

    # TODO: extract into helper
    try:
        module = importlib.import_module(module_name)
    except Exception as e:
        raise click.ClickException(
            f'Failed to load "{module_name}". Please, verify that '
            "AbciApps and classes are correctly defined within the module. "
        ) from e

    if not hasattr(module, class_name):
        raise click.ClickException(f'Class "{class_name}" is not in "{module_name}".')

    abci_app_cls = getattr(module, class_name)
    output_file = Path(output_file).absolute()
    dfa = DFA.abci_to_dfa(abci_app_cls, app_class)
    dfa.dump(output_file, spec_format)
    click.echo("Done")


@abci_group.command(name="check-app-specs")
@click.option(
    "--check-all", type=bool, is_flag=True, help="Check all available definitions."
)
@click.option(
    "--packages-dir",
    type=click.Path(),
    default=Path.cwd() / "packages",
    help="Path to packages directory; Use with `--check-all` flag",
)
@abci_spec_format_flag()
@click.option("--app-class", type=str, help="Dotted path to app definition class.")
@click.option("--infile", type=click.Path(), help="Path to input file.")
def check_abci_app_specs(
    check_all: bool, packages_dir: Path, spec_format: str, app_class: str, infile: Path
) -> None:
    """Check ABCI app specs."""

    if check_all:
        packages_dir = Path(packages_dir).absolute()
        SpecCheck.check_all(packages_dir)
    else:
        if app_class is None:
            print("Please provide class name for ABCI app.")
            sys.exit(1)

        if infile is None:
            print("Please provide path to specification file.")
            sys.exit(1)

        if SpecCheck.check_one(
            informat=spec_format,
            infile=str(infile),
            classfqn=app_class,
        ):
            print("Check successful")
            sys.exit(0)

        print("Check failed.")
        sys.exit(1)


@abci_group.command(name="docstrings")
@click.argument(
    "packages_dir",
    type=click.Path(dir_okay=True, file_okay=False, exists=True),
    default=Path("packages/"),
)
@click.option("--check", is_flag=True, default=False)
def docstrings(packages_dir: Path, check: bool) -> None:
    """Analyse ABCI docstring definitions."""

    packages_dir = Path(packages_dir)
    needs_update = set()
    abci_compositions = packages_dir.glob("*/skills/*/rounds.py")

    try:
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
    except Exception as e:  # pylint: disable=broad-except
        raise click.ClickException(str(e)) from e


@abci_group.command(name="logs")
@click.argument("file", type=click.Path(file_okay=True, dir_okay=False, exists=True))
def parse_logs(file: Path) -> None:
    """Parse logs of an agent service."""

    try:
        parse_file(str(file))
    except Exception as e:  # pylint: disable=broad-except
        raise click.ClickException(str(e)) from e


@analyse_group.command(name="handlers")
@pass_ctx
@click.option(
    "--common-handlers",
    "-h",
    type=str,
    default=[
        "abci",
    ],
    help="Specify which handlers to check. Eg. -h handler_a -h handler_b -h handler_c",
    multiple=True,
)
@click.option(
    "--ignore",
    "-i",
    type=str,
    default=[
        "abstract_abci",
    ],
    help="Specify which skills to skip. Eg. -i skill_0 -i skill_1 -i skill_2",
    multiple=True,
)
def run_handler_check(
    ctx: Context, ignore: List[str], common_handlers: List[str]
) -> None:
    """Check handler definitions."""

    try:
        for yaml_file in sorted(
            Path(ctx.registry_path).glob(f"*/*/*/{DEFAULT_SKILL_CONFIG_FILE}")
        ):
            if yaml_file.parent.name in ignore:
                click.echo(f"Skipping {yaml_file.parent}")
                continue

            click.echo(f"Checking {yaml_file.parent}")
            check_handlers(
                yaml_file.resolve(),
                common_handlers=common_handlers,
            )
    except (FileNotFoundError, ValueError, ImportError) as e:
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
    default=BENCHMARKS_DIR,
)
def benchmark(path: Path, block_type: str, period: int, output: Path) -> None:
    """Benchmark aggregator."""

    try:
        aggregate(path=path, block_type=block_type, period=period, output=Path(output))
    except Exception as e:  # pylint: disable=broad-except
        raise click.ClickException(str(e)) from e
