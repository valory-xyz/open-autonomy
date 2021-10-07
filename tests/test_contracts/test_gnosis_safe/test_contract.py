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

"""Tests for valory/gnosis contract."""

import binascii
import secrets
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pytest
from aea.crypto.registries import crypto_registry
from aea_ledger_ethereum import EthereumCrypto
from web3 import Web3

from tests.conftest import ETHEREUM_KEY_PATH_1, ETHEREUM_KEY_PATH_2, ROOT_DIR
from tests.helpers.contracts import get_register_contract
from tests.test_contracts.base import BaseGanacheContractTest, BaseHardhatContractTest


class BaseContractTest(BaseGanacheContractTest):
    """Base test case for GnosisSafeContract"""

    NB_OWNERS: int = 4
    THRESHOLD: int = 1
    SALT_NONCE: Optional[int] = None
    contract_directory = Path(
        ROOT_DIR, "packages", "valory", "contracts", "gnosis_safe"
    )

    @classmethod
    def setup_class(
        cls,
    ):
        """Setup test."""
        # workaround for the fact that contract dependencies are not possible yet
        directory = Path(
            ROOT_DIR, "packages", "valory", "contracts", "gnosis_safe_proxy_factory"
        )
        _ = get_register_contract(directory)
        super().setup_class()

    @classmethod
    def deployment_kwargs(cls) -> Dict[str, Any]:
        """Get deployment kwargs."""
        return dict(owners=cls.owners(), threshold=int(cls.threshold()))

    @classmethod
    def owners(cls) -> List[str]:
        """Get the owners."""
        return [Web3.toChecksumAddress(t[0]) for t in cls.key_pairs()[: cls.NB_OWNERS]]

    @classmethod
    def deployer(cls) -> Tuple[str, str]:
        """Get the key pair of the deployer."""
        # for simplicity, get the first owner
        return cls.key_pairs()[0]

    @classmethod
    def threshold(
        cls,
    ) -> int:
        """Returns the amount of threshold."""
        return cls.THRESHOLD

    @classmethod
    def get_nonce(cls) -> int:
        """Get the nonce."""
        if cls.SALT_NONCE is not None:
            return cls.SALT_NONCE
        return secrets.SystemRandom().randint(0, 2 ** 256 - 1)


class BaseContractTestHardHatSafeNet(BaseHardhatContractTest):
    """Base test case for GnosisSafeContract"""

    NB_OWNERS: int = 4
    THRESHOLD: int = 1
    SALT_NONCE: Optional[int] = None
    contract_directory = Path(
        ROOT_DIR, "packages", "valory", "contracts", "gnosis_safe"
    )
    sanitize_from_deploy_tx = ["contract_address"]

    @classmethod
    def setup_class(
        cls,
    ):
        """Setup test."""
        directory = Path(
            ROOT_DIR, "packages", "valory", "contracts", "gnosis_safe_proxy_factory"
        )
        _ = get_register_contract(directory)
        super().setup_class()

    @classmethod
    def deployment_kwargs(cls) -> Dict[str, Any]:
        """Get deployment kwargs."""
        return dict(owners=cls.owners(), threshold=int(cls.threshold()))

    @classmethod
    def owners(cls) -> List[str]:
        """Get the owners."""
        return [Web3.toChecksumAddress(t[0]) for t in cls.key_pairs()[: cls.NB_OWNERS]]

    @classmethod
    def deployer(cls) -> Tuple[str, str]:
        """Get the key pair of the deployer."""
        # for simplicity, get the first owner
        return cls.key_pairs()[0]

    @classmethod
    def threshold(
        cls,
    ) -> int:
        """Returns the amount of threshold."""
        return cls.THRESHOLD

    @classmethod
    def get_nonce(cls) -> int:
        """Get the nonce."""
        if cls.SALT_NONCE is not None:
            return cls.SALT_NONCE
        return secrets.SystemRandom().randint(0, 2 ** 256 - 1)


@pytest.mark.skip
class TestDeployTransactionGanache(BaseContractTest):
    """Test."""

    def test_run(self):
        """Run tests."""
        # TOFIX: predeploy gnosis safe factory


class TestDeployTransactionHardhat(BaseContractTestHardHatSafeNet):
    """Test."""

    def test_deployed(self):
        """Run tests."""

        result = self.contract.get_deploy_transaction(
            ledger_api=self.ledger_api,
            deployer_address=str(self.deployer_crypto.address),
            owners=self.owners(),
            threshold=int(self.threshold()),
        )

        assert len(result) == 9
        data = result.pop("data")
        assert len(data) > 0 and data.startswith("0x")
        assert all(
            [
                key in result
                for key in [
                    "value",
                    "from",
                    "gas",
                    "gasPrice",
                    "chainId",
                    "nonce",
                    "to",
                    "contract_address",
                ]
            ]
        ), "Error, found: {}".format(result)

    def test_exceptions(
        self,
    ):
        """Test exceptions."""

        with pytest.raises(ValueError, match="Threshold cannot be bigger than the number of unique owners"):
            # Tests for `ValueError("Threshold cannot be bigger than the number of unique owners")`.`
            self.contract.get_deploy_transaction(
                ledger_api=self.ledger_api,
                deployer_address=str(self.deployer_crypto.address),
                owners=[],
                threshold=1,
            )

        with pytest.raises(ValueError, match="Client does not have any funds"):
            # Tests for  `ValueError("Client does not have any funds")`.
            self.contract.get_deploy_transaction(
                ledger_api=self.ledger_api,
                deployer_address=crypto_registry.make(
                    EthereumCrypto.identifier
                ).address,
                owners=self.owners(),
                threshold=int(self.threshold()),
            )

    def test_non_implemented_methods(
        self,
    ):
        """Test not implemented methods."""
        with pytest.raises(NotImplementedError):
            self.contract.get_raw_transaction(None, None)

        with pytest.raises(NotImplementedError):
            self.contract.get_raw_message(None, None)

        with pytest.raises(NotImplementedError):
            self.contract.get_state(None, None)


class TestRawSafeTransaction(BaseContractTestHardHatSafeNet):
    """Test `get_raw_safe_transaction`"""

    def test_run(self):
        """Run tests."""
        sender = crypto_registry.make(
            EthereumCrypto.identifier, private_key_path=ETHEREUM_KEY_PATH_1
        )
        receiver = crypto_registry.make(
            EthereumCrypto.identifier, private_key_path=ETHEREUM_KEY_PATH_2
        )
        self.deploy(
            owners=self.owners(),
            threshold=self.threshold()
        )
        signatures_by_owners = {}

        self.contract.get_raw_safe_transaction(
            self.ledger_api,
            self.contract_address,
            sender.address,
            self.owners(),
            receiver.address,
            10,
            b"",
            signatures_by_owners
        )


@pytest.mark.skip
class TestRawSafeTransactionHash(BaseContractTest):
    """Test `get_raw_safe_transaction_hash` method."""

    def test_run(self):
        """Run tests."""
        receiver = crypto_registry.make(
            EthereumCrypto.identifier, private_key_path=ETHEREUM_KEY_PATH_1
        )

        self.contract.get_raw_safe_transaction_hash(
            self.ledger_api, self.deployer_crypto.address, receiver.address, 10, b""
        )
