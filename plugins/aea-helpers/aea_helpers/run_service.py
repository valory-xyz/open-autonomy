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

"""Python wrapper for run_service.sh shell script."""

import subprocess  # nosec
import sys
from importlib import resources

import click


@click.command(name="run-service")
@click.option("--name", required=True, help="Service name (e.g. valory/trader).")
@click.option("--env-file", default=".env", help="Env file to source (default: .env).")
@click.option(
    "--keys-file", default="keys.json", help="Keys file (default: keys.json)."
)
@click.option("--agents", type=int, default=4, help="Number of agents (default: 4).")
@click.option(
    "--author", default="valory", help="Author for init step (default: valory)."
)
@click.option("--cpu-limit", type=float, default=None, help="Agent CPU limit.")
@click.option("--memory-limit", type=int, default=None, help="Agent memory limit (MB).")
@click.option(
    "--memory-request", type=int, default=None, help="Agent memory request (MB)."
)
@click.option("--detach", is_flag=True, help="Run deployment in detached mode.")
@click.option(
    "--docker-cleanup", is_flag=True, help="Clean up Docker containers before start."
)
@click.option("--skip-init", is_flag=True, help="Skip the init step.")
@click.option(
    "--pre-deploy-cmd", default=None, help="Command to run before deploy build."
)
@click.option(
    "--post-deploy-cmd", default=None, help="Command to run after deploy build."
)
def run_service(**kwargs: object) -> None:
    """Build and deploy an agent service."""
    script = resources.files("aea_helpers.scripts").joinpath("run_service.sh")
    cmd = ["bash", str(script)]

    for key, val in kwargs.items():
        flag = f"--{key.replace('_', '-')}"
        if isinstance(val, bool) and val:
            cmd.append(flag)
        elif val is not None and not isinstance(val, bool):
            cmd.extend([flag, str(val)])

    result = subprocess.run(cmd, check=False)  # nosec
    sys.exit(result.returncode)
