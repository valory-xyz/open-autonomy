# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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

"""Base test."""

import itertools
from pathlib import Path
from typing import List

import pytest
from aea.components.base import load_aea_package
from aea.configurations.base import PACKAGE_TYPE_TO_CONFIG_CLASS
from aea.configurations.constants import PACKAGES, PACKAGE_TYPE_TO_CONFIG_FILE
from aea.configurations.data_types import PackageType
from aea.configurations.loader import ConfigLoader
from aea.helpers.io import open_file

import autonomy

from tests.conftest import ROOT_DIR


def get_test_files(package_type: PackageType) -> List[Path]:
    """Returns the list of components to be tested."""
    return list(
        (ROOT_DIR / PACKAGES).glob(
            f"*/{package_type.to_plural()}/*/{PACKAGE_TYPE_TO_CONFIG_FILE[package_type.value]}"
        )
    )


def test_version() -> None:
    """Test the version."""
    assert autonomy.__version__ == "0.2.1"


@pytest.mark.parametrize(
    "component_type,config_file_path",
    itertools.chain.from_iterable(
        [
            itertools.zip_longest([], files, fillvalue=component_type)
            for files, component_type in [
                (get_test_files(PackageType.PROTOCOL), PackageType.PROTOCOL),
                (get_test_files(PackageType.CONTRACT), PackageType.CONTRACT),
                (get_test_files(PackageType.CONNECTION), PackageType.CONNECTION),
                (get_test_files(PackageType.SKILL), PackageType.SKILL),
            ]
        ]
    ),
)
def test_load_all_packages(component_type: PackageType, config_file_path: str) -> None:
    """Load all AEA component packages."""

    configuration_loader = ConfigLoader.from_configuration_type(
        component_type, PACKAGE_TYPE_TO_CONFIG_CLASS
    )
    with open_file(config_file_path) as fp:
        configuration_object = configuration_loader.load(fp)
        directory = Path(config_file_path).parent
        configuration_object.directory = directory
        load_aea_package(configuration_object)
