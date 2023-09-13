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

"""Test for contract module."""

from pathlib import Path

from aea_test_autonomy.base_test_classes.contracts import BaseRegistriesContractsTest
from aea_test_autonomy.docker.base import skip_docker_tests
from aea_test_autonomy.docker.registries import COMPONENT_REGISTRY

from packages.valory.contracts.component_registry.contract import (
    ComponentRegistryContract,
)


PACKAGE_DIR = Path(__file__).parent.parent


@skip_docker_tests
class TestComponentRegistry(BaseRegistriesContractsTest):
    """Test component registry."""

    contract: ComponentRegistryContract
    contract_address = COMPONENT_REGISTRY
    contract_directory = PACKAGE_DIR

    def test_get_token_uri(self) -> None:
        """Test get token URI method."""

        token_uri = self.contract.get_token_uri(
            ledger_api=self.ledger_api,
            contract_address=self.contract_address,
            token_id=1,
        )

        assert (
            token_uri
            == "https://gateway.autonolas.tech/ipfs/f01701220f6da10e4468f23f9a435c6bbd3f292271823991e637a23ec8a040b2502169275"  # nosec
        )
