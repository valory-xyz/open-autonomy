# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023 Valory AG
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

"""Implementation of the `autonomy service` command"""

from pathlib import Path
from typing import List, Optional

import click
from aea.cli.utils.context import Context
from aea.cli.utils.decorators import pass_ctx

from autonomy.chain.config import ChainType
from autonomy.cli.helpers.chain import (
    activate_service,
    deploy_service,
    print_service_info,
    register_instance,
    terminate_service,
    unbond_service,
)
from autonomy.cli.mint import (
    hwi_flag,
    key_path_decorator,
    password_decorator,
    timeout_flag,
)
from autonomy.cli.utils.click_utils import chain_selection_flag


@click.group("service")
@pass_ctx
@chain_selection_flag()
@timeout_flag
def service(ctx: Context, chain_type: str, timeout: float) -> None:
    """Manage on-chain services."""

    ctx.config["chain_type"] = ChainType(chain_type)
    ctx.config["timeout"] = timeout


@service.command()
@pass_ctx
@click.argument("service_id", type=int)
@key_path_decorator
@hwi_flag
@password_decorator
def activate(
    ctx: Context,
    service_id: int,
    key: Path,
    hwi: bool,
    password: Optional[str],
) -> None:
    """Activate service."""

    activate_service(
        service_id=service_id,
        key=key,
        hwi=hwi,
        chain_type=ctx.config["chain_type"],
        password=password,
        timeout=ctx.config["timeout"],
    )


@service.command()
@pass_ctx
@click.argument("service_id", type=int)
@click.option(
    "-i",
    "--instance",
    "instances",
    type=str,
    required=True,
    multiple=True,
    help="Agent instance address",
)
@click.option(
    "-a",
    "--agent-id",
    "agent_ids",
    type=int,
    required=True,
    multiple=True,
    help="Agent ID",
)
@key_path_decorator
@hwi_flag
@password_decorator
def register(  # pylint: disable=too-many-arguments
    ctx: Context,
    service_id: int,
    instances: List[str],
    agent_ids: List[int],
    key: Path,
    hwi: bool,
    password: Optional[str],
) -> None:
    """Register instances."""

    register_instance(
        service_id=service_id,
        instances=instances,
        agent_ids=agent_ids,
        key=key,
        hwi=hwi,
        chain_type=ctx.config["chain_type"],
        password=password,
        timeout=ctx.config["timeout"],
    )


@service.command()
@pass_ctx
@click.argument("service_id", type=int)
@click.option(
    "-d",
    "--deployment-payload",
    type=int,
    help="Deployment payload value",
)
@key_path_decorator
@hwi_flag
@password_decorator
def deploy(
    ctx: Context,
    service_id: int,
    key: Path,
    hwi: bool,
    password: Optional[str],
    deployment_payload: Optional[str],
) -> None:
    """Deploy a service."""

    deploy_service(
        service_id=service_id,
        key=key,
        hwi=hwi,
        chain_type=ctx.config["chain_type"],
        password=password,
        deployment_payload=deployment_payload,
    )


@service.command(name="terminate")
@pass_ctx
@click.argument("service_id", type=int)
@key_path_decorator
@hwi_flag
@password_decorator
def _terminate(
    ctx: Context,
    service_id: int,
    key: Path,
    hwi: bool,
    password: Optional[str],
) -> None:
    """Terminate a service."""

    terminate_service(
        service_id=service_id,
        key=key,
        hwi=hwi,
        chain_type=ctx.config["chain_type"],
        password=password,
    )


@service.command(name="unbond")
@pass_ctx
@click.argument("service_id", type=int)
@key_path_decorator
@hwi_flag
@password_decorator
def _unbond(
    ctx: Context,
    service_id: int,
    key: Path,
    hwi: bool,
    password: Optional[str],
) -> None:
    """Unbond a service."""

    unbond_service(
        service_id=service_id,
        key=key,
        hwi=hwi,
        chain_type=ctx.config["chain_type"],
        password=password,
    )


@service.command(name="info")
@pass_ctx
@click.argument("service_id", type=int)
def _info(
    ctx: Context,
    service_id: int,
) -> None:
    """Print service information."""

    print_service_info(
        service_id=service_id,
        chain_type=ctx.config["chain_type"],
    )
