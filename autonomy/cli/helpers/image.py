# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023-2024 Valory AG
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

"""Image helpers."""

from pathlib import Path
from typing import Optional, Tuple

import click
from aea.configurations.data_types import Dependency, PublicId

from autonomy.configurations.loader import load_service_config
from autonomy.deploy.image import build_image as _build_image


def build_image(  # pylint: disable=too-many-arguments
    agent: Optional[PublicId],
    service_dir: Optional[Path],
    pull: bool = False,
    version: Optional[str] = None,
    image_author: Optional[str] = None,
    extra_dependencies: Optional[Tuple[Dependency, ...]] = None,
    dockerfile: Optional[Path] = None,
) -> None:
    """Build agent/service image."""
    extra_dependencies = extra_dependencies or ()
    if agent is None:
        service_dir = Path(service_dir or Path.cwd()).absolute()
        service = load_service_config(service_dir)
        agent = service.agent
        extra_dependencies = (*extra_dependencies, *service.dependencies.values())

    click.echo(f"Building image with agent: {agent}\n")
    _build_image(
        agent=agent,
        pull=pull,
        version=version,
        image_author=image_author,
        extra_dependencies=extra_dependencies,
        dockerfile=dockerfile,
    )
