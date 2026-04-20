#!/usr/bin/env python3
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

import os
import re
from typing import Dict


PACKAGE_NAME = "autonomy"
here = os.path.abspath(os.path.dirname(__file__))


def get_all_extras() -> Dict:
    # `click`, `pytest`, `coverage` are pulled transitively via
    # `open-aea[all]` (which implies its own `[cli]` extra), so we only
    # need to declare the IPFS CLI plugin here.
    cli_deps = [
        "open-aea-cli-ipfs==2.2.1",
    ]

    chain_deps = [
        "open-aea-ledger-ethereum==2.2.1",
    ]

    docker_deps = [
        "docker==7.1.0",
    ]

    hwi_deps = [
        "open-aea-ledger-ethereum-hwi==2.2.1",
    ]

    extras = {
        "cli": cli_deps,
        "chain": chain_deps,
        "docker": docker_deps,
        "hwi": hwi_deps,
    }

    # [all] intentionally excludes [hwi] and [docker]:
    # * HWI's transitive deps (hidapi, Pillow via ledgerwallet) have
    #   no armv7 wheels, breaking multi-platform Docker builds.
    # * [docker] is only needed for docker-compose-based deployments;
    #   users deploying to Kubernetes / localhost don't need it.
    # Install them explicitly: `pip install open-autonomy[hwi,docker]`.
    _opt_out = {"hwi", "docker"}
    extras["all"] = list(
        set(dep for k, e in extras.items() for dep in e if k not in _opt_out)
    )
    return extras


all_extras = get_all_extras()


base_deps = [
    "open-aea[all]==2.2.1",
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
    from setuptools import find_packages, setup

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
                "data/contracts/*",
                "data/contracts/registries_manager/*",
                "data/contracts/registries_manager/build/*",
                "data/contracts/component_registry/*",
                "data/contracts/component_registry/build/*",
                "data/contracts/service_registry/*",
                "data/contracts/service_registry/build/*",
                "data/contracts/service_registry/tests/*",
                "data/contracts/agent_registry/*",
                "data/contracts/agent_registry/build/*",
                "data/contracts/service_manager/*",
                "data/contracts/service_manager/build/*",
                "test_tools/data/*",
            ],
            "packages": ["packages/valory/contracts/service_registry/*"],
        },
        packages=find_packages(include=["autonomy*", "packages*"]),
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
        python_requires=">=3.10",
        keywords="autonomy open-autonomy aea open-aea autonomous-economic-agents agent-framework multi-agent-systems multi-agent cryptocurrency cryptocurrencies dezentralized dezentralized-network",
        project_urls={
            "Bug Reports": "https://github.com/valory-xyz/open-autonomy/issues",
            "Source": "https://github.com/valory/open-autonomy",
        },
    )
