# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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

"""Consensus algorithms implemented with the AEA framework."""

import click
from aea.cli.core import cli as aea_cli

from aea_swarm.analyse.cli import cmd1


@click.group(name="swarm")  # type: ignore
@click.pass_context
def swarm_cli(click_context: click.Context) -> None:
    """Command-line tool for setting up an swarms of AEAs."""


swarm_cli.add_command(cmd1)

cli = click.CommandCollection(sources=[aea_cli, swarm_cli])

if __name__ == "__main__":
    cli(prog_name="swarm")  # pragma: no cover
