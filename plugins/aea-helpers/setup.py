#!/usr/bin/env python3
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
"""Setup script for the plug-in."""

from setuptools import find_packages  # type: ignore
from setuptools import setup  # type: ignore

base_deps = [
    "open-autonomy>=0.21.0,<0.22.0",
    "click>=8.1.0,<9",
    "requests>=2.28.0,<3",
    "toml>=0.10,<1",
    "python-dotenv>=0.14.5,<2",
    "PyYAML>=6.0,<7",
]

setup(
    name="aea-helpers",
    version="0.21.16rc2",
    author="Valory AG",
    license="Apache-2.0",
    description="CLI helpers for CI and dependency management in AEA-based projects.",
    long_description="CLI helpers for CI and dependency management in AEA-based projects.",
    long_description_content_type="text/markdown",
    packages=find_packages(where=".", include=["aea_helpers", "aea_helpers.*"]),
    package_data={
        "aea_helpers": [
            "py.typed",
            "scripts/*.sh",
        ]
    },
    entry_points={
        "console_scripts": [
            "aea-helpers=aea_helpers.cli:cli",
        ],
    },
    install_requires=base_deps,
    classifiers=[
        "Environment :: Console",
        "Development Status :: 3 - Alpha",
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
        "Topic :: Software Development",
    ],
)
