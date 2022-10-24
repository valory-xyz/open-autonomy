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

"""
Implement a scaffold sub-command to scaffold ABCI skills.

This module patches the 'aea scaffold' command so to add a new subcommand for scaffolding a skill
 starting from FSM specification.
"""

import json
import os
import re
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from textwrap import dedent, indent
from typing import Dict, List, Type

import click
from aea.cli.add import add_item
from aea.cli.fingerprint import fingerprint_item
from aea.cli.scaffold import scaffold, scaffold_item
from aea.cli.utils.click_utils import registry_flag
from aea.cli.utils.context import Context
from aea.cli.utils.decorators import pass_ctx
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
from aea.configurations.data_types import CRUDCollection, PublicId
from aea.protocols.generator.common import _camel_case_to_snake_case

from autonomy.analyse.abci.app_spec import DFA
from autonomy.cli.scaffold_fsm_templates import (
    BEHAVIOURS,
    COPYRIGHT_HEADER,
    DIALOGUES,
    HANDLERS,
    MODELS,
    PAYLOADS,
    ROUNDS,
    TEST_BEHAVIOURS,
    TEST_DIALOGUES,
    TEST_HANDLERS,
    TEST_MODELS,
    TEST_PAYLOADS,
    TEST_ROUNDS,
)
from autonomy.configurations.constants import INIT_PY, PYCACHE
from autonomy.constants import ABSTRACT_ROUND_ABCI_SKILL_WITH_HASH


DEGENERATE_ROUND = "DegenerateRound"
ABSTRACT_ROUND = "AbstractRound"

ROUND = "Round"
BEHAVIOUR = "Behaviour"
PAYLOAD = "Payload"
ABCI_APP = "AbciApp"
BASE_BEHAVIOUR = "BaseBehaviour"
ROUND_BEHAVIOUR = "RoundBehaviour"

TEMPLATE_INDENTATION = " " * 8


def _remove_quotes(input_str: str) -> str:
    """Remove single or double quotes from a string."""
    return input_str.replace("'", "").replace('"', "")


def _indent_wrapper(lines: str) -> str:
    """Indentation"""
    return indent(lines, TEMPLATE_INDENTATION).strip()


class AbstractFileGenerator(ABC):
    """An abstract class for file generators."""

    FILENAME: str

    def __init__(self, ctx: Context, skill_name: str, dfa: DFA) -> None:
        """Initialize the abstract file generator."""
        self.ctx = ctx
        self.skill_name = skill_name
        self.dfa = dfa

    @abstractmethod
    def get_file_content(self) -> str:
        """Get file content."""

    def write_file(self, output_dir: Path) -> None:
        """Write the file to output_dir/FILENAME."""
        (output_dir / self.FILENAME).write_text(dedent(self.get_file_content()))

    @property
    def abci_app_name(self) -> str:
        """ABCI app class name"""
        return self.dfa.label.split(".")[-1]

    @property
    def fsm_name(self) -> str:
        """FSM base name"""
        return re.sub(ABCI_APP, "", self.abci_app_name, flags=re.IGNORECASE)

    @property
    def author(self) -> str:
        """Author"""
        return self.ctx.agent_config.author

    @property
    def all_rounds(self) -> List[str]:
        """Rounds"""
        return sorted(self.dfa.states)

    @property
    def degenerate_rounds(self) -> List[str]:
        """Degenerate rounds"""
        return sorted(self.dfa.final_states)

    @property
    def rounds(self) -> List[str]:
        """Non-degenerate rounds"""
        return sorted(self.dfa.states - self.dfa.final_states)

    @property
    def base_names(self) -> List[str]:
        """Base names"""
        return [s.replace(ROUND, "") for s in self.rounds]

    @property
    def behaviours(self) -> List[str]:
        """Behaviours"""
        return [s.replace(ROUND, BEHAVIOUR) for s in self.rounds]

    @property
    def payloads(self) -> List[str]:
        """Payloads"""
        return [s.replace(ROUND, PAYLOAD) for s in self.rounds]

    @property  # TODO: functools cached property
    def template_kwargs(self) -> Dict[str, str]:
        """All keywords for string formatting of templates"""

        events_list = [
            f'{event_name} = "{event_name.lower()}"'
            for event_name in self.dfa.alphabet_in
        ]

        tx_type_list = list(map(_camel_case_to_snake_case, self.base_names))
        tx_type_list = [f'{tx_type.upper()} = "{tx_type}"' for tx_type in tx_type_list]

        tf = json.dumps(self.dfa.parse_transition_func(), indent=4)
        behaviours = json.dumps(self.behaviours, indent=4)

        return dict(
            author=self.author,
            skill_name=self.skill_name,
            FSMName=self.fsm_name,
            AbciApp=self.abci_app_name,
            rounds=_indent_wrapper(",\n".join(self.rounds)),
            all_rounds=_indent_wrapper(",\n".join(self.all_rounds)),
            behaviours=_indent_wrapper(",\n".join(self.behaviours)),
            payloads=_indent_wrapper(",\n".join(self.payloads)),
            tx_types=_indent_wrapper("\n".join(tx_type_list)),
            events=_indent_wrapper("\n".join(events_list)),
            initial_round_cls=self.dfa.default_start_state,
            initial_states=_remove_quotes(str(self.dfa.start_states)),
            transition_function=_indent_wrapper(_remove_quotes(str(tf))),
            final_states=_remove_quotes(str(self.dfa.final_states)),
            BaseBehaviourCls=re.sub(
                ABCI_APP, BASE_BEHAVIOUR, self.abci_app_name, flags=re.IGNORECASE
            ),
            RoundBehaviourCls=re.sub(
                ABCI_APP, ROUND_BEHAVIOUR, self.abci_app_name, flags=re.IGNORECASE
            ),
            InitialBehaviourCls=self.dfa.default_start_state.replace(ROUND, BEHAVIOUR),
            round_behaviours=_indent_wrapper(_remove_quotes(str(behaviours))),
        )


class SimpleFileGenerator(AbstractFileGenerator):
    """For files that require minimal formatting"""

    HEADER: str

    def get_file_content(self) -> str:
        """Get the file content."""

        file_content = [
            COPYRIGHT_HEADER,
            self.HEADER.format(**self.template_kwargs),
        ]

        return "\n".join(file_content)


class RoundFileGenerator(AbstractFileGenerator, ROUNDS):
    """File generator for 'rounds.py' modules."""

    def get_file_content(self) -> str:
        """Scaffold the 'rounds.py' file."""

        file_content = [
            COPYRIGHT_HEADER,
            ROUNDS.HEADER.format(**self.template_kwargs),
            self._get_rounds_section(),
            self.ABCI_APP_CLS.format(**self.template_kwargs),
        ]

        return "\n".join(file_content)

    def _get_rounds_section(self) -> str:
        """Get the round section of the module (i.e. the round classes)."""

        rounds: List[str] = []

        todo_abstract_round_cls = "# TODO: replace AbstractRound with one of CollectDifferentUntilAllRound, CollectSameUntilAllRound, CollectSameUntilThresholdRound, CollectDifferentUntilThresholdRound, OnlyKeeperSendsRound, VotingRound"
        for round_name, payload_name in zip(self.rounds, self.payloads):
            base_name = round_name.replace(ROUND, "")
            round_id = _camel_case_to_snake_case(base_name)
            round_class = self.ROUND_CLS.format(
                round_id=round_id,
                RoundCls=round_name,
                PayloadCls=payload_name,
                ABCRoundCls=ABSTRACT_ROUND,
                todo_abstract_round_cls=todo_abstract_round_cls,
            )
            rounds.append(round_class)

        for round_name in self.degenerate_rounds:
            base_name = round_name.replace(ROUND, "")
            round_id = _camel_case_to_snake_case(base_name)
            round_class_str = self.DEGENERATE_ROUND_CLS.format(
                round_id=round_id,
                RoundCls=round_name,
                ABCRoundCls=DEGENERATE_ROUND,
            )
            rounds.append(round_class_str)

        # build final content
        return "\n".join(rounds)


class BehaviourFileGenerator(AbstractFileGenerator, BEHAVIOURS):
    """File generator for 'behaviours.py' modules."""

    def get_file_content(self) -> str:
        """Scaffold the 'behaviours.py' file."""

        file_content = [
            COPYRIGHT_HEADER,
            self.HEADER.format(**self.template_kwargs),
            self.BASE_BEHAVIOUR_CLS.format(**self.template_kwargs),
            self._get_behaviours_section(),
            self.ROUND_BEHAVIOUR_CLS.format(**self.template_kwargs),
        ]

        return "\n".join(file_content)

    def _get_behaviours_section(self) -> str:
        """Get the behaviours section of the module (i.e. the list of behaviour classes)."""

        behaviours: List[str] = []
        base_behaviour_name = self.abci_app_name.replace(ABCI_APP, BASE_BEHAVIOUR)
        for behaviour_name, round_name, payload_name in zip(
            self.behaviours, self.rounds, self.payloads
        ):
            behaviour_id = behaviour_name.replace(BEHAVIOUR, "")
            behaviour = self.BEHAVIOUR_CLS.format(
                BehaviourCls=behaviour_name,
                BaseBehaviourCls=base_behaviour_name,
                PayloadCls=payload_name,
                behaviour_id=_camel_case_to_snake_case(behaviour_id),
                matching_round=round_name,
            )
            behaviours.append(behaviour)

        return "\n".join(behaviours)


class PayloadsFileGenerator(AbstractFileGenerator, PAYLOADS):
    """File generator for 'payloads.py' modules."""

    def _get_base_payload_section(self) -> str:
        """Get the base payload section."""

        payloads: List[str] = [self.BASE_PAYLOAD_CLS.format(**self.template_kwargs)]

        for payload_name, round_name in zip(self.payloads, self.rounds):
            tx_type = _camel_case_to_snake_case(round_name.replace(ROUND, ""))
            payload_class_str = self.PAYLOAD_CLS.format(
                FSMName=self.fsm_name,
                PayloadCls=payload_name,
                RoundCls=round_name,
                tx_type=tx_type.upper(),
            )
            payloads.append(payload_class_str)

        return "\n".join(payloads)

    def get_file_content(self) -> str:
        """Get the file content."""

        file_content = [
            COPYRIGHT_HEADER,
            self.HEADER.format(**self.template_kwargs),
            self.TRANSACTION_TYPE_SECTION.format(**self.template_kwargs),
            self._get_base_payload_section(),
        ]

        return "\n".join(file_content)


class ModelsFileGenerator(SimpleFileGenerator, MODELS):
    """File generator for 'models.py' modules."""


class HandlersFileGenerator(SimpleFileGenerator, HANDLERS):
    """File generator for 'handlers.py' modules."""


class DialoguesFileGenerator(SimpleFileGenerator, DIALOGUES):
    """File generator for 'dialogues.py' modules."""


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
        fingerprint_item(self.ctx, SKILL, config.public_id)

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
        config.handlers.create("abci", SkillComponentConfiguration("ABCIRoundHandler"))
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

    def _update_dependencies(self, config: SkillConfig) -> None:
        """Update skill dependencies."""
        # retrieve the actual valory/abstract_round_abci package
        agent_config = self._load_agent_config()
        abstract_round_abci = [
            public_id
            for public_id in agent_config.skills
            if public_id.author == "valory" and public_id.name == "abstract_round_abci"
        ][0]
        config.skills.add(abstract_round_abci)

    def _load_agent_config(self) -> AgentConfig:
        """Load the current agent configuration."""
        with (Path(self.ctx.cwd) / DEFAULT_AEA_CONFIG_FILE).open() as f:
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
            "history_check_timeout": 1205,
            "keeper_allowed_retries": 3,
            "keeper_timeout": 30.0,
            "max_healthcheck": 120,
            "observation_interval": 10,
            "on_chain_service_id": None,
            "reset_tendermint_after": 2,
            "retry_attempts": 400,
            "retry_timeout": 3,
            "round_timeout_seconds": 30.0,
            "service_id": service_id,
            "service_registry_address": None,
            "setup": {},
            "sleep_time": 1,
            "tendermint_check_sleep_delay": 3,
            "tendermint_com_url": "http://localhost:8080",
            "tendermint_max_retries": 5,
            "tendermint_url": "http://localhost:26657",
            "validate_timeout": 1205,
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
        }


def _add_abstract_round_abci_if_not_present(ctx: Context) -> None:
    """Add 'abstract_round_abci' skill if not present."""
    abstract_round_abci_public_id = PublicId.from_str(
        ABSTRACT_ROUND_ABCI_SKILL_WITH_HASH
    )
    if abstract_round_abci_public_id.to_latest() not in {
        public_id.to_latest() for public_id in ctx.agent_config.skills
    }:
        click.echo(
            "Skill valory/abstract_round_abci not found in agent dependencies, adding it..."
        )
        add_item(ctx, SKILL, abstract_round_abci_public_id)


# Scaffolding of tests
class RoundTestsFileGenerator(AbstractFileGenerator, TEST_ROUNDS):
    """RoundTestsFileGenerator"""

    def get_file_content(self) -> str:
        """Scaffold the 'test_rounds.py' file."""

        file_content = [
            COPYRIGHT_HEADER,
            self.HEADER.format(**self.template_kwargs),
            self._get_rounds_section(),
        ]

        return "\n".join(file_content)

    def _get_rounds_section(self) -> str:
        """Get rounds section"""

        rounds: List[str] = [self.BASE_ROUND_TEST_CLS.format(**self.template_kwargs)]

        for round_name in self.rounds:
            round_class_str = self.TEST_ROUND_CLS.format(
                FSMName=self.fsm_name,
                RoundCls=round_name,
            )
            rounds.append(round_class_str)

        return "\n".join(rounds)


class BehaviourTestsFileGenerator(AbstractFileGenerator, TEST_BEHAVIOURS):
    """File generator for 'test_behaviours.py' modules."""

    def get_file_content(self) -> str:
        """Scaffold the 'test_behaviours.py' file."""

        behaviour_file_content = [
            COPYRIGHT_HEADER,
            self.HEADER.format(**self.template_kwargs),
            self._get_behaviour_section(),
        ]

        return "\n".join(behaviour_file_content)

    def _get_behaviour_section(self) -> str:
        """Get behaviour section"""

        behaviours = [self.BASE_BEHAVIOUR_TEST_CLS.format(**self.template_kwargs)]

        for behaviour_name in self.behaviours:
            round_class_str = self.TEST_BEHAVIOUR_CLS.format(
                FSMName=self.fsm_name,
                BehaviourCls=behaviour_name,
            )
            behaviours.append(round_class_str)

        return "\n".join(behaviours)


class PayloadTestsFileGenerator(AbstractFileGenerator, TEST_PAYLOADS):
    """File generator for 'test_payloads.py' modules."""

    def get_file_content(self) -> str:
        """Scaffold the 'test_payloads.py' file."""

        behaviour_file_content = [
            COPYRIGHT_HEADER,
            self.HEADER.format(**self.template_kwargs),
            self.TEST_PAYLOAD_CLS.format(**self.template_kwargs),
        ]

        return "\n".join(behaviour_file_content)


class ModelTestFileGenerator(SimpleFileGenerator, TEST_MODELS):
    """File generator for 'test_models.py'."""


class HandlersTestFileGenerator(SimpleFileGenerator, TEST_HANDLERS):
    """File generator for 'test_dialogues.py'."""


class DialoguesTestFileGenerator(SimpleFileGenerator, TEST_DIALOGUES):
    """File generator for 'test_dialogues.py'."""


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

    def __init__(self, ctx: Context, skill_name: str, dfa: DFA) -> None:
        """Initialize the utility class."""
        self.ctx = ctx
        self.skill_name = skill_name
        self.dfa = dfa

    @property
    def skill_dir(self) -> Path:
        """Get the directory to the skill."""
        return Path(SKILLS, self.skill_name)

    @property
    def skill_test_dir(self) -> Path:
        """Get the directory to the skill tests."""
        return self.skill_dir / "tests"

    def do_scaffolding(self) -> None:
        """Do the scaffolding."""

        self.skill_dir.mkdir(exist_ok=True)
        self.skill_test_dir.mkdir(exist_ok=True)

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
        self._update_config()

    def _update_config(self) -> None:
        """Update the skill configuration."""
        click.echo("Updating skill configuration...")
        SkillConfigUpdater(self.ctx, self.skill_dir, self.dfa).update()

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


@scaffold.command()  # noqa
@registry_flag()
@click.argument("skill_name", type=str, required=True)
@click.option("--spec", type=click.Path(exists=True, dir_okay=False), required=True)
@pass_ctx
def fsm(ctx: Context, registry: str, skill_name: str, spec: str) -> None:
    """Add an ABCI skill scaffolding from an FSM specification."""
    ctx.registry_type = registry
    # check abstract_round_abci is in dependencies; if not, add it
    _add_abstract_round_abci_if_not_present(ctx)

    # scaffold AEA skill - as usual
    scaffold_item(ctx, SKILL, skill_name)

    # process FSM specification
    spec_path = Path(spec)
    with spec_path.open(encoding="utf-8") as fp:
        dfa = DFA.load(fp, input_format="yaml")

    ScaffoldABCISkill(ctx, skill_name, dfa).do_scaffolding()
