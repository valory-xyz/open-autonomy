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

"""Component generators."""


from typing import List

from aea.protocols.generator.common import _camel_case_to_snake_case

from autonomy.fsm.scaffold.base import AbstractFileGenerator
from autonomy.fsm.scaffold.constants import (
    ABCI_APP,
    ABSTRACT_ROUND,
    BASE_BEHAVIOUR,
    BEHAVIOUR,
    DEGENERATE_ROUND,
    ROUND,
)
from autonomy.fsm.scaffold.templates import COPYRIGHT_HEADER
from autonomy.fsm.scaffold.templates.components import (
    BEHAVIOURS,
    DIALOGUES,
    HANDLERS,
    MODELS,
    PAYLOADS,
    ROUNDS,
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
            self.ABCI_APP_CLS.format(
                **self.template_kwargs,
            ),
        ]

        return "\n".join(file_content)

    def _get_rounds_section(self) -> str:
        """Get the round section of the module (i.e. the round classes)."""

        rounds: List[str] = []

        todo_abstract_round_cls = "# TODO: replace AbstractRound with one of CollectDifferentUntilAllRound,\n        # CollectSameUntilAllRound, CollectSameUntilThresholdRound,\n        # CollectDifferentUntilThresholdRound, OnlyKeeperSendsRound, VotingRound,\n        # from packages/valory/skills/abstract_round_abci/base.py\n        # or implement the methods"
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

        payloads: List[str] = []

        for payload_name, round_name in zip(self.payloads, self.rounds):
            payload_class_str = self.PAYLOAD_CLS.format(
                FSMName=self.fsm_name,
                PayloadCls=payload_name,
                RoundCls=round_name,
            )
            payloads.append(payload_class_str)

        return "\n".join(payloads)

    def get_file_content(self) -> str:
        """Get the file content."""

        file_content = [
            COPYRIGHT_HEADER,
            self.HEADER.format(**self.template_kwargs),
            self._get_base_payload_section(),
        ]

        return "\n".join(file_content)


class ModelsFileGenerator(SimpleFileGenerator, MODELS):
    """File generator for 'models.py' modules."""


class HandlersFileGenerator(SimpleFileGenerator, HANDLERS):
    """File generator for 'handlers.py' modules."""


class DialoguesFileGenerator(SimpleFileGenerator, DIALOGUES):
    """File generator for 'dialogues.py' modules."""
