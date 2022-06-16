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

"""Tests for valory/gnosis contract."""

import binascii
import secrets
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, cast
from unittest import mock

import pytest
from aea.crypto.registries import crypto_registry
from aea_ledger_ethereum import EthereumCrypto
from web3 import Web3
from web3.exceptions import SolidityError
from web3.types import TxData

from packages.valory.contracts.gnosis_safe.contract import (
    GnosisSafeContract,
    SAFE_CONTRACT,
)

from tests.conftest import (
    ETHEREUM_KEY_PATH_1,
    ETHEREUM_KEY_PATH_2,
    ETHEREUM_KEY_PATH_3,
    ROOT_DIR,
)
from tests.helpers.contracts import get_register_contract
from tests.helpers.docker.base import skip_docker_tests
from tests.test_contracts.base import (
    BaseGanacheContractTest,
    BaseHardhatGnosisContractTest,
)


DEFAULT_GAS = 1000000
DEFAULT_MAX_FEE_PER_GAS = 10 ** 15
DEFAULT_MAX_PRIORITY_FEE_PER_GAS = 10 ** 15


class BaseContractTest(BaseGanacheContractTest):
    """Base test case for GnosisSafeContract"""

    NB_OWNERS: int = 4
    THRESHOLD: int = 1
    SALT_NONCE: Optional[int] = None
    contract_directory = Path(
        ROOT_DIR, "packages", "valory", "contracts", "gnosis_safe"
    )
    contract: GnosisSafeContract

    @classmethod
    def setup_class(
        cls,
    ) -> None:
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
        return dict(
            owners=cls.owners(),
            threshold=int(cls.threshold()),
            gas=DEFAULT_GAS,
        )

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


class BaseContractTestHardHatSafeNet(BaseHardhatGnosisContractTest):
    """Base test case for GnosisSafeContract"""

    NB_OWNERS: int = 4
    THRESHOLD: int = 1
    SALT_NONCE: Optional[int] = None
    contract_directory = Path(
        ROOT_DIR, "packages", "valory", "contracts", "gnosis_safe"
    )
    sanitize_from_deploy_tx = ["contract_address"]
    contract: GnosisSafeContract

    @classmethod
    def setup_class(
        cls,
    ) -> None:
        """Setup test."""
        directory = Path(
            ROOT_DIR, "packages", "valory", "contracts", "gnosis_safe_proxy_factory"
        )
        _ = get_register_contract(directory)
        super().setup_class()

    @classmethod
    def deployment_kwargs(cls) -> Dict[str, Any]:
        """Get deployment kwargs."""
        return dict(
            owners=cls.owners(),
            threshold=int(cls.threshold()),
            gas=DEFAULT_GAS,
        )

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


@skip_docker_tests
class TestDeployTransactionHardhat(BaseContractTestHardHatSafeNet):
    """Test."""

    def test_deployed(self) -> None:
        """Run tests."""

        result = self.contract.get_deploy_transaction(
            ledger_api=self.ledger_api,
            deployer_address=str(self.deployer_crypto.address),
            owners=self.owners(),
            threshold=int(self.threshold()),
            gas=DEFAULT_GAS,
        )
        assert type(result) == dict
        assert len(result) == 10
        data = result.pop("data")
        assert type(data) == str
        assert len(data) > 0 and data.startswith("0x")
        assert all(
            [
                key in result
                for key in [
                    "value",
                    "from",
                    "gas",
                    "maxFeePerGas",
                    "maxPriorityFeePerGas",
                    "chainId",
                    "nonce",
                    "to",
                    "contract_address",
                ]
            ]
        ), "Error, found: {}".format(result)

    def test_exceptions(
        self,
    ) -> None:
        """Test exceptions."""

        with pytest.raises(
            ValueError,
            match="Threshold cannot be bigger than the number of unique owners",
        ):
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
    ) -> None:
        """Test not implemented methods."""
        with pytest.raises(NotImplementedError):
            self.contract.get_raw_transaction(self.ledger_api, "")

        with pytest.raises(NotImplementedError):
            self.contract.get_raw_message(self.ledger_api, "")

        with pytest.raises(NotImplementedError):
            self.contract.get_state(self.ledger_api, "")

    def test_verify(self) -> None:
        """Run verify test."""
        assert self.contract_address is not None
        result = self.contract.verify_contract(
            ledger_api=self.ledger_api,
            contract_address=self.contract_address,
        )
        assert result["verified"], "Contract not verified."

        verified = self.contract.verify_contract(
            ledger_api=self.ledger_api,
            contract_address=SAFE_CONTRACT,
        )["verified"]
        assert not verified, "Not verified"

    def test_get_safe_nonce(self) -> None:
        """Run get_safe_nonce test."""
        safe_nonce = self.contract.get_safe_nonce(
            ledger_api=self.ledger_api,
            contract_address=cast(str, self.contract_address),
        )["safe_nonce"]
        assert safe_nonce == 0

    def test_revert_reason(
        self,
    ) -> None:
        """Test `revert_reason` method."""

        tx = {
            "to": "to",
            "from": "from",
            "value": "value",
            "input": "input",
            "blockNumber": 1,
        }

        def _raise_solidity_error(*args: Any) -> None:
            raise SolidityError("reason")

        with mock.patch.object(
            self.ledger_api.api.eth, "call", new=_raise_solidity_error
        ):
            reason = self.contract.revert_reason(
                self.ledger_api, "contract_address", cast(TxData, tx)
            )
            assert "revert_reason" in reason
            assert reason["revert_reason"] == "SolidityError('reason')"

        with mock.patch.object(self.ledger_api.api.eth, "call"), pytest.raises(
            ValueError, match=f"The given transaction has not been reverted!\ntx: {tx}"
        ):
            self.contract.revert_reason(
                self.ledger_api, "contract_address", cast(TxData, tx)
            )


@skip_docker_tests
class TestRawSafeTransaction(BaseContractTestHardHatSafeNet):
    """Test `get_raw_safe_transaction`"""

    def test_run(self) -> None:
        """Run tests."""
        assert self.contract_address is not None
        value = 0
        data = b""
        sender = crypto_registry.make(
            EthereumCrypto.identifier, private_key_path=ETHEREUM_KEY_PATH_1
        )
        assert sender.address == self.owners()[1]
        receiver = crypto_registry.make(
            EthereumCrypto.identifier, private_key_path=ETHEREUM_KEY_PATH_2
        )
        assert receiver.address == self.owners()[2]
        fourth = crypto_registry.make(
            EthereumCrypto.identifier, private_key_path=ETHEREUM_KEY_PATH_3
        )
        assert fourth.address == self.owners()[3]
        cryptos = [self.deployer_crypto, sender, receiver, fourth]
        tx_hash = self.contract.get_raw_safe_transaction_hash(
            ledger_api=self.ledger_api,
            contract_address=self.contract_address,
            to_address=receiver.address,
            value=value,
            data=data,
        )["tx_hash"]
        b_tx_hash = binascii.unhexlify(cast(str, tx_hash)[2:])
        signatures_by_owners = {
            crypto.address: crypto.sign_message(b_tx_hash, is_deprecated_mode=True)[2:]
            for crypto in cryptos
        }
        assert [key for key in signatures_by_owners.keys()] == self.owners()

        tx = self.contract.get_raw_safe_transaction(
            ledger_api=self.ledger_api,
            contract_address=self.contract_address,
            sender_address=sender.address,
            owners=(self.deployer_crypto.address.lower(),),
            to_address=receiver.address,
            value=value,
            data=data,
            gas_price=DEFAULT_MAX_FEE_PER_GAS,
            signatures_by_owner={
                self.deployer_crypto.address.lower(): signatures_by_owners[
                    self.deployer_crypto.address
                ]
            },
        )

        assert all(
            key
            in [
                "chainId",
                "data",
                "from",
                "gas",
                "gasPrice",
                "nonce",
                "to",
                "value",
            ]
            for key in tx.keys()
        ), "Missing key"

        tx = self.contract.get_raw_safe_transaction(
            ledger_api=self.ledger_api,
            contract_address=self.contract_address,
            sender_address=sender.address,
            owners=(self.deployer_crypto.address.lower(),),
            to_address=receiver.address,
            value=value,
            data=data,
            signatures_by_owner={
                self.deployer_crypto.address.lower(): signatures_by_owners[
                    self.deployer_crypto.address
                ]
            },
        )

        assert all(
            key
            in [
                "chainId",
                "data",
                "from",
                "gas",
                "maxFeePerGas",
                "maxPriorityFeePerGas",
                "nonce",
                "to",
                "value",
            ]
            for key in tx.keys()
        ), "Missing key"

        tx_signed = sender.sign_transaction(tx)
        tx_hash = self.ledger_api.send_signed_transaction(tx_signed)
        assert tx_hash is not None, "Tx hash not none"

        verified = self.contract.verify_tx(
            ledger_api=self.ledger_api,
            contract_address=self.contract_address,
            tx_hash=tx_hash,
            owners=(self.deployer_crypto.address.lower(),),
            to_address=receiver.address,
            value=value,
            data=data,
            signatures_by_owner={
                self.deployer_crypto.address.lower(): signatures_by_owners[
                    self.deployer_crypto.address
                ]
            },
        )
        assert verified["verified"], f"Not verified: {verified}"

    def test_verify_negative(self) -> None:
        """Test verify negative."""
        assert self.contract_address is not None
        verified = self.contract.verify_tx(
            ledger_api=self.ledger_api,
            contract_address=self.contract_address,
            tx_hash="0xfc6d7c491688840e79ed7d8f0fc73494be305250f0d5f62d04c41bc4467e8603",
            owners=("",),
            to_address=crypto_registry.make(
                EthereumCrypto.identifier, private_key_path=ETHEREUM_KEY_PATH_1
            ).address,
            value=0,
            data=b"",
            signatures_by_owner={},
        )["verified"]
        assert not verified, "Should not be verified"
