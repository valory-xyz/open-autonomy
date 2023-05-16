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

"""Override for packages command."""

import sys
from pathlib import Path
from typing import List, Tuple, cast
from warnings import warn

import click
from aea.cli.packages import package_manager, package_type_selector_prompt
from aea.cli.utils.click_utils import reraise_as_click_exception
from aea.cli.utils.context import Context
from aea.cli.utils.decorators import pass_ctx
from aea.configurations.base import PackageConfiguration
from aea.configurations.constants import PACKAGE_TYPE_TO_CONFIG_FILE
from aea.configurations.data_types import PackageId, PackageType
from aea.helpers.dependency_tree import dump_yaml, load_yaml
from aea.package_manager.base import (
    BasePackageManager,
    DepedencyMismatchErrors,
    PackageFileNotValid,
)
from aea.package_manager.v0 import PackageManagerV0 as BasePackageManagerV0
from aea.package_manager.v1 import PackageManagerV1 as BasePackageManagerV1

from autonomy.cli.helpers.ipfs_hash import load_configuration
from autonomy.configurations.base import Service


@package_manager.command(name="lock")
@click.option(
    "--check",
    is_flag=True,
    help="Check that fingerprints in packages.json match the local packages",
)
@click.option(
    "--skip-missing",
    is_flag=True,
    help="Skip packages missing from the `packages.json` file.",
)
@pass_ctx
def lock_packages(ctx: Context, check: bool, skip_missing: bool) -> None:
    """Lock local packages."""

    packages_dir = Path(ctx.registry_path)

    with reraise_as_click_exception(Exception):
        if check:
            click.echo("Verifying packages.json")
            return_code = get_package_manager(packages_dir).verify()

            if return_code:
                click.echo("Verification failed.")
            else:
                click.echo("Verification successful")

            sys.exit(return_code)

        click.echo("Updating hashes...")
        get_package_manager(packages_dir).update_package_hashes(
            selector_prompt=package_type_selector_prompt,
            skip_missing=skip_missing,
        ).dump()
        click.echo("Done")


def get_package_manager(packages_dir: Path) -> BasePackageManager:
    """Get package manager."""

    try:
        return PackageManagerV1.from_dir(
            packages_dir=packages_dir, config_loader=load_configuration
        )
    except PackageFileNotValid:
        warn(
            "The provided `packages.json` still follows an older format which will be deprecated on v2.0.0",
            DeprecationWarning,
            stacklevel=2,
        )
        click.echo(
            "The provided `packages.json` still follows an older format which will be deprecated on v2.0.0"
        )
        return PackageManagerV0.from_dir(
            packages_dir=packages_dir, config_loader=load_configuration
        )


class _PackageManagerWithServicePatch(BasePackageManager):
    """Patch package manager for service component."""

    def update_dependencies(self, package_id: PackageId) -> None:
        """Update dependencies."""

        if package_id.package_type != PackageType.SERVICE:  # pragma: nocover
            super().update_dependencies(package_id=package_id)
            return

        package_path = self.package_path_from_package_id(
            package_id=package_id,
        )
        config_file = (
            package_path / PACKAGE_TYPE_TO_CONFIG_FILE[package_id.package_type.value]
        )
        package_config, extra = load_yaml(file_path=config_file)
        package_config["agent"] = self.update_public_id_hash(
            public_id_str=package_config["agent"],
            package_type=PackageType.AGENT,
        )

        dump_yaml(
            file_path=config_file,
            data=package_config,
            extra_data=extra,
        )

    def check_dependencies(
        self, configuration: PackageConfiguration
    ) -> List[Tuple[PackageId, DepedencyMismatchErrors]]:
        """Update dependencies."""

        if configuration.package_type != PackageType.SERVICE:  # pragma: nocover
            return super().check_dependencies(
                configuration=configuration,
            )

        configuration = cast(Service, configuration)
        agent_id = PackageId(
            package_type=PackageType.AGENT,
            public_id=configuration.agent,
        )

        expected_hash = self.get_package_hash(package_id=agent_id)
        if expected_hash is None:
            return [
                (agent_id, DepedencyMismatchErrors.HASH_NOT_FOUND),
            ]

        if expected_hash != agent_id.package_hash:
            return [
                (agent_id, DepedencyMismatchErrors.HASH_DOES_NOT_MATCH),
            ]

        return []


class PackageManagerV0(BasePackageManagerV0, _PackageManagerWithServicePatch):
    """Patch package manager for service component."""


class PackageManagerV1(BasePackageManagerV1, _PackageManagerWithServicePatch):
    """Patch package manager for service component."""
