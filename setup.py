#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021 Valory AG
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

import os
import platform
import re
from typing import Dict

from setuptools import find_packages, setup  # type: ignore


PACKAGE_NAME = "autonomy"
here = os.path.abspath(os.path.dirname(__file__))


def get_all_extras() -> Dict:

    cli_deps = [
        "click==8.0.2",
        "open-aea-cli-ipfs>=1.19.0,<2.0.0",
    ]

    extras = {
        "cli": cli_deps,
    }

    # add "all" extras
    extras["all"] = list(set(dep for e in extras.values() for dep in e))
    return extras


all_extras = get_all_extras()


def _get_docker_dependency() -> str:
    """
    Get the `docker-py` dependency, according to the underlying platform.

    If on Windows, we need to install the cutting-edge package version of `docker` directly from the GitHub repository;
    as the PyPI distribution of `docker` causes the following conflict:

        docker 5.0.3 depends on pywin32==227; sys_platform == "win32"
        open-aea[all] 1.19.0 depends on pywin32==304

    Instead, at commit docker/docker-py@3f0095a, `setup.py` has an extra that forces pywin32>=304.
    """
    return (
        "docker==5.0.3"
        if platform.system() != "Windows"
        else "docker @ git+https://github.com/docker/docker-py.git@3f0095a7c1966c521652314e524ff362c24ff58c"
    )


base_deps = [
    "Flask>=2.0.2,<3.0.0",
    "open-aea[all]>=1.19.0,<2.0.0",
    "pandas<1.4,>=1.3.4",
    "watchdog >=2.1.6",
    "pytest==7.0.0",
    "open-aea-ledger-ethereum==1.19.0",
    "docker-compose==1.29.2",
    "werkzeug==2.0.3",
    _get_docker_dependency(),
]
base_deps.extend(all_extras["cli"])

here = os.path.abspath(os.path.dirname(__file__))
about: Dict[str, str] = {}
with open(os.path.join(here, PACKAGE_NAME, "__version__.py"), "r") as f:
    exec(f.read(), about)


def parse_readme():
    with open("README.md", "r") as f:
        readme = f.read()

    # replace relative links of images
    raw_url_root = "https://raw.githubusercontent.com/valory-xyz/open-autonomy/main/"
    replacement = raw_url_root + r"\g<0>"
    readme = re.sub(r"(?<=<img src=\")(/.*)(?=\")", replacement, readme, re.DOTALL)
    return "\n".join([readme])


if __name__ == "__main__":
    setup(
        name=about["__title__"],
        description=about["__description__"],
        version=about["__version__"],
        author=about["__author__"],
        url=about["__url__"],
        long_description=parse_readme(),
        long_description_content_type="text/markdown",
        package_data={
            "autonomy": [
                "py.typed",
                "data/*",
                "data/Dockerfiles/agent/*",
                "data/Dockerfiles/dev/*",
                "data/Dockerfiles/hardhat/*",
                "data/Dockerfiles/tendermint/*",
                "test_tools/data/*",
            ]
        },
        packages=find_packages(include=["autonomy*"]),
        classifiers=[
            "Environment :: Console",
            "Environment :: Web Environment",
            "Development Status :: 2 - Pre-Alpha",
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
            "Topic :: Scientific/Engineering",
            "Topic :: Software Development",
            "Topic :: System",
        ],
        install_requires=base_deps,
        tests_require=["tox"],
        extras_require=all_extras,
        entry_points={"console_scripts": ["autonomy=autonomy.cli:cli"]},
        zip_safe=False,
        include_package_data=True,
        license=about["__license__"],
        python_requires=">=3.7",
        keywords="autonomy open-autonomy aea open-aea autonomous-economic-agents agent-framework multi-agent-systems multi-agent cryptocurrency cryptocurrencies dezentralized dezentralized-network",
        project_urls={
            "Bug Reports": "https://github.com/valory-xyz/open-autonomy/issues",
            "Source": "https://github.com/valory/open-autonomy",
        },
    )
