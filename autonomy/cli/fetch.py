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
"""Implementation of the 'autonomy fetch' subcommand."""

from typing import cast

import click
from aea.cli.fetch import NotAnAgentPackage, do_fetch
from aea.cli.utils.click_utils import PublicIdParameter, registry_flag
from aea.cli.utils.context import Context
from aea.configurations.base import PublicId
from aea.configurations.constants import AGENT, SERVICE

from autonomy.cli.helpers.registry import fetch_service


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
@click.argument("public-id", type=PublicIdParameter(), required=True)
@click.pass_context
def fetch(
    click_context: click.Context,
    public_id: PublicId,
    alias: str,
    package_type: str,
    registry: str,
) -> None:
    """Fetch an agent from the registry."""
    ctx = cast(Context, click_context.obj)
    ctx.registry_type = registry

    try:
        if package_type == AGENT:
            do_fetch(ctx, public_id, alias)
        else:
            fetch_service(ctx, public_id)
    except NotAnAgentPackage as e:
        raise click.ClickException(
            "Downloaded packages is not an agent package, "
            "if you intend to download a service please use `--service` flag "
            "or check the hash"
        ) from e
    except Exception as e:  # pylint: disable=broad-except
        raise click.ClickException(str(e)) from e
