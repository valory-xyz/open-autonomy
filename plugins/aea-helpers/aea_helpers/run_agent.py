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

"""Python wrapper for run_agent.sh shell script."""

import subprocess  # nosec
import sys
from importlib import resources

import click


@click.command(name="run-agent")
@click.option("--name", required=True, help="Agent name (e.g. valory/trader).")
@click.option("--env-file", default=".env", help="Env file to source (default: .env).")
@click.option(
    "--agent-env-file", default=None, help="Env file passed to aea run --env."
)
@click.option("--config-replace", is_flag=True, help="Run config-replace after fetch.")
@click.option("--config-mapping", default=None, help="Path to config mapping file.")
@click.option(
    "--connection-key", is_flag=True, help="Add connection key (second add-key call)."
)
@click.option(
    "--free-ports", is_flag=True, help="Auto-find free ports for tendermint/HTTP."
)
@click.option("--skip-make-clean", is_flag=True, help="Skip make clean step.")
@click.option("--abci-port", type=int, default=None, help="Explicit ABCI port.")
@click.option("--rpc-port", type=int, default=None, help="Explicit RPC port.")
@click.option("--p2p-port", type=int, default=None, help="Explicit P2P port.")
@click.option("--com-port", type=int, default=None, help="Explicit COM port.")
@click.option("--http-port", type=int, default=None, help="Explicit HTTP port.")
def run_agent(**kwargs: object) -> None:
    """Fetch, configure, and run an agent locally."""
    script = resources.files("aea_helpers.scripts").joinpath("run_agent.sh")
    cmd = ["bash", str(script)]

    for key, val in kwargs.items():
        flag = f"--{key.replace('_', '-')}"
        if isinstance(val, bool) and val:
            cmd.append(flag)
        elif val is not None and not isinstance(val, bool):
            cmd.extend([flag, str(val)])

    result = subprocess.run(cmd, check=False)  # nosec
    sys.exit(result.returncode)
