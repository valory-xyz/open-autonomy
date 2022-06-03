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
from typing import Dict, List, Optional

from tests.conftest import ROOT_DIR
from tests.test_docs.helper import (  # type: ignore
    CodeType,
    NON_CODE_TOKENS,
    check_code_block,
    contains_code_blocks,
    remove_ips_hashes,
    remove_tokens,
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
            str(p.relative_to(ROOT_DIR)) for p in Path(ROOT_DIR, "docs").rglob("*.md")
        ]
        files_with_blocks = list(
            filter(
                lambda f: contains_code_blocks(f, self.code_type.value), all_md_files
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
            check_code_block(
                md_file=md_file,
                code_info=code_info,
                code_type=self.code_type,
                doc_process_fn=lambda s: remove_tokens(s, NON_CODE_TOKENS),
                code_process_fn=lambda s: remove_ips_hashes(s),
            ),

            print("OK")


class TestYamlSnippets(BaseTestDocCode):
    """Test that all the yaml snippets in the documentation exist in the repository"""

    code_type = CodeType.YAML

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


class TestPythonSnippets(BaseTestDocCode):
    """Test that all the python snippets in the documentation exist in the repository"""

    code_type = CodeType.PYTHON

    # This variable holds a mapping between every doc file and the code file
    # that contains the referenced code. Since a doc file can contain several code
    # snippets, a list with the target files ordered is provided.
    md_to_code = {
        "docs/abci_app_abstract_round_behaviour.md": {
            "code_files": ["packages/valory/skills/abstract_round_abci/behaviours.py"],
            "skip_blocks": [1],
            "line_by_line": True,
        },
    }

    skipped_files = [
        "docs/abci_app_async_behaviour.md",
        "docs/api/skills/transaction_settlement_abci/payloads.md",
        "docs/api/skills/price_estimation_abci/models.md",
        "docs/price_oracle_intro.md",
        "docs/api/skills/abstract_round_abci/common.md",
        "docs/api/skills/abstract_abci/dialogues.md",
        "docs/api/contracts/gnosis_safe_proxy_factory/contract.md",
        "docs/api/replay/agent.md",
        "docs/api/skills/abstract_round_abci/base.md",
        "docs/api/deploy/generators/docker_compose/base.md",
        "docs/api/skills/price_estimation_abci/rounds.md",
        "docs/api/skills/abstract_round_abci/serializer.md",
        "docs/price_oracle_fsms.md",
        "docs/api/protocols/abci/custom_types.md",
        "docs/abci_app_class.md",
        "docs/api/protocols/abci/dialogues.md",
        "docs/api/configurations/loader.md",
        "docs/api/skills/transaction_settlement_abci/rounds.md",
        "docs/api/cli/replay.md",
        "docs/api/skills/transaction_settlement_abci/behaviours.md",
        "docs/get_started.md",
        "docs/api/analyse/abci/app_spec.md",
        "docs/api/skills/abstract_round_abci/dialogues.md",
        "docs/api/skills/safe_deployment_abci/models.md",
        "docs/api/skills/abstract_round_abci/io/store.md",
        "docs/api/skills/registration_abci/payloads.md",
        "docs/api/cli/deploy.md",
        "docs/api/analyse/abci/logs.md",
        "docs/api/protocols/abci/message.md",
        "docs/api/analyse/abci/docstrings.md",
        "docs/api/analyse/benchmark/aggregate.md",
        "docs/api/skills/registration_abci/rounds.md",
        "docs/simple_abci.md",
        "docs/api/connections/abci/tendermint_encoder.md",
        "docs/api/skills/registration_abci/models.md",
        "docs/api/connections/abci/tendermint_decoder.md",
        "docs/api/skills/safe_deployment_abci/behaviours.md",
        "docs/api/connections/abci/dialogues.md",
        "docs/api/skills/registration_abci/behaviours.md",
        "docs/api/skills/price_estimation_abci/payloads.md",
        "docs/api/skills/oracle_deployment_abci/rounds.md",
        "docs/api/skills/abstract_round_abci/io/paths.md",
        "docs/api/deploy/constants.md",
        "docs/api/skills/oracle_deployment_abci/models.md",
        "docs/api/configurations/base.md",
        "docs/api/cli/utils/click_utils.md",
        "docs/api/deploy/generators/kubernetes/base.md",
        "docs/api/replay/utils.md",
        "docs/api/skills/abstract_round_abci/io/ipfs.md",
        "docs/api/connections/abci/scripts/genproto.md",
        "docs/api/protocols/abci/serialization.md",
        "docs/api/cli/analyse.md",
        "docs/api/deploy/base.md",
        "docs/api/skills/abstract_abci/handlers.md",
        "docs/api/connections/abci/connection.md",
        "docs/api/skills/safe_deployment_abci/payloads.md",
        "docs/api/connections/abci/check_dependencies.md",
        "docs/api/skills/safe_deployment_abci/rounds.md",
        "docs/api/skills/transaction_settlement_abci/payload_tools.md",
        "docs/api/deploy/image.md",
        "docs/api/skills/oracle_abci/models.md",
        "docs/api/analyse/abci/handlers.md",
        "docs/api/replay/tendermint.md",
        "docs/api/cli/develop.md",
        "docs/api/skills/abstract_round_abci/abci_app_chain.md",
        "docs/api/deploy/build.md",
        "docs/api/skills/abstract_round_abci/utils.md",
        "docs/api/skills/abstract_round_abci/behaviours.md",
        "docs/api/skills/price_estimation_abci/behaviours.md",
        "docs/api/skills/abstract_round_abci/models.md",
        "docs/api/skills/oracle_abci/behaviours.md",
        "docs/api/skills/oracle_deployment_abci/behaviours.md",
        "docs/networks.md",
        "docs/api/cli/core.md",
        "docs/api/skills/transaction_settlement_abci/models.md",
        "docs/api/skills/abstract_round_abci/handlers.md",
        "docs/api/contracts/gnosis_safe/contract.md",
        "docs/api/skills/oracle_deployment_abci/payloads.md",
        "docs/api/skills/abstract_round_abci/behaviour_utils.md",
        "docs/api/skills/abstract_round_abci/io/load.md",
        "docs/api/cli/hash.md",
        "docs/api/configurations/validation.md",
    ]
