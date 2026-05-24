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

"""Test if constants are valid."""

from pathlib import Path
from typing import Dict

from aea.cli.packages import get_package_manager
from aea.configurations.data_types import PackageId, PackageType, PublicId

from autonomy.constants import ABSTRACT_ROUND_ABCI_SKILL_WITH_HASH

from tests.conftest import ROOT_DIR


def get_hash(key: str) -> Dict[str, str]:
    """Get packages."""
    data = get_package_manager(Path(ROOT_DIR, "packages")).json
    if "dev" in data:
        return data["dev"][key]
    return data[key]


def test_abstract_round_abci_skill_hash() -> None:
    """Test abstract_round_abci skill public_id constants"""

    public_id = PublicId.from_str(ABSTRACT_ROUND_ABCI_SKILL_WITH_HASH)
    package_id = PackageId(PackageType.SKILL, public_id)

    assert public_id.hash == get_hash(package_id.to_uri_path)
