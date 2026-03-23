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

from aea_helpers.check_doc_hashes import check_doc_hashes
from aea_helpers.check_dependencies import check_dependencies
from aea_helpers.bump_dependencies import bump_dependencies


@click.group()
@click.version_option()
def cli() -> None:
    """AEA helper utilities for CI and dependency management."""


cli.add_command(check_doc_hashes)
cli.add_command(check_dependencies)
cli.add_command(bump_dependencies)
