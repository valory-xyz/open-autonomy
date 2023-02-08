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

"""Helpers for analyse command"""

import tempfile
from pathlib import Path
from typing import List, Optional

import click
from aea.components.base import load_aea_package
from aea.configurations.base import AgentConfig
from aea.configurations.constants import (
    DEFAULT_AEA_CONFIG_FILE,
    DEFAULT_SKILL_CONFIG_FILE,
)
from aea.configurations.data_types import PackageType, PublicId
from aea.configurations.loader import load_configuration_object
from aea.package_manager.v1 import PackageManagerV1
from aea_cli_ipfs.ipfs_utils import IPFSTool

from autonomy.analyse.dialogues import check_dialogues_in_a_skill_package
from autonomy.analyse.service import ServiceAnalyser, ServiceValidationFailed
from autonomy.chain.config import ChainType
from autonomy.cli.helpers.chain import get_ledger_and_crypto_objects
from autonomy.cli.utils.click_utils import sys_path_patch


def load_package_tree(packages_dir: Path) -> None:
    """Load package tree."""

    pm = PackageManagerV1.from_dir(packages_dir=packages_dir)

    for package_id in pm.iter_dependency_tree():
        if package_id.package_type in (PackageType.AGENT, PackageType.SERVICE):
            continue

        package_path = pm.package_path_from_package_id(package_id=package_id)
        config_obj = load_configuration_object(
            package_type=package_id.package_type, directory=package_path
        )
        config_obj.directory = package_path
        load_aea_package(configuration=config_obj)


def list_all_skill_yaml_files(registry_path: Path) -> List[Path]:
    """List all skill yaml files in a local registry"""
    return sorted(registry_path.glob(f"*/skills/*/{DEFAULT_SKILL_CONFIG_FILE}"))


def run_dialogues_check(
    packages_dir: Path,
    ignore: List[str],
    dialogues: List[str],
) -> None:
    """Run dialogues check."""

    try:
        with sys_path_patch(packages_dir.parent):
            load_package_tree(packages_dir=packages_dir)
            for yaml_file in list_all_skill_yaml_files(packages_dir):
                if yaml_file.parent.name in ignore:
                    click.echo(f"Skipping {yaml_file.parent.name}")
                    continue

                click.echo(f"Checking {yaml_file.parent.name}")
                check_dialogues_in_a_skill_package(
                    config_file=yaml_file,
                    dialogues=dialogues,
                )
    except (ValueError, FileNotFoundError, ImportError) as e:
        raise click.ClickException(str(e))


def _load_agent_from_ipfs(agent: PublicId) -> AgentConfig:
    """Load agent config from the IPFS hash."""
    ipfs_tool = IPFSTool()

    with tempfile.TemporaryDirectory() as agent_dir:
        agent_config_content = ipfs_tool.client.cat(
            f"{agent.hash}/{agent.name}/{DEFAULT_AEA_CONFIG_FILE}"
        )

        Path(agent_dir, DEFAULT_AEA_CONFIG_FILE).write_bytes(agent_config_content)

        return load_configuration_object(
            package_type=PackageType.AGENT,
            directory=Path(agent_dir),
        )


def check_service_readiness(
    token_id: Optional[int],
    service_path: Path,
    chain_type: ChainType,
) -> None:
    """Check deployment readiness of a service."""

    try:
        service_analyser = ServiceAnalyser(service_path=service_path)
        if token_id is not None:
            click.echo("Checking if the service is deployed on-chain")
            ledger_api, _ = get_ledger_and_crypto_objects(chain_type=chain_type)
            service_analyser.check_on_chain_state(
                ledger_api=ledger_api,
                chain_type=chain_type,
                token_id=token_id,
            )

        ipfs_pins = IPFSTool().all_pins()

        click.echo("Verifying overrides")
        service_analyser.validate_service_overrides()

        click.echo("Checking if the agent package is published")
        service_analyser.check_agent_package_published(ipfs_pins=ipfs_pins)

        agent_config = _load_agent_from_ipfs(
            agent=service_analyser.service_config.agent
        )
        click.echo("Cross verifying overrides between agent and service")
        service_analyser.verify_overrides(agent_config=agent_config)
        service_analyser.validate_agent_overrides(agent_config=agent_config)

        click.echo("Checking if agent dependencies are published")
        service_analyser.check_agent_dependencies_published(
            ipfs_pins=ipfs_pins, agent_config=agent_config
        )
        click.echo("Service is ready to be deployed.")
    except ServiceValidationFailed as e:
        raise click.ClickException(str(e)) from e
