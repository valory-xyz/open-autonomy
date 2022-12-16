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


from pathlib import Path

import click
from aea.cli.add import add_item
from aea.cli.scaffold import scaffold, scaffold_item
from aea.cli.utils.click_utils import registry_flag
from aea.cli.utils.context import Context
from aea.cli.utils.decorators import pass_ctx
from aea.configurations.constants import SKILL

# the decoration does side-effect on the 'aea scaffold' command
from aea.configurations.data_types import PackageId, PackageType, PublicId
from aea.package_manager.v1 import PackageManagerV1

from autonomy.constants import ABSTRACT_ROUND_ABCI_SKILL_WITH_HASH
from autonomy.fsm.scaffold.scaffold_skill import (
    ScaffoldABCISkill,
    SkillConfigUpdater,
    TO_LOCAL_REGISTRY_FLAG,
)


def _add_abstract_round_abci_if_not_present(ctx: Context) -> None:
    """Add 'abstract_round_abci' skill if not present."""
    MSG = (
        "Skill valory/abstract_round_abci not found in agent dependencies, adding it..."
    )

    if ctx.config.get(TO_LOCAL_REGISTRY_FLAG):
        skill_id = SkillConfigUpdater.get_actual_abstract_round_abci_package_public_id(
            ctx
        )

        if not skill_id:
            # add package to local registry
            click.echo(MSG)
            package_manager = PackageManagerV1.from_dir(Path(ctx.registry_path))
            package_id = PackageId(
                package_type=PackageType.SKILL,
                public_id=PublicId.from_str(ABSTRACT_ROUND_ABCI_SKILL_WITH_HASH),
            )
            package_manager.add_package(package_id, with_dependencies=True)
            package_manager.dump()
    else:
        # add package to agent
        abstract_round_abci_public_id = PublicId.from_str(
            ABSTRACT_ROUND_ABCI_SKILL_WITH_HASH
        )
        if abstract_round_abci_public_id.to_latest() not in {
            public_id.to_latest() for public_id in ctx.agent_config.skills
        }:
            click.echo(MSG)

            add_item(ctx, SKILL, abstract_round_abci_public_id)


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
    # TODO: open-aea/aea/cli/scaffold.py:279 bad trick with update of ctx.cwd
    preserve_cwd = ctx.cwd
    scaffold_item(ctx, SKILL, skill_name)
    ctx.cwd = preserve_cwd

    ScaffoldABCISkill(ctx, skill_name, Path(spec)).do_scaffolding()
