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

"""Build images."""


from pathlib import Path
from typing import Optional

import click
from aea.configurations.constants import PACKAGES

from autonomy.cli.utils.click_utils import image_profile_flag
from autonomy.configurations.loader import load_service_config
from autonomy.constants import DEFAULT_IMAGE_VERSION
from autonomy.data import DATA_DIR
from autonomy.deploy.constants import DOCKERFILES
from autonomy.deploy.image import build_image


@click.command(name="build-images")
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

    build_dir = Path(build_dir or Path.cwd()).absolute()
    packages_dir = Path(packages_dir or Path.cwd() / PACKAGES).absolute()
    skaffold_dir = Path(skaffold_dir or DATA_DIR / DOCKERFILES).absolute()

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
