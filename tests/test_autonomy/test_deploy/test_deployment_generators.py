# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022-2023 Valory AG
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

"""Test deployment generators."""

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Optional, cast
from unittest import mock

import pytest
from aea.configurations.data_types import PublicId
from aea.helpers.base import cd
from aea_test_autonomy.docker.base import skip_docker_tests

from autonomy.configurations.base import Service
from autonomy.deploy.base import BaseDeploymentGenerator, ServiceBuilder
from autonomy.deploy.generators.docker_compose.base import DockerComposeGenerator
from autonomy.deploy.generators.kubernetes.base import KubernetesGenerator

from tests.conftest import ROOT_DIR


AGENT = PublicId(
    author="valory",
    name="oracle",
    package_hash="bafybeibygdzriewuhsabsab4vait3pdyoc5nswupijtysk4zpntilloaji",
)
KEYS_PATH = ROOT_DIR / "deployments" / "keys" / "hardhat_keys.json"


def get_dummy_service() -> Service:
    """Create a dummy service config."""

    return Service(name="dummy", author="default", agent=AGENT)


@skip_docker_tests
@pytest.mark.parametrize("generator_cls", (DockerComposeGenerator, KubernetesGenerator))
@pytest.mark.parametrize("image_version", [None, "0.1.0"])
@pytest.mark.parametrize("use_hardhat", [False, True])
@pytest.mark.parametrize("use_acn", [False, True])
def test_versioning(
    generator_cls: Any, image_version: Optional[str], use_hardhat: bool, use_acn: bool
) -> None:
    """Test versioning in builds."""

    generate_kwargs = locals()
    generate_kwargs.pop("generator_cls")

    with TemporaryDirectory() as temp_dir:
        with cd(temp_dir), mock.patch(
            "autonomy.deploy.base.load_service_config",
            return_value=get_dummy_service(),
        ):
            service_builder = ServiceBuilder.from_dir(
                path=Path.cwd(),
                keys_file=KEYS_PATH,
                number_of_agents=1,
            )

            deployment_generator = cast(
                BaseDeploymentGenerator,
                generator_cls(
                    service_builder=service_builder,
                    build_dir=Path.cwd(),
                ),
            )

            deployment_generator.generate(**generate_kwargs)
            expected = f"valory/oar-oracle:{image_version or AGENT.hash}"
            assert expected in deployment_generator.output
