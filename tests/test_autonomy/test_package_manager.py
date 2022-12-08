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

"""Test package manager API."""


import json
import tempfile
from pathlib import Path
from unittest import mock

from aea.configurations.data_types import PackageId, PackageType, PublicId
from aea.package_manager.base import DepedencyMismatchErrors
from aea.test_tools.test_cases import BaseAEATestCase

from autonomy.cli.packages import (
    PackageManagerV0,
    PackageManagerV1,
    get_package_manager,
)
from autonomy.configurations.base import Service
from autonomy.configurations.constants import DEFAULT_SERVICE_CONFIG_FILE


DUMMY_HASH = "bafybei0000000000000000000000000000000000000000000000000000"
SERVICE_ID = PackageId(
    package_type=PackageType.SERVICE,
    public_id=PublicId(author="valory", name="service"),
)
SERVICE_CONFIG = {
    "name": "dummy_service",
    "author": "valory",
    "version": "0.1.0",
    "description": "A dummy service config file.",
    "aea_version": ">=1.0.0, <2.0.0",
    "license": "Apache-2.0",
    "fingerprint": {
        "README.md": "bafybeiapubcoersqnsnh3acia5hd7otzt7kjxekr6gkbrlumv6tkajl6jm",
    },
    "fingerprint_ignore_patterns": "[]",
    "agent": f"valory/hello_world:0.1.0:{DUMMY_HASH}",
    "number_of_agents": "1",
}


class TestPackageManagerServicePatch(BaseAEATestCase):
    """Test package manager V0 service patch."""

    def test_update_dependencies(self) -> None:
        """Test update dependencies."""

        pm = PackageManagerV1(path=self.packages_dir_path)

        updated_config = SERVICE_CONFIG.copy()
        updated_config[
            "agent"
        ] = "valory/hello_world:0.1.0:bafybei0000000000000000000000000000000000000000000000000001"

        with mock.patch(
            "autonomy.cli.packages.load_yaml",
            return_value=[updated_config, None],
        ), mock.patch(
            "autonomy.cli.packages.dump_yaml"
        ) as dump_yaml_patch, mock.patch.object(
            pm, "get_package_hash", return_value=DUMMY_HASH
        ):
            pm.update_dependencies(package_id=SERVICE_ID)
            dump_yaml_patch.assert_called_with(
                file_path=(
                    pm.package_path_from_package_id(package_id=SERVICE_ID)
                    / DEFAULT_SERVICE_CONFIG_FILE
                ),
                data=SERVICE_CONFIG,
                extra_data=None,
            )

    def test_check_dependencies(
        self,
    ) -> None:
        """Test check dependencies method."""

        pm = PackageManagerV1(path=self.packages_dir_path)
        service_config = SERVICE_CONFIG.copy()
        service_config["license_"] = service_config.pop("license")

        with mock.patch.object(pm, "get_package_hash", return_value=DUMMY_HASH):
            errors = pm.check_dependencies(
                configuration=Service(**service_config),  # type: ignore
            )

            assert len(errors) == 0

    def test_check_dependencies_failure(
        self,
    ) -> None:
        """Test check dependencies method."""

        pm = PackageManagerV1(path=self.packages_dir_path)
        service_config = SERVICE_CONFIG.copy()
        service_config["license_"] = service_config.pop("license")
        with mock.patch.object(pm, "get_package_hash", return_value=None):
            errors = pm.check_dependencies(
                configuration=Service(**service_config),  # type: ignore
            )

            assert len(errors) == 1

            ((_, error),) = errors
            assert error == DepedencyMismatchErrors.HASH_NOT_FOUND

        service_config[
            "agent"
        ] = "valory/hello_world:0.1.0:bafybei0000000000000000000000000000000000000000000000000001"

        with mock.patch.object(pm, "get_package_hash", return_value=DUMMY_HASH):
            errors = pm.check_dependencies(
                configuration=Service(**service_config),  # type: ignore
            )

            assert len(errors) == 1

            ((_, error),) = errors
            assert error == DepedencyMismatchErrors.HASH_DOES_NOT_MATCH


def test_get_package_manager() -> None:
    """Test `get_package_manager` method."""

    with tempfile.TemporaryDirectory() as temp_dir:
        packages_dir = Path(temp_dir)
        (packages_dir / "packages.json").write_text(
            json.dumps({"service/valory/service/0.1.0": DUMMY_HASH})
        )

        pm_v0 = get_package_manager(packages_dir=packages_dir)
        assert isinstance(pm_v0, PackageManagerV0)

    with tempfile.TemporaryDirectory() as temp_dir:
        packages_dir = Path(temp_dir)
        (packages_dir / "packages.json").write_text(
            json.dumps(
                {"dev": {"service/valory/service/0.1.0": DUMMY_HASH}, "third_party": {}}
            )
        )

        pm_v0 = get_package_manager(packages_dir=packages_dir)
        assert isinstance(pm_v0, PackageManagerV1)
