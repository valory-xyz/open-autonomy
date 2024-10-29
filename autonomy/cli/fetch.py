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
"""Implementation of the 'autonomy fetch' subcommand."""

from typing import Union, cast

import click
from aea.cli.fetch import NotAnAgentPackage, do_fetch
from aea.cli.utils.click_utils import registry_flag
from aea.cli.utils.context import Context
from aea.configurations.base import PublicId
from aea.configurations.constants import AGENT, SERVICE

from autonomy.chain.config import ChainType
from autonomy.cli.helpers.deployment import _resolve_on_chain_token_id
from autonomy.cli.helpers.registry import fetch_service, fetch_service_ipfs
from autonomy.cli.utils.click_utils import PublicIdOrHashOrTokenId, chain_selection_flag


@click.command(name="fetch")
@registry_flag()
@click.option(
    "--alias",
    type=str,
    required=False,
    help="Provide a local alias for the agent.",
)
@click.option(
    "--agent",
    "package_type",
    help="Specify the package type as agent (default).",
    default=True,
    flag_value=AGENT,
)
@click.option(
    "--service",
    "package_type",
    help="Specify the package type as service.",
    flag_value=SERVICE,
)
@click.argument("public-id", type=PublicIdOrHashOrTokenId(), required=True)
@chain_selection_flag(help_string_format="Use {} chain to resolve the token id.")
@click.pass_context
def fetch(
    click_context: click.Context,
    public_id: Union[PublicId, int],
    alias: str,
    package_type: str,
    registry: str,
    chain_type: str,
) -> None:
    """Fetch an agent from the registry."""
    ctx = cast(Context, click_context.obj)
    ctx.registry_type = registry

    try:
        if isinstance(public_id, int):
            (
                service_metadata,
                *_,
            ) = _resolve_on_chain_token_id(
                token_id=public_id,
                chain_type=ChainType(chain_type),
            )

            click.echo("Service name: " + service_metadata["name"])
            *_, service_hash = service_metadata["code_uri"].split("//")
            public_id = PublicId(
                author="valory", name="service", package_hash=service_hash
            )
            fetch_service_ipfs(public_id)
        elif package_type == AGENT:
            do_fetch(ctx, public_id, alias)
        else:
            fetch_service(ctx, public_id, alias)
    except NotAnAgentPackage as e:
        raise click.ClickException(
            "Downloaded packages is not an agent package, "
            "if you intend to download a service please use `--service` flag "
            "or check the hash"
        ) from e
    except Exception as e:  # pylint: disable=broad-except
        raise click.ClickException(str(e)) from e
