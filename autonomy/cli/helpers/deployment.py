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

"""Deployment helpers."""
import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import click
from aea.configurations.data_types import PublicId
from aea.helpers.base import cd
from compose.cli import main as docker_compose
from compose.config.errors import ConfigurationError
from docker.errors import NotFound
from web3.exceptions import BadFunctionCallOutput

from autonomy.chain.config import ChainType, ContractConfigs
from autonomy.chain.exceptions import FailedToRetrieveComponentMetadata
from autonomy.chain.service import get_agent_instances, get_service_info
from autonomy.chain.utils import resolve_component_id
from autonomy.cli.helpers.chain import get_ledger_and_crypto_objects
from autonomy.cli.helpers.registry import fetch_service_ipfs
from autonomy.configurations.constants import DEFAULT_SERVICE_CONFIG_FILE
from autonomy.configurations.loader import load_service_config
from autonomy.constants import DEFAULT_BUILD_FOLDER
from autonomy.deploy.build import generate_deployment
from autonomy.deploy.constants import (
    AGENT_KEYS_DIR,
    BENCHMARKS_DIR,
    INFO,
    LOG_DIR,
    PERSISTENT_DATA_DIR,
    TM_STATE_DIR,
    VENVS_DIR,
)
from autonomy.deploy.generators.docker_compose.base import DockerComposeGenerator
from autonomy.deploy.image import build_image


def _build_dirs(build_dir: Path) -> None:
    """Build necessary directories."""

    for dir_path in [
        (PERSISTENT_DATA_DIR,),
        (PERSISTENT_DATA_DIR, LOG_DIR),
        (PERSISTENT_DATA_DIR, TM_STATE_DIR),
        (PERSISTENT_DATA_DIR, BENCHMARKS_DIR),
        (PERSISTENT_DATA_DIR, VENVS_DIR),
        (AGENT_KEYS_DIR,),
    ]:
        path = Path(build_dir, *dir_path)
        path.mkdir()
        # TOFIX: remove this safely
        try:
            os.chown(path, 1000, 1000)
        except PermissionError:  # pragma: no cover
            click.echo(
                f"Updating permissions failed for {path}, please do it manually."
            )


def run_deployment(
    build_dir: Path, no_recreate: bool = False, remove_orphans: bool = False
) -> None:
    """Run deployment."""

    click.echo(f"Running build @ {build_dir}")
    try:
        project = docker_compose.project_from_options(build_dir, {})
    except ConfigurationError as e:  # pragma: no cover
        if "Invalid interpolation format" in e.msg:
            raise click.ClickException(
                "Provided docker compose file contains environment placeholders, "
                "please use `--aev` flag if you intend to use environment variables."
            )
        raise

    try:
        commands = docker_compose.TopLevelCommand(project=project)
        commands.up(
            {
                "--detach": False,
                "--no-color": False,
                "--quiet-pull": False,
                "--no-deps": False,
                "--force-recreate": not no_recreate,
                "--always-recreate-deps": False,
                "--no-recreate": no_recreate,
                "--no-build": False,
                "--no-start": False,
                "--build": True,
                "--abort-on-container-exit": False,
                "--attach-dependencies": False,
                "--timeout": None,
                "--renew-anon-volumes": False,
                "--remove-orphans": remove_orphans,
                "--exit-code-from": None,
                "--scale": [],
                "--no-log-prefix": False,
                "SERVICE": None,
            }
        )
    except NotFound as e:  # pragma: no cover
        raise click.ClickException(e.explanation)


def build_deployment(  # pylint: disable=too-many-arguments, too-many-locals
    keys_file: Path,
    build_dir: Path,
    deployment_type: str,
    dev_mode: bool,
    force_overwrite: bool,
    number_of_agents: Optional[int] = None,
    password: Optional[str] = None,
    packages_dir: Optional[Path] = None,
    open_aea_dir: Optional[Path] = None,
    open_autonomy_dir: Optional[Path] = None,
    agent_instances: Optional[List[str]] = None,
    multisig_address: Optional[str] = None,
    log_level: str = INFO,
    apply_environment_variables: bool = False,
    image_version: Optional[str] = None,
    use_hardhat: bool = False,
    use_acn: bool = False,
) -> None:
    """Build deployment."""
    if build_dir.is_dir():  # pragma: no cover
        if not force_overwrite:
            raise click.ClickException(f"Build already exists @ {build_dir}")
        shutil.rmtree(build_dir)

    if not (Path.cwd() / DEFAULT_SERVICE_CONFIG_FILE).exists():
        raise FileNotFoundError(
            f"No service configuration found at {Path.cwd()}"
        )  # pragma: no cover

    click.echo(f"Building deployment @ {build_dir}")
    build_dir.mkdir()
    _build_dirs(build_dir)

    report = generate_deployment(
        service_path=Path.cwd(),
        type_of_deployment=deployment_type,
        keys_file=keys_file,
        private_keys_password=password,
        number_of_agents=number_of_agents,
        build_dir=build_dir,
        dev_mode=dev_mode,
        packages_dir=packages_dir,
        open_aea_dir=open_aea_dir,
        open_autonomy_dir=open_autonomy_dir,
        agent_instances=agent_instances,
        multisig_address=multisig_address,
        log_level=log_level,
        apply_environment_variables=apply_environment_variables,
        image_version=image_version,
        use_hardhat=use_hardhat,
        use_acn=use_acn,
    )
    click.echo(report)


def _resolve_on_chain_token_id(
    token_id: int,
    chain_type: ChainType,
) -> Tuple[Dict[str, str], List[str], str]:
    """Resolve service metadata from tokenID"""

    ledger_api, _ = get_ledger_and_crypto_objects(chain_type=chain_type)
    contract_address = ContractConfigs.service_registry.contracts[chain_type]

    click.echo(f"Fetching service metadata using chain type {chain_type.value}")

    try:
        metadata = resolve_component_id(
            ledger_api=ledger_api, contract_address=contract_address, token_id=token_id
        )
        info = get_agent_instances(
            ledger_api=ledger_api, chain_type=chain_type, token_id=token_id
        )
        agent_instances = info["agentInstances"]
        (_, multisig_address, *_,) = get_service_info(
            ledger_api=ledger_api, chain_type=chain_type, token_id=token_id
        )
    except FailedToRetrieveComponentMetadata as e:
        raise click.ClickException(str(e)) from e
    except BadFunctionCallOutput as e:
        raise click.ClickException(
            f"Cannot find the service registry deployment; Service contract address {contract_address}"
        ) from e

    return metadata, agent_instances, multisig_address


def build_and_deploy_from_token(  # pylint: disable=too-many-arguments, too-many-locals
    token_id: int,
    keys_file: Path,
    chain_type: ChainType,
    skip_image: bool,
    n: Optional[int],
    aev: bool = False,
    password: Optional[str] = None,
) -> None:
    """Build and run deployment from tokenID."""

    click.echo(f"Building service deployment using token ID: {token_id}")
    service_metadata, agent_instances, multisig_address = _resolve_on_chain_token_id(
        token_id=token_id,
        chain_type=chain_type,
    )

    click.echo("Service name: " + service_metadata["name"])
    *_, service_hash = service_metadata["code_uri"].split("//")
    public_id = PublicId(author="valory", name="service", package_hash=service_hash)
    service_path = fetch_service_ipfs(public_id)
    build_dir = service_path / DEFAULT_BUILD_FOLDER

    with cd(service_path):
        build_deployment(
            keys_file=keys_file,
            build_dir=build_dir,
            deployment_type=DockerComposeGenerator.deployment_type,
            dev_mode=False,
            force_overwrite=True,
            number_of_agents=n,
            agent_instances=agent_instances,
            multisig_address=multisig_address,
            apply_environment_variables=aev,
            password=password,
        )
        if not skip_image:
            click.echo("Building required images.")
            service = load_service_config(service_path, substitute_env_vars=aev)
            build_image(agent=service.agent)

    click.echo("Service build successful.")
    run_deployment(build_dir)
