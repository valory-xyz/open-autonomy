#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022-2026 Valory AG
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
"""Setup script for the plug-in."""

from pathlib import Path

from setuptools import find_packages  # type: ignore
from setuptools import setup  # type: ignore


def _read_long_description() -> str:
    """Read the plugin README as the PyPI long description."""
    return (Path(__file__).parent / "README.md").read_text(encoding="utf-8")


base_deps = [
    # `open-autonomy[all]` supplies everything the plugin's direct
    # imports resolve to, EXCEPT `docker` which is declared below:
    #   * `pytest`, `aea.*` — via `open-aea[all]`
    #   * `aea_ledger_ethereum`, `web3`, `eth_account` — via the
    #     `[all]` extra's `open-aea-ledger-ethereum`
    # NOTE: `docker` is pinned directly (rather than inherited via
    # `open-autonomy[docker]`) because the `[docker]` extra was
    # introduced in 0.21.20 — relying on it creates a resolver loop
    # where pip walks back to pre-0.21.20 versions missing the extra
    # whenever the target open-autonomy version is unreleased.
    "open-autonomy[all]>=0.21.0,<0.22.0",
    "docker==7.1.0",
]

setup(
    name="open-aea-test-autonomy",
    version="0.21.20",
    author="Valory AG",
    license="Apache-2.0",
    description="Plugin containing test tools for open-autonomy packages.",
    long_description=_read_long_description(),
    long_description_content_type="text/markdown",
    packages=find_packages(
        where=".", include=["aea_test_autonomy", "aea_test_autonomy.*"]
    ),
    package_data={
        "aea_test_autonomy": [
            "py.typed",
            "data/*",
        ]
    },
    entry_points={},
    install_requires=base_deps,
    classifiers=[
        "Environment :: Console",
        "Environment :: Web Environment",
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Operating System :: MacOS",
        "Operating System :: Microsoft",
        "Operating System :: Unix",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "Topic :: Communications",
        "Topic :: Internet",
        "Topic :: Software Development",
    ],
)
