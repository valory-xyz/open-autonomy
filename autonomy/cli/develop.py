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

"""Develop CLI module."""

import click
from docker import from_env

from autonomy.constants import (
    DEFAULT_SERVICE_REGISTRY_CONTRACTS_IMAGE,
    SERVICE_REGISTRY_CONTRACT_CONTAINER_NAME,
)


@click.group(name="develop")
def develop_group() -> None:
    """Develop an agent service."""

    click.echo("Develop module.")  # pragma: nocover


@develop_group.command(name="service-registry-network")
@click.argument(
    "image",
    type=str,
    required=False,
    default=DEFAULT_SERVICE_REGISTRY_CONTRACTS_IMAGE,
)
def run_service_locally(image: str) -> None:
    """Run the service registry contracts on a local network."""
    click.echo(f"Starting {image}.")
    client = from_env()
    container = client.containers.run(
        image=image,
        detach=True,
        network_mode="host",
        name=SERVICE_REGISTRY_CONTRACT_CONTAINER_NAME,
    )
    try:
        for line in client.api.logs(container.id, follow=True, stream=True):
            click.echo(line.decode())
    except KeyboardInterrupt:
        click.echo("Stopping container.")
    except Exception:  # pyline: disable=broad-except
        click.echo("Stopping container.")
        container.stop()
        raise

    click.echo("Stopping container.")
    container.stop()
