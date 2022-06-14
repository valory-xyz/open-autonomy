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

"""Core for cli."""

import click
from aea.cli.core import cli as aea_cli

from autonomy.cli.analyse import analyse_group
from autonomy.cli.deploy import deploy_group
from autonomy.cli.develop import develop_group
from autonomy.cli.hash import hash_group
from autonomy.cli.replay import replay_group


@click.group(name="autonomy")  # type: ignore
@click.pass_context
def autonomy_cli(
    click_context: click.Context,  # pylint: disable=unused-argument
) -> None:
    """Command-line tool for managing agent services of the Open Autonomy framework."""


autonomy_cli.add_command(analyse_group)
autonomy_cli.add_command(deploy_group)
autonomy_cli.add_command(develop_group)
autonomy_cli.add_command(replay_group)
aea_cli.add_command(hash_group)

cli = click.CommandCollection(sources=[aea_cli, autonomy_cli])
