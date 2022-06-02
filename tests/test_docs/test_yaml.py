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

from pathlib import Path

from tests.conftest import ROOT_DIR
from tests.test_docs.helper import (  # type: ignore
    NON_CODE_TOKENS,
    check_code_block,
    contains_code_blocks,
    remove_ips_hashes,
    remove_tokens,
)


def test_yaml_snippets() -> None:
    """Test that all the yaml snippets in the documentation exist in the repository"""

    # This variable holds a mapping between every doc file and the code file
    # that contains the referenced code. Since a doc file can contain several code
    # snippets, a list with the target files ordered is provided.
    md_to_code = {
        "docs/get_started.md": {
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

    # Get all doc files that contain a yaml block
    all_md_files = [
        str(p.relative_to(ROOT_DIR)) for p in Path(ROOT_DIR, "docs").rglob("*.md")
    ]
    files_with_yaml_blocks = list(
        filter(lambda f: contains_code_blocks(f, "yaml"), all_md_files)
    )
    not_checked_files = set(files_with_yaml_blocks).difference(set(md_to_code.keys()))

    assert (
        not not_checked_files
    ), f"The following doc files contain yaml blocks but are not being checked: {not_checked_files}"

    # Check all files
    for md_file, code_info in md_to_code.items():
        print(f"Checking yaml snippets in file {md_file}... ", end="")

        # In doc files: remove tokens like "# ...\n" from the code
        # In code files: replace ipfs hashes with a placeholder
        check_code_block(
            md_file=md_file,
            code_info=code_info,
            doc_process_fn=lambda s: remove_tokens(s, NON_CODE_TOKENS),
            code_process_fn=lambda s: remove_ips_hashes(s),
        ),

        print("OK")
