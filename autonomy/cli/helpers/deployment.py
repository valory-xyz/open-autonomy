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

"""Deployment helpers."""
import os
import shutil
from pathlib import Path
from typing import List, Optional

import click
from aea.configurations.constants import SKILL
from aea.helpers.io import open_file
from aea.helpers.yaml_utils import yaml_dump_all, yaml_load_all
from compose.cli import main as docker_compose

from autonomy.configurations.constants import DEFAULT_SERVICE_CONFIG_FILE
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
        except PermissionError:
            click.echo(
                f"Updating permissions failed for {path}, please do it manually."
            )


def run_deployment(
    build_dir: Path, no_recreate: bool = False, remove_orphans: bool = False
) -> None:
    """Run deployment."""

    click.echo(f"Running build @ {build_dir}")
    project = docker_compose.project_from_options(build_dir, {})
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
    log_level: str = INFO,
    substitute_env_vars: bool = False,
    image_version: Optional[str] = None,
    use_hardhat: bool = False,
    use_acn: bool = False,
) -> None:
    """Build deployment."""
    if build_dir.is_dir():
        if not force_overwrite:
            raise click.ClickException(f"Build already exists @ {build_dir}")
        shutil.rmtree(build_dir)

    click.echo(f"Building deployment @ {build_dir}")
    build_dir.mkdir()
    _build_dirs(build_dir)

    report = generate_deployment(
        service_path=Path.cwd(),
        type_of_deployment=deployment_type,
        private_keys_file_path=keys_file,
        private_keys_password=password,
        number_of_agents=number_of_agents,
        build_dir=build_dir,
        dev_mode=dev_mode,
        packages_dir=packages_dir,
        open_aea_dir=open_aea_dir,
        open_autonomy_dir=open_autonomy_dir,
        agent_instances=agent_instances,
        log_level=log_level,
        substitute_env_vars=substitute_env_vars,
        image_version=image_version,
        use_hardhat=use_hardhat,
        use_acn=use_acn,
    )
    click.echo(report)


# TODO: add validation
def update_multisig_address(service_path: Path, address: str) -> None:
    """Update the multisig address on the service config."""

    with open_file(service_path / DEFAULT_SERVICE_CONFIG_FILE) as fp:
        config, *overrides = yaml_load_all(
            fp,
        )

    for override in overrides:
        if override["type"] == SKILL:
            override["setup_args"]["args"]["setup"]["safe_contract_address"] = [
                address,
            ]

    with open_file(service_path / DEFAULT_SERVICE_CONFIG_FILE, mode="w+") as fp:
        yaml_dump_all([config, *overrides], fp)
