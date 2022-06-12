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
from typing import Optional, cast

import click
from aea.cli.ipfs_hash import (
    IPFSHashOnly,
    PackageConfiguration,
    PackageType,
    check_hashes,
    load_configuration_object,
    update_hashes,
)
from aea.configurations.base import (
    PACKAGE_TYPE_TO_CONFIG_CLASS as _PACKAGE_TYPE_TO_CONFIG_CLASS,
)

from autonomy.configurations.base import Service as ServiceConfig


PACKAGE_TYPE_TO_CONFIG_CLASS = {
    **_PACKAGE_TYPE_TO_CONFIG_CLASS,
    PackageType.SERVICE: ServiceConfig,
}


def load_configuration(
    package_type: PackageType, package_path: Path
) -> PackageConfiguration:
    """
    Load a configuration, knowing the type and the path to the package root.

    :param package_type: the package type.
    :param package_path: the path to the package root.
    :return: the configuration object.
    """
    configuration_obj = load_configuration_object(
        package_type,
        package_path,
        package_type_config_class=PACKAGE_TYPE_TO_CONFIG_CLASS,
    )
    configuration_obj._directory = package_path  # pylint: disable=protected-access
    return cast(PackageConfiguration, configuration_obj)


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
@click.option("--check", is_flag=True)
def generate_all(
    packages_dir: Path,
    vendor: Optional[str],
    no_wrap: bool,
    check: bool,
) -> None:
    """Generate IPFS hashes."""
    packages_dir = Path(packages_dir).absolute()
    if check:
        return_code = check_hashes(
            packages_dir, no_wrap, vendor=vendor, config_loader=load_configuration
        )
    else:
        return_code = update_hashes(
            packages_dir, no_wrap, vendor=vendor, config_loader=load_configuration
        )
    sys.exit(return_code)


@hash_group.command(name="one")
@click.argument("path", type=click.Path(exists=True, file_okay=True, dir_okay=True))
@click.option("--no-wrap", is_flag=True)
def hash_file(path: str, no_wrap: bool) -> None:
    """Hash a single file/directory."""

    click.echo(f"Path : {path}")
    click.echo(f"Hash : {IPFSHashOnly.get(path, wrap=not no_wrap)}")
