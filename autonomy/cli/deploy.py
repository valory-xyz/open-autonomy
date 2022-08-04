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

"""Deploy CLI module."""

import os
import shutil
from pathlib import Path
from typing import Optional, cast

import click
from aea.cli.utils.click_utils import password_option, registry_flag
from aea.cli.utils.context import Context
from aea.configurations.data_types import PublicId
from aea.helpers.base import cd

from autonomy.cli.fetch import fetch_service
from autonomy.constants import DEFAULT_KEYS_FILE
from autonomy.deploy.build import generate_deployment
from autonomy.deploy.chain import resolve_token_id
from autonomy.deploy.constants import (
    AGENT_KEYS_DIR,
    BENCHMARKS_DIR,
    DEFAULT_ABCI_BUILD_DIR,
    LOG_DIR,
    PERSISTENT_DATA_DIR,
    TM_STATE_DIR,
    VENVS_DIR,
)
from autonomy.deploy.generators.docker_compose.base import DockerComposeGenerator
from autonomy.deploy.generators.kubernetes.base import KubernetesGenerator


RPC_URL = "https://chain.staging.autonolas.tech"
SERVICE_REGISTRY_ABI = "https://abi-server.staging.autonolas.tech/autonolas-registries/ServiceRegistry.json"
SERVICE_ADDRESS = "0x0DCd1Bf9A1b36cE34237eEaFef220932846BCD82"


@click.group(name="deploy")
@click.pass_context
def deploy_group(
    click_context: click.Context,  # pylint: disable=unused-argument
) -> None:
    """Deploy an agent service."""


@deploy_group.command(name="build")
@click.argument("keys_file", type=str, required=False)
@click.option(
    "--o",
    "output_dir",
    type=click.Path(exists=False, dir_okay=True),
    help="Path to output dir.",
)
@click.option(
    "--n",
    "number_of_agents",
    type=int,
    default=None,
    help="Number of agents.",
)
@click.option(
    "--docker",
    "deployment_type",
    flag_value=DockerComposeGenerator.deployment_type,
    default=True,
    help="Use docker as a backend.",
)
@click.option(
    "--kubernetes",
    "deployment_type",
    flag_value=KubernetesGenerator.deployment_type,
    help="Use kubernetes as a backend.",
)
@click.option(
    "--dev",
    "dev_mode",
    is_flag=True,
    default=False,
    help="Create development environment.",
)
@click.option(
    "--version",
    "version",
    help="Specify deployment version.",
)
@click.option(
    "--force",
    "force_overwrite",
    is_flag=True,
    default=False,
    help="Remove existing build and overwrite with new one.",
)
@registry_flag()
@password_option(confirmation_prompt=True)
@click.pass_context
def build_deployment_command(  # pylint: disable=too-many-arguments, too-many-locals
    click_context: click.Context,
    keys_file: Optional[Path],
    deployment_type: str,
    output_dir: Optional[Path],
    dev_mode: bool,
    force_overwrite: bool,
    registry: str,
    number_of_agents: Optional[int] = None,
    password: Optional[str] = None,
    version: Optional[str] = None,
) -> None:
    """Build deployment setup for n agents."""

    keys_file = Path(keys_file or DEFAULT_KEYS_FILE).absolute()
    build_dir = Path(output_dir or DEFAULT_ABCI_BUILD_DIR).absolute()

    ctx = cast(Context, click_context.obj)
    ctx.registry_type = registry

    try:
        build_deployment(
            keys_file,
            build_dir,
            deployment_type,
            dev_mode,
            force_overwrite,
            number_of_agents,
            password,
            version,
        )
    except Exception as e:  # pylint: disable=broad-except
        shutil.rmtree(build_dir)
        raise click.ClickException(str(e)) from e


@deploy_group.command(name="from-token")
@click.argument("token_id", type=int)
@click.argument("keys_file", type=click.Path())
@registry_flag()
@click.pass_context
def run_deployment(
    click_context: click.Context,
    token_id: int,
    keys_file: Path,
    registry: str,
) -> None:
    """Run service deployment."""

    ctx = cast(Context, click_context.obj)
    ctx.registry_type = registry
    keys_file = Path(keys_file or DEFAULT_KEYS_FILE).absolute()

    metadata = resolve_token_id(token_id)
    *_, service_hash = metadata["code_uri"].split("//")
    public_id = PublicId(author="valory", name="service", package_hash=service_hash)
    service_path = fetch_service(ctx, public_id)

    with cd(service_path):
        build_deployment(
            keys_file,
            build_dir=service_path / DEFAULT_ABCI_BUILD_DIR,
            deployment_type=DockerComposeGenerator.deployment_type,
            dev_mode=False,
            force_overwrite=True,
        )

    with cd(service_path / DEFAULT_ABCI_BUILD_DIR):
        run_existing_deployment()


def run_existing_deployment() -> None:
    """Run existing deployment."""


def build_deployment(  # pylint: disable=too-many-arguments
    keys_file: Path,
    build_dir: Path,
    deployment_type: str,
    dev_mode: bool,
    force_overwrite: bool,
    number_of_agents: Optional[int] = None,
    password: Optional[str] = None,
    version: Optional[str] = None,
) -> None:
    """Build deployment."""
    if build_dir.is_dir():
        if not force_overwrite:
            raise click.ClickException(f"Build already exists @ {build_dir}")
        shutil.rmtree(build_dir)

    build_dir.mkdir()
    _build_dirs(build_dir)

    report = generate_deployment(
        service_path=Path.cwd(),
        type_of_deployment=deployment_type,
        private_keys_file_path=keys_file,
        private_keys_password=password,
        number_of_agents=number_of_agents,
        build_dir=build_dir,
        dev_mode=dev_mode,
        version=version,
    )
    click.echo(report)


def _build_dirs(build_dir: Path) -> None:
    """Build necessary directories."""

    for dir_path in [
        (PERSISTENT_DATA_DIR,),
        (PERSISTENT_DATA_DIR, LOG_DIR),
        (PERSISTENT_DATA_DIR, TM_STATE_DIR),
        (PERSISTENT_DATA_DIR, BENCHMARKS_DIR),
        (PERSISTENT_DATA_DIR, VENVS_DIR),
        (AGENT_KEYS_DIR,),
    ]:
        path = Path(build_dir, *dir_path)
        path.mkdir()
        # TOFIX for macOS
        try:
            os.chown(path, 1000, 1000)
        except PermissionError:
            click.echo(
                f"Updating permissions failed for {path}, please do it manually."
            )
