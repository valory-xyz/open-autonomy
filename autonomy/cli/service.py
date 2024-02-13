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
from autonomy.cli.helpers.chain import ServiceHelper, print_service_info
from autonomy.cli.mint import (
    dry_run_flag,
    hwi_flag,
    key_path_decorator,
    password_decorator,
    retries_flag,
    sleep_flag,
    timeout_flag,
    token_flag,
)
from autonomy.cli.utils.click_utils import chain_selection_flag


service_id_flag = click.argument("service_id", type=int)


@click.group("service")
@pass_ctx
@timeout_flag
@retries_flag
@sleep_flag
@dry_run_flag
@chain_selection_flag()
def service(
    ctx: Context,
    chain_type: str,
    timeout: float,
    retries: int,
    sleep: float,
    dry_run: bool,
) -> None:
    """Manage on-chain services."""

    ctx.config["chain_type"] = ChainType(chain_type)
    ctx.config["timeout"] = timeout
    ctx.config["retries"] = retries
    ctx.config["sleep"] = sleep
    ctx.config["dry_run"] = dry_run


@service.command(name="activate")
@pass_ctx
@service_id_flag
@key_path_decorator
@hwi_flag
@token_flag
@password_decorator
def _activate(
    ctx: Context,
    service_id: int,
    key: Path,
    hwi: bool,
    token: Optional[str],
    password: Optional[str],
) -> None:
    """Activate service."""
    ServiceHelper(
        service_id=service_id,
        chain_type=ctx.config["chain_type"],
        key=key,
        password=password,
        hwi=hwi,
        dry_run=ctx.config.get("dry_run"),
        timeout=ctx.config.get("timeout"),
        retries=ctx.config.get("retries"),
        sleep=ctx.config.get("sleep"),
    ).check_is_service_token_secured(
        token=token,
    ).activate_service()


@service.command("register")
@pass_ctx
@service_id_flag
@key_path_decorator
@hwi_flag
@token_flag
@password_decorator
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
def _register(  # pylint: disable=too-many-arguments
    ctx: Context,
    service_id: int,
    instances: List[str],
    agent_ids: List[int],
    token: Optional[str],
    key: Path,
    hwi: bool,
    password: Optional[str],
) -> None:
    """Register instances."""
    ServiceHelper(
        service_id=service_id,
        chain_type=ctx.config["chain_type"],
        key=key,
        password=password,
        hwi=hwi,
        dry_run=ctx.config.get("dry_run"),
        timeout=ctx.config.get("timeout"),
        retries=ctx.config.get("retries"),
        sleep=ctx.config.get("sleep"),
    ).check_is_service_token_secured(
        token=token,
    ).register_instance(
        instances=instances,
        agent_ids=agent_ids,
    )


@service.command("deploy")
@click.option(
    "--reuse-multisig",
    is_flag=True,
    help="Reuse mutlisig from previous deployment.",
)
@pass_ctx
@service_id_flag
@key_path_decorator
@hwi_flag
@password_decorator
@click.option(
    "-f",
    "--fallback-handler",
    type=str,
    help="Fallback handler address for the gnosis safe multisig",
)
def _deploy(  # pylint: disable=too-many-arguments
    ctx: Context,
    service_id: int,
    key: Path,
    hwi: bool,
    reuse_multisig: bool,
    password: Optional[str],
    fallback_handler: Optional[str],
) -> None:
    """Deploy a service."""
    ServiceHelper(
        service_id=service_id,
        chain_type=ctx.config["chain_type"],
        key=key,
        password=password,
        hwi=hwi,
        dry_run=ctx.config.get("dry_run"),
        timeout=ctx.config.get("timeout"),
        retries=ctx.config.get("retries"),
        sleep=ctx.config.get("sleep"),
    ).deploy_service(
        reuse_multisig=reuse_multisig,
        fallback_handler=fallback_handler,
    )


@service.command(name="terminate")
@pass_ctx
@service_id_flag
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
    ServiceHelper(
        service_id=service_id,
        chain_type=ctx.config["chain_type"],
        key=key,
        password=password,
        hwi=hwi,
        dry_run=ctx.config.get("dry_run"),
        timeout=ctx.config.get("timeout"),
        retries=ctx.config.get("retries"),
        sleep=ctx.config.get("sleep"),
    ).terminate_service()


@service.command(name="unbond")
@pass_ctx
@service_id_flag
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
    ServiceHelper(
        service_id=service_id,
        chain_type=ctx.config["chain_type"],
        key=key,
        password=password,
        hwi=hwi,
        dry_run=ctx.config.get("dry_run"),
        timeout=ctx.config.get("timeout"),
        retries=ctx.config.get("retries"),
        sleep=ctx.config.get("sleep"),
    ).unbond_service()


@service.command(name="info")
@pass_ctx
@service_id_flag
def _info(
    ctx: Context,
    service_id: int,
) -> None:
    """Print service information."""
    print_service_info(
        service_id=service_id,
        chain_type=ctx.config["chain_type"],
    )
