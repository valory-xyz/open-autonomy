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
import traceback
from pathlib import Path
from typing import Callable, Dict, Optional, cast

import click
from aea.cli.ipfs_hash import (
    extend_public_ids,
    hash_file,
    hash_package,
    package_id_and_path,
    sort_configuration_file,
    to_package_id,
    to_v0_string,
    to_v1_string,
)
from aea.configurations.base import PackageConfiguration, PackageType
from aea.configurations.constants import PACKAGE_TYPE_TO_CONFIG_FILE, SCAFFOLD_PACKAGES
from aea.configurations.data_types import PackageId, PublicId
from aea.configurations.loader import load_configuration_object
from aea.helpers.dependency_tree import DependencyTree, dump_yaml, load_yaml
from aea.helpers.fingerprint import update_fingerprint

from autonomy.configurations.base import PACKAGE_TYPE_TO_CONFIG_CLASS


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


def update_hashes(  # pylint: disable=too-many-locals
    packages_dir: Path,
    no_wrap: bool = False,
    vendor: Optional[str] = None,
    config_loader: Callable[
        [PackageType, Path], PackageConfiguration
    ] = load_configuration,
) -> int:
    """Process all AEA packages, update fingerprint, and update hashes.csv files."""
    return_code = 0
    package_hashes: Dict[str, str] = {}

    try:
        public_id_to_hash_mappings: Dict = {}
        dependency_tree = DependencyTree.generate(packages_dir)
        packages = [
            [package_id_and_path(package_id, packages_dir) for package_id in tree_level]
            for tree_level in dependency_tree
        ]
        packages[0] = packages[0] + list(map(to_package_id, SCAFFOLD_PACKAGES))
        for tree_level in packages:
            for package_id, package_path in tree_level:
                click.echo(
                    "Processing package {} of type {}".format(
                        package_path.name, package_id.package_type
                    )
                )

                config_file = package_path / cast(
                    str, PACKAGE_TYPE_TO_CONFIG_FILE.get(package_id.package_type.value)
                )
                item_config, extra_config = load_yaml(config_file)
                if package_id.package_type == PackageType.SERVICE:
                    agent_id = PackageId(
                        PackageType.AGENT, PublicId.from_str(item_config["agent"])
                    )
                    item_config["agent"] = str(
                        PublicId(
                            author=agent_id.author,
                            name=agent_id.name,
                            version=agent_id.version,
                            package_hash=public_id_to_hash_mappings[agent_id],
                        )
                    )
                else:
                    extend_public_ids(item_config, public_id_to_hash_mappings)

                dump_yaml(config_file, item_config, extra_config)

                configuration_obj = config_loader(
                    package_id.package_type.value, package_path
                )
                sort_configuration_file(configuration_obj)
                update_fingerprint(configuration_obj)
                key, package_hash = hash_package(
                    configuration_obj, package_id.package_type, no_wrap=no_wrap
                )
                public_id_to_hash_mappings[package_id] = package_hash

                if vendor is not None and package_id.author != vendor:
                    continue  # pragma: nocover
                package_hashes[key] = package_hash
        click.echo("Done!")

    except Exception:  # pylint: disable=broad-except  # pragma: nocover
        traceback.print_exc()
        return_code = 1

    return return_code


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
    packages_dir = Path(packages_dir).absolute()
    return_code = update_hashes(
        packages_dir, no_wrap, vendor=vendor, config_loader=load_configuration
    )
    sys.exit(return_code)


hash_group.add_command(hash_file)
hash_group.add_command(to_v0_string)
hash_group.add_command(to_v1_string)
