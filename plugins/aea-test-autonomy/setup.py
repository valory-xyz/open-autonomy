#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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
    "open-aea[all]>=1.56.0,<2.0.0",
    "pytest==7.2.1",
    "open-aea-ledger-ethereum>=1.56.0,<2.0.0",
    "docker==6.1.2",
]

setup(
    name="open-aea-test-autonomy",
    version="0.16.0",
    author="Valory AG",
    license="Apache-2.0",
    description="Plugin containing test tools for open-autonomy packages.",
    long_description="Plugin containing test tools for open-autonomy packages.",
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
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Operating System :: MacOS",
        "Operating System :: Microsoft",
        "Operating System :: Unix",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Communications",
        "Topic :: Internet",
        "Topic :: Software Development",
    ],
)
