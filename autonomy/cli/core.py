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
from aea.cli.core import cli

import autonomy
from autonomy.cli.analyse import analyse_group
from autonomy.cli.deploy import deploy_group
from autonomy.cli.develop import develop_group
from autonomy.cli.fetch import fetch
from autonomy.cli.hash import hash_group
from autonomy.cli.publish import publish
from autonomy.cli.push_all import push_all
from autonomy.cli.replay import replay_group


cli.add_command(analyse_group)
cli.add_command(deploy_group)
cli.add_command(develop_group)
cli.add_command(replay_group)
cli.add_command(hash_group)
cli.add_command(push_all)
cli.add_command(publish)
cli.add_command(fetch)


click.version_option(autonomy.__version__, prog_name="autonomy")(cli)
cli.help = "Command-line tool for managing agent services of the Open Autonomy framework.\n\nExtends the command-line tool for setting up an Autonomous Economic Agent (AEA)."
cli.name = "autonomy"
