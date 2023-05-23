#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023 Valory AG
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

import os
from pathlib import Path
from typing import Dict, List

from setuptools import find_packages  # type: ignore
from setuptools import setup  # type: ignore


try:
    from aea.configurations.data_types import Dependency, PackageType
    from aea.package_manager.base import load_configuration
    from aea.package_manager.v1 import PackageManagerV1
except ImportError as e:
    raise ImportError("open-aea installation not found") from e


def get_package_dependencies() -> List[str]:
    """Returns a list of package dependencies."""
    package_manager = PackageManagerV1.from_dir(
        Path(os.environ.get("PACKAGES_DIR", str(Path.cwd() / "packages")))
    )
    dependencies: Dict[str, Dependency] = {}
    for package in package_manager.iter_dependency_tree():
        if package.package_type == PackageType.SERVICE:
            continue
        _dependencies = load_configuration(
            package_type=package.package_type,
            package_path=package_manager.package_path_from_package_id(
                package_id=package
            ),
        ).dependencies
        dependencies.update(_dependencies)

    return [
        " ".join(package.get_pip_install_args()) for package in dependencies.values()
    ]


package_dependencies = get_package_dependencies()

setup(
    name="open-aea-install-package-dependencies",
    version="0.10.4",
    author="Valory AG",
    license="Apache-2.0",
    description="Plugin to collect and install packages from the local packages repository.",
    long_description="Plugin to collect and install packages from the local packages repository.",
    long_description_content_type="text/markdown",
    packages=find_packages(
        where=".",
        include=[
            "aea_install_package_dependencies",
            "aea_install_package_dependencies.*",
        ],
    ),
    entry_points={},
    install_requires=package_dependencies,
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
