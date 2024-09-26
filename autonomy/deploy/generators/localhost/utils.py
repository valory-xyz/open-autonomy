# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2024 Valory AG
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
import os
import platform
import shutil
import subprocess  # nosec
import sys
from pathlib import Path


LOCAL_TENDERMINT_VERSION = "0.34.19"


def check_tendermint_version() -> Path:
    """Check tendermint version."""
    tendermint_executable = Path(str(shutil.which("tendermint")))
    if platform.system() == "Windows":
        tendermint_executable = Path(os.path.dirname(sys.executable)) / "tendermint.exe"

    if (  # check tendermint version
        tendermint_executable is None
        or subprocess.check_output([tendermint_executable, "version"])  # nosec
        .decode("utf-8")
        .strip()
        != LOCAL_TENDERMINT_VERSION
    ):
        raise FileNotFoundError(
            f"Please install tendermint version {LOCAL_TENDERMINT_VERSION} "
            f"or build and run via docker by using the --docker flag."
        )

    return tendermint_executable
