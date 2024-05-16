# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022-2024 Valory AG
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
from typing import Optional, Tuple

import click
from aea.cli.utils.click_utils import (
    PublicIdParameter,
    PyPiDependency,
    reraise_as_click_exception,
)
from aea.configurations.data_types import Dependency, PublicId

from autonomy.cli.helpers.image import build_image as _build_image
from autonomy.cli.utils.click_utils import image_author_option
from autonomy.deploy.image import ImageBuildFailed


@click.command(name="build-image")
@click.argument(
    "agent",
    type=PublicIdParameter(),
    required=False,
)
@click.option(
    "--service-dir",
    type=click.Path(dir_okay=True),
    help="Path to service dir.",
)
@click.option(
    "-e",
    "--extra-dependency",
    "extra_dependencies",
    type=PyPiDependency(),
    help="Provide extra dependency.",
    multiple=True,
)
@click.option("--version", type=str, help="Specify tag version for the image.")
@click.option("--dev", is_flag=True, help="Build development image.", default=False)
@click.option("--pull", is_flag=True, help="Pull latest dependencies.", default=False)
@click.option(
    "-f",
    "--dockerfile",
    type=click.Path(
        file_okay=True,
        dir_okay=False,
        exists=False,
    ),
    help="Specify custom dockerfile for building the agent",
)
@image_author_option
def build_image(  # pylint: disable=too-many-arguments
    agent: Optional[PublicId],
    service_dir: Optional[Path],
    dockerfile: Optional[Path],
    extra_dependencies: Tuple[Dependency, ...],
    pull: bool = False,
    dev: bool = False,
    version: Optional[str] = None,
    image_author: Optional[str] = None,
) -> None:
    """Build runtime images for autonomous agents."""
    if dev:
        click.echo(
            "`--dev` flag is deprecated, development mode does not require you to build docker image manually anymore."
        )

    with reraise_as_click_exception(ImageBuildFailed, FileNotFoundError):
        _build_image(
            agent=agent,
            service_dir=service_dir,
            extra_dependencies=extra_dependencies,
            pull=pull,
            version=version,
            image_author=image_author,
            dockerfile=dockerfile,
        )
