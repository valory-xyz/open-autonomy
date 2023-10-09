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

"""Component registry helpers."""

import os
import shutil
import tempfile
from distutils.dir_util import copy_tree  # pylint: disable=deprecated-module
from pathlib import Path
from shutil import copytree
from typing import Optional, cast

import click
from aea.cli.registry.settings import REGISTRY_LOCAL, REGISTRY_REMOTE, REMOTE_IPFS
from aea.cli.utils.click_utils import reraise_as_click_exception
from aea.cli.utils.config import (
    get_default_remote_registry,
    get_ipfs_node_multiaddr,
    load_item_config,
)
from aea.cli.utils.context import Context
from aea.cli.utils.package_utils import (
    try_get_item_source_path,
    try_get_item_target_path,
)
from aea.configurations.constants import DEFAULT_README_FILE, SERVICE, SERVICES
from aea.configurations.data_types import PublicId
from aea.helpers.cid import to_v1

from autonomy.configurations.base import (
    DEFAULT_SERVICE_CONFIG_FILE,
    PACKAGE_TYPE_TO_CONFIG_CLASS,
)


try:
    from aea_cli_ipfs.ipfs_utils import IPFSTool  # type: ignore

    IS_IPFS_PLUGIN_INSTALLED = True
except ImportError:  # pragma: nocover
    IS_IPFS_PLUGIN_INSTALLED = False


def fetch_service(
    ctx: Context,
    public_id: PublicId,
    alias: Optional[str] = None,
) -> Path:
    """Fetch service."""

    if ctx.registry_type == REGISTRY_REMOTE:
        return fetch_service_remote(public_id, alias=alias)
    if ctx.registry_type == REGISTRY_LOCAL:
        return fetch_service_local(ctx, public_id, alias=alias)
    return fetch_service_mixed(ctx, public_id, alias=alias)


def fetch_service_mixed(
    ctx: Context,
    public_id: PublicId,
    alias: Optional[str] = None,
) -> Path:
    """Fetch service in mixed mode."""
    try:
        return fetch_service_local(ctx, public_id, alias=alias)
    except Exception as e:  # pylint: disable=broad-except
        click.echo(
            f"Fetch from local registry failed (reason={str(e)}), trying remote registry..."
        )
        return fetch_service_remote(public_id, alias=alias)


def fetch_service_remote(
    public_id: PublicId,
    alias: Optional[str] = None,
) -> Path:
    """Fetch service in remote mode."""
    if get_default_remote_registry() == REMOTE_IPFS:
        return fetch_service_ipfs(public_id, alias=alias)

    raise Exception("HTTP registry not supported.")  # pragma: nocover


def fetch_service_ipfs(
    public_id: PublicId,
    alias: Optional[str] = None,
) -> Path:
    """Fetch service from IPFS node."""

    if not IS_IPFS_PLUGIN_INSTALLED:
        raise RuntimeError("IPFS plugin not installed.")  # pragma: no cover

    with tempfile.TemporaryDirectory() as temp_dir:
        ipfs_tool = IPFSTool(get_ipfs_node_multiaddr())
        download_path = Path(ipfs_tool.download(public_id.hash, temp_dir))
        package_path = Path.cwd() / (alias or download_path.name)
        shutil.copytree(download_path, package_path)

    if not Path(package_path, DEFAULT_SERVICE_CONFIG_FILE).exists():
        raise click.ClickException(
            "Downloaded packages is not a service package, "
            "if you intend to download an agent please use `--agent` flag "
            "or check the hash"
        )

    service_config = load_item_config(
        SERVICE, package_path, PACKAGE_TYPE_TO_CONFIG_CLASS
    )

    click.echo(
        f"Downloaded service package {service_config.public_id} @ {package_path}"
    )

    return package_path


def fetch_service_local(
    ctx: Context,
    public_id: PublicId,
    alias: Optional[str] = None,
) -> Path:
    """Fetch service from local directory."""

    with reraise_as_click_exception(ValueError):
        registry_path = ctx.registry_path

    source_path = try_get_item_source_path(
        registry_path, public_id.author, SERVICES, public_id.name
    )

    target_path = Path(ctx.cwd, alias or public_id.name)
    if target_path.exists():
        raise click.ClickException(
            f'Item "{target_path.name}" already exists in target folder "{target_path.parent}".'
        )

    copy_tree(source_path, str(target_path))
    click.echo(f"Copied service package {public_id}")
    return target_path


def publish_service_package(click_context: click.Context, registry: str) -> None:
    """Publish a service package."""

    # TODO ensure we have error handling here.
    service_config = load_item_config(
        SERVICE, Path(click_context.obj.cwd), PACKAGE_TYPE_TO_CONFIG_CLASS
    )

    if registry == REGISTRY_REMOTE:
        if get_default_remote_registry() == REMOTE_IPFS:
            publish_service_ipfs(service_config.public_id, Path(click_context.obj.cwd))
        else:
            raise Exception("HTTP registry not supported.")  # pragma: no cover

    else:
        publish_service_local(
            cast(
                Context,
                click_context.obj,
            ),
            service_config.public_id,
        )


def publish_service_ipfs(public_id: PublicId, package_path: Path) -> None:
    """Publish a service package on the IPFS registry."""

    if not IS_IPFS_PLUGIN_INSTALLED:  # pragma: nocover
        raise RuntimeError("IPFS plugin not installed.")

    package_path = package_path.resolve()

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_service_dir = Path(temp_dir, public_id.name)
        temp_service_dir.mkdir()
        shutil.copyfile(
            package_path / DEFAULT_SERVICE_CONFIG_FILE,
            temp_service_dir / DEFAULT_SERVICE_CONFIG_FILE,
        )
        shutil.copyfile(
            package_path / DEFAULT_README_FILE,
            temp_service_dir / DEFAULT_README_FILE,
        )

        ipfs_tool = IPFSTool(get_ipfs_node_multiaddr())
        _, package_hash, _ = ipfs_tool.add(str(temp_service_dir.resolve()))
        package_hash = to_v1(package_hash)

        click.echo(
            f'Service "{public_id.name}" successfully published on the IPFS registry.\n\tPublicId: {public_id}\n\tPackage hash: {package_hash}'
        )


def publish_service_local(ctx: Context, public_id: PublicId) -> None:
    """Publish a service package on the local packages directory."""

    with reraise_as_click_exception(ValueError):
        registry_path = ctx.registry_path

    target_dir = try_get_item_target_path(
        registry_path,
        public_id.author,
        SERVICES,
        public_id.name,
    )
    author_dir = Path(target_dir).parent
    if not os.path.exists(author_dir):
        os.makedirs(author_dir, exist_ok=True)
    # TODO: also make services dir?

    copytree(ctx.cwd, target_dir)
    click.echo(
        f'Service "{public_id.name}" successfully published on the local packages directory.'
    )
