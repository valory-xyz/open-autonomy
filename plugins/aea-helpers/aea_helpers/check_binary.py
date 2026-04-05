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

"""Check that a built agent runner binary starts correctly."""

import os
import subprocess  # nosec
import sys
import time
from pathlib import Path
from typing import Dict, Optional

import click


def run_binary_check(
    binary_path: str,
    agent_dir: str = "agent",
    timeout: int = 80,
    search_string: str = "Starting AEA",
    env_vars: Optional[Dict[str, str]] = None,
) -> bool:
    """Spawn the agent runner binary and check for successful startup.

    Runs the binary in a subprocess, monitoring stdout for a search string
    that indicates the agent started successfully.

    :param binary_path: path to the compiled binary.
    :param agent_dir: path to agent directory.
    :param timeout: max seconds to wait for the search string.
    :param search_string: string indicating successful startup.
    :param env_vars: additional environment variables to set.
    :return: True if search string found within timeout.
    """
    binary_abs = str(Path(binary_path).resolve())
    agent_abs = str(Path(agent_dir).resolve())

    env = os.environ.copy()
    if env_vars:
        env.update(env_vars)

    proc = subprocess.Popen(  # nosec
        [binary_abs, "-s", "run"],
        cwd=agent_abs,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
    )

    start = time.time()
    found = False
    try:
        for line in iter(proc.stdout.readline, ""):  # type: ignore
            try:
                sys.stdout.write(line)
                sys.stdout.flush()
            except UnicodeEncodeError:
                sys.stdout.write(
                    line.encode("utf-8", errors="ignore").decode("utf-8")
                )

            if search_string in line:
                found = True
                break
            if time.time() - start > timeout:
                break
    finally:
        proc.terminate()

    return found


@click.command(name="check-binary")
@click.argument("binary_path", type=click.Path(exists=True))
@click.argument("agent_dir", type=click.Path(exists=True), default="agent")
@click.option(
    "--timeout",
    default=80,
    type=int,
    help="Max seconds to wait for the search string (default: 80).",
)
@click.option(
    "--search-string",
    default="Starting AEA",
    help='String indicating successful startup (default: "Starting AEA").',
)
@click.option(
    "--env-var",
    "env_vars_raw",
    multiple=True,
    help="Extra env vars as KEY=VALUE (repeatable).",
)
def check_binary(
    binary_path: str,
    agent_dir: str,
    timeout: int,
    search_string: str,
    env_vars_raw: tuple,
) -> None:
    """Check that a built agent runner binary starts correctly.

    Spawns BINARY_PATH in a subprocess, monitors stdout for the search string,
    and exits 0 on success or 1 on timeout.
    """
    env_vars = {}
    for item in env_vars_raw:
        if "=" not in item:
            raise click.BadParameter(
                f"Expected KEY=VALUE format, got: {item}", param_hint="--env-var"
            )
        key, value = item.split("=", 1)
        env_vars[key] = value

    click.echo(
        f"Running binary check: {binary_path}\n"
        f"Waiting up to {timeout}s for '{search_string}'..."
    )

    found = run_binary_check(
        binary_path=binary_path,
        agent_dir=agent_dir,
        timeout=timeout,
        search_string=search_string,
        env_vars=env_vars or None,
    )

    if found:
        click.echo(f"[OK] Found '{search_string}' within {timeout}s")
        sys.exit(0)
    else:
        click.echo(f"[FAIL] Did not find '{search_string}' within {timeout}s")
        sys.exit(1)
