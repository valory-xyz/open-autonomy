# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022-2023 Valory AG
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
from typing import List, Optional, cast
from warnings import filterwarnings

import click
from aea.cli.utils.click_utils import reraise_as_click_exception
from aea.cli.utils.context import Context
from aea.cli.utils.decorators import pass_ctx
from aea.configurations.constants import PACKAGES

from autonomy.analyse.abci.logs import parse_file
from autonomy.analyse.benchmark.aggregate import BlockTypes, aggregate
from autonomy.analyse.handlers import check_handlers
from autonomy.cli.helpers.analyse import list_all_skill_yaml_files, load_package_tree
from autonomy.cli.helpers.docstring import analyse_docstrings
from autonomy.cli.helpers.fsm_spec import check_all as check_all_fsm
from autonomy.cli.helpers.fsm_spec import check_one as check_one_fsm
from autonomy.cli.helpers.fsm_spec import update_one as update_one_fsm
from autonomy.cli.utils.click_utils import (
    PathArgument,
    abci_spec_format_flag,
    sys_path_patch,
)


BENCHMARKS_DIR = Path("./benchmarks.html")

filterwarnings("ignore")


@click.group(name="analyse")
def analyse_group() -> None:
    """Analyse an agent service."""


@analyse_group.command(name="fsm-specs")
@click.option("--package", type=PathArgument())
@click.option("--app-class", type=str)
@click.option("--update", is_flag=True, help="Update FSM definition if check fails.")
@abci_spec_format_flag()
@pass_ctx
def abci_app_specs(
    ctx: Context,
    package: Optional[Path],
    app_class: Optional[str],
    spec_format: str,
    update: bool,
) -> None:
    """Generate ABCI app specs."""

    all_packages = package is None

    # The command expects 'packages_dir' to be named 'packages', so to make import statements to be compatible with
    # the standard Python import machinery. The directory can be outside the working directory from which the command
    # is executed.
    packages_dir = Path(ctx.registry_path)

    # make sure the package_dir is named "packages", otherwise
    # the import of packages.* modules won't work
    if packages_dir.name != PACKAGES:
        raise click.ClickException(
            f"packages directory {packages_dir} is not named '{PACKAGES}'"
        )

    # add parent directory to Python system path so to give priority to the import of packages modules.
    # Note that this is a Click command that is run in a separate Python interpreter, and all the execution paths die
    # with sys.exit in any possible execution, so there are no dangerous side effects. We do not add sys.path
    # patching in the SpecCheck methods as they implicitly assume that the AEA modules in packages are importable
    # using standard Python import machinery).
    with sys_path_patch(packages_dir.parent):
        with reraise_as_click_exception(Exception):
            if all_packages:
                # If package path is not provided check all available packages
                click.echo("Checking all available packages")
                check_all_fsm(packages_dir=packages_dir)
                click.echo("Done")
                return

            if not all_packages and not update:
                click.echo(f"Checking {package}")
                check_one_fsm(
                    package_path=cast(Path, package),
                    app_class=app_class,
                    spec_format=spec_format,
                )
                click.echo("Check successful")
                return

            if not all_packages and update:
                click.echo(f"Updating {package}")
                update_one_fsm(
                    package_path=cast(Path, package),
                    app_class=app_class,
                    spec_format=spec_format,
                )
                click.echo(f"Updated FSM specification for {package}")
                return


@analyse_group.command(name="docstrings")
@click.option(
    "--update",
    is_flag=True,
    default=False,
    help="Update docstrings if required.",
)
@pass_ctx
def docstrings(ctx: Context, update: bool) -> None:
    """Analyse ABCI docstring definitions."""

    packages_dir = Path(ctx.registry_path).resolve()
    needs_update = set()
    abci_compositions = packages_dir.glob("*/skills/*/rounds.py")

    if packages_dir.name != PACKAGES:
        raise click.ClickException(  # pragma: no cover
            f"packages directory {packages_dir} is not named '{PACKAGES}'"
        )

    with sys_path_patch(packages_dir.parent):
        with reraise_as_click_exception(Exception):
            for path in sorted(abci_compositions):
                *_, author, _, skill_name, _ = path.parts
                click.echo(f"Processing skill {skill_name} with author {author}")
                if analyse_docstrings(path, update=update, packages_dir=packages_dir):
                    needs_update.add(str(path))

            if len(needs_update) > 0:
                file_string = "\n".join(sorted(needs_update))
                if not update:
                    raise click.ClickException(
                        f"Following files needs updating.\n\n{file_string}"
                    )
                click.echo(f"\nUpdated following files.\n\n{file_string}")
            else:
                click.echo("No update needed.")


@analyse_group.command(name="logs")
@click.argument("file", type=click.Path(file_okay=True, dir_okay=False, exists=True))
def parse_logs(file: str) -> None:
    """Parse logs of an agent service."""

    with reraise_as_click_exception(Exception):
        parse_file(file)


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

    registry_path = Path(ctx.registry_path)
    with reraise_as_click_exception(
        FileNotFoundError, ValueError, ImportError
    ), sys_path_patch(registry_path.parent):
        load_package_tree(packages_dir=registry_path)
        for yaml_file in list_all_skill_yaml_files(registry_path):
            if yaml_file.parent.name in ignore:
                click.echo(f"Skipping {yaml_file.parent.name}")
                continue

            click.echo(f"Checking {yaml_file.parent.name}")
            check_handlers(
                yaml_file.resolve(),
                common_handlers=common_handlers,
            )


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

    with reraise_as_click_exception(Exception):
        aggregate(path=path, block_type=block_type, period=period, output=Path(output))
