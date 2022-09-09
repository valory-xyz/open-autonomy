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
from scripts.check_doc_ipfs_hashes import read_file


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

    def validate(self, cmd: str, file_: str = "") -> bool:
        """Validates a command"""

        # Copy the tree
        tree = self.tree

        latest_subcmd = None

        cmd_parts = [i for i in cmd.split(" ") if i]

        # Iterate the command parts
        for cmd_part in cmd_parts:

            # Subcommands
            if cmd_part in tree["commands"].keys():
                latest_subcmd = cmd_part
                tree = tree["commands"][cmd_part]
                continue

            # Options
            if cmd_part.startswith("-"):
                if cmd_part not in tree["options"]:
                    print(
                        f"Command validation error in {file_}: option '{cmd_part}' is not present on the command tree {list(tree['options'])}:\n    {cmd}"
                    )
                    return False
                continue

            # Arguments
            if not latest_subcmd:
                print(f"Command validation error in {file_}: detected argument '{cmd_part}' but no latest subcommand exists yet:\n    {cmd}")
                return False

            if not tree["arguments"]:
                print(f"Command validation error in {file_}: argument '{cmd_part}' is not valid as the latest subcommand [{latest_subcmd}] does not admit arguments:\n    {cmd}")
                return False

            # If we reach here, this command part is an argument for either a command or for an option.
            # It could also be an non-existent option (or typo) but since we have no way of validating this,
            # we take for granted that it is correct.

        return True


def test_validate_doc_commands() -> None:
    """Test that doc commands are valid"""

    # Get the markdown files and the Makefile
    target_files = list(Path("docs").rglob("*.md"))
    target_files.append(Path("Makefile"))

    # Get the validator
    validator = CommandValidator(autonomy_cli)

    AUTONOMY_COMMAND_REGEX = r"(?P<full_cmd>(?P<cli>aea|autonomy) ((?!(&|'|\(|\[|\n|\.|`|\|)).)*)"

    skips = ["aea repo", "autonomy repo"]

    # Validate all matches
    for file_ in target_files:
        content = read_file(str(file_))

        # The regex currently finds package related commands. We need to use a general one.
        for match in [m.groupdict() for m in re.finditer(AUTONOMY_COMMAND_REGEX, content)]:
            cmd = match["full_cmd"].strip()

            if cmd in skips:
                continue
            assert validator.validate(cmd, file_)


def test_validator() -> None:
    """Test the command validator"""

    validator = CommandValidator(autonomy_cli)

    good_cmds = [
        "autonomy deploy build keys.json",
        "autonomy deploy build --docker --remote keys.json",
        "autonomy init --remote --ipfs",
    ]

    bad_cmds = [
        "autonomy deploy build --docker --bad_option keys.json", # non-existent option
        "autonomy bad_arg", # non-existent argument
    ]

    for cmd in good_cmds:
        assert validator.validate(cmd), f"Command {cmd} is not valid"

    for cmd in bad_cmds:
        assert not validator.validate(cmd), f"Command {cmd} is valid and it shouldn't."

validator = CommandValidator(autonomy_cli)
cmd = "autonomy analyse abci generate-app-specs"
validator.validate(cmd)

# test_validate_doc_commands()