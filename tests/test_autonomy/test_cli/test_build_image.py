# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022-2024 Valory AG
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

"""Test build image."""

import os
from pathlib import Path
from random import choices
from string import ascii_letters
from typing import Tuple

import docker
from aea.cli.utils.config import get_default_author_from_cli_config
from aea.configurations.data_types import PackageId, PackageType, PublicId
from aea.configurations.loader import ConfigLoader
from aea.helpers.io import open_file

from autonomy.configurations.base import Service
from autonomy.constants import DEFAULT_DOCKER_IMAGE_AUTHOR

from tests.conftest import skip_docker_tests
from tests.test_autonomy.base import get_dummy_service_config
from tests.test_autonomy.test_cli.base import BaseCliTest


@skip_docker_tests
class TestBuildImage(BaseCliTest):
    """Test build image command."""

    cli_options: Tuple[str, ...] = ("build-image",)
    docker_api: docker.APIClient
    build_dir: Path
    package_hash: str
    package_id: PackageId

    def setup(self) -> None:
        """Setup class."""
        super().setup()

        self.docker_api = docker.APIClient()
        self.package_id = PackageId(
            package_type=PackageType.AGENT,
            public_id=PublicId(author="valory", name="test_abci", version="0.1.0"),
        )

        # TODO: Revert after release
        package_hash = "bafybeibe6kgnwkuhcydk5gr3wvsybdlc7gfuzt2ia24czudsvxlbmdlrwe"
        self.package_id = self.package_id.with_hash(package_hash=package_hash)

        os.chdir(self.t)

        service_config, *_ = get_dummy_service_config()
        service_config["agent"] = str(self.package_id.public_id)
        service_file = self.t / "service.yaml"

        with open_file(service_file, "w+") as fp:
            service = Service.from_json(service_config)
            ConfigLoader(Service.schema, Service).dump(service, fp)

    def test_build_prod(
        self,
    ) -> None:
        """Test prod build."""

        result = self.run_cli()

        assert result.exit_code == 0, result.output
        assert (
            len(
                self.docker_api.images(
                    name=f"{get_default_author_from_cli_config() or DEFAULT_DOCKER_IMAGE_AUTHOR}/oar-{self.package_id.name}:{self.package_id.package_hash}"
                )
            )
            == 1
        )

    def test_build_version(
        self,
    ) -> None:
        """Test prod build."""

        test_version = "".join(choices(ascii_letters, k=6))  # nosec
        result = self.run_cli(("--version", test_version))

        assert result.exit_code == 0, result.output
        assert (
            len(
                self.docker_api.images(
                    name=f"{get_default_author_from_cli_config() or DEFAULT_DOCKER_IMAGE_AUTHOR}/oar-{self.package_id.name}:{test_version}"
                )
            )
            == 1
        )

    @skip_docker_tests
    def test_image_author_flag(self) -> None:
        """Test image_author flag."""
        test_version = "".join(choices(ascii_letters, k=6))  # nosec
        default_author = (
            get_default_author_from_cli_config() or DEFAULT_DOCKER_IMAGE_AUTHOR
        )
        result = self.run_cli(
            (
                "--version",
                test_version,
            )
        )
        assert result.exit_code == 0, result.output
        assert self.docker_api.images(
            name=f"{default_author}/oar-{self.package_id.name}:{test_version}"
        )

        test_version = "".join(choices(ascii_letters, k=6))  # nosec
        image_author = "test_author"
        result = self.run_cli(
            (
                "--version",
                test_version,
                "--image-author",
                image_author,
            )
        )
        assert result.exit_code == 0, result.output
        assert self.docker_api.images(
            name=f"{image_author}/oar-{self.package_id.name}:{test_version}"
        )

        test_version = "".join(choices(ascii_letters, k=6))  # nosec
        image_author = "0bad*author"
        result = self.run_cli(
            (
                "--version",
                test_version,
                "--image-author",
                image_author,
            )
        )
        assert result.exit_code == 1, result.output
        assert f"Value {image_author} does not match the regular expression " in str(
            result
        )


class TestBuildImageFailures(BaseCliTest):
    """Test build image command."""

    cli_options: Tuple[str, ...] = ("build-image",)
    docker_api: docker.APIClient
    build_dir: Path
    package_hash: str

    def test_service_file_missing(
        self,
    ) -> None:
        """Test prod build."""

        result = self.run_cli()

        assert result.exit_code == 1, result.output
        assert "No such file or directory: " in result.output
        assert "service.yaml" in result.output

    @skip_docker_tests
    def test_image_build_fail(self) -> None:
        """Test prod build."""

        result = self.run_cli(
            commands=(
                "valory/agent:bafybeihyasfforsfualp6jnhh2jj7nreqmws2ygyfnh4p3idmfkm5yxu11",
            )
        )

        assert result.exit_code == 1, result.output
        assert "Error occured while downloading agent" in result.output
