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
"""Implementation of the 'autonomy fetch' subcommand."""
import shutil
import tempfile
from distutils.dir_util import copy_tree
from pathlib import Path
from typing import cast

import click
from aea.cli.fetch import do_fetch
from aea.cli.registry.settings import REGISTRY_REMOTE, REMOTE_IPFS
from aea.cli.utils.click_utils import PublicIdParameter, registry_flag
from aea.cli.utils.config import (
    get_default_remote_registry,
    get_ipfs_node_multiaddr,
    load_item_config,
)
from aea.cli.utils.context import Context
from aea.cli.utils.package_utils import try_get_item_source_path
from aea.configurations.base import PublicId
from aea.configurations.constants import AGENT, SERVICE, SERVICES

from autonomy.configurations.base import PACKAGE_TYPE_TO_CONFIG_CLASS


try:
    from aea_cli_ipfs.ipfs_utils import IPFSTool  # type: ignore

    IS_IPFS_PLUGIN_INSTALLED = True
except ImportError:  # pragma: nocover
    IS_IPFS_PLUGIN_INSTALLED = False


@click.command(name="fetch")
@registry_flag()
@click.option(
    "--alias",
    type=str,
    required=False,
    help="Provide a local alias for the agent.",
)
@click.option(
    "--agent",
    "package_type",
    help="Provide a local alias for the agent.",
    default=True,
    flag_value=AGENT,
)
@click.option(
    "--service",
    "package_type",
    help="Provide a local alias for the agent.",
    flag_value=SERVICE,
)
@click.argument("public-id", type=PublicIdParameter(), required=True)
@click.pass_context
def fetch(
    click_context: click.Context,
    public_id: PublicId,
    alias: str,
    package_type: str,
    registry: str,
) -> None:
    """Fetch an agent from the registry."""
    ctx = cast(Context, click_context.obj)
    ctx.registry_type = registry

    try:
        if package_type == AGENT:  # pragma: nocover
            do_fetch(ctx, public_id, alias)
        else:
            fetch_service(ctx, public_id)
    except Exception as e:  # pylint: disable=broad-except
        raise click.ClickException(str(e)) from e


def fetch_service(ctx: Context, public_id: PublicId) -> Path:
    """Fetch service."""

    if ctx.registry_type == REGISTRY_REMOTE:
        if get_default_remote_registry() == REMOTE_IPFS:
            return fetch_service_ipfs(public_id)

        raise Exception("HTTP registry not supported.")

    return fetch_service_local(ctx, public_id)


def fetch_service_ipfs(public_id: PublicId) -> Path:
    """Fetch service from IPFS node."""

    if not IS_IPFS_PLUGIN_INSTALLED:
        raise RuntimeError("IPFS plugin not installed.")

    with tempfile.TemporaryDirectory() as temp_dir:
        ipfs_tool = IPFSTool(get_ipfs_node_multiaddr())
        download_path = Path(ipfs_tool.download(public_id.hash, temp_dir))
        package_path = Path.cwd() / download_path.name
        shutil.copytree(download_path, package_path)

    service_config = load_item_config(
        SERVICE, package_path, PACKAGE_TYPE_TO_CONFIG_CLASS
    )

    click.echo(
        f"Downloaded service package {service_config.public_id} @ {package_path}"
    )

    return package_path


def fetch_service_local(ctx: Context, public_id: PublicId) -> Path:
    """Fetch service from local directory."""

    try:
        registry_path = ctx.registry_path
    except ValueError as e:  # pragma: nocover
        raise click.ClickException(str(e))

    source_path = try_get_item_source_path(
        registry_path, public_id.author, SERVICES, public_id.name
    )

    target_path = Path(ctx.cwd, public_id.name)
    if target_path.exists():
        raise click.ClickException(
            f'Item "{target_path.name}" already exists in target folder "{target_path.parent}".'
        )

    copy_tree(source_path, str(target_path))
    click.echo(f"Copied service package {public_id}")
    return target_path
