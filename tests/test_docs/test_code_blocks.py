# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022-2023 Valory AG
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

from pathlib import Path
from typing import Dict, List, Optional

from tests.conftest import ROOT_DIR
from tests.test_docs.helper import (  # type: ignore
    CodeType,
    check_bash_commands_exist,
    check_code_blocks_exist,
    contains_code_blocks,
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

    def _to_os_path(self, file_path: str) -> str:
        r"""
        Transforms a file path to a path in the OS the code is being executed on.

        Example:
        Given file_path="docs/fsm.yaml",
        this method would transform it to:
         - "docs/fsm.yaml" for POSIX systems. (no changes)
         - "docs\\fsm.yaml" for Windows systems.

        :param file_path: the file path to transform.
        :return: the transformed file path
        """
        path = Path(file_path)
        return str(path)

    def test_run_check(self) -> None:
        """Check the documentation code"""

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
            os_path_skipped_files = {
                self._to_os_path(file) for file in self.skipped_files
            }
            files_with_blocks = [
                f for f in files_with_blocks if f not in os_path_skipped_files
            ]
        os_path_md_to_code = {self._to_os_path(file) for file in self.md_to_code.keys()}
        not_checked_files = set(files_with_blocks).difference(os_path_md_to_code)

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


class TestYamlSnippets(BaseTestDocCode):
    """Test that all the yaml snippets in the documentation exist in the repository"""

    code_type = CodeType.YAML

    # This variable holds a mapping between every doc file and the code file
    # that contains the referenced code. Since a doc file can contain several code
    # snippets, a list with the target files ordered is provided.
    #
    # Use skip_blocks to specify a list of blocks that need to be skipped
    # Add by_line:: at the beginning of a code file path so the check is performed line by line
    # instead of checking the code block as a whole.

    md_to_code = {
        "docs/demos/hello_world_demo.md": {
            "code_files": ["packages/valory/agents/hello_world/aea-config.yaml"],
        },
        # TODO uncomment and update this doc, when the safe-related rounds get removed from the `price-oracle`.
        # "docs/demos/price_oracle_fsms.md": {  # flake8: noqa: E800
        #     "code_files": [  # flake8: noqa: E800
        #         "packages/valory/skills/registration_abci/fsm_specification.yaml",  # flake8: noqa: E800
        #         "packages/valory/skills/transaction_settlement_abci/fsm_specification.yaml",  # flake8: noqa: E800
        #         "packages/valory/skills/reset_pause_abci/fsm_specification.yaml",  # flake8: noqa: E800
        #     ],  # flake8: noqa: E800
        #     "skip_blocks": [2, 3, 6],  # flake8: noqa: E800
        # },  # flake8: noqa: E800
        "docs/guides/configure_access_external_chains.md": {"skip_blocks": [0]},
    }

    skipped_files = [
        "docs/guides/service_configuration_file.md",
        "docs/demos/price_oracle_fsms.md",
    ]


class TestPythonSnippets(BaseTestDocCode):
    """Test that all the python snippets in the documentation exist in the repository"""

    code_type = CodeType.PYTHON

    # This variable holds a mapping between every doc file and the code file
    # that contains the referenced code. Since a doc file can contain several code
    # snippets, a list with the target files ordered is provided.
    #
    # Use skip_blocks to specify a list of blocks that need to be skipped
    # Add by_line:: at the beginning of a code file path so the check is performed line by line
    # instead of checking the code block as a whole.

    md_to_code = {
        "docs/key_concepts/abci_app_abstract_round_behaviour.md": {
            "code_files": [
                "by_line::packages/valory/skills/abstract_round_abci/behaviours.py"
            ],
            "skip_blocks": [1],
        },
        "docs/key_concepts/abci_app_class.md": {
            "code_files": [
                "by_line::packages/valory/skills/abstract_round_abci/base.py"
            ],
            "skip_blocks": [1],
        },
        "docs/demos/hello_world_demo.md": {
            "code_files": [
                "by_line::packages/valory/skills/hello_world_abci/rounds.py",
                "by_line::packages/valory/skills/hello_world_abci/rounds.py",
                "packages/valory/skills/hello_world_abci/behaviours.py",
                "packages/valory/skills/hello_world_abci/behaviours.py",
                "packages/valory/skills/hello_world_abci/payloads.py",
            ],
        },
    }

    skipped_files = [
        "docs/key_concepts/abci_app_async_behaviour.md",  # just placeholder examples
        "docs/guides/configure_access_external_chains.md",  # only irrelevant one-liners,
        "docs/key_concepts/abci_app_abstract_round.md",  # just a placeholder example
        "docs/demos/price_oracle_fsms.md",  # price oracle has been extracted to a separate repo on #1441
        "docs/demos/price_oracle_technical_details.md",  # price oracle has been extracted to a separate repo on #1441
        "docs/advanced_reference/developer_tooling/benchmarking.md",  # just placeholder examples
    ]


class TestDocBashSnippets:
    """Class for doc bash snippet testing"""

    def test_run_check(self) -> None:
        """Check the documentation code"""

        code_type = CodeType.BASH

        skipped_files: List[str] = []

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

        all_mk_files = [str(p.absolute()) for p in Path(ROOT_DIR).rglob("*Makefile")]

        all_mk_files = list(
            filter(
                lambda f: "third_party/" not in f
                and ".tox" not in f,  # skip some folders
                all_mk_files,
            )
        )

        make_commands = extract_make_commands(all_mk_files)

        for md_file in files_with_blocks:
            check_bash_commands_exist(
                md_file,
                make_commands,
            )
