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
"""Implementation of the 'autonomy publish' subcommand."""

import os
from pathlib import Path
from shutil import copytree
from typing import cast

import click
from aea.cli.publish import publish_agent_package
from aea.cli.registry.settings import REGISTRY_REMOTE, REMOTE_IPFS
from aea.cli.utils.click_utils import registry_flag
from aea.cli.utils.config import (
    get_default_remote_registry,
    get_ipfs_node_multiaddr,
    load_item_config,
)
from aea.cli.utils.context import Context
from aea.cli.utils.package_utils import try_get_item_target_path
from aea.configurations.constants import (
    DEFAULT_AEA_CONFIG_FILE,
    DEFAULT_SERVICE_CONFIG_FILE,
    SERVICE,
    SERVICES,
)
from aea.configurations.data_types import PublicId
from aea.helpers.cid import to_v1

from autonomy.configurations.base import PACKAGE_TYPE_TO_CONFIG_CLASS


try:
    from aea_cli_ipfs.ipfs_utils import IPFSTool  # type: ignore

    IS_IPFS_PLUGIN_INSTALLED = True
except ImportError:  # pragma: nocover
    IS_IPFS_PLUGIN_INSTALLED = False


@click.command(name="publish")
@registry_flag()
@click.option(
    "--push-missing", is_flag=True, help="Push missing components to registry."
)
@click.pass_context
def publish(
    click_context: click.Context, registry: str, push_missing: bool
) -> None:  # pylint: disable=unused-argument
    """Publish the agent to the registry."""
    try:
        if Path(click_context.obj.cwd, DEFAULT_SERVICE_CONFIG_FILE).exists():
            publish_service_package(click_context, registry)
        elif Path(
            click_context.obj.cwd, DEFAULT_AEA_CONFIG_FILE
        ).exists():  # pragma: nocover
            publish_agent_package(click_context, registry, push_missing)
        else:
            raise FileNotFoundError("No package config found in this directory.")
    except Exception as e:  # pylint: disable=broad-except  # pragma: nocover
        raise click.ClickException(str(e)) from e


def publish_service_package(click_context: click.Context, registry: str) -> None:
    """Publish an agent package."""
    service_config = load_item_config(
        SERVICE, Path(click_context.obj.cwd), PACKAGE_TYPE_TO_CONFIG_CLASS
    )

    if registry == REGISTRY_REMOTE:
        if get_default_remote_registry() == REMOTE_IPFS:
            publish_service_ipfs(service_config.public_id, Path(click_context.obj.cwd))
        else:
            raise Exception("HTTP registry not supported.")

    else:
        publish_service_local(
            cast(
                Context,
                click_context.obj,
            ),
            service_config.public_id,
        )


def publish_service_ipfs(public_id: PublicId, package_path: Path) -> None:
    """Publish a service package to the IPFS registry."""

    if not IS_IPFS_PLUGIN_INSTALLED:  # pragma: nocover
        raise RuntimeError("IPFS plugin not installed.")

    ipfs_tool = IPFSTool(get_ipfs_node_multiaddr())
    _, package_hash, _ = ipfs_tool.add(str(package_path.resolve()))
    package_hash = to_v1(package_hash)
    click.echo(
        f"Published service package with\n\tPublicId: {public_id}\n\tPackage hash: {package_hash}"
    )


def publish_service_local(ctx: Context, public_id: PublicId) -> None:
    """Publish a service package to the local packages directory."""

    try:
        registry_path = ctx.registry_path
    except ValueError as e:  # pragma: nocover
        raise click.ClickException(str(e))

    target_dir = try_get_item_target_path(
        registry_path,
        public_id.author,
        SERVICES,
        public_id.name,
    )
    author_dir = Path(target_dir).parent
    if not os.path.exists(author_dir):
        os.makedirs(author_dir, exist_ok=True)

    copytree(ctx.cwd, target_dir)
    click.echo(f'Service "{public_id.name}" successfully saved in packages folder.')
