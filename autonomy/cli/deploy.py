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

"""Deploy CLI module."""

import shutil
from pathlib import Path
from typing import Optional, cast

import click
from aea import AEA_DIR
from aea.cli.registry.settings import REGISTRY_REMOTE
from aea.cli.utils.click_utils import (
    password_option,
    registry_flag,
    reraise_as_click_exception,
)
from aea.cli.utils.context import Context
from aea.configurations.constants import DEFAULT_ENV_DOTFILE

from autonomy.chain.config import ChainType
from autonomy.cli.helpers.deployment import (
    build_and_deploy_from_token,
    build_deployment,
    run_deployment,
    stop_deployment,
)
from autonomy.cli.helpers.env import load_env_file
from autonomy.cli.utils.click_utils import (
    PathArgument,
    chain_selection_flag,
    image_author_option,
)
from autonomy.constants import DEFAULT_BUILD_FOLDER, DEFAULT_KEYS_FILE
from autonomy.deploy.base import (
    DEFAULT_AGENT_CPU_LIMIT,
    DEFAULT_AGENT_CPU_REQUEST,
    DEFAULT_AGENT_MEMORY_LIMIT,
    DEFAULT_AGENT_MEMORY_REQUEST,
    NotValidKeysFile,
)
from autonomy.deploy.constants import INFO, LOGGING_LEVELS
from autonomy.deploy.generators.docker_compose.base import DockerComposeGenerator
from autonomy.deploy.generators.kubernetes.base import KubernetesGenerator


def _validate_packages_path(path: Optional[Path] = None) -> Path:
    """Find packages dir for development mode."""
    path = Path(path or Path.cwd()).resolve()
    while path != path.root:
        if path.name == "packages" and (path / "packages.json").exists():
            return path
        path = path.parent
    raise click.ClickException(
        "Please provide path to packages directory for development mode"
    )


def _validate_open_aea_dir(path: Optional[Path] = None) -> Path:
    """Validate open-aea directory."""
    path = Path(path or Path(AEA_DIR).parent).resolve()
    for child in ("aea", "plugins", "setup.py"):
        if not (path / child).exists():
            raise click.ClickException(
                "Please provide valid open-aea repository path for development mode"
            )
    return path


@click.group(name="deploy")
@click.option(
    "--env-file",
    type=PathArgument(
        exists=True,
        dir_okay=False,
        file_okay=True,
    ),
    help="File containing environment variable mappings",
)
@click.pass_context
def deploy_group(
    click_context: click.Context,  # pylint: disable=unused-argument
    env_file: Optional[Path],
) -> None:
    """Deploy an agent service."""
    dot_env_file = Path.cwd() / DEFAULT_ENV_DOTFILE
    if dot_env_file.exists():
        load_env_file(file=dot_env_file)
    if env_file is not None:
        load_env_file(file=env_file, serialize_json=True)


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
@click.option(
    "-ltm",
    "--local-tm-setup",
    "use_tm_testnet_setup",
    is_flag=True,
    default=False,
    help="Use local tendermint chain setup.",
)
@click.option("--image-version", type=str, help="Define runtime image version.")
@click.option(
    "--agent-cpu-request",
    type=float,
    help="Set agent CPU usage request.",
    default=DEFAULT_AGENT_CPU_REQUEST,
)
@click.option(
    "--agent-memory-request",
    type=int,
    help="Set agent memory usage request.",
    default=DEFAULT_AGENT_MEMORY_REQUEST,
)
@click.option(
    "--agent-cpu-limit",
    type=float,
    help="Set agent CPU usage limit.",
    default=DEFAULT_AGENT_CPU_LIMIT,
)
@click.option(
    "--agent-memory-limit",
    type=int,
    help="Set agent memory usage limit.",
    default=DEFAULT_AGENT_MEMORY_LIMIT,
)
@registry_flag()
@password_option(confirmation_prompt=True)
@image_author_option
@click.pass_context
def build_deployment_command(  # pylint: disable=too-many-arguments, too-many-locals
    click_context: click.Context,
    keys_file: Optional[Path],
    deployment_type: str,
    output_dir: Optional[Path],
    dev_mode: bool,
    registry: str,
    number_of_agents: Optional[int] = None,
    password: Optional[str] = None,
    open_aea_dir: Optional[Path] = None,
    packages_dir: Optional[Path] = None,
    log_level: str = INFO,
    aev: bool = False,
    image_version: Optional[str] = None,
    use_hardhat: bool = False,
    use_acn: bool = False,
    use_tm_testnet_setup: bool = False,
    image_author: Optional[str] = None,
    agent_cpu_limit: Optional[float] = None,
    agent_memory_limit: Optional[int] = None,
    agent_cpu_request: Optional[float] = None,
    agent_memory_request: Optional[int] = None,
) -> None:
    """Build deployment setup for n agents."""
    if password is not None:  # pragma: nocover
        click.echo(
            "WARNING: `--password` flag has been deprecated, "
            "use `OPEN_AUTONOMY_PRIVATE_KEY_PASSWORD` to export the password value"
        )

    keys_file = Path(keys_file or DEFAULT_KEYS_FILE).absolute()
    if not keys_file.exists() and not dev_mode:
        message = f"No such file or directory: {keys_file}. Please provide valid path for keys file."
        raise click.ClickException(message)

    build_dir = Path(output_dir or DEFAULT_BUILD_FOLDER).absolute()
    if dev_mode:
        packages_dir = _validate_packages_path(path=packages_dir)
        open_aea_dir = _validate_open_aea_dir(path=open_aea_dir)

    ctx = cast(Context, click_context.obj)
    ctx.registry_type = registry

    try:
        build_deployment(
            keys_file=keys_file,
            build_dir=build_dir,
            deployment_type=deployment_type,
            dev_mode=dev_mode,
            number_of_agents=number_of_agents,
            packages_dir=packages_dir,
            open_aea_dir=open_aea_dir,
            log_level=log_level,
            apply_environment_variables=aev,
            image_version=image_version,
            use_hardhat=use_hardhat,
            use_acn=use_acn,
            use_tm_testnet_setup=use_tm_testnet_setup,
            image_author=image_author,
            resources={
                "agent": {
                    "limit": {"cpu": agent_cpu_limit, "memory": agent_memory_limit},
                    "requested": {
                        "cpu": agent_cpu_request,
                        "memory": agent_memory_request,
                    },
                }
            },
        )
    except (NotValidKeysFile, FileNotFoundError, FileExistsError) as e:
        shutil.rmtree(build_dir)
        raise click.ClickException(str(e)) from e


@deploy_group.command(name="run")
@click.option(
    "--build-dir",
    type=click.Path(),
    help="Path to the deployment build directory.",
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
@click.option(
    "--detach",
    is_flag=True,
    default=False,
    help="Run service in the background.",
)
def run(
    build_dir: Path, no_recreate: bool, remove_orphans: bool, detach: bool = False
) -> None:
    """Run deployment."""
    build_dir = Path(build_dir or Path.cwd()).absolute()
    if not (build_dir / DockerComposeGenerator.output_name).exists():
        raise click.ClickException(
            f"Deployment configuration does not exist @ {build_dir}"
        )
    run_deployment(build_dir, no_recreate, remove_orphans, detach=detach)


@deploy_group.command(name="stop")
@click.option(
    "--build-dir",
    type=click.Path(),
    help="Path to the deployment build directory.",
)
def stop(build_dir: Path) -> None:
    """Stop a running deployment."""
    build_dir = Path(build_dir or Path.cwd()).absolute()
    if not (build_dir / DockerComposeGenerator.output_name).exists():
        raise click.ClickException(
            f"Deployment configuration does not exist @ {build_dir}"
        )
    stop_deployment(build_dir=build_dir)


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
    "--no-deploy",
    is_flag=True,
    help="If set to true, the deployment won't run automatically",
)
@click.option(
    "--detach",
    is_flag=True,
    default=False,
    help="Run service in the background.",
)
@click.option(
    "--agent-cpu-request",
    type=float,
    help="Set agent CPU usage request.",
    default=DEFAULT_AGENT_CPU_REQUEST,
)
@click.option(
    "--agent-memory-request",
    type=int,
    help="Set agent memory usage request.",
    default=DEFAULT_AGENT_MEMORY_REQUEST,
)
@click.option(
    "--agent-cpu-limit",
    type=float,
    help="Set agent CPU usage limit.",
    default=DEFAULT_AGENT_CPU_LIMIT,
)
@click.option(
    "--agent-memory-limit",
    type=int,
    help="Set agent memory usage limit.",
    default=DEFAULT_AGENT_MEMORY_LIMIT,
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
    deployment_type: str,
    no_deploy: bool,
    detach: bool,
    aev: bool = False,
    password: Optional[str] = None,
    agent_cpu_limit: Optional[float] = None,
    agent_memory_limit: Optional[int] = None,
    agent_cpu_request: Optional[float] = None,
    agent_memory_request: Optional[int] = None,
) -> None:
    """Run service deployment."""
    if password is not None:  # pragma: nocover
        click.echo(
            "WARNING: `--password` flag has been deprecated, "
            "use `OPEN_AUTONOMY_PRIVATE_KEY_PASSWORD` to export the password value"
        )

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
            deployment_type=deployment_type,
            aev=aev,
            no_deploy=no_deploy,
            detach=detach,
            resources={
                "agent": {
                    "limit": {"cpu": agent_cpu_limit, "memory": agent_memory_limit},
                    "requested": {
                        "cpu": agent_cpu_request,
                        "memory": agent_memory_request,
                    },
                }
            },
        )
