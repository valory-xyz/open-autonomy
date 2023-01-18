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

"""Deploy CLI module."""

import shutil
from pathlib import Path
from typing import Optional, cast

import click
from aea.cli.registry.settings import REGISTRY_REMOTE
from aea.cli.utils.click_utils import (
    password_option,
    registry_flag,
    reraise_as_click_exception,
)
from aea.cli.utils.context import Context

from autonomy.chain.config import ChainType
from autonomy.cli.helpers.deployment import (
    build_and_deploy_from_token,
    build_deployment,
    run_deployment,
)
from autonomy.cli.utils.click_utils import chain_selection_flag
from autonomy.constants import DEFAULT_BUILD_FOLDER, DEFAULT_KEYS_FILE
from autonomy.deploy.base import NotValidKeysFile
from autonomy.deploy.constants import INFO, LOGGING_LEVELS
from autonomy.deploy.generators.docker_compose.base import DockerComposeGenerator
from autonomy.deploy.generators.kubernetes.base import KubernetesGenerator


PACKAGES_DIR = "packages_dir"
OPEN_AEA_DIR = "open_aea_dir"
OPEN_AUTONOMY_DIR = "open_autonomy_dir"


@click.group(name="deploy")
@click.pass_context
def deploy_group(
    click_context: click.Context,  # pylint: disable=unused-argument
) -> None:
    """Deploy an agent service."""


@deploy_group.command(name="build")
@click.argument("keys_file", type=str, required=False)
@click.option(
    "--o",
    "output_dir",
    type=click.Path(exists=False, dir_okay=True),
    help="Path to output dir.",
)
@click.option(
    "--n",
    "number_of_agents",
    type=int,
    default=None,
    help="Number of agents.",
)
@click.option(
    "--docker",
    "deployment_type",
    flag_value=DockerComposeGenerator.deployment_type,
    default=True,
    help="Use docker as a backend.",
)
@click.option(
    "--kubernetes",
    "deployment_type",
    flag_value=KubernetesGenerator.deployment_type,
    help="Use kubernetes as a backend.",
)
@click.option(
    "--dev",
    "dev_mode",
    is_flag=True,
    default=False,
    help="Create development environment.",
)
@click.option(
    "--force",
    "force_overwrite",
    is_flag=True,
    default=False,
    help="Remove existing build and overwrite with new one.",
)
@click.option(
    "--log-level",
    type=click.Choice(choices=LOGGING_LEVELS, case_sensitive=True),
    help="Logging level for runtime.",
    default=INFO,
)
@click.option(
    "--packages-dir", type=click.Path(), help="Path to packages dir (Use with dev mode)"
)
@click.option(
    "--open-aea-dir",
    type=click.Path(),
    help="Path to open-aea repo (Use with dev mode)",
)
@click.option(
    "--open-autonomy-dir",
    type=click.Path(),
    help="Path to open-autonomy repo (Use with dev mode)",
)
@click.option(
    "--aev",
    is_flag=True,
    default=False,
    help="Apply environment variable when loading service config.",
)
@click.option(
    "--use-hardhat",
    is_flag=True,
    default=False,
    help="Include a hardhat node in the deployment setup.",
)
@click.option(
    "--use-acn",
    is_flag=True,
    default=False,
    help="Include an ACN node in the deployment setup.",
)
@click.option("--image-version", type=str, help="Define runtime image version.")
@registry_flag()
@password_option(confirmation_prompt=True)
@click.pass_context
def build_deployment_command(  # pylint: disable=too-many-arguments, too-many-locals
    click_context: click.Context,
    keys_file: Optional[Path],
    deployment_type: str,
    output_dir: Optional[Path],
    dev_mode: bool,
    force_overwrite: bool,
    registry: str,
    number_of_agents: Optional[int] = None,
    password: Optional[str] = None,
    open_aea_dir: Optional[Path] = None,
    packages_dir: Optional[Path] = None,
    open_autonomy_dir: Optional[Path] = None,
    log_level: str = INFO,
    aev: bool = False,
    image_version: Optional[str] = None,
    use_hardhat: bool = False,
    use_acn: bool = False,
) -> None:
    """Build deployment setup for n agents."""

    keys_file = Path(keys_file or DEFAULT_KEYS_FILE).absolute()
    if not keys_file.exists():
        message = f"No such file or directory: {keys_file}. Please provide valid path for keys file."
        raise click.ClickException(message)

    build_dir = Path(output_dir or DEFAULT_BUILD_FOLDER).absolute()
    packages_dir = Path(packages_dir or Path.cwd() / "packages").absolute()
    open_aea_dir = Path(open_aea_dir or Path.home() / "open-aea").absolute()
    open_autonomy_dir = Path(
        open_autonomy_dir or Path.home() / "open-autonomy"
    ).absolute()

    if dev_mode:
        for name, path in (
            (PACKAGES_DIR, packages_dir),
            (OPEN_AEA_DIR, open_aea_dir),
            (OPEN_AUTONOMY_DIR, open_autonomy_dir),
        ):
            if not path.exists():
                flag = "--" + "-".join(name.split("_"))
                raise click.ClickException(
                    f"Path does not exist @ {path} for {name}; Please provide proper value for {flag}"
                )

    ctx = cast(Context, click_context.obj)
    ctx.registry_type = registry

    try:
        build_deployment(
            keys_file=keys_file,
            build_dir=build_dir,
            deployment_type=deployment_type,
            dev_mode=dev_mode,
            force_overwrite=force_overwrite,
            number_of_agents=number_of_agents,
            password=password,
            packages_dir=packages_dir,
            open_aea_dir=open_aea_dir,
            open_autonomy_dir=open_autonomy_dir,
            log_level=log_level,
            apply_environment_variables=aev,
            image_version=image_version,
            use_hardhat=use_hardhat,
            use_acn=use_acn,
        )
    except (NotValidKeysFile, FileNotFoundError, FileExistsError) as e:
        shutil.rmtree(build_dir)
        raise click.ClickException(str(e)) from e


@deploy_group.command(name="run")
@click.option(
    "--build-dir",
    type=click.Path(),
)
@click.option(
    "--no-recreate",
    is_flag=True,
    default=False,
    help="If containers already exist, don't recreate them.",
)
@click.option(
    "--remove-orphans",
    is_flag=True,
    default=False,
    help="Remove containers for services not defined in the Compose file.",
)
def run(build_dir: Path, no_recreate: bool, remove_orphans: bool) -> None:
    """Run deployment."""
    build_dir = Path(build_dir or Path.cwd()).absolute()

    if not (build_dir / DockerComposeGenerator.output_name).exists():
        raise click.ClickException(
            f"Deployment configuration does not exist @ {build_dir}"
        )

    run_deployment(build_dir, no_recreate, remove_orphans)


@deploy_group.command(name="from-token")
@click.argument("token_id", type=int)
@click.argument("keys_file", type=click.Path())
@click.option("--n", type=int, help="Number of agents to include in the build.")
@click.option("--skip-image", is_flag=True, default=False, help="Skip building images.")
@click.option(
    "--aev",
    is_flag=True,
    default=False,
    help="Apply environment variable when loading service config.",
)
@chain_selection_flag(help_string_format="Use {} chain to resolve the token id.")
@click.pass_context
@password_option(confirmation_prompt=True)
def run_deployment_from_token(  # pylint: disable=too-many-arguments, too-many-locals
    click_context: click.Context,
    token_id: int,
    keys_file: Path,
    chain_type: ChainType,
    skip_image: bool,
    n: Optional[int],
    aev: bool = False,
    password: Optional[str] = None,
) -> None:
    """Run service deployment."""

    ctx = cast(Context, click_context.obj)
    ctx.registry_type = REGISTRY_REMOTE
    keys_file = Path(keys_file or DEFAULT_KEYS_FILE).absolute()

    with reraise_as_click_exception(
        NotValidKeysFile, FileNotFoundError, FileExistsError
    ):
        build_and_deploy_from_token(
            token_id=token_id,
            keys_file=keys_file,
            chain_type=ChainType(chain_type),
            skip_image=skip_image,
            n=n,
            aev=aev,
            password=password,
        )
