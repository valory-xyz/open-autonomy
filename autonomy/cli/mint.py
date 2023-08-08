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

"""Mint command group definitions."""

from pathlib import Path
from typing import Optional, Tuple, Union, cast

import click
from aea.cli.utils.context import Context
from aea.cli.utils.decorators import pass_ctx
from aea.configurations.data_types import PackageType
from aea.helpers.base import IPFSHash

from autonomy.chain.config import ChainType
from autonomy.cli.helpers.chain import mint_component, mint_service
from autonomy.cli.utils.click_utils import (
    NFTArgument,
    PathArgument,
    chain_selection_flag,
)


package_path_decorator = click.argument(
    "package_path",
    type=PathArgument(exists=True, file_okay=False, dir_okay=True),
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
    help="Dependencies for the package",
)
nft_decorator = click.option(
    "--nft",
    type=NFTArgument(),
    help="IPFS hash or path for the NFT image",
)
timeout_flag = click.option(
    "-t", "--timeout", type=float, help="Timeout for verifying emnitted events"
)
owner_flag = click.option(
    "--owner",
    type=str,
    help="Owner address for the component",
)

key_path_decorator = click.option(
    "--key",
    type=PathArgument(exists=True, file_okay=True, dir_okay=False),
    help="Use private key from a file for signing the transactions",
)
hwi_flag = click.option(
    "--hwi",
    is_flag=True,
    help="Use hardware wallet for signing the transactions.",
)


@click.group("mint")
@pass_ctx
@chain_selection_flag()
@timeout_flag
@click.option(
    "--skip-hash-check",
    is_flag=True,
    help="Skip hash check when verifying dependencies on chain",
)
@click.option(
    "--skip-dependencies-check",
    is_flag=True,
    help="Skip dependencies check.",
)
def mint(  # pylint: disable=too-many-arguments
    ctx: Context,
    chain_type: str,
    skip_hash_check: bool,
    skip_dependencies_check: bool,
    timeout: float,
) -> None:
    """Mint component on-chain."""

    ctx.config["chain_type"] = ChainType(chain_type)
    ctx.config["skip_hash_check"] = skip_hash_check
    ctx.config["skip_dependencies_check"] = skip_dependencies_check
    ctx.config["timeout"] = timeout


@mint.command()
@package_path_decorator
@key_path_decorator
@hwi_flag
@password_decorator
@dependencies_decorator
@nft_decorator
@owner_flag
@pass_ctx
def protocol(  # pylint: disable=too-many-arguments
    ctx: Context,
    package_path: Path,
    key: Path,
    password: Optional[str],
    dependencies: Tuple[str],
    nft: Optional[Union[Path, IPFSHash]],
    owner: Optional[str],
    hwi: bool = False,
) -> None:
    """Mint a protocol component."""

    mint_component(
        package_path=package_path,
        package_type=PackageType.PROTOCOL,
        key=key,
        chain_type=cast(ChainType, ctx.config.get("chain_type")),
        dependencies=list(map(int, dependencies)),
        password=password,
        nft=nft,
        owner=owner,
        skip_hash_check=ctx.config.get("skip_hash_check", False),
        skip_dependencies_check=ctx.config.get("skip_dependencies_check", False),
        timeout=ctx.config["timeout"],
        hwi=hwi,
    )


@mint.command()
@package_path_decorator
@key_path_decorator
@hwi_flag
@password_decorator
@dependencies_decorator
@nft_decorator
@owner_flag
@pass_ctx
def contract(  # pylint: disable=too-many-arguments
    ctx: Context,
    package_path: Path,
    key: Path,
    password: Optional[str],
    dependencies: Tuple[str],
    nft: Optional[Union[Path, IPFSHash]],
    owner: Optional[str],
    hwi: bool = False,
) -> None:
    """Mint a contract component."""

    mint_component(
        package_path=package_path,
        package_type=PackageType.CONTRACT,
        key=key,
        chain_type=cast(ChainType, ctx.config.get("chain_type")),
        dependencies=list(map(int, dependencies)),
        password=password,
        nft=nft,
        owner=owner,
        skip_hash_check=ctx.config.get("skip_hash_check", False),
        skip_dependencies_check=ctx.config.get("skip_dependencies_check", False),
        timeout=ctx.config["timeout"],
        hwi=hwi,
    )


@mint.command()
@package_path_decorator
@key_path_decorator
@hwi_flag
@password_decorator
@dependencies_decorator
@nft_decorator
@owner_flag
@pass_ctx
def connection(  # pylint: disable=too-many-arguments
    ctx: Context,
    package_path: Path,
    key: Path,
    password: Optional[str],
    dependencies: Tuple[str],
    nft: Optional[Union[Path, IPFSHash]],
    owner: Optional[str],
    hwi: bool = False,
) -> None:
    """Mint a connection component."""

    mint_component(
        package_path=package_path,
        package_type=PackageType.CONNECTION,
        key=key,
        chain_type=cast(ChainType, ctx.config.get("chain_type")),
        dependencies=list(map(int, dependencies)),
        password=password,
        nft=nft,
        owner=owner,
        skip_hash_check=ctx.config.get("skip_hash_check", False),
        skip_dependencies_check=ctx.config.get("skip_dependencies_check", False),
        timeout=ctx.config["timeout"],
        hwi=hwi,
    )


@mint.command()
@package_path_decorator
@key_path_decorator
@hwi_flag
@password_decorator
@dependencies_decorator
@nft_decorator
@owner_flag
@pass_ctx
def skill(  # pylint: disable=too-many-arguments
    ctx: Context,
    package_path: Path,
    key: Path,
    password: Optional[str],
    dependencies: Tuple[str],
    nft: Optional[Union[Path, IPFSHash]],
    owner: Optional[str],
    hwi: bool = False,
) -> None:
    """Mint a skill component."""

    mint_component(
        package_path=package_path,
        package_type=PackageType.SKILL,
        key=key,
        chain_type=cast(ChainType, ctx.config.get("chain_type")),
        dependencies=list(map(int, dependencies)),
        password=password,
        nft=nft,
        owner=owner,
        skip_hash_check=ctx.config.get("skip_hash_check", False),
        skip_dependencies_check=ctx.config.get("skip_dependencies_check", False),
        timeout=ctx.config["timeout"],
        hwi=hwi,
    )


@mint.command()
@package_path_decorator
@key_path_decorator
@hwi_flag
@password_decorator
@dependencies_decorator
@nft_decorator
@owner_flag
@pass_ctx
def agent(  # pylint: disable=too-many-arguments
    ctx: Context,
    package_path: Path,
    key: Path,
    password: Optional[str],
    dependencies: Tuple[str],
    nft: Optional[Union[Path, IPFSHash]],
    owner: Optional[str],
    hwi: bool = False,
) -> None:
    """Mint an agent."""

    mint_component(
        package_path=package_path,
        package_type=PackageType.AGENT,
        key=key,
        chain_type=cast(ChainType, ctx.config.get("chain_type")),
        dependencies=list(map(int, dependencies)),
        password=password,
        nft=nft,
        owner=owner,
        skip_hash_check=ctx.config.get("skip_hash_check", False),
        skip_dependencies_check=ctx.config.get("skip_dependencies_check", False),
        timeout=ctx.config["timeout"],
        hwi=hwi,
    )


@mint.command()
@package_path_decorator
@key_path_decorator
@hwi_flag
@password_decorator
@nft_decorator
@owner_flag
@pass_ctx
@click.option(
    "-a",
    "--agent-id",
    type=int,
    help="Canonical agent ID",
    required=True,
)
@click.option(
    "-n",
    "--number-of-slots",
    type=int,
    help="Number of agent instances for the agent",
    required=True,
)
@click.option(
    "-c",
    "--cost-of-bond",
    type=int,
    help="Cost of bond for the agent (Wei)",
    required=True,
)
@click.option(
    "--threshold",
    type=int,
    required=True,
    help="Threshold for the minimum numbers required to run the service",
)
def service(  # pylint: disable=too-many-arguments  # pylint: disable=too-many-arguments
    ctx: Context,
    package_path: Path,
    key: Path,
    agent_id: int,
    number_of_slots: int,
    cost_of_bond: int,
    threshold: int,
    password: Optional[str],
    nft: Optional[Union[Path, IPFSHash]],
    owner: Optional[str],
    hwi: bool = False,
) -> None:
    """Mint a service"""

    mint_service(
        package_path=package_path,
        key=key,
        agent_id=agent_id,
        number_of_slots=number_of_slots,
        cost_of_bond=cost_of_bond,
        threshold=threshold,
        chain_type=cast(ChainType, ctx.config.get("chain_type")),
        password=password,
        nft=nft,
        owner=owner,
        skip_hash_check=ctx.config.get("skip_hash_check", False),
        skip_dependencies_check=ctx.config.get("skip_dependencies_check", False),
        timeout=ctx.config["timeout"],
        hwi=hwi,
    )
