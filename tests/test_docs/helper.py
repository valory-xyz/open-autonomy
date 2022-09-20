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

"""This module contains helper function to extract code from the .md files."""
import os
import re
from enum import Enum
from functools import partial
from pathlib import Path
from typing import Callable, Dict, List, Optional

import mistune  # type: ignore

from tests.conftest import ROOT_DIR


MISTUNE_BLOCK_CODE_ID = "block_code"
IPFS_HASH_REGEX = r"bafybei[A-Za-z0-9]{52}"
PYTHON_LINE_COMMENT_REGEX = r"^#.*\n"
DOC_ELLIPSIS_REGEX = r"\s*#\s...\n"
PYTHON_COMMAND = r"^pyt(hon|est) (?P<file_name>.*\.py).*$"
MAKE_COMMAND = r"^make (?P<cmd_name>.*)$"
AUTONOMY_COMMAND = r"^(?P<cmd_name>autonomy .*)$"
MAKEFILE_COMMAND = r"^(?P<command>.*):$"
MAKEFILE_COMMAND_PHONY = r"^\.PHONY: (?P<command>.*)$"


class CodeType(Enum):
    """Types of code blocks in the docs"""

    PYTHON = "python"
    YAML = "yaml"
    BASH = "bash"
    NOCODE = "nocode"


def block_code_filter(b: Dict) -> bool:
    """Check Mistune block is a code block."""
    return b["type"] == MISTUNE_BLOCK_CODE_ID


def type_filter(type_: Optional[str], b: Dict) -> bool:
    """
    Check Mistune code block is of a certain type.

    If the field "info" is None, return False.
    If type_ is None, this function always return true.

    :param type_: the expected type of block (optional)
    :param b: the block dicionary.
    :return: True if the block should be accepted, false otherwise.
    """
    if type_ is None:
        return True
    return b["info"].strip() == type_ if b["info"] is not None else False


def extract_code_blocks(filepath: str, filter_: Optional[str] = None) -> list:
    """Extract code blocks from .md files."""
    content = Path(filepath).read_text(encoding="utf-8")
    markdown_parser = mistune.create_markdown(renderer=mistune.AstRenderer())
    blocks = markdown_parser(content)
    actual_type_filter = partial(type_filter, filter_)
    code_blocks = list(filter(block_code_filter, blocks))
    bash_code_blocks = filter(actual_type_filter, code_blocks)
    return list(b["text"] for b in bash_code_blocks)


def extract_python_code(filepath: str) -> str:
    """Removes the license part from the scripts"""
    python_str = ""
    with open(filepath, "r") as python_file:
        read_python_file = python_file.readlines()
    for i in range(21, len(read_python_file)):
        python_str += read_python_file[i]

    return python_str


def read_file(filepath: str) -> str:
    """Loads a file into a string"""
    with open(filepath, "r") as file_:
        file_str = file_.read()
    return file_str


def remove_line_comments(string: str) -> str:
    """Removes tokens from a python string"""
    return re.sub(PYTHON_LINE_COMMENT_REGEX, "", string)


def remove_doc_ellipsis(string: str) -> str:
    """Removes # ... from a python string"""
    return re.sub(DOC_ELLIPSIS_REGEX, "", string)


def remove_ips_hashes(string: str) -> str:
    """Replaces IPFS hashes with a placeholder"""
    return re.sub(IPFS_HASH_REGEX, "<ipfs_hash>", string)


def contains_code_blocks(file_path: str, block_type: str) -> bool:
    """Check if a doc file contains code blocks"""
    doc_path = os.path.join(ROOT_DIR, file_path)
    code_blocks = extract_code_blocks(filepath=doc_path, filter_=block_type)
    return len(code_blocks) > 0


def check_code_blocks_exist(
    md_file: str,
    code_info: Dict,
    code_type: CodeType,
    doc_process_fn: Optional[Callable] = None,
    code_process_fn: Optional[Callable] = None,
) -> None:
    """Check code blocks from the documentation"""
    code_files: List = code_info.get("code_files", None)
    skip_blocks: List = code_info.get("skip_blocks", None)

    # Load the code blocks from the doc file
    doc_path = os.path.join(ROOT_DIR, md_file)
    code_blocks = extract_code_blocks(filepath=doc_path, filter_=code_type.value)

    if skip_blocks:
        code_blocks = [
            code_blocks[i] for i in range(len(code_blocks)) if i not in skip_blocks
        ]

    if not code_blocks:
        return

    # Process the code blocks
    code_blocks = (
        list(map(doc_process_fn, code_blocks)) if doc_process_fn else code_blocks
    )

    # Ensure the code block mapping is correct. We ned a code file for each code block in the doc file
    assert len(code_blocks) == len(
        code_files
    ), f"Doc checker found {len(code_blocks)} non-skipped code blocks in {md_file} but only {len(code_files)} are being checked"

    for i, code_file in enumerate(code_files):
        # Check if the match must be performed line by line
        line_by_line = code_file.startswith("by_line::")
        code_file = code_file.replace("by_line::", "")

        # Load the code file and process it
        code_path = os.path.join(ROOT_DIR, code_file)
        code = read_file(code_path)
        code = code_process_fn(code) if code_process_fn else code

        # Perform the check
        if line_by_line:
            for line in code_blocks[i].split("\n"):
                assert (
                    line in code
                ), f"This line in {md_file} doesn't exist in the code file {code_file}:\n\n'{line}'"
            continue
        assert (
            code_blocks[i] in code
        ), f"This code-block in {md_file} doesn't exist in the code file {code_file}:\n\n{code_blocks[i]}"


def extract_make_commands(makefile_paths: List[str]) -> List[str]:
    """Extract make commands from a file"""
    commands = ["clean"]
    for makefile_path in makefile_paths:
        with open(makefile_path, "r", encoding="utf-8") as makefile:
            for line in makefile.readlines():
                match = re.match(MAKEFILE_COMMAND, line)
                if match:
                    commands += match.groupdict()["command"].split(" ")
                    continue
                match = re.match(MAKEFILE_COMMAND_PHONY, line)
                if match:
                    commands += match.groupdict()["command"].split(" ")
    return commands


def check_bash_commands_exist(md_file: str, make_commands: List[str]) -> None:
    """Check whether a bash code block exists in the codebase"""
    # Load the code file and process it
    doc_path = os.path.join(ROOT_DIR, md_file)
    code_blocks = extract_code_blocks(filepath=doc_path, filter_=CodeType.BASH.value)

    for code_block in code_blocks:
        for line in code_block.split("\n"):

            # Python/pytest commands
            match = re.match(PYTHON_COMMAND, line)
            if match:
                file_name = os.path.join(
                    ROOT_DIR, ROOT_DIR, match.groupdict()["file_name"]
                )
                assert os.path.isfile(
                    file_name
                ), f"File {file_name} referenced in {md_file} does not exist"
                continue

            # Make commands
            match = re.match(MAKE_COMMAND, line)
            if match:
                mk_cmds = match.groupdict()["cmd_name"]
                for mk_cmd in mk_cmds.split(" "):
                    assert (
                        mk_cmd in make_commands
                    ), f"Make command '{mk_cmd}' referenced in {md_file} is not present in the Makefile"
                continue
