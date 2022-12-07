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

from pathlib import Path
from typing import Optional, Tuple

import click
from aea.configurations.data_types import PackageType
from aea_ledger_ethereum.ethereum import EthereumCrypto
from docker import from_env

from autonomy.cli.helpers.chain import mint_component
from autonomy.cli.utils.click_utils import PathArgument
from autonomy.constants import (
    DEFAULT_SERVICE_REGISTRY_CONTRACTS_IMAGE,
    SERVICE_REGISTRY_CONTRACT_CONTAINER_NAME,
)


package_path_decorator = click.argument(
    "package_path",
    type=PathArgument(exists=True, file_okay=False, dir_okay=True),
)
key_path_decorator = click.argument(
    "keys",
    type=PathArgument(exists=True, file_okay=True, dir_okay=False),
)
password_decorator = click.option(
    "--password",
    type=str,
    help="Password for key pair",
)
dependencies_decorator = click.option(
    "-d",
    "--dependencies",
    type=str,
    multiple=True,
    help="Password for key pair",
)


@click.group(name="develop")
def develop_group() -> None:
    """Develop an agent service."""


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


@develop_group.group("mint")
def mint_component_on_chain() -> None:
    """Mint component on-chain."""


@mint_component_on_chain.command()
@package_path_decorator
@key_path_decorator
@password_decorator
@dependencies_decorator
def protocol(
    package_path: Path, keys: Path, password: Optional[str], dependencies: Tuple[str]
) -> None:
    """Mint a protocol component."""

    account = EthereumCrypto(
        private_key_path=keys,
        password=password,
    )

    mint_component(
        package_path=package_path,
        package_type=PackageType.PROTOCOL,
        crypto=account,
        dependencies=list(map(int, dependencies)),
    )
