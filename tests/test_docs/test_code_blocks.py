# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022-2024 Valory AG
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
from typing import Callable, Dict, List, Optional, cast

from tests.conftest import ROOT_DIR
from tests.test_docs.helper import (  # type: ignore
    CodeType,
    check_bash_commands_exist,
    check_code_blocks_exist,
    contains_code_blocks,
    extract_make_commands,
    remove_doc_ellipsis,
    remove_line_comments,
    remove_yaml_hashes,
)


class BaseTestDocCode:
    """Base class for doc code testing"""

    md_to_code: Dict[str, Dict] = {}
    code_type: CodeType = CodeType.NOCODE
    skipped_files: Optional[List[str]] = None
    doc_process_fn: Optional[Callable] = None
    code_process_fn: Optional[Callable] = None

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
                    cast(
                        Callable[[Path], bool],
                        lambda f: "api" not in f.parts  # skip api folder
                        and contains_code_blocks(f, self.code_type.value),
                    ),
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

            # Eliminate the "self" dependency of the lambda functions.
            # This assignment cannot be condensed using the "if" ternary operator.
            doc_process_fn = None
            if self.doc_process_fn is not None:

                def doc_process_fn(s):  # type: ignore
                    return self.doc_process_fn(s)

            code_process_fn = None
            if self.code_process_fn is not None:

                def code_process_fn(s):  # type: ignore
                    return self.code_process_fn(s)

            check_code_blocks_exist(
                md_file=md_file,
                code_info=code_info,
                code_type=self.code_type,
                doc_process_fn=doc_process_fn,
                code_process_fn=code_process_fn,
            )

            print("OK")


class TestYamlSnippets(BaseTestDocCode):
    """Test that all the yaml snippets in the documentation exist in the repository"""

    code_type = CodeType.YAML

    # Preprocessing function:
    # - For Yaml snippets: `doc_process_fn` -> remove tokens like "# (...)\n" from the code
    # - For Yaml snippets: `code_process_fn` -> remove ":bafybei..." hashes after component ID
    def doc_process_fn(self, s):  # type: ignore
        """Doc preprocessing function"""
        return remove_doc_ellipsis(remove_line_comments(s))

    def code_process_fn(self, s):  # type: ignore
        """Code preprocessing function"""
        return remove_yaml_hashes(s)

    # This variable holds a mapping between every doc file and the code files
    # that contains the referenced code. Since a doc file can contain several code
    # snippets, a list with the target files ordered is provided.
    #
    # Use skip_blocks to specify a list of blocks that need to be skipped or add a file to skipped_files
    # to skip it completely.
    # Add by_line:: at the beginning of a code file path so the check is performed line by line
    # instead of checking the code block as a whole.

    md_to_code = {
        "docs/guides/deploy_service.md": {"skip_blocks": [0]},
        "docs/advanced_reference/developer_tooling/benchmarking.md": {
            "skip_blocks": [0]
        },
        "docs/guides/draft_service_idea_and_define_fsm_specification.md": {
            "code_files": [
                "https://raw.githubusercontent.com/valory-xyz/hello-world/main/packages/valory/skills/hello_world_abci/fsm_specification.yaml"
            ]
        },
    }

    skipped_files = [
        "docs/guides/define_agent.md",  # TODO: How to check against hello w.? only changes name of vendor and agent.
        "docs/guides/define_service.md",  # TODO: How to check against hello w.? only changes name of vendor and service
        "docs/configure_service/service_configuration_file.md",
        "docs/configure_service/on-chain_deployment_checklist.md",  # just placeholder examples
        "docs/configure_service/configure_access_external_chains.md",  # just placeholder examples
        "docs/advanced_reference/developer_tooling/dev_mode.md",  # just placeholder examples
        "docs/advanced_reference/commands/autonomy_deploy.md",  # blocks contain resource values on deployment configurations
    ]


class TestPythonSnippets(BaseTestDocCode):
    """Test that all the python snippets in the documentation exist in the repository"""

    code_type = CodeType.PYTHON

    # Preprocessing function:
    # - For Python snippets: `doc_process_fn` -> remove tokens like "# (...)\n" from the code
    def doc_process_fn(self, s):  # type: ignore
        """Doc preprocessing function"""
        return remove_doc_ellipsis(remove_line_comments(s))

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
        "docs/advanced_reference/commands/autonomy_analyse.md": {"skip_blocks": [0]},
        "docs/key_concepts/aea.md": {"code_files": [], "skip_blocks": [0, 1]},
    }

    skipped_files = [
        "docs/key_concepts/abci_app_async_behaviour.md",  # just placeholder examples
        "docs/configure_service/configure_access_external_chains.md",  # only irrelevant one-liners,
        "docs/key_concepts/abci_app_abstract_round.md",  # just a placeholder example
        "docs/demos/price_oracle_fsms.md",  # price oracle has been extracted to a separate repo on #1441
        "docs/demos/price_oracle_technical_details.md",  # price oracle has been extracted to a separate repo on #1441
        "docs/advanced_reference/developer_tooling/benchmarking.md",  # just placeholder examples
        "docs/configure_service/on-chain_deployment_checklist.md",  # just placeholder examples
    ]


class TestJsonSnippets(BaseTestDocCode):
    """Test that all the yaml snippets in the documentation exist in the repository"""

    code_type = CodeType.JSON

    # This variable holds a mapping between every doc file and the code files
    # that contains the referenced code. Since a doc file can contain several code
    # snippets, a list with the target files ordered is provided.
    #
    # Use skip_blocks to specify a list of blocks that need to be skipped or add a file to skipped_files
    # to skip it completely.
    # Add by_line:: at the beginning of a code file path so the check is performed line by line
    # instead of checking the code block as a whole.

    md_to_code = {
        # "docs/guides/deploy_service.md": { # noqa: E800
        #     "code_files": [ # noqa: E800
        #         "by_line::deployments/keys/hardhat_keys.json", # noqa: E800
        #         "by_line::deployments/keys/hardhat_keys.json", # noqa: E800
        #     ], # noqa: E800
        # }, # noqa: E800
        "docs/guides/quick_start.md": {
            "code_files": ["by_line::deployments/keys/hardhat_keys.json"],
        },
        "docs/advanced_reference/developer_tooling/dev_mode.md": {
            "code_files": ["by_line::deployments/keys/hardhat_keys.json"]
        },
        "docs/counter_example.md": {
            "code_files": ["by_line::deployments/keys/hardhat_keys.json"]
        },
    }

    skipped_files = [
        "docs/guides/deploy_service.md",
        "docs/advanced_reference/commands/autonomy_deploy.md",
        "docs/guides/set_up.md",
        "docs/guides/overview_of_the_development_process.md",
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
