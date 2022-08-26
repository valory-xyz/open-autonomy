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
from aea.cli.utils.click_utils import PublicIdParameter
from aea.configurations.data_types import PublicId

from autonomy.configurations.loader import load_service_config
from autonomy.deploy.image import build_image as _build_image


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
@click.option("--dev", is_flag=True, help="Build developement image.", default=False)
@click.option("--pull", is_flag=True, help="Pull latest dependencies.", default=False)
def build_image(
    agent: Optional[PublicId],
    service_dir: Optional[Path],
    pull: bool = False,
    dev: bool = False,
) -> None:
    """Build image using skaffold."""

    service_dir = Path(service_dir or Path.cwd()).absolute()

    if agent is None:
        service = load_service_config(service_dir)
        agent = service.agent

    try:
        click.echo(f"Building image with agent: {agent}\n")
        _build_image(agent=agent, pull=pull, dev=dev)
    except Exception as e:  # pylint: disable=broad-except
        raise click.ClickException(str(e)) from e
