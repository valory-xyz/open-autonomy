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

"""Override for hash command."""

import sys
from pathlib import Path
from typing import Optional
from warnings import warn

import click
from aea.cli.ipfs_hash import hash_file, to_v0_string, to_v1_string

from autonomy.cli.helpers.ipfs_hash import load_configuration, update_hashes


@click.group(name="hash")
def hash_group() -> None:
    """Hashing utils."""


@hash_group.command(name="all")
@click.option(
    "--packages-dir",
    type=click.Path(exists=True, dir_okay=True, file_okay=False),
    default=Path("packages/"),
)
@click.option("--vendor", type=str)
@click.option("--no-wrap", is_flag=True)
def generate_all(
    packages_dir: Path,
    vendor: Optional[str],
    no_wrap: bool,
) -> None:
    """Generate IPFS hashes."""
    message = (
        "`autonomy hash all` command has been deprecated and will be removed on v2.0.0, "
        "please use `autonomy packages lock` command to perform package hash updates"
    )
    warn(
        message=message,
        category=DeprecationWarning,
        stacklevel=2,
    )
    click.echo(message=message)
    packages_dir = Path(packages_dir).absolute()
    return_code = update_hashes(
        packages_dir, no_wrap, vendor=vendor, config_loader=load_configuration
    )
    sys.exit(return_code)


hash_group.add_command(hash_file)
hash_group.add_command(to_v0_string)
hash_group.add_command(to_v1_string)
