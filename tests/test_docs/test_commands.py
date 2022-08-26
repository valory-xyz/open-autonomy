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
from pathlib import Path
from typing import Dict, Union

import click
from click.core import Command, Group, Option

from autonomy.cli import cli as autonomy_cli
from scripts.check_doc_ipfs_hashes import AEA_COMMAND_REGEX, read_file


def get_cmd_data(cmd: Union[Command, Group]) -> Dict:
    """Returns a dict containing the command options and arguments."""

    return {
        "commands": {},
        "options": list(
            itertools.chain(*[i.opts for i in cmd.params if isinstance(i, Option)])
        ),
        "arguments": list(
            itertools.chain(
                *[i.opts for i in cmd.params if isinstance(i, click.Argument)]
            )
        ),
    }


class CommandValidator:
    """Validates commands against a CLI"""

    def __init__(self, cli: Group):
        """Extract autonomy command tree from the autonomy cli"""

        # CLI level
        self.tree = {
            "commands": {cli.name: get_cmd_data(cli)},
        }

        # Command level
        for cmd_name, cmd in cli.commands.items():
            self.tree["commands"][cli.name]["commands"][cmd_name] = get_cmd_data(cmd)

            # Sub-command level
            if isinstance(cmd, click.Group):
                for sub_cmd_name in cmd.list_commands(click.Context):
                    sub_cmd = cli.commands[cmd_name].get_command(
                        click.Context, sub_cmd_name
                    )
                    self.tree["commands"][cli.name]["commands"][cmd_name]["commands"][
                        sub_cmd_name
                    ] = get_cmd_data(sub_cmd)

    def validate(self, cmd: str) -> bool:
        """Validates a command"""

        # Copy the tree
        tree = self.tree

        # Iterate the command parts
        for cmd_part in cmd.split(" "):

            # Check options
            if cmd_part.startswith("-") and cmd_part not in tree["options"]:
                print(
                    f"Command validation error: option '{cmd_part}' is not present on the command tree {list(tree['options'])}:\n    {cmd}"
                )
                return False

            # Leaf: check arguments
            if not tree["commands"].keys():
                if len(tree["arguments"]) == 0:
                    print(
                        f"Command validation error: argument '{cmd_part}' is not present on the command tree {list(tree['arguments'].keys())}:\n    {cmd}"
                    )
                    return False

                # Stop if this is the final command part
                if cmd.endswith(cmd_part):
                    break
                continue

            # Branch: check command
            if cmd_part not in tree["commands"].keys():
                print(
                    f"Command validation error: command '{cmd_part}' is not present on the command tree {list(tree['commands'].keys())}:\n    {cmd}"
                )
                return False

            # Update the tree if this is not an option or an argument.
            # Options/arguments are at the same level as their corresponding commands.
            if not cmd_part.startswith("-") and tree["commands"].keys():
                tree = tree["commands"][cmd_part]

        return True


def test_validate_doc_commands() -> None:
    """Test that doc commands are valid"""

    # Get the markdown files and the Makefile
    target_files = list(Path("docs").rglob("*.md"))
    target_files.append(Path("Makefile"))

    # Get the validator
    validator = CommandValidator(autonomy_cli)

    #
    for file_ in target_files:
        content = read_file(str(file_))

        # The regex currently finds package related commands. We need to use a general one.
        for match in [m.groupdict() for m in re.finditer(AEA_COMMAND_REGEX, content)]:
            assert validator.validate(match["full_cmd"])


def test_validator() -> None:
    """Test the command validator"""

    validator = CommandValidator(autonomy_cli)

    good_cmds = [
        "autonomy deploy build keys.json",
        "autonomy deploy build --docker --remote keys.json",
    ]

    bad_cmds = [
        "autonomy deploy build --docker --remoote keys.json",
    ]

    for cmd in good_cmds:
        assert validator.validate(cmd), f"Command {cmd} is not valid"

    for cmd in bad_cmds:
        assert not validator.validate(cmd), f"Command {cmd} is valid and it shouldn't."
