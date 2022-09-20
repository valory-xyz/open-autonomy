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

import platform

from setuptools import find_packages  # type: ignore
from setuptools import setup  # type: ignore


def _get_docker_dependency() -> str:
    """
    Get the `docker-py` dependency, according to the underlying platform.

    If on Windows, we need to install the cutting-edge package version of `docker` directly from the GitHub repository;
    as the PyPI distribution of `docker` causes the following conflict:

        docker 5.0.3 depends on pywin32==227; sys_platform == "win32"
        open-aea[all] 1.19.0 depends on pywin32==304

    Instead, at commit docker/docker-py@3f0095a, `setup.py` has an extra that forces pywin32>=304.

    :return: the docker version
    """
    return (
        "docker==5.0.3"
        if platform.system() != "Windows"
        else "docker @ git+https://github.com/docker/docker-py.git@3f0095a7c1966c521652314e524ff362c24ff58c"
    )


base_deps = [
    "open-aea[all]>=1.19.0,<2.0.0",
    "pytest==7.0.0",
    "open-aea-ledger-ethereum==1.19.0",
    _get_docker_dependency(),
]

setup(
    name="open-aea-test-autonomy",
    version="0.3.0",
    author="Valory AG",
    license="Apache-2.0",
    description="Plugin containing test tools for open-autonomy packages.",
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
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Communications",
        "Topic :: Internet",
        "Topic :: Software Development",
    ],
)
