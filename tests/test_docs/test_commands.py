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
from scripts.check_doc_ipfs_hashes import AEA_COMMAND_REGEX
import re
import click
from click.core import Option

from autonomy.cli import cli as autonomy_cli


class CommandValidator:
    """Validates commands against a CLI"""

    def __init__(self, cli):
        """Extract autonomy command tree from the autonomy cli"""
        self.tree = {}
        for cmd_name, cmd in cli.commands.items():
            self.tree[cmd_name] = {
                "options": list(
                    itertools.chain(*[i.opts for i in cmd.params if isinstance(i, Option)])
                ),
                "commands": {},
            }
            if isinstance(cmd, click.Group):
                for sub_cmd_name in cmd.list_commands(click.Context):
                    sub_cmd = cli.commands[cmd_name].get_command(
                        click.Context, sub_cmd_name
                    )
                    self.tree[cmd_name]["commands"][sub_cmd_name] = {
                        "options": list(
                            itertools.chain(
                                *[i.opts for i in sub_cmd.params if isinstance(i, Option)]
                            )
                        )
                    }

    def validate(self, cmd) -> bool:
        m = re.match(AEA_COMMAND_REGEX, cmd)
        if not m:
            return False
        print(m[0])



# cmd = "autonomy deploy build deployment valory/hello_world:0.1.0:bafybeigvxwhxk3tyulfhhsfxvdfs5yd6rutlsnkv7ngnzi236yycjgrgaa keys.json --remote"
# v = CommandValidator(autonomy_cli)
# print(v.validate(cmd))

cmd = autonomy_cli.commands["deploy"].get_command(click.Context, "build")

print(dir(cmd))

# print([i.opts for i in cmd.params if isinstance(i, click.Argument)])