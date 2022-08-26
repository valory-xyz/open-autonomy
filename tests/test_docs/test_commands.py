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

"""This module contains the tests for the commands in the documentation."""

import itertools
import re

import click
from click.core import Option

from autonomy.cli import cli as autonomy_cli


class CommandValidator:
    """Validates commands against a CLI"""

    def __init__(self, cli):
        """Extract autonomy command tree from the autonomy cli"""
        self.tree = {
            "commands": {
                cli.name: {
                    "commands": {},
                    "options": list(
                        itertools.chain(
                            *[i.opts for i in cli.params if isinstance(i, Option)]
                        )
                    ),
                }
            },
        }

        for cmd_name, cmd in cli.commands.items():
            self.tree["commands"][cli.name]["commands"][cmd_name] = {
                "options": list(
                    itertools.chain(
                        *[i.opts for i in cmd.params if isinstance(i, Option)]
                    )
                ),
                "commands": {},
            }
            if isinstance(cmd, click.Group):
                for sub_cmd_name in cmd.list_commands(click.Context):
                    sub_cmd = cli.commands[cmd_name].get_command(
                        click.Context, sub_cmd_name
                    )
                    self.tree["commands"][cli.name]["commands"][cmd_name]["commands"][
                        sub_cmd_name
                    ] = {
                        "options": list(
                            itertools.chain(
                                *[
                                    i.opts
                                    for i in sub_cmd.params
                                    if isinstance(i, Option)
                                ]
                            )
                        )
                    }

    def validate(self, cmd: str) -> bool:
        tree = self.tree
        for cmd_part in cmd.split(" "):
            if cmd_part not in tree["commands"].keys():
                print(f"Error in {cmd_part}")
                return False
            print(list(tree["commands"].keys()))
            tree = tree["commands"][cmd_part]

        return True


cmd = "autonomy deploy build keys.json"
v = CommandValidator(autonomy_cli)
print(v.validate(cmd))

# cmd = autonomy_cli.commands["deploy"].get_command(click.Context, "build")

# print(dir(cmd))

# print([i.opts for i in cmd.params if isinstance(i, click.Argument)])
