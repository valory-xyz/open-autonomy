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
from aea.cli.utils.click_utils import PublicIdParameter, password_option
from aea.configurations.constants import PACKAGES
from aea.configurations.data_types import PublicId

from autonomy.cli.utils.click_utils import image_profile_flag
from autonomy.constants import DEFAULT_IMAGE_VERSION
from autonomy.deploy.build import generate_deployment
from autonomy.deploy.generators.docker_compose.base import DockerComposeGenerator
from autonomy.deploy.generators.kubernetes.base import KubernetesGenerator
from autonomy.deploy.image import ImageBuilder


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
    type=click.Path(exists=True, dir_okay=True),
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
@password_option(confirmation_prompt=True)
def build_deployment(  # pylint: disable=too-many-arguments
    service_id: PublicId,
    keys_file: Path,
    deployment_type: str,
    output_dir: Path,
    packages_dir: Path,
    dev_mode: bool,
    force_overwrite: bool,
    number_of_agents: Optional[int] = None,
    password: Optional[str] = None,
    version: Optional[str] = None,
) -> None:
    """Build deployment setup for n agents."""

    packages_dir = Path(packages_dir)
    keys_file = Path(keys_file)
    build_dir = Path(output_dir, "abci_build")

    if not packages_dir.is_dir():
        raise click.ClickException(
            f"Packages directory does not exists @ {packages_dir}"
        )

    if build_dir.is_dir():
        if not force_overwrite:
            raise click.ClickException(f"Build already exists @ {output_dir}")
        shutil.rmtree(build_dir)

    build_dir.mkdir()
    _build_dirs(build_dir)

    service_path = _find_path_to_service(service_id, packages_dir)
    try:
        report = generate_deployment(
            service_path=service_path,
            type_of_deployment=deployment_type,
            private_keys_file_path=keys_file,
            private_keys_password=password,
            number_of_agents=number_of_agents,
            packages_dir=packages_dir,
            build_dir=build_dir,
            dev_mode=dev_mode,
            version=version,
        )
        click.echo(report)
    except Exception as e:  # pylint: disable=broad-except
        raise click.ClickException(str(e)) from e


@build_group.command(name="image")
@click.argument(
    "service-id",
    type=PublicIdParameter(),
)
@click.option(
    "--packages-dir",
    type=click.Path(exists=True, dir_okay=True),
    default=Path.cwd() / PACKAGES,
    help="Path to packages folder (for local usage).",
)
@click.option(
    "--build-dir",
    type=click.Path(exists=True, dir_okay=True),
    default=Path.cwd() / "deployments" / "Dockerfiles" / "open_aea",
    help="Path to build directory.",
)
@click.option(
    "--skaffold-dir",
    type=click.Path(exists=True, dir_okay=True),
    default=Path.cwd(),
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
    service_id: PublicId,
    profile: str,
    packages_dir: Path,
    build_dir: Path,
    skaffold_dir: Path,
    version: str,
    push: bool,
) -> None:
    """Build image using skaffold."""

    packages_dir = Path(packages_dir).absolute()
    build_dir = Path(build_dir).absolute()
    skaffold_dir = Path(skaffold_dir).absolute()

    try:
        click.echo(
            f"Building image with:\n\tProfile: {profile}\n\tServiceId: {service_id}\n"
        )
        deployment_file_path = _find_path_to_service_file(service_id, packages_dir)
        ImageBuilder.build_images(
            profile=profile,
            deployment_file_path=deployment_file_path,
            push=push,
            packages_dir=packages_dir,
            build_dir=build_dir,
            version=version,
            skaffold_dir=skaffold_dir,
        )
    except Exception as e:  # pylint: disable=broad-except
        raise click.ClickException(str(e)) from e


def _find_path_to_service_file(public_id: PublicId, packages_dir: Path) -> Path:
    """Find path to service file using package dir."""
    service_file = (
        packages_dir / public_id.author / "services" / public_id.name / "service.yaml"
    )
    if not service_file.is_file():
        raise click.ClickException(f"Cannot find service file for {public_id}")

    return service_file


def _find_path_to_service(public_id: PublicId, packages_dir: Path) -> Path:
    """Find path to service file using package dir."""
    service_path = packages_dir / public_id.author / "services" / public_id.name
    if not service_path.is_dir():
        raise click.ClickException(f"Cannot find service file for {public_id}")

    return service_path


def _build_dirs(build_dir: Path) -> None:
    """Build necessary directories."""

    for dir_path in [
        ("persistent_data",),
        ("persistent_data", "logs"),
        ("persistent_data", "tm_state"),
        ("persistent_data", "benchmarks"),
        ("persistent_data", "venvs"),
        ("agent_keys",),
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
