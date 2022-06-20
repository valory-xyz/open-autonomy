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

"""This module contains the tests for the code-blocks in the documentation."""

import platform
from pathlib import Path
from typing import Dict, List, Optional

import pytest

from tests.conftest import ROOT_DIR
from tests.test_docs.helper import (  # type: ignore
    CodeType,
    check_bash_commands_exist,
    check_code_blocks_exist,
    contains_code_blocks,
    extract_autonomy_commands,
    extract_make_commands,
    remove_doc_ellipsis,
    remove_ips_hashes,
    remove_line_comments,
)


class BaseTestDocCode:
    """Base class for doc code testing"""

    md_to_code: Dict[str, Dict] = {}
    code_type: CodeType = CodeType.NOCODE
    skipped_files: Optional[List[str]] = None

    def test_run_check(self) -> None:
        """Check the documentaion code"""

        assert (
            self.code_type != CodeType.NOCODE
        ), "This test class has not specified a code type to check for"
        assert (
            self.md_to_code != {}
        ), "This test class has not specified the md_to_code mapping"

        # Get all doc files that contain a block
        all_md_files = [
            p.relative_to(ROOT_DIR) for p in Path(ROOT_DIR, "docs").rglob("*.md")
        ]
        files_with_blocks = list(
            map(
                str,
                filter(
                    lambda f: "api" not in f.parts  # skip api folder
                    and contains_code_blocks(f, self.code_type.value),
                    all_md_files,
                ),
            )
        )
        if self.skipped_files:
            files_with_blocks = [
                f for f in files_with_blocks if f not in self.skipped_files
            ]
        not_checked_files = set(files_with_blocks).difference(
            set(self.md_to_code.keys())
        )

        assert (
            not not_checked_files
        ), f"The following (not skipped) doc files contain {self.code_type.value} blocks but are not being checked: {not_checked_files}"

        # Check all files
        for md_file, code_info in self.md_to_code.items():
            print(
                f"Checking {self.code_type.value} snippets in file {md_file}... ",
                end="",
            )

            # In doc files: remove tokens like "# ...\n" from the code
            # In code files: replace ipfs hashes with a placeholder
            check_code_blocks_exist(
                md_file=md_file,
                code_info=code_info,
                code_type=self.code_type,
                doc_process_fn=lambda s: remove_doc_ellipsis(remove_line_comments(s)),
                code_process_fn=lambda s: remove_ips_hashes(s),
            ),

            print("OK")


@pytest.mark.skipif(platform.system() == "Windows", reason="Need to be investigated.")
class TestYamlSnippets(BaseTestDocCode):
    """Test that all the yaml snippets in the documentation exist in the repository"""

    code_type = CodeType.YAML

    # This variable holds a mapping between every doc file and the code file
    # that contains the referenced code. Since a doc file can contain several code
    # snippets, a list with the target files ordered is provided.
    #
    # Use skip_blocks to specify a list of blocks that need to be skipped
    # Add by_line:: at the beggining of a code file path so the check is performed line by line
    # instead of checking the code block as a whole.

    md_to_code = {
        "docs/service_example.md": {
            "code_files": ["packages/valory/agents/hello_world/aea-config.yaml"],
        },
        "docs/price_oracle_fsms.md": {
            "code_files": [
                "packages/valory/skills/registration_abci/fsm_specification.yaml",
                "packages/valory/skills/safe_deployment_abci/fsm_specification.yaml",
                "packages/valory/skills/oracle_deployment_abci/fsm_specification.yaml",
                "packages/valory/skills/price_estimation_abci/fsm_specification.yaml",
                "packages/valory/skills/transaction_settlement_abci/fsm_specification.yaml",
                "packages/valory/skills/reset_pause_abci/fsm_specification.yaml",
                "packages/valory/skills/oracle_abci/fsm_specification.yaml",
            ],
        },
        "docs/simple_abci.md": {
            "code_files": ["packages/valory/skills/simple_abci/fsm_specification.yaml"],
        },
        "docs/networks.md": {"skip_blocks": [0]},
    }


@pytest.mark.skipif(platform.system() == "Windows", reason="Need to be investigated.")
class TestPythonSnippets(BaseTestDocCode):
    """Test that all the python snippets in the documentation exist in the repository"""

    code_type = CodeType.PYTHON

    # This variable holds a mapping between every doc file and the code file
    # that contains the referenced code. Since a doc file can contain several code
    # snippets, a list with the target files ordered is provided.
    #
    # Use skip_blocks to specify a list of blocks that need to be skipped
    # Add by_line:: at the beggining of a code file path so the check is performed line by line
    # instead of checking the code block as a whole.

    md_to_code = {
        "docs/abci_app_abstract_round_behaviour.md": {
            "code_files": [
                "by_line::packages/valory/skills/abstract_round_abci/behaviours.py"
            ],
            "skip_blocks": [1],
        },
        "docs/abci_app_class.md": {
            "code_files": [
                "by_line::packages/valory/skills/abstract_round_abci/base.py"
            ],
            "skip_blocks": [1],
        },
        "docs/service_example.md": {
            "code_files": [
                "by_line::packages/valory/skills/hello_world_abci/rounds.py",
                "by_line::packages/valory/skills/hello_world_abci/rounds.py",
                "packages/valory/skills/hello_world_abci/behaviours.py",
                "packages/valory/skills/hello_world_abci/behaviours.py",
                "packages/valory/skills/hello_world_abci/payloads.py",
            ],
        },
        "docs/price_oracle_intro.md": {
            "code_files": [
                "packages/valory/skills/oracle_abci/composition.py",
                "packages/valory/skills/oracle_abci/behaviours.py",
            ],
        },
        "docs/price_oracle_fsms.md": {
            "code_files": [
                "packages/valory/skills/oracle_abci/composition.py",
                "packages/valory/skills/oracle_abci/composition.py",
            ],
        },
        "docs/simple_abci.md": {
            "code_files": [
                "packages/valory/skills/simple_abci/behaviours.py",
                "packages/valory/skills/simple_abci/rounds.py",
            ],
        },
    }

    skipped_files = [
        "docs/abci_app_async_behaviour.md",  # just placeholder examples
        "docs/networks.md",  # only irrelevant one-liners,
        "docs/abci_app_abstract_round.md",  # just a placeholder example
    ]


class TestDocBashSnippets:
    """Class for doc bash snippet testing"""

    def test_run_check(self) -> None:
        """Check the documentaion code"""

        code_type = CodeType.BASH

        skipped_files: List[str] = ["docs/quick_start.md"]

        # Get all doc files that contain a block
        all_md_files = [
            str(p.relative_to(ROOT_DIR)) for p in Path(ROOT_DIR, "docs").rglob("*.md")
        ]
        files_with_blocks = list(
            filter(
                lambda f: "/api/" not in f  # skip api folder
                and contains_code_blocks(f, code_type.value),
                all_md_files,
            )
        )
        if skipped_files:
            files_with_blocks = [f for f in files_with_blocks if f not in skipped_files]

        all_mk_files = [
            str(p.relative_to(ROOT_DIR)) for p in Path(ROOT_DIR).rglob("*Makefile")
        ]

        all_mk_files = list(
            filter(
                lambda f: "third_party/" not in f
                and ".tox" not in f,  # skip some folders
                all_mk_files,
            )
        )

        make_commands = extract_make_commands(all_mk_files)
        autonomy_commands = extract_autonomy_commands()

        for md_file in files_with_blocks:
            check_bash_commands_exist(md_file, make_commands, autonomy_commands)
