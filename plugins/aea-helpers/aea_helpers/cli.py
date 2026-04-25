# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2026 Valory AG
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

"""CLI entry point for aea-helpers."""

import click
from aea_helpers.bump_dependencies import bump_dependencies
from aea_helpers.check_binary import check_binary
from aea_helpers.check_dependencies import check_dependencies
from aea_helpers.check_doc_hashes import check_doc_hashes
from aea_helpers.config_replace import config_replace
from aea_helpers.generate_contract_list import generate_contract_list
from aea_helpers.make_release import make_release
from aea_helpers.pyinstaller_deps import bin_template_path, build_binary_deps
from aea_helpers.run_agent import run_agent
from aea_helpers.run_service import run_service

# NOTE: ``check-third-party-hashes`` and ``generate-api-docs`` used to live
# here but have been promoted to the upstream ``open-aea-ci-helpers`` plugin
# (valory-xyz/open-aea#876, released in open-aea 2.2.1). Tox envs now call
# ``aea-ci check-third-party-hashes --upstream valory-xyz/open-aea@2.2.2`` and
# ``aea-ci generate-api-docs --source-dir autonomy ...`` directly.


@click.group()
@click.version_option()
def cli() -> None:
    """AEA helper utilities for CI, dependency management, and deployment."""


cli.add_command(bin_template_path)
cli.add_command(build_binary_deps)
cli.add_command(bump_dependencies)
cli.add_command(check_binary)
cli.add_command(check_dependencies)
cli.add_command(check_doc_hashes)
cli.add_command(config_replace)
cli.add_command(generate_contract_list)
cli.add_command(make_release)
cli.add_command(run_agent)
cli.add_command(run_service)
