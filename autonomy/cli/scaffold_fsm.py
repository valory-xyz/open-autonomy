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
import re
from abc import ABC, abstractmethod
from pathlib import Path
from textwrap import dedent, indent
from typing import Dict, Set

import click
from aea.cli.add import add_item
from aea.cli.fingerprint import fingerprint_item
from aea.cli.scaffold import scaffold, scaffold_item
from aea.cli.utils.context import Context
from aea.cli.utils.decorators import pass_ctx
from aea.configurations.base import SkillComponentConfiguration, SkillConfig
from aea.configurations.constants import DEFAULT_SKILL_CONFIG_FILE, SKILL, SKILLS

# the decoration does side-effect on the 'aea scaffold' command
from aea.configurations.data_types import CRUDCollection, PublicId

from autonomy.analyse.abci.app_spec import DFA


FILE_HEADER = """\
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2021 Fetch.AI Limited
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

ROUNDS_FILENAME = "rounds.py"
BEHAVIOURS_FILENAME = "behaviours.py"
MODELS_FILENAME = "models.py"
HANDLERS_FILENAME = "handlers.py"


def _remove_quotes(input_str: str) -> str:
    """Remove single or double quotes from a string."""
    return input_str.replace("'", "").replace('"', "")


def _get_abci_app_cls_name_from_dfa(dfa: DFA) -> str:
    """Get the Abci app class name from a DFA object."""
    return dfa.label.split(".")[-1]


def _try_get_behaviour_cls_name_from_round_cls_name(round_cls_name: str) -> str:
    """
    Try to get the behaviour class name from the round class name.

    It tries to replace the suffix "Round" with "Behaviour".

    :param round_cls_name: the round class name
    :return: the new behaviour class name
    """
    return re.sub("(.*)Round", "\\1Behaviour", round_cls_name)


def _try_get_round_behaviour_cls_name_from_abci_app_cls_name(
    abci_app_cls_name: str,
) -> str:
    """
    Try to get the round behaviour class name from the Abci app class name.

    It tries to replace the suffix "AbciApp" with "RoundBehaviour".

    :param abci_app_cls_name: the abci app class name
    :return: the new round behaviour class name
    """
    return re.sub("(.*)AbciApp", "\\1RoundBehaviour", abci_app_cls_name)


class AbstractFileGenerator(ABC):
    """An abstract class for file generators."""

    FILENAME: str

    def __init__(self, dfa: DFA) -> None:
        """Initialize the abstract file generator."""
        self.dfa = dfa

    @abstractmethod
    def get_file(self) -> str:
        """Get file content."""

    def write_file(self, output_dir: Path) -> None:
        """Write the file to output_dir/FILENAME."""
        (output_dir / self.FILENAME).write_text(self.get_file())


class RoundFileGenerator(AbstractFileGenerator):
    """File generator for 'rounds.py' modules."""

    FILENAME = ROUNDS_FILENAME

    ROUNDS_FILE_HEADER = dedent(
        """\
        \"\"\"This package contains the rounds of {FSMName}.\"\"\"

        from enum import Enum
        from typing import List, Optional, Set, Tuple

        from packages.valory.skills.abstract_round_abci.base import (
            AbciApp,
            AbciAppTransitionFunction,
            AbstractRound,
            AppState,
            BaseSynchronizedData,
            BaseTxPayload,
            DegenerateRound,
            EventToTimeout,
            TransactionType
        )

    """
    )

    ROUND_CLS_TEMPLATE = dedent(
        """\
        class {RoundCls}({ABCRoundCls}):
            # TODO: set the following class attributes
            round_id: str
            allowed_tx_type: Optional[TransactionType]
            payload_attribute: str

            def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Enum]]:
                \"\"\"Process the end of the block.\"\"\"
                raise NotImplementedError

            def check_payload(self, payload: BaseTxPayload) -> None:
                \"\"\"Check payload.\"\"\"
                raise NotImplementedError

            def process_payload(self, payload: BaseTxPayload) -> None:
                \"\"\"Process payload.\"\"\"
                raise NotImplementedError

    """
    )

    ABCI_APP_CLS_TEMPLATE = dedent(
        """\
        class {AbciAppCls}(AbciApp[Event]):
            initial_round_cls: AppState = {initial_round_cls}
            initial_states: Set[AppState] = {initial_states}
            transition_function: AbciAppTransitionFunction = {transition_function}
            final_states: Set[AppState] = {final_states}
            event_to_timeout: EventToTimeout = {{}}
            cross_period_persisted_keys: List[str] = []
    """
    )

    def get_file(self) -> str:
        """Scaffold the 'rounds.py' file."""
        rounds_header_section = self._get_rounds_header_section()
        event_section = self._get_event_section()
        rounds_section = self._get_rounds_section()
        abci_app_section = self._get_abci_app_section()

        # build final content
        rounds_file_content = "\n".join(
            [
                FILE_HEADER,
                rounds_header_section,
                event_section,
                rounds_section,
                abci_app_section,
            ]
        )

        return rounds_file_content

    def _get_rounds_header_section(self) -> str:
        """Get the rounds header section."""
        return self.ROUNDS_FILE_HEADER.format(
            FSMName=_get_abci_app_cls_name_from_dfa(self.dfa)
        )

    def _get_rounds_section(self) -> str:
        """Get the round section of the module (i.e. the round classes)."""
        all_round_classes_str = []

        # add round classes
        for abci_round_name in self.dfa.states:
            abci_round_base_cls_name = (
                "DegenerateRound"
                if abci_round_name in self.dfa.final_states
                else "AbstractRound"
            )
            round_class_str = RoundFileGenerator.ROUND_CLS_TEMPLATE.format(
                RoundCls=abci_round_name, ABCRoundCls=abci_round_base_cls_name
            )
            all_round_classes_str.append(round_class_str)

        # build final content
        return "\n".join(all_round_classes_str)

    def _get_event_section(self) -> str:
        """Get the event section of the module (i.e. the event enum class definition)."""
        class_header = "class Event(Enum):\n"
        events = [
            f'{event_name} = "{event_name.lower()}"'
            for event_name in self.dfa.alphabet_in
        ]
        class_body = indent("\n".join(events), " " * 4)
        enum_event_class = class_header + "\n" + class_body + "\n\n"
        return enum_event_class

    def _get_abci_app_section(self) -> str:
        """Get the abci app section (i.e. the declaration of the AbciApp class)."""
        abci_app_cls_name = _get_abci_app_cls_name_from_dfa(self.dfa)
        return RoundFileGenerator.ABCI_APP_CLS_TEMPLATE.format(
            AbciAppCls=abci_app_cls_name,
            initial_round_cls=self.dfa.default_start_state,
            initial_states=_remove_quotes(str(self.dfa.default_start_state)),
            transition_function=self._parse_transition_func(),
            final_states=_remove_quotes(str(self.dfa.final_states)),
        )

    def _parse_transition_func(self) -> str:
        """Parse the transition function from the spec to a nested dictionary."""
        result: Dict[str, Dict[str, str]] = {}  # type: ignore
        for (round_cls_name, event_name), value in self.dfa.transition_func.items():
            result.setdefault(round_cls_name, {})[f"Event.{event_name}"] = value
        return _remove_quotes(str(result))


class BehaviourFileGenerator(AbstractFileGenerator):
    """File generator for 'behaviours.py' modules."""

    FILENAME = BEHAVIOURS_FILENAME

    BEHAVIOUR_FILE_HEADER = dedent(
        """\
        \"\"\"This package contains round behaviours of {FSMName}.\"\"\"

        from abc import abstractmethod
        from typing import Generator, Set, Type

        from packages.valory.skills.abstract_round_abci.base import AbstractRound
        from packages.valory.skills.abstract_round_abci.behaviours import (
            AbstractRoundBehaviour,
            BaseBehaviour,
        )

        """
    )

    BEHAVIOUR_CLS_TEMPLATE = dedent(
        """\
        class {BehaviourCls}(BaseBehaviour):
            # TODO: set the following class attributes
            state_id: str
            behaviour_id: str
            matching_round: Type[AbstractRound]

            @abstractmethod
            def async_act(self) -> Generator:
                \"\"\"Do the act, supporting asynchronous execution.\"\"\"

    """
    )

    ROUND_BEHAVIOUR_CLS_TEMPLATE = dedent(
        """\
        class {RoundBehaviourCls}(AbstractRoundBehaviour):
            initial_behaviour_cls = {initial_behaviour_cls}
            abci_app_cls = {abci_app_cls}  # type: ignore
            behaviours: Set[Type[BaseBehaviour]] = {behaviours}
    """
    )

    def get_file(self) -> str:
        """Scaffold the 'rounds.py' file."""
        behaviours_header_section = self._get_behaviours_header_section()
        behaviours_section = self._get_behaviours_section()
        round_behaviour_section = self._get_round_behaviour_section()

        # build final content
        behaviours_file_content = "\n".join(
            [
                FILE_HEADER,
                behaviours_header_section,
                behaviours_section,
                round_behaviour_section,
            ]
        )

        return behaviours_file_content

    def _get_behaviours_header_section(self) -> str:
        """Get the behaviours header section."""
        return self.BEHAVIOUR_FILE_HEADER.format(
            FSMName=_get_abci_app_cls_name_from_dfa(self.dfa)
        )

    def _get_behaviours_section(self) -> str:
        """Get the behaviours section of the module (i.e. the list of behaviour classes)."""
        all_behaviour_classes_str = []

        # add behaviour classes
        for abci_round_name in self.dfa.states:
            # try to replace 'Round' suffix with 'Behaviour'
            abci_behaviour_name = _try_get_behaviour_cls_name_from_round_cls_name(
                abci_round_name
            )
            behaviour_class_str = BehaviourFileGenerator.BEHAVIOUR_CLS_TEMPLATE.format(
                BehaviourCls=abci_behaviour_name,
            )
            all_behaviour_classes_str.append(behaviour_class_str)

        # build final content
        return "\n".join(all_behaviour_classes_str)

    def _get_behaviour_set(self) -> Set[str]:
        """Get the set of behaviour states (excluding final states)."""
        result: Set[str] = set()
        for abci_round_name in self.dfa.states:
            if abci_round_name in self.dfa.final_states:
                continue
            # try to replace 'Round' suffix with 'Behaviour'
            abci_behaviour_name = _try_get_behaviour_cls_name_from_round_cls_name(
                abci_round_name
            )
            result.add(abci_behaviour_name)
        return result

    def _get_round_behaviour_section(self) -> str:
        """Get the round behaviour section of the module (i.e. the declaration of the round behaviour class)."""
        abci_app_cls_name = _get_abci_app_cls_name_from_dfa(self.dfa)
        round_behaviour_cls_name = (
            _try_get_round_behaviour_cls_name_from_abci_app_cls_name(abci_app_cls_name)
        )
        initial_round_cls_name = self.dfa.default_start_state
        initial_behaviour_cls_name = _try_get_behaviour_cls_name_from_round_cls_name(
            initial_round_cls_name
        )
        return BehaviourFileGenerator.ROUND_BEHAVIOUR_CLS_TEMPLATE.format(
            RoundBehaviourCls=round_behaviour_cls_name,
            initial_behaviour_cls=initial_behaviour_cls_name,
            abci_app_cls=abci_app_cls_name,
            behaviours=_remove_quotes(str(self._get_behaviour_set())),
        )


class ModelsFileGenerator(AbstractFileGenerator):
    """File generator for 'models.py' modules."""

    FILENAME = MODELS_FILENAME

    MODEL_FILE_TEMPLATE = dedent(
        """\
        \"\"\"This module contains the shared state for the abci skill of {FSMName}.\"\"\"

        from typing import Any

        from packages.valory.skills.abstract_round_abci.models import BaseParams
        from packages.valory.skills.abstract_round_abci.models import Requests as BaseRequests
        from packages.valory.skills.abstract_round_abci.models import (
            SharedState as BaseSharedState,
        )
        from packages.valory.skills.registration_abci.rounds import {AbciAppCls}


        class SharedState(BaseSharedState):
            \"\"\"Keep the current shared state of the skill.\"\"\"

            def __init__(self, *args: Any, **kwargs: Any) -> None:
                \"\"\"Initialize the state.\"\"\"
                super().__init__(*args, abci_app_cls={AbciAppCls}, **kwargs)


        Params = BaseParams
        Requests = BaseRequests
        """
    )

    def get_file(self) -> str:
        """Get the file content."""
        abci_app_cls_name = _get_abci_app_cls_name_from_dfa(self.dfa)
        return "\n".join(
            [
                FILE_HEADER,
                ModelsFileGenerator.MODEL_FILE_TEMPLATE.format(
                    FSMName=abci_app_cls_name, AbciAppCls=abci_app_cls_name
                ),
            ]
        )


class HandlersFileGenerator(AbstractFileGenerator):
    """File generator for 'handlers.py' modules."""

    FILENAME = HANDLERS_FILENAME

    HANDLERS_FILE = dedent(
        """\
        \"\"\"This module contains the handlers for the skill of {FSMName}.\"\"\"

        from packages.valory.skills.abstract_round_abci.handlers import (
            ABCIRoundHandler as BaseABCIRoundHandler,
        )
        from packages.valory.skills.abstract_round_abci.handlers import (
            ContractApiHandler as BaseContractApiHandler,
        )
        from packages.valory.skills.abstract_round_abci.handlers import (
            HttpHandler as BaseHttpHandler,
        )
        from packages.valory.skills.abstract_round_abci.handlers import (
            LedgerApiHandler as BaseLedgerApiHandler,
        )
        from packages.valory.skills.abstract_round_abci.handlers import (
            SigningHandler as BaseSigningHandler,
        )
        from packages.valory.skills.abstract_round_abci.handlers import (
            TendermintHandler as BaseTendermintHandler,
        )


        ABCIRoundHandler = BaseABCIRoundHandler
        HttpHandler = BaseHttpHandler
        SigningHandler = BaseSigningHandler
        LedgerApiHandler = BaseLedgerApiHandler
        ContractApiHandler = BaseContractApiHandler
        TendermintHandler = BaseTendermintHandler
        """
    )

    def get_file(self) -> str:
        """Get the file content."""
        abci_app_cls_name = _get_abci_app_cls_name_from_dfa(self.dfa)
        return "\n".join(
            [
                FILE_HEADER,
                HandlersFileGenerator.HANDLERS_FILE.format(FSMName=abci_app_cls_name),
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
        self.ctx.skill_loader.dump(config, self.skill_config_path.open("w"))
        fingerprint_item(self.ctx, SKILL, config.public_id)

    def _update_behaviours(self, config: SkillConfig) -> None:
        """Update the behaviours section of the skill configuration."""
        config.behaviours = CRUDCollection[SkillComponentConfiguration]()
        abci_app_cls_name = _get_abci_app_cls_name_from_dfa(self.dfa)
        round_behaviour_cls_name = _try_get_behaviour_cls_name_from_round_cls_name(
            abci_app_cls_name
        )
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


class ScaffoldABCISkill:
    """Utility class that implements the scaffolding of the ABCI skill."""

    def __init__(self, ctx: Context, skill_name: str, dfa: DFA) -> None:
        """Initialize the utility class."""
        self.ctx = ctx
        self.skill_name = skill_name
        self.dfa = dfa

    @property
    def skill_dir(self) -> Path:
        """Get the directory to the skill."""
        return Path(SKILLS, self.skill_name)

    def do_scaffolding(self) -> None:
        """Do the scaffolding."""
        self._scaffold_rounds()
        self._scaffold_behaviours()
        self._scaffold_models()
        self._scaffold_handlers()

        # remove original 'my_model.py' file
        (self.skill_dir / "my_model.py").unlink(missing_ok=True)

        self._update_config()

    def _scaffold_rounds(self) -> None:
        """Scaffold the 'rounds.py' module."""
        click.echo(f"Generating module {RoundFileGenerator.FILENAME}...")
        RoundFileGenerator(self.dfa).write_file(self.skill_dir)

    def _scaffold_behaviours(self) -> None:
        """Scaffold the 'behaviours.py' module."""
        click.echo(f"Generating module {BehaviourFileGenerator.FILENAME}...")
        BehaviourFileGenerator(self.dfa).write_file(self.skill_dir)

    def _scaffold_models(self) -> None:
        """Scaffold the 'models.py' module."""
        click.echo(f"Generating module {ModelsFileGenerator.FILENAME}...")
        ModelsFileGenerator(self.dfa).write_file(self.skill_dir)

    def _scaffold_handlers(self) -> None:
        """Scaffold the 'handlers.py' module."""
        click.echo(f"Generating module {HandlersFileGenerator.FILENAME}...")
        HandlersFileGenerator(self.dfa).write_file(self.skill_dir)

    def _update_config(self) -> None:
        """Update the skill configuration."""
        click.echo("Updating skill configuration...")
        SkillConfigUpdater(self.ctx, self.skill_dir, self.dfa).update()


def _add_abstract_round_abci_if_not_present(ctx: Context) -> None:
    """Add 'abstract_round_abci' skill if not present."""
    if PublicId("valory", "abstract_round_abci") not in {
        public_id.to_latest() for public_id in ctx.agent_config.skills
    }:
        click.echo(
            "Skill valory/abstract_round_abci not found in agent dependencies, adding it..."
        )
        add_item(ctx, SKILL, PublicId("valory", "abstract_round_abci"))


@scaffold.command()  # noqa
@click.argument("skill_name", type=str, required=True)
@click.option("--spec", type=click.Path(exists=True, dir_okay=False), required=True)
@pass_ctx
def fsm(ctx: Context, skill_name: str, spec: str) -> None:
    """Add an ABCI skill scaffolding from an FSM specification."""
    # check abstract_round_abci is in dependencies; if not, add it
    _add_abstract_round_abci_if_not_present(ctx)

    # scaffold AEA skill - as usual
    scaffold_item(ctx, SKILL, skill_name)

    # process FSM specification
    spec_path = Path(spec)
    with spec_path.open(encoding="utf-8") as fp:
        dfa = DFA.load(fp, input_format="yaml")

    ScaffoldABCISkill(ctx, skill_name, dfa).do_scaffolding()
