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

"""Override for packages command."""

import sys
from pathlib import Path

import click
from aea.cli.packages import PackageManager, package_manager
from aea.cli.utils.context import Context
from aea.cli.utils.decorators import pass_ctx

from autonomy.cli.hash import load_configuration


@package_manager.command(name="lock")
@click.option(
    "--check",
    is_flag=True,
    help="Check packages.json",
)
@pass_ctx
def lock_packages(ctx: Context, check: bool) -> None:
    """Lock packages"""

    packages_dir = Path(ctx.registry_path)

    try:
        if check:
            packages_dir = Path(ctx.registry_path)
            click.echo("Verifying packages.json")
            return_code = PackageManager.from_dir(packages_dir).verify(
                config_loader=load_configuration
            )

            if return_code:
                click.echo("Verification failed.")
            else:
                click.echo("Verification successful")

            sys.exit(return_code)

        PackageManager(packages_dir).update_package_hashes().dump()
    except Exception as e:  # pylint: disable=broad-except
        raise click.ClickException(str(e)) from e
