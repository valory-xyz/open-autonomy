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
from typing import Optional

import click
from aea.cli.utils.click_utils import PublicIdParameter, password_option, registry_flag
from aea.cli.utils.context import Context
from aea.configurations.constants import PACKAGES
from aea.configurations.data_types import PublicId
from aea.helpers.base import cd

from autonomy.cli.fetch import fetch_service
from autonomy.cli.utils.click_utils import image_profile_flag
from autonomy.configurations.constants import DEFAULT_SERVICE_FILE
from autonomy.configurations.loader import load_service_config
from autonomy.constants import DEFAULT_IMAGE_VERSION
from autonomy.data import DATA_DIR
from autonomy.deploy.build import generate_deployment
from autonomy.deploy.constants import (
    AGENT_KEYS_DIR,
    BENCHMARKS_DIR,
    DOCKERFILES,
    LOG_DIR,
    PERSISTENT_DATA_DIR,
    TM_STATE_DIR,
    VENVS_DIR,
)
from autonomy.deploy.generators.docker_compose.base import DockerComposeGenerator
from autonomy.deploy.generators.kubernetes.base import KubernetesGenerator
from autonomy.deploy.image import ImageProfiles, build_image


@click.group(name="deploy")
def deploy_group() -> None:
    """Deploy an agent service."""


@deploy_group.group(name="build")
def build_group() -> None:
    """Build an agent service deployment."""


@build_group.command(name="deployment")
@click.argument(
    "service-id",
    type=PublicIdParameter(),
)
@click.argument("keys_file", type=str, required=True)
@click.option(
    "--o",
    "output_dir",
    type=click.Path(exists=False, dir_okay=True),
    default=Path.cwd(),
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
    "--packages-dir",
    type=click.Path(dir_okay=True),
    default=Path.cwd() / PACKAGES,
    help="Path to packages folder (for local usage).",
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
@click.option(
    "--skip-images",
    is_flag=True,
    default=False,
    help="Specify whether to build images or not.",
)
@registry_flag()
@password_option(confirmation_prompt=True)
def build_deployment(  # pylint: disable=too-many-arguments, too-many-locals
    service_id: PublicId,
    keys_file: Path,
    deployment_type: str,
    output_dir: Path,
    packages_dir: Path,
    dev_mode: bool,
    force_overwrite: bool,
    registry: str,
    number_of_agents: Optional[int] = None,
    password: Optional[str] = None,
    version: Optional[str] = None,
    skip_images: bool = False,
) -> None:
    """Build deployment setup for n agents."""

    packages_dir = Path(packages_dir).absolute()
    keys_file = Path(keys_file).absolute()
    build_dir = Path(output_dir, "abci_build").absolute()

    if build_dir.is_dir():
        if not force_overwrite:
            raise click.ClickException(f"Build already exists @ {output_dir}")
        shutil.rmtree(build_dir)

    try:
        build_dir.mkdir()
        _build_dirs(build_dir)

        with cd(build_dir):
            context = Context(
                cwd=build_dir, verbosity="INFO", registry_path=packages_dir
            )
            context.registry_type = registry
            download_path = fetch_service(context, service_id)

            shutil.move(
                str(download_path / DEFAULT_SERVICE_FILE),
                str(build_dir / DEFAULT_SERVICE_FILE),
            )
            shutil.rmtree(download_path)

        _copy_docker_files(build_dir)

        if not skip_images:
            _build_images(build_dir, version, dev_mode)

        report = generate_deployment(
            service_path=build_dir,
            type_of_deployment=deployment_type,
            private_keys_file_path=keys_file,
            private_keys_password=password,
            number_of_agents=number_of_agents,
            build_dir=build_dir,
            dev_mode=dev_mode,
            version=version,
        )
        click.echo(report)

    except Exception as e:  # pylint: disable=broad-except
        shutil.rmtree(build_dir)
        raise click.ClickException(str(e)) from e


def _build_images(
    build_dir: Path, version: Optional[str], dev_mode: bool = False
) -> None:
    """Build images."""

    service = load_service_config(build_dir)
    profile = ImageProfiles.PRODUCTION
    if dev_mode:
        profile = ImageProfiles.DEVELOPMENT

    if version is None:
        version = DEFAULT_IMAGE_VERSION

    with cd(build_dir):
        click.echo("\nBuilding agent image")
        build_image(
            agent=service.agent,
            profile=profile,
            skaffold_dir=build_dir / DOCKERFILES,
            version=version,
            push=False,
        )
        click.echo("\nBuilding dependency image")
        build_image(
            agent=service.agent,
            profile=ImageProfiles.DEPENDENCIES,
            skaffold_dir=build_dir / DOCKERFILES,
            version=version,
            push=False,
        )
        click.echo()


@build_group.command(name="image")
@click.option(
    "--build-dir",
    type=click.Path(dir_okay=True),
    help="Path to build dir.",
)
@click.option(
    "--packages-dir",
    type=click.Path(dir_okay=True),
    help="Path to packages folder (for local usage).",
)
@click.option(
    "--skaffold-dir",
    type=click.Path(exists=True, dir_okay=True),
    help="Path to directory containing the skaffold config.",
)
@click.option(
    "--version",
    type=str,
    default=DEFAULT_IMAGE_VERSION,
    help="Image version.",
)
@click.option("--push", is_flag=True, default=False, help="Push image after build.")
@image_profile_flag()
def build_images(  # pylint: disable=too-many-arguments
    profile: str,
    packages_dir: Optional[Path],
    build_dir: Optional[Path],
    skaffold_dir: Optional[Path],
    version: str,
    push: bool,
) -> None:
    """Build image using skaffold."""

    build_dir = build_dir or Path.cwd()
    packages_dir = packages_dir or Path.cwd() / PACKAGES
    skaffold_dir = skaffold_dir or Path.cwd() / DOCKERFILES

    packages_dir = Path(packages_dir).absolute()
    skaffold_dir = Path(skaffold_dir).absolute()

    service = load_service_config(build_dir)
    service_id = service.public_id

    try:
        click.echo(
            f"Building image with:\n\tProfile: {profile}\n\tServiceId: {service_id}\n"
        )
        build_image(
            agent=service.agent,
            profile=profile,
            skaffold_dir=skaffold_dir,
            version=version,
            push=push,
        )
    except Exception as e:  # pylint: disable=broad-except
        raise click.ClickException(str(e)) from e


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


def _copy_docker_files(dest: Path) -> None:
    """Copy Dockerfile to a build directory."""

    src = DATA_DIR / DOCKERFILES
    dest = dest / DOCKERFILES

    shutil.copytree(src, dest)
    click.echo("Copied Dockerfiles to build directory.")
