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
"""Implementation of the 'aea build_deployment' subcommand."""
from typing import Optional

import aea
import click
from aea.cli.plugin import with_plugins
from aea.cli.utils.click_utils import registry_path_option
from aea.cli.utils.config import get_registry_path_from_cli_config
from aea.cli.utils.context import Context
from aea.cli.utils.loggers import logger, simple_verbosity_option
from aea.helpers.win32 import enable_ctrl_c_support
from pkg_resources import iter_entry_points

from deployments.constants import DEFAULT_KEY_PATH
from deployments.create_deployment import generate_deployment
from deployments.generators.docker_compose.docker_compose import DockerComposeGenerator
from deployments.generators.kubernetes.kubernetes import KubernetesGenerator
from deployments.image_builder import ImageBuilder


@click.command()
@click.option(
    "--valory-app",
)
@click.option(
    "--deployment-file-path",
)
@click.option("--keys-file-path", type=str, default=str(DEFAULT_KEY_PATH))
@click.option(
    "--deployment-type",
    required=True,
    type=click.Choice(
        [DockerComposeGenerator.deployment_type, KubernetesGenerator.deployment_type],
        case_sensitive=False,
    ),
)
@click.option("--configure-tendermint", is_flag=True, default=False)
def build_deployment(
    valory_app: str,
    deployment_type: str,
    configure_tendermint: bool,
    keys_file_path: str,
    deployment_file_path: Optional[str],
) -> None:
    """Build the agent and its components."""

    report = generate_deployment(
        type_of_deployment=deployment_type,
        valory_application=valory_app,
        configure_tendermint=configure_tendermint,
        deployment_file_path=deployment_file_path,
        private_keys_file_path=keys_file_path,
    )
    print(report)


@click.command()
@click.option(
    "--valory-app",
)
@click.option(
    "--profile",
    required=True,
)
@click.option(
    "--deployment-file-path",
)
@click.option("--push", is_flag=True, default=False)
def build_images(
    profile: str,
    valory_app: Optional[str],
    deployment_file_path: Optional[str],
    push: bool,
) -> None:
    """Build the agent and its components."""
    image_builder = ImageBuilder()
    image_builder.build_images(
        profile=profile,
        deployment_file_path=deployment_file_path,
        valory_application=valory_app,
        push=push,
    )


@with_plugins(iter_entry_points("aea.cli"))
@click.group(name="aea")  # type: ignore
@click.version_option(aea.__version__, prog_name="aea")
@simple_verbosity_option(logger, default="INFO")
@click.option(
    "-s",
    "--skip-consistency-check",
    "skip_consistency_check",
    is_flag=True,
    required=False,
    default=False,
    help="Skip consistency checks of agent during command execution.",
)
@registry_path_option
@click.pass_context
def cli(
    click_context: click.Context,
    skip_consistency_check: bool,
    registry_path: Optional[str],
) -> None:
    """Command-line tool for setting up an Autonomous Economic Agent (AEA)."""
    verbosity_option = click_context.meta.pop("verbosity")
    if not registry_path:
        registry_path = get_registry_path_from_cli_config()
    click_context.obj = Context(
        cwd=".", verbosity=verbosity_option, registry_path=registry_path
    )
    click_context.obj.set_config("skip_consistency_check", skip_consistency_check)

    # enables CTRL+C support on windows!
    enable_ctrl_c_support()


if __name__ == "__main__":
    cli.add_command(build_deployment)
    cli.add_command(build_images)
    cli()  # pylint: disable=no-value-for-parameter
