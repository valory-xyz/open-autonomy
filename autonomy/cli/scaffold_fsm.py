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

import os
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
from autonomy.cli.scaffolding_templates import (
    FILE_HEADER,
    ROUNDS_FILE_HEADER,
    EVENT_SECTION,
    SYNCHRONIZED_DATA_SECTION,
    ROUND_CLS_TEMPLATE,
    DEGENERATE_ROUND_CLS_TEMPLATE,
    ABCI_APP_CLS_TEMPLATE,
    BEHAVIOUR_FILE_HEADER,
    BASE_BEHAVIOUR_CLS_TEMPLATE,
    BEHAVIOUR_CLS_TEMPLATE,
    ROUND_BEHAVIOUR_CLS_TEMPLATE,
    PAYLOADS_FILE,
    TRANSACTION_TYPE_SECTION,
    BASE_PAYLOAD_CLS,
    PAYLOAD_CLS_TEMPLATE,
    MODEL_FILE_TEMPLATE,
    HANDLERS_FILE,
    DIALOGUES_FILE,
)
from autonomy.constants import ABSTRACT_ROUND_ABCI_SKILL_WITH_HASH


ROUNDS_FILENAME = "rounds.py"
BEHAVIOURS_FILENAME = "behaviours.py"
PAYLOADS_FILENAME = "payloads.py"
MODELS_FILENAME = "models.py"
HANDLERS_FILENAME = "handlers.py"
DIALOGUES_FILENAME = "dialogues.py"

DEGENERATE_ROUND = "DegenerateRound"
ABSTRACT_ROUND = "AbstractRound"

ROUND = "Round"
BEHAVIOUR = "Behaviour"
PAYLOAD = "Payload"
EVENT = "Event"
ABCI_APP = "AbciApp"
BASE_BEHAVIOUR = "BaseBehaviour"
ROUND_BEHAVIOUR = "RoundBehaviour"


def _remove_quotes(input_str: str) -> str:
    """Remove single or double quotes from a string."""
    return input_str.replace("'", "").replace('"', "")


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
        (output_dir / self.FILENAME).write_text(self.get_file_content())

    @property
    def abci_app_name(self) -> str:
        """ABCI app class name"""
        return self.dfa.label.split(".")[-1]

    @property
    def fsm_name(self) -> str:
        """FSM base name"""
        return self.abci_app_name.replace(ABCI_APP, "")

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

    def _parse_transition_func(self) -> str:
        """Parse the transition function from the spec to a nested dictionary."""
        result: Dict[str, Dict[str, str]] = {}  # type: ignore
        for (round_cls_name, event_name), value in self.dfa.transition_func.items():
            result.setdefault(round_cls_name, {})[f"{EVENT}.{event_name}"] = value
        for state in self.dfa.states:
            if state not in result:
                result[state] = {}
        return _remove_quotes(str(result))

    @property
    def template_kwargs(self) -> Dict[str, str]:
        """All keywords for string formatting of templates"""

        return dict(
            author=self.author,
            skill_name=self.skill_name,
            FSMName=self.fsm_name,
            AbciApp=self.abci_app_name,
            rounds=indent(",\n".join(self.rounds), " " * 4).strip(),
            payloads=indent(",\n".join(self.payloads), " " * 4).strip(),
            AbciAppCls=self.abci_app_name,
            initial_round_cls=self.dfa.default_start_state,
            initial_states=_remove_quotes(str(self.dfa.start_states)),
            transition_function=self._parse_transition_func(),
            final_states=_remove_quotes(str(self.dfa.final_states)),
            BaseBehaviourCls=self.abci_app_name.replace(ABCI_APP, BASE_BEHAVIOUR),
            RoundBehaviourCls=self.abci_app_name.replace(ABCI_APP, ROUND_BEHAVIOUR),
            InitialBehaviourCls=self.dfa.default_start_state.replace(ROUND, BEHAVIOUR),
            behaviours=_remove_quotes(str(self.behaviours)),
        )


class RoundFileGenerator(AbstractFileGenerator):
    """File generator for 'rounds.py' modules."""

    FILENAME = ROUNDS_FILENAME

    def get_file_content(self) -> str:
        """Scaffold the 'rounds.py' file."""
        rounds_header_section = self._get_rounds_header_section()
        event_section = self._get_event_section()
        synchronized_data_section = self._get_synchronized_data_section()
        rounds_section = self._get_rounds_section()
        abci_app_section = self._get_abci_app_section()

        # build final content
        rounds_file_content = "\n".join(
            [
                FILE_HEADER,
                rounds_header_section,
                event_section,
                synchronized_data_section,
                rounds_section,
                abci_app_section,
            ]
        )

        return rounds_file_content

    def _get_rounds_header_section(self) -> str:
        """Get the rounds header section."""

        return ROUNDS_FILE_HEADER.format(**self.template_kwargs)

    def _get_rounds_section(self) -> str:
        """Get the round section of the module (i.e. the round classes)."""
        all_round_classes_str = []

        # add round classes
        todo_abstract_round_cls = "# TODO: replace AbstractRound with one of CollectDifferentUntilAllRound, CollectSameUntilAllRound, CollectSameUntilThresholdRound, CollectDifferentUntilThresholdRound, OnlyKeeperSendsRound, VotingRound"
        for round_name, payload_name in zip(self.rounds, self.payloads):
            base_name = round_name.replace(ROUND, "")
            round_id = _camel_case_to_snake_case(base_name)
            round_class_str = ROUND_CLS_TEMPLATE.format(
                round_id=round_id,
                RoundCls=round_name,
                PayloadCls=payload_name,
                ABCRoundCls=ABSTRACT_ROUND,
                todo_abstract_round_cls=todo_abstract_round_cls,
            )
            all_round_classes_str.append(round_class_str)

        for round_name in self.degenerate_rounds:
            base_name = round_name.replace(ROUND, "")
            round_id = _camel_case_to_snake_case(base_name)
            round_class_str = DEGENERATE_ROUND_CLS_TEMPLATE.format(
                round_id=round_id,
                RoundCls=round_name,
                ABCRoundCls=DEGENERATE_ROUND,
            )
            all_round_classes_str.append(round_class_str)

        # build final content
        return "\n".join(all_round_classes_str)

    def _get_event_section(self) -> str:
        """Get the event section of the module (i.e. the event enum class definition)."""

        events_list = [
            f'{event_name} = "{event_name.lower()}"'
            for event_name in self.dfa.alphabet_in
        ]
        events = indent("\n".join(events_list), " " * 4).strip()
        return EVENT_SECTION.format(AbciApp=self.abci_app_name, events=events)

    def _get_synchronized_data_section(self) -> str:
        """Get the event section of the module (i.e. the event enum class definition)."""
        return SYNCHRONIZED_DATA_SECTION

    def _get_abci_app_section(self) -> str:
        """Get the abci app section (i.e. the declaration of the AbciApp class)."""

        return ABCI_APP_CLS_TEMPLATE.format(**self.template_kwargs)


class BehaviourFileGenerator(AbstractFileGenerator):
    """File generator for 'behaviours.py' modules."""

    FILENAME = BEHAVIOURS_FILENAME

    def get_file_content(self) -> str:
        """Scaffold the 'behaviours.py' file."""

        behaviours_header_section = self._get_behaviours_header_section()
        base_behaviour_section = self._get_base_behaviour_section()
        behaviours_section = self._get_behaviours_section()
        round_behaviour_section = self._get_round_behaviour_section()

        # build final content
        behaviours_file_content = "\n".join(
            [
                FILE_HEADER,
                behaviours_header_section,
                base_behaviour_section,
                behaviours_section,
                round_behaviour_section,
            ]
        )

        return behaviours_file_content

    def _get_behaviours_header_section(self) -> str:
        """Get the behaviours header section."""

        return BEHAVIOUR_FILE_HEADER.format(**self.template_kwargs)

    def _get_base_behaviour_section(self) -> str:
        """Get the base behaviour section."""

        return BASE_BEHAVIOUR_CLS_TEMPLATE.format(**self.template_kwargs)

    def _get_behaviours_section(self) -> str:
        """Get the behaviours section of the module (i.e. the list of behaviour classes)."""

        all_behaviour_classes_str = []

        for behaviour_name, round_name in zip(self.behaviours, self.rounds):
            base_behaviour_cls_name = self.abci_app_name.replace(
                ABCI_APP, BASE_BEHAVIOUR
            )
            behaviour_id = behaviour_name.replace(BEHAVIOUR, "")
            behaviour_class_str = BEHAVIOUR_CLS_TEMPLATE.format(
                BehaviourCls=behaviour_name,
                BaseBehaviourCls=base_behaviour_cls_name,
                behaviour_id=_camel_case_to_snake_case(behaviour_id),
                matching_round=round_name,
            )
            all_behaviour_classes_str.append(behaviour_class_str)

        # build final content
        return "\n".join(all_behaviour_classes_str)

    def _get_round_behaviour_section(self) -> str:
        """Get the round behaviour section of the module (i.e. the declaration of the round behaviour class)."""

        return ROUND_BEHAVIOUR_CLS_TEMPLATE.format(**self.template_kwargs)


class PayloadsFileGenerator(AbstractFileGenerator):
    """File generator for 'payloads.py' modules."""

    FILENAME = PAYLOADS_FILENAME

    def _get_base_payload_section(self) -> str:
        """Get the base payload section."""

        all_payloads_classes_str = [BASE_PAYLOAD_CLS.format(FSMName=self.fsm_name)]

        for payload_name, round_name in zip(self.payloads, self.rounds):
            tx_type = _camel_case_to_snake_case(round_name.replace(ROUND, ""))
            payload_class_str = PAYLOAD_CLS_TEMPLATE.format(
                FSMName=self.fsm_name,
                PayloadCls=payload_name,
                RoundCls=round_name,
                tx_type=tx_type.upper(),
            )
            all_payloads_classes_str.append(payload_class_str)

        return "\n".join(all_payloads_classes_str)

    def get_file_content(self) -> str:
        """Get the file content."""

        tx_type_list = list(map(_camel_case_to_snake_case, self.base_names))
        tx_type_list = [f'{tx_type.upper()} = "{tx_type}"' for tx_type in tx_type_list]
        tx_types = indent("\n".join(tx_type_list), " " * 4).strip()

        return "\n".join(
            [
                FILE_HEADER,
                PAYLOADS_FILE.format(FSMName=self.abci_app_name),
                TRANSACTION_TYPE_SECTION.format(tx_types=tx_types),
                self._get_base_payload_section(),
            ]
        )


class ModelsFileGenerator(AbstractFileGenerator):
    """File generator for 'models.py' modules."""

    FILENAME = MODELS_FILENAME

    def get_file_content(self) -> str:
        """Get the file content."""

        return "\n".join(
            [
                FILE_HEADER,
                MODEL_FILE_TEMPLATE.format(**self.template_kwargs),
            ]
        )


class HandlersFileGenerator(AbstractFileGenerator):
    """File generator for 'handlers.py' modules."""

    FILENAME = HANDLERS_FILENAME

    def get_file_content(self) -> str:
        """Get the file content."""

        return "\n".join(
            [
                FILE_HEADER,
                HANDLERS_FILE.format(**self.template_kwargs),
            ]
        )


class DialoguesFileGenerator(AbstractFileGenerator):
    """File generator for 'dialogues.py' modules."""

    FILENAME = DIALOGUES_FILENAME

    def get_file_content(self) -> str:
        """Get the file content."""

        return "\n".join(
            [
                FILE_HEADER,
                DIALOGUES_FILE.format(FSMName=self.abci_app_name),
            ]
        )


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
        round_behaviour_cls_name = abci_app_cls_name.replace(ROUND, BEHAVIOUR)
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
        config.models.create("params", SkillComponentConfiguration("Params"))

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
class RoundTestsFileGenerator(AbstractFileGenerator):
    """RoundTestsFileGenerator"""

    FILENAME = "tests_" + ROUNDS_FILENAME

    ROUNDS_FILE_HEADER = dedent(
        """\
        \"\"\"This package contains the tests for rounds of {FSMName}.\"\"\"

        from typing import Any, Dict, List, Callable, Hashable
        from dataclasses import dataclass, field

        import pytest

        # TODO: define and import specific payloads explicitly by name
        from {author}.skills.{skill_name}.payloads import *
        from {author}.skills.{skill_name}.rounds import (
            Event,
            SynchronizedData,
            {non_degenerate_rounds},
        )
        from packages.valory.skills.abstract_round_abci.base import (
            BaseTxPayload,
        )
        from packages.valory.skills.abstract_round_abci.test_tools.rounds import (
            BaseRoundTestClass,
            BaseOnlyKeeperSendsRoundTest,
            BaseCollectDifferentUntilThresholdRoundTest,
            BaseCollectSameUntilThresholdRoundTest,
         )


        @dataclass
        class RoundTestCase:
            \"\"\"RoundTestCase\"\"\"

            initial_data: Dict[str, Hashable]
            payloads: BaseTxPayload
            final_data: Dict[str, Hashable]
            event: Event
            synchronized_data_attr_checks: List[Callable] = field(default_factory=list)


        MAX_PARTICIPANTS: int = 4

    """
    )

    BASE_CLASS = dedent(
        """\
        class Base{FSMName}RoundTestClass(BaseRoundTestClass):
            \"\"\"Base test class for {FSMName} rounds.\"\"\"

            synchronized_data: SynchronizedData
            _synchronized_data_class = SynchronizedData
            _event_class = Event

            def run_test(self, test_case: RoundTestCase, **kwargs) -> None:
                \"\"\"Run the test\"\"\"

                self.synchronized_data.update(**test_case.initial_data)

                test_round = self.round_class(
                    synchronized_data=self.synchronized_data,
                    consensus_params=self.consensus_params,
                )

                self._complete_run(
                    self._test_round(
                        test_round=test_round,
                        round_payloads=test_case.payloads,
                        synchronized_data_update_fn=lambda sync_data, _: sync_data.update(**test_case.final_data),
                        synchronized_data_attr_checks=test_case.synchronized_data_attr_checks,
                        exit_event=test_case.event,
                        **kwargs,  # varies per BaseRoundTestClass child
                    )
                )

            """
    )

    ROUND_CLS_TEMPLATE = dedent(
        """\
        class Test{RoundCls}(Base{FSMName}RoundTestClass):
            \"\"\"Tests for {RoundCls}.\"\"\"

            round_class = {RoundCls}

            # TODO: provide test cases
            @pytest.mark.parametrize("test_case, kwargs", [])
            def test_run(self, test_case: RoundTestCase, **kwargs: Any) -> None:
                \"\"\"Run tests.\"\"\"

                self.run_test(test_case, **kwargs)

    """
    )

    def get_file_content(self) -> str:
        """Scaffold the 'test_rounds.py' file."""

        rounds_header_section = self._get_rounds_header_section()
        rounds_section = self._get_rounds_section()

        rounds_file_content = "\n".join(
            [
                FILE_HEADER,
                rounds_header_section,
                rounds_section,
            ]
        )

        return rounds_file_content

    def _get_rounds_header_section(self) -> str:
        """Get the rounds header section."""

        return self.ROUNDS_FILE_HEADER.format(**self.template_kwargs)

    def _get_rounds_section(self) -> str:
        """Get rounds section"""

        all_round_classes_str = [self.BASE_CLASS.format(**self.template_kwargs)]

        for abci_round_name in self.dfa.states - self.dfa.final_states:
            round_class_str = self.ROUND_CLS_TEMPLATE.format(
                FSMName=self.fsm_name,
                RoundCls=abci_round_name,
            )
            all_round_classes_str.append(round_class_str)

        return "\n".join(all_round_classes_str)


class BehaviourTestsFileGenerator(AbstractFileGenerator):
    """File generator for 'test_behaviours.py' modules."""

    FILENAME = "test_" + BEHAVIOURS_FILENAME

    BEHAVIOUR_FILE_HEADER = dedent(
        """\
        \"\"\"This package contains round behaviours of {AbciAppCls}.\"\"\"

        from pathlib import Path
        from typing import Any, Dict, Hashable, Optional, Type
        from dataclasses import dataclass

        import pytest

        from packages.valory.skills.abstract_round_abci.base import AbciAppDB
        from packages.valory.skills.abstract_round_abci.behaviours import (
            AbstractRoundBehaviour,
            BaseBehaviour,
            make_degenerate_behaviour,
        )
        from {author}.skills.{skill_name}.behaviours import (
            {FSMName}BaseBehaviour,
            {behaviours},
        )
        from {author}.skills.{skill_name}.rounds import (
            SynchronizedData,
            DegenerateRound,
            Event,
            {AbciAppCls},
            {rounds},
        )

        from packages.valory.skills.abstract_round_abci.test_tools.base import (
            FSMBehaviourBaseCase,
        )


        @dataclass
        class BehaviourTestCase:
            \"\"\"BehaviourTestCase\"\"\"

            initial_data: Dict[str, Hashable]
            event: Event

        """
    )

    BASE_CLASS = dedent(
        """\
        class Base{FSMName}Test(FSMBehaviourBaseCase):
            \"\"\"Base test case.\"\"\"

            path_to_skill = Path(__file__).parent.parent

            behaviour: {FSMName}BaseBehaviour
            behaviour_class: Type[{FSMName}BaseBehaviour]
            next_behaviour_class: Type[{FSMName}BaseBehaviour]
            synchronized_data: SynchronizedData
            done_event = Event.DONE

            def fast_forward(self, data: Optional[Dict[str, Any]] = None) -> None:
                \"\"\"Fast-forward on initialization\"\"\"

                data = data if data is not None else {{}}
                self.fast_forward_to_behaviour(
                    self.behaviour,
                    self.behaviour_class.behaviour_id,
                    SynchronizedData(AbciAppDB(setup_data=AbciAppDB.data_to_lists(data))),
                )
                assert self.behaviour.behaviour_id == self.behaviour_class.behaviour_id

            def complete(self, event: Event) -> None:
                \"\"\"Complete test\"\"\"

                self.behaviour.act_wrapper()
                self.mock_a2a_transaction()
                self._test_done_flag_set()
                self.end_round(done_event=event)
                assert self.behaviour.behaviour_id == self.next_behaviour_class.behaviour_id

    """
    )

    BEHAVIOUR_CLS_TEMPLATE = dedent(
        """\
        class Test{BehaviourCls}(Base{FSMName}Test):
            \"\"\"Tests {BehaviourCls}\"\"\"

            # TODO: set next_behaviour_class
            behaviour_class: Type[BaseBehaviour] = {BehaviourCls}
            next_behaviour_class: Type[BaseBehaviour] = ...

            # TODO: provide test cases
            @pytest.mark.parametrize("test_case, kwargs", [])
            def test_run(self, test_case: BehaviourTestCase, **kwargs: Any) -> None:
                \"\"\"Run tests.\"\"\"

                self.fast_forward(test_case.initial_data)
                # TODO: mock the necessary calls
                # self.mock_ ...
                self.complete(test_case.event)

    """
    )

    def get_file_content(self) -> str:
        """Scaffold the 'test_behaviours.py' file."""

        behaviour_header_section = self._get_behaviour_header_section()
        behaviour_section = self._get_behaviour_section()

        behaviour_file_content = "\n".join(
            [
                FILE_HEADER,
                behaviour_header_section,
                behaviour_section,
            ]
        )

        return behaviour_file_content

    def _get_behaviour_header_section(self) -> str:
        """Get the rounds header section."""

        return self.BEHAVIOUR_FILE_HEADER.format(
            AbciAppCls=self.abci_app_name,
            FSMName=self.fsm_name,
            author=self.author,
            skill_name=self.skill_name,
            rounds=indent(",\n".join(self.all_rounds), " " * 4).strip(),
            behaviours=indent(",\n".join(self.behaviours), " " * 4).strip(),
        )

    def _get_behaviour_section(self) -> str:
        """Get behaviour section"""

        all_behaviour_classes_str = [
            self.BASE_CLASS.format(
                FSMName=self.fsm_name,
                author=self.author,
                skill_name=self.skill_name,
            )
        ]

        for behaviour_name in self.behaviours:
            round_class_str = self.BEHAVIOUR_CLS_TEMPLATE.format(
                FSMName=self.fsm_name,
                BehaviourCls=behaviour_name,
            )
            all_behaviour_classes_str.append(round_class_str)

        return "\n".join(all_behaviour_classes_str)


class PayloadTestsFileGenerator(AbstractFileGenerator):
    """File generator for 'test_payloads.py' modules."""

    FILENAME = "test_" + PAYLOADS_FILENAME

    PAYLOAD_FILE_HEADER = dedent(
        """\
        \"\"\"This package contains payload tests for the {AbciApp}.\"\"\"

        from typing import Hashable
        from dataclasses import dataclass

        import pytest

        from {author}.skills.{skill_name}.payloads import (
            TransactionType,
            Base{FSMName}Payload,
            {payloads},
        )


        @dataclass
        class PayloadTestCase:
            \"\"\"PayloadTestCase\"\"\"

            payload_cls: Base{FSMName}Payload
            content: Hashable
            transaction_type: TransactionType

        """
    )

    PAYLOAD_CLS_TEMPLATE = dedent(
        """\
        # TODO: provide test cases
        @pytest.mark.parametrize("test_case", [])
        def test_payloads(test_case: PayloadTestCase) -> None:
            \"\"\"Tests for {AbciApp} payloads\"\"\"

            payload = test_case.payload_cls(sender="sender", content=test_case.content)
            assert payload.sender == "sender"
            assert getattr(payload, f"{{payload.transaction_type}}") == test_case.content
            assert payload.transaction_type == test_case.transaction_type
            assert payload.from_json(payload.json) == payload

    """
    )

    def get_file_content(self) -> str:
        """Scaffold the 'test_payloads.py' file."""

        behaviour_file_content = "\n".join(
            [
                FILE_HEADER,
                self._get_payload_header_section(),
                self._get_payload_section(),
            ]
        )

        return behaviour_file_content

    def _get_payload_header_section(self) -> str:
        """Get the rounds header section."""

        return self.PAYLOAD_FILE_HEADER.format(
            AbciApp=self.abci_app_name,
            FSMName=self.fsm_name,
            author=self.author,
            skill_name=self.skill_name,
            payloads=indent(",\n".join(self.payloads), " " * 4).strip(),
        )

    def _get_payload_section(self) -> str:
        """Get payload section"""

        return self.PAYLOAD_CLS_TEMPLATE.format(AbciApp=self.abci_app_name)


class ModelTestFileGenerator(AbstractFileGenerator):
    """File generator for 'test_models.py'."""

    FILENAME = "test_" + MODELS_FILENAME

    MODELS_FILE = dedent(
        """\
        \"\"\"Test the models.py module of the {FSMName}.\"\"\"

        from packages.valory.skills.abstract_round_abci.test_tools.base import DummyContext
        from {author}.skills.{skill_name}.models import SharedState


        class TestSharedState:
            \"\"\"Test SharedState of {FSMName}.\"\"\"

            def test_initialization(self) -> None:
                \"\"\"Test initialization.\"\"\"
                SharedState(name="", skill_context=DummyContext())

        """
    )

    def _get_models_header_section(self) -> str:
        """Get the models header section."""

        return self.MODELS_FILE.format(
            FSMName=self.fsm_name,
            author=self.author,
            skill_name=self.skill_name,
        )

    def get_file_content(self) -> str:
        """Get the file content."""

        return "\n".join([FILE_HEADER, self._get_models_header_section()])


class HandlersTestFileGenerator(AbstractFileGenerator):
    """File generator for 'test_dialogues.py'."""

    FILENAME = "test_" + HANDLERS_FILENAME

    HANDLERS_FILE = dedent(
        """\
        \"\"\"Test the handlers.py module of the {FSMName}.\"\"\"

        import packages.{author}.skills.{skill_name}.handlers  # noqa


        def test_import() -> None:
            \"\"\"Test that the 'handlers.py' of the {FSMName} can be imported.\"\"\"

        """
    )

    def _get_handlers_header_section(self) -> str:
        """Get the handlers header section."""

        return self.HANDLERS_FILE.format(
            FSMName=self.fsm_name,
            author=self.author,
            skill_name=self.skill_name,
        )

    def get_file_content(self) -> str:
        """Get the file content."""

        return "\n".join([FILE_HEADER, self._get_handlers_header_section()])


class DialoguesTestFileGenerator(AbstractFileGenerator):
    """File generator for 'test_dialogues.py'."""

    FILENAME = "test_" + DIALOGUES_FILENAME

    DIALOGUES_FILE = dedent(
        """\
        \"\"\"Test the dialogues.py module of the {FSMName}.\"\"\"

        import packages.{author}.skills.{skill_name}.dialogues  # noqa


        def test_import() -> None:
            \"\"\"Test that the 'dialogues.py' of the {FSMName} can be imported.\"\"\"
        """
    )

    def _get_dialogues_header_section(self) -> str:
        """Get the dialogues header section."""

        return self.DIALOGUES_FILE.format(
            FSMName=self.fsm_name,
            author=self.author,
            skill_name=self.skill_name,
        )

    def get_file_content(self) -> str:
        """Get the file content."""

        return "\n".join([FILE_HEADER, self._get_dialogues_header_section()])


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

        init_py_path = self.skill_dir / "__init__.py"
        lines = init_py_path.read_text().splitlines()
        content = "\n".join(line for line in lines if not line.startswith("#"))
        init_py_path.write_text(f"{FILE_HEADER} {content}\n")
        (Path(self.skill_test_dir) / "__init__.py").write_text(FILE_HEADER)

    def _remove_pycache(self) -> None:
        """Remove __pycache__ folders."""
        for path in self.skill_dir.rglob("*__pycache__*"):
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
