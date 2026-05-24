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
"""Implementation of the 'autonomy publish' subcommand."""

from pathlib import Path

import click
from aea.cli.publish import publish_agent_package
from aea.cli.utils.click_utils import registry_flag, reraise_as_click_exception
from aea.configurations.constants import (
    DEFAULT_AEA_CONFIG_FILE,
    DEFAULT_SERVICE_CONFIG_FILE,
)

from autonomy.cli.helpers.registry import publish_service_package


@click.command(name="publish")
@registry_flag()
@click.option(
    "--push-missing", is_flag=True, help="Push missing components on the registry."
)
@click.pass_context
def publish(
    click_context: click.Context, registry: str, push_missing: bool
) -> None:  # pylint: disable=unused-argument
    """Publish the agent or service on the registry."""

    with reraise_as_click_exception(Exception):
        if Path(click_context.obj.cwd, DEFAULT_SERVICE_CONFIG_FILE).exists():
            # TODO: support push_missing
            publish_service_package(click_context, registry)
        elif Path(
            click_context.obj.cwd, DEFAULT_AEA_CONFIG_FILE
        ).exists():  # pragma: nocover
            publish_agent_package(click_context, registry, push_missing)
        else:
            raise FileNotFoundError(
                "No package config found in this directory."
            )  # pragma: no cover
