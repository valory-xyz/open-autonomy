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

"""Scaffold skill from an FSM"""


import os
import re
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Type

import click
from aea.cli.fingerprint import fingerprint_item
from aea.cli.utils.context import Context
from aea.configurations.base import (
    AgentConfig,
    SkillComponentConfiguration,
    SkillConfig,
)
from aea.configurations.constants import (
    DEFAULT_AEA_CONFIG_FILE,
    DEFAULT_SKILL_CONFIG_FILE,
    SKILL,
    SKILLS,
)

# the decoration does side-effect on the 'aea scaffold' command
from aea.configurations.data_types import CRUDCollection, PackageType, PublicId
from aea.package_manager.v1 import PackageManagerV1

from autonomy.analyse.abci.app_spec import DFA, FSMSpecificationLoader
from autonomy.configurations.constants import INIT_PY, PYCACHE
from autonomy.constants import ABSTRACT_ROUND_ABCI_SKILL_WITH_HASH
from autonomy.fsm.scaffold.base import AbstractFileGenerator
from autonomy.fsm.scaffold.constants import ABCI_APP, ROUND_BEHAVIOUR
from autonomy.fsm.scaffold.generators.components import (
    BehaviourFileGenerator,
    DialoguesFileGenerator,
    HandlersFileGenerator,
    ModelsFileGenerator,
    PayloadsFileGenerator,
    RoundFileGenerator,
)
from autonomy.fsm.scaffold.generators.tests import (
    BehaviourTestsFileGenerator,
    DialoguesTestFileGenerator,
    HandlersTestFileGenerator,
    ModelTestFileGenerator,
    PayloadTestsFileGenerator,
    RoundTestsFileGenerator,
)
from autonomy.fsm.scaffold.templates import COPYRIGHT_HEADER


TO_LOCAL_REGISTRY_FLAG = "to_local_registry"

ABSTRACT_ROUND_SKILL_PUBLIC_ID = PublicId.from_str(ABSTRACT_ROUND_ABCI_SKILL_WITH_HASH)


class SkillConfigUpdater:  # pylint: disable=too-few-public-methods
    """Update the skill configuration according to the Abci classes."""

    def __init__(self, ctx: Context, skill_dir: Path, dfa: DFA) -> None:
        """
        Initialize the skill config updater.

        :param ctx: the AEA CLI context object.
        :param skill_dir: the directory of the AEA skill package.
        :param dfa: the DFA object.
        """
        self.ctx = ctx
        self.skill_dir = skill_dir
        self.dfa = dfa

        self.skill_config_path = self.skill_dir / DEFAULT_SKILL_CONFIG_FILE

    def update(self) -> None:
        """Update the skill configuration file."""
        config = self.ctx.skill_loader.load(self.skill_config_path.open())
        self._update_behaviours(config)
        self._update_handlers(config)
        self._update_models(config)
        self._update_dependencies(config)
        self.ctx.skill_loader.dump(config, self.skill_config_path.open("w"))
        # TODO: update fingerprint_item to use path instead of context
        preserve_cwd = self.ctx.cwd
        if self.ctx.config.get(TO_LOCAL_REGISTRY_FLAG):
            self.ctx.cwd = Path(self.ctx.registry_path) / self.ctx.agent_config.author
        fingerprint_item(self.ctx, SKILL, config.public_id)
        self.ctx.cwd = preserve_cwd

    def _update_behaviours(self, config: SkillConfig) -> None:
        """Update the behaviours section of the skill configuration."""
        config.behaviours = CRUDCollection[SkillComponentConfiguration]()
        abci_app_cls_name = self.dfa.label.split(".")[-1]
        round_behaviour_cls_name = abci_app_cls_name.replace(ABCI_APP, ROUND_BEHAVIOUR)
        main_config = SkillComponentConfiguration(round_behaviour_cls_name)
        config.behaviours.create("main", main_config)

    def _update_handlers(  # pylint: disable=no-self-use
        self, config: SkillConfig
    ) -> None:
        """Update the handlers section of the skill configuration."""
        config.handlers = CRUDCollection[SkillComponentConfiguration]()
        config.handlers.create("abci", SkillComponentConfiguration("ABCIHandler"))
        config.handlers.create(
            "contract_api", SkillComponentConfiguration("ContractApiHandler")
        )
        config.handlers.create("http", SkillComponentConfiguration("HttpHandler"))
        config.handlers.create(
            "ledger_api", SkillComponentConfiguration("LedgerApiHandler")
        )
        config.handlers.create("signing", SkillComponentConfiguration("SigningHandler"))
        config.handlers.create(
            "tendermint", SkillComponentConfiguration("TendermintHandler")
        )
        config.handlers.create("ipfs", SkillComponentConfiguration("IpfsHandler"))

    def _update_models(  # pylint: disable=no-self-use
        self, config: SkillConfig
    ) -> None:
        """Update the models section of the skill configuration."""
        config.models = CRUDCollection[SkillComponentConfiguration]()
        config.models.create("state", SkillComponentConfiguration("SharedState"))
        config.models.create("requests", SkillComponentConfiguration("Requests"))
        config.models.create(
            "params",
            SkillComponentConfiguration("Params", **self._default_params_config),
        )
        config.models.create(
            "abci_dialogues", SkillComponentConfiguration("AbciDialogues")
        )
        config.models.create(
            "benchmark_tool",
            SkillComponentConfiguration("BenchmarkTool", log_dir="/logs"),
        )
        config.models.create(
            "http_dialogues", SkillComponentConfiguration("HttpDialogues")
        )
        config.models.create(
            "signing_dialogues", SkillComponentConfiguration("SigningDialogues")
        )
        config.models.create(
            "ledger_api_dialogues", SkillComponentConfiguration("LedgerApiDialogues")
        )
        config.models.create(
            "contract_api_dialogues",
            SkillComponentConfiguration("ContractApiDialogues"),
        )
        config.models.create(
            "tendermint_dialogues", SkillComponentConfiguration("TendermintDialogues")
        )
        config.models.create(
            "ipfs_dialogues", SkillComponentConfiguration("IpfsDialogues")
        )

    @classmethod
    def get_actual_abstract_round_abci_package_public_id(
        cls, ctx: Context
    ) -> Optional[PublicId]:
        """Get abstract round abci pacakge id from the registry."""
        package_manager = PackageManagerV1.from_dir(Path(ctx.registry_path))
        packages = [
            package_id.public_id
            for package_id in package_manager.dev_packages.keys()
            if package_id.author == ABSTRACT_ROUND_SKILL_PUBLIC_ID.author
            and package_id.name == ABSTRACT_ROUND_SKILL_PUBLIC_ID.name
            and package_id.package_type == PackageType.SKILL
        ]
        if not packages:
            return None
        abstract_round_abci = packages[0]
        return abstract_round_abci

    def _update_dependencies(self, config: SkillConfig) -> None:
        """Update skill dependencies."""
        # retrieve the actual valory/abstract_round_abci package

        if self.ctx.config.get(TO_LOCAL_REGISTRY_FLAG):
            abstract_round_abci = self.get_actual_abstract_round_abci_package_public_id(
                self.ctx
            )
            if not abstract_round_abci:
                raise ValueError("valory/abstract_round_abci package not found")
        else:
            agent_config = self._load_agent_config()
            abstract_round_abci = [
                public_id
                for public_id in agent_config.skills
                if public_id.author == ABSTRACT_ROUND_SKILL_PUBLIC_ID.author
                and public_id.name == ABSTRACT_ROUND_SKILL_PUBLIC_ID.name
            ][0]

        config.skills.add(abstract_round_abci)

    def _load_agent_config(self) -> AgentConfig:
        """Load the current agent configuration."""
        agent_config_path = Path(self.ctx.cwd) / DEFAULT_AEA_CONFIG_FILE
        with agent_config_path.open() as f:
            return self.ctx.agent_loader.load(f)

    @property
    def _default_params_config(self) -> Dict:
        """The default `params` configuration."""
        abci_app_cls_name = self.dfa.label.split(".")[-1]
        service_id = abci_app_cls_name.replace(ABCI_APP, "")
        service_id = re.sub(r"(?<!^)(?=[A-Z])", "_", service_id).lower()
        return {
            "cleanup_history_depth": 1,
            "cleanup_history_depth_current": None,
            "consensus": {"max_participants": 1},
            "drand_public_key": "868f005eb8e6e4ca0a47c8a77ceaa5309a47978a7c71bc5cce96366b5d7a569937c529eeda66c7293784a9402801af31",
            "finalize_timeout": 60.0,
            "genesis_config": {
                "genesis_time": "2022-05-20T16:00:21.735122717Z",
                "chain_id": "chain-c4daS1",
                "consensus_params": {
                    "block": {
                        "max_bytes": "22020096",
                        "max_gas": "-1",
                        "time_iota_ms": "1000",
                    },
                    "evidence": {
                        "max_age_num_blocks": "100000",
                        "max_age_duration": "172800000000000",
                        "max_bytes": "1048576",
                    },
                    "validator": {"pub_key_types": ["ed25519"]},
                    "version": {},
                },
                "voting_power": "10",
            },
            "history_check_timeout": 1205,
            "ipfs_domain_name": None,
            "keeper_allowed_retries": 3,
            "keeper_timeout": 30.0,
            "max_attempts": 10,
            "max_healthcheck": 120,
            "observation_interval": 10,
            "on_chain_service_id": None,
            "request_retry_delay": 1.0,
            "request_timeout": 10.0,
            "reset_tendermint_after": 2,
            "retry_attempts": 400,
            "retry_timeout": 3,
            "round_timeout_seconds": 30.0,
            "service_id": service_id,
            "service_registry_address": None,
            "setup": {
                "all_participants": [["0x0000000000000000000000000000000000000000"]],
                "safe_contract_address": ["0x0000000000000000000000000000000000000000"],
            },
            "share_tm_config_on_startup": False,
            "sleep_time": 1,
            "tendermint_check_sleep_delay": 3,
            "tendermint_com_url": "http://localhost:8080",
            "tendermint_max_retries": 5,
            "tendermint_p2p_url": "localhost:26656",
            "tendermint_url": "http://localhost:26657",
            "tx_timeout": 10.0,
            "validate_timeout": 1205,
        }


class ScaffoldABCISkill:
    """Utility class that implements the scaffolding of the ABCI skill."""

    file_generators: List[Type[AbstractFileGenerator]] = [
        RoundFileGenerator,
        BehaviourFileGenerator,
        PayloadsFileGenerator,
        ModelsFileGenerator,
        HandlersFileGenerator,
        DialoguesFileGenerator,
    ]

    test_file_generators: List[Type[AbstractFileGenerator]] = [
        RoundTestsFileGenerator,
        BehaviourTestsFileGenerator,
        PayloadTestsFileGenerator,
        ModelTestFileGenerator,
        HandlersTestFileGenerator,
        DialoguesTestFileGenerator,
    ]

    def __init__(self, ctx: Context, skill_name: str, spec_path: Path) -> None:
        """Initialize the utility class."""
        self.ctx = ctx
        self.skill_name = skill_name

        self.spec_path = spec_path

        # process FSM specification
        self.dfa = DFA.load(
            file=spec_path, spec_format=FSMSpecificationLoader.OutputFormats.YAML
        )

    @property
    def skill_dir(self) -> Path:
        """Get the directory to the skill."""
        if self.ctx.config.get(TO_LOCAL_REGISTRY_FLAG):
            return Path(
                self.ctx.registry_path,
                self.ctx.agent_config.author,
                SKILLS,
                self.skill_name,
            )
        return Path(self.ctx.cwd, SKILLS, self.skill_name)

    @property
    def skill_test_dir(self) -> Path:
        """Get the directory to the skill tests."""
        return self.skill_dir / "tests"

    def do_scaffolding(self) -> None:
        """Do the scaffolding."""
        self.skill_dir.mkdir(parents=True, exist_ok=True)
        self.skill_test_dir.mkdir(parents=True, exist_ok=True)

        file_dirs = self.skill_dir, self.skill_test_dir
        file_gens = self.file_generators, self.test_file_generators
        for (f_dir, gens) in zip(file_dirs, file_gens):
            for f_gen in gens:
                click.echo(f"Generating module {f_gen.FILENAME}...")
                f_gen(self.ctx, self.skill_name, self.dfa).write_file(f_dir)

        # remove original 'my_model.py' file
        os.remove(self.skill_dir / "my_model.py")

        self._remove_pycache()
        self._update_init_py()
        self._copy_spec_file()
        self._update_config()

    def _update_config(self) -> None:
        """Update the skill configuration."""
        click.echo("Updating skill configuration...")
        SkillConfigUpdater(self.ctx, self.skill_dir, self.dfa).update()

    def _copy_spec_file(self) -> None:
        """Copy the spec file in the skill directory."""
        click.echo("Copying the spec file in the skill directory...")
        shutil.copy(self.spec_path, self.skill_dir / self.spec_path.name)

    def _update_init_py(self) -> None:
        """Update Copyright __init__.py files"""

        init_py_path = self.skill_dir / INIT_PY
        lines = init_py_path.read_text().splitlines()
        content = "\n".join(line for line in lines if not line.startswith("#"))
        init_py_path.write_text(f"{COPYRIGHT_HEADER} {content}\n")
        (Path(self.skill_test_dir) / INIT_PY).write_text(COPYRIGHT_HEADER)

    def _remove_pycache(self) -> None:
        """Remove __pycache__ folders."""
        for path in self.skill_dir.rglob(f"*{PYCACHE}*"):
            shutil.rmtree(path, ignore_errors=True)
