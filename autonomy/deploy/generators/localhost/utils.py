# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2024 Valory AG
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

"""Localhost Deployment utilities."""
import json
import os
import platform
import shutil
import subprocess  # nosec
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from aea.configurations.constants import DEFAULT_AEA_CONFIG_FILE, VENDOR

from autonomy.deploy.constants import (
    BENCHMARKS_DIR,
    TENDERMINT_BIN_UNIX,
    TENDERMINT_BIN_WINDOWS,
)


LOCAL_TENDERMINT_VERSION = "0.34.19"


def check_tendermint_version() -> Path:
    """Check tendermint version."""
    tendermint_executable = Path(str(shutil.which(TENDERMINT_BIN_UNIX)))
    if platform.system() == "Windows":
        tendermint_executable = (
            Path(os.path.dirname(sys.executable)) / TENDERMINT_BIN_WINDOWS
        )

    if (  # check tendermint version
        tendermint_executable is None
        or (
            current_version := subprocess.check_output(  # nosec
                [tendermint_executable, "version"]
            )
            .strip()
            .decode()
        )
        != LOCAL_TENDERMINT_VERSION
    ):
        raise FileNotFoundError(
            f"Please install tendermint version {LOCAL_TENDERMINT_VERSION} "
            f"or build and run via docker by using the --docker flag."
            + f"\nYour tendermint version is: {current_version}"
            if current_version
            else ""
        )

    return tendermint_executable


def _run_aea_cmd(
    args: List[str],
    cwd: Optional[Path] = None,
    stdout: int = subprocess.PIPE,
    stderr: int = subprocess.PIPE,
    ignore_error: Optional[str] = None,
    **kwargs: Any,
) -> None:
    """Run an aea command in a subprocess."""
    result = subprocess.run(  # pylint: disable=subprocess-run-check # nosec
        args=[sys.executable, "-m", "aea.cli", *args],
        cwd=cwd,
        stdout=stdout,
        stderr=stderr,
        **kwargs,
    )
    if result.returncode != 0:
        result_error = result.stderr.decode()
        if ignore_error and ignore_error not in result_error:
            raise RuntimeError(f"Error running: {args} @ {cwd}\n{result_error}")


def _prepare_agent_env(working_dir: Path) -> None:
    """Prepare agent env, add keys, run aea commands."""
    env = json.loads((working_dir / "agent.json").read_text(encoding="utf-8"))

    # TODO: Dynamic port allocation, backport to service builder
    env["CONNECTION_ABCI_CONFIG_HOST"] = "localhost"
    env["CONNECTION_ABCI_CONFIG_PORT"] = "26658"

    for var in env:
        # Fix tendermint connection params
        if var.endswith("MODELS_PARAMS_ARGS_TENDERMINT_COM_URL"):
            env[var] = "http://localhost:8080"

        if var.endswith("MODELS_PARAMS_ARGS_TENDERMINT_URL"):
            env[var] = "http://localhost:26657"

        if var.endswith("MODELS_PARAMS_ARGS_TENDERMINT_P2P_URL"):
            env[var] = "localhost:26656"

        if var.endswith("MODELS_BENCHMARK_TOOL_ARGS_LOG_DIR"):
            benchmarks_dir = working_dir / BENCHMARKS_DIR
            benchmarks_dir.mkdir(exist_ok=True, parents=True)
            env[var] = str(benchmarks_dir.resolve())

    (working_dir / "agent.json").write_text(
        json.dumps(env, indent=2),
        encoding="utf-8",
    )


def setup_agent(working_dir: Path, agent_config: Dict[str, Any]) -> None:
    """Setup locally deployed agent."""
    _prepare_agent_env(working_dir)
    shutil.copy(DEFAULT_AEA_CONFIG_FILE, working_dir)

    # add dependencies
    if (working_dir.parent / VENDOR).exists():
        shutil.copytree(working_dir.parent / VENDOR, working_dir / VENDOR)

    # add private keys
    for ledger_name, path in agent_config.get("private_key_paths", {}).items():
        if Path(path).exists():
            shutil.copy(path, working_dir)
            _run_aea_cmd(
                ["add-key", ledger_name],
                cwd=working_dir,
                ignore_error="already present",
            )
