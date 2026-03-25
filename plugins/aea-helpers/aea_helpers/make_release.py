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

"""Create a git tag and GitHub release."""

import subprocess
import sys

import click


@click.command(name="make-release")
@click.option("--version", required=True, help="Release version (e.g. 1.0.0).")
@click.option("--env", "environment", required=True, help="Release environment (e.g. prod, staging).")
@click.option("--description", required=True, help="Release description.")
def make_release(version: str, environment: str, description: str) -> None:
    """Create a git tag and GitHub release."""
    if not version:
        print("Error: VERSION is required.")
        sys.exit(1)
    if not environment:
        print("Error: ENV is required.")
        sys.exit(1)

    tag = f"release_{version}_{environment}"
    title = f"Release {version} ({environment})"

    print(f"Creating tag: {tag}")
    subprocess.run(["git", "tag", "-a", tag, "-m", description], check=True)

    print(f"Pushing tag: {tag}")
    subprocess.run(["git", "push", "origin", tag], check=True)

    print(f"Creating GitHub release: {title}")
    subprocess.run(
        [
            "gh",
            "release",
            "create",
            tag,
            "--title",
            title,
            "--notes",
            description,
        ],
        check=True,
    )

    print(f"Release {tag} created successfully.")
