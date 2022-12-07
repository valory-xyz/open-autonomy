# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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

"""Conftest module for Pytest."""
import inspect
import os
import platform
import subprocess  # nosec
from pathlib import Path
from typing import Optional

import pytest


CUR_PATH = os.path.dirname(inspect.getfile(inspect.currentframe()))  # type: ignore
ROOT_DIR = Path(CUR_PATH, "..").resolve().absolute()

skip_docker_tests = pytest.mark.skipif(
    platform.system() != "Linux",
    reason="Docker daemon is not available in Windows and macOS CI containers.",
)


def get_latest_git_tag() -> str:
    """Get the latest git tag"""
    res = subprocess.run(  # nosec
        [
            "git",
            "tag",
            "--sort=-committerdate",
        ],  # sort by commit date in descending order
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )

    stdout = res.stdout.decode("utf-8")
    latest, *_ = stdout.split("\n")
    return latest.strip()


def get_file_from_tag(file_path: str, latest_tag: Optional[str] = None) -> str:
    """Get a specific file version from the commit history given a tag/commit"""
    latest_tag = latest_tag or get_latest_git_tag()
    res = subprocess.run(  # nosec
        ["git", "show", f"{latest_tag}:{file_path}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return res.stdout.decode("utf-8")
