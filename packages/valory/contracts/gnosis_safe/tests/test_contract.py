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

"""Tests for valory/gnosis contract."""

import binascii
import secrets
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, cast
from unittest import mock

import pytest
from aea.common import JSONLike
from aea.crypto.registries import crypto_registry
from aea_ledger_ethereum import EthereumApi, EthereumCrypto
from aea_test_autonomy.base_test_classes.contracts import (
    BaseGanacheContractTest,
    BaseHardhatGnosisContractTest,
)
from aea_test_autonomy.configurations import (
    ETHEREUM_KEY_PATH_1,
    ETHEREUM_KEY_PATH_2,
    ETHEREUM_KEY_PATH_3,
    KEY_PAIRS,
)
from aea_test_autonomy.docker.base import skip_docker_tests
from aea_test_autonomy.helpers.contracts import get_register_contract
from hexbytes import HexBytes
from web3 import Web3
from web3.datastructures import AttributeDict
from web3.eth import Eth
from web3.exceptions import ContractLogicError
from web3.types import TxData

from packages.valory.contracts.gnosis_safe.contract import (
    GnosisSafeContract,
    SAFE_CONTRACT,
)
from packages.valory.contracts.gnosis_safe_proxy_factory.tests.test_contract import (
    PACKAGE_DIR as PROXY_DIR,
)


PACKAGE_DIR = Path(__file__).parent.parent

DEFAULT_GAS = 1000000
DEFAULT_MAX_FEE_PER_GAS = 10**15
DEFAULT_MAX_PRIORITY_FEE_PER_GAS = 10**15
EXPECTED_TX_KEYS = {
    "chainId",
    "data",
    "from",
    "gas",
    "maxFeePerGas",
    "maxPriorityFeePerGas",
    "nonce",
    "to",
    "value",
}


class BaseContractTest(BaseGanacheContractTest):
    """Base test case for GnosisSafeContract"""

    NB_OWNERS: int = 4
    THRESHOLD: int = 1
    SALT_NONCE: Optional[int] = None
    contract_directory = PACKAGE_DIR
    contract: GnosisSafeContract

    @classmethod
    def setup_class(
        cls,
    ) -> None:
        """Setup test."""
        # workaround for the fact that contract dependencies are not possible yet
        _ = get_register_contract(PROXY_DIR)
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
        return [
            Web3.to_checksum_address(t[0]) for t in cls.key_pairs()[: cls.NB_OWNERS]
        ]

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
        return secrets.SystemRandom().randint(0, 2**256 - 1)


class BaseContractTestHardHatSafeNet(BaseHardhatGnosisContractTest):
    """Base test case for GnosisSafeContract"""

    NB_OWNERS: int = 4
    THRESHOLD: int = 1
    SALT_NONCE: Optional[int] = None
    contract_directory = PACKAGE_DIR
    sanitize_from_deploy_tx = ["contract_address"]
    contract: GnosisSafeContract

    @classmethod
    def setup_class(
        cls,
    ) -> None:
        """Setup test."""
        _ = get_register_contract(PROXY_DIR)
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
        return [
            Web3.to_checksum_address(t[0]) for t in cls.key_pairs()[: cls.NB_OWNERS]
        ]

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
        return secrets.SystemRandom().randint(0, 2**256 - 1)

    def _verify_safe_tx(
        self,
        tx_hash: str,
        value: int,
        data: bytes,
        to_address: str,
        signatures_by_owners: Dict,
    ) -> bool:
        """Helper to verify tx."""
        ledger_api = cast(EthereumApi, self.ledger_api)
        contract_address = cast(str, self.contract_address)
        return self.contract.verify_tx(
            ledger_api=ledger_api,
            contract_address=contract_address,
            tx_hash=tx_hash,
            owners=(self.deployer_crypto.address.lower(),),
            to_address=to_address,
            value=value,
            data=data,
            signatures_by_owner={
                self.deployer_crypto.address.lower(): signatures_by_owners[
                    self.deployer_crypto.address
                ]
            },
        )["verified"]

    def _get_raw_safe_tx(
        self,
        sender_address: str,
        value: int,
        data: bytes,
        to_address: str,
        signatures_by_owners: Dict,
    ) -> JSONLike:
        """Helper to prepare a safe tx."""
        ledger_api = cast(EthereumApi, self.ledger_api)
        contract_address = cast(str, self.contract_address)
        tx = self.contract.get_raw_safe_transaction(
            ledger_api=ledger_api,
            contract_address=contract_address,
            sender_address=sender_address,
            owners=(self.deployer_crypto.address.lower(),),
            to_address=to_address,
            value=value,
            data=data,
            signatures_by_owner={
                self.deployer_crypto.address.lower(): signatures_by_owners[
                    self.deployer_crypto.address
                ]
            },
        )
        return tx


@skip_docker_tests
class TestDeployTransactionHardhat(BaseContractTestHardHatSafeNet):
    """Test."""

    ledger_api: EthereumApi

    def test_deployed(self) -> None:
        """Run tests."""
        result = self.contract.get_deploy_transaction(
            ledger_api=self.ledger_api,
            deployer_address=str(self.deployer_crypto.address),
            owners=self.owners(),
            threshold=int(self.threshold()),
            gas=DEFAULT_GAS,
        )
        assert isinstance(result, dict)
        assert len(result) == 10
        data = result.pop("data")
        assert isinstance(data, str)
        assert len(data) > 0 and data.startswith("0x")
        # there is no "data" field on the deploy tx
        # but there is contract_address
        expected_deploy_tx_fields = EXPECTED_TX_KEYS - {"data"}
        expected_deploy_tx_fields.add("contract_address")
        assert all(
            key in result.keys() for key in expected_deploy_tx_fields
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
            # Tests for `ValueError("Client does not have any funds")`.
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

        def _raise_solidity_error(*_: Any) -> None:
            raise ContractLogicError("reason")

        with mock.patch.object(
            self.ledger_api.api.eth, "call", new=_raise_solidity_error
        ):
            reason = self.contract.revert_reason(
                self.ledger_api, "contract_address", cast(TxData, tx)
            )
            assert "revert_reason" in reason
            assert (
                reason["revert_reason"] == "ContractLogicError('reason')"
                or reason["revert_reason"] == "ContractLogicError('reason', None)"
            )

        with mock.patch.object(self.ledger_api.api.eth, "call"), pytest.raises(
            ValueError, match=f"The given transaction has not been reverted!\ntx: {tx}"
        ):
            self.contract.revert_reason(
                self.ledger_api, "contract_address", cast(TxData, tx)
            )

    def test_get_incoming_transfers(self) -> None:
        """Run get_incoming txs."""
        from_block = cast(int, self.ledger_api.api.eth.get_block_number()) + 1
        self.ledger_api.api.eth.send_transaction(
            {
                "to": self.contract_address,
                "from": self.deployer_crypto.address,
                "value": 10,
            }
        )

        res = cast(
            JSONLike,
            self.contract.get_ingoing_transfers(
                ledger_api=self.ledger_api,
                contract_address=cast(str, self.contract_address),
                from_block=hex(from_block),
            ),
        )
        data = cast(List[JSONLike], res["data"])

        time.sleep(1)

        assert len(res) == 1, "one transfer should exist"
        assert data[0]["amount"] == 10, "transfer amount should be 10"
        assert (
            data[0]["sender"] == self.deployer_crypto.address
        ), f"{data[0]['sender']} should be the sender"
        assert data[0]["blockNumber"] is not None, "tx is still pending"
        assert (
            self.ledger_api.api.eth.get_balance(self.contract_address) == 10
        ), "incorrect balance"

        self.ledger_api.api.eth.send_transaction(
            {
                "to": self.contract_address,
                "from": self.deployer_crypto.address,
                "value": 100,
            }
        )
        from_block = cast(int, data[0]["blockNumber"]) + 1

        time.sleep(3)
        res = self.contract.get_ingoing_transfers(
            ledger_api=self.ledger_api,
            contract_address=cast(str, self.contract_address),
            from_block=hex(from_block),
        )
        data = cast(List[JSONLike], res["data"])

        assert len(res) == 1, "one transfer should exist"
        assert data[0]["amount"] == 100, "transfer amount should be 100"
        assert (
            data[0]["sender"] == self.deployer_crypto.address
        ), f"{data[0]['sender']} should be the sender"
        assert data[0]["blockNumber"] is not None, "tx is still pending"
        assert (
            self.ledger_api.api.eth.get_balance(self.contract_address) == 110
        ), "incorrect balance"

    def test_get_zero_transfer_events(self) -> None:
        """Test get_zero_transfer_events."""
        # check that the safe has no zero transfers
        res = cast(
            JSONLike,
            self.contract.get_zero_transfer_events(
                ledger_api=self.ledger_api,
                contract_address=cast(str, self.contract_address),
                sender_address=self.deployer_crypto.address,
            ),
        )
        data = cast(List[JSONLike], res["data"])
        assert len(data) == 0, "no zero transfers should be in the safe"

        # make a zero transfer
        self.ledger_api.api.eth.send_transaction(
            {
                "to": self.contract_address,
                "from": self.deployer_crypto.address,
                "value": 0,
            }
        )

        time.sleep(3)

        res = cast(
            JSONLike,
            self.contract.get_zero_transfer_events(
                ledger_api=self.ledger_api,
                contract_address=cast(str, self.contract_address),
                sender_address=self.deployer_crypto.address,
            ),
        )
        data = cast(List[JSONLike], res["data"])

        assert len(res) == 1, "one zero transfer should exist"
        assert (
            data[0]["sender"] == self.deployer_crypto.address
        ), f"{data[0]['sender']} should be the sender"
        assert data[0]["block_number"] is not None, "tx is still pending"

        # make a second zero transfer
        prev_block = cast(int, self.ledger_api.api.eth.get_block_number()) + 1
        self.ledger_api.api.eth.send_transaction(
            {
                "to": self.contract_address,
                "from": self.deployer_crypto.address,
                "value": 0,
            }
        )
        time.sleep(3)

        res = self.contract.get_zero_transfer_events(
            ledger_api=self.ledger_api,
            contract_address=cast(str, self.contract_address),
            sender_address=self.deployer_crypto.address,
            from_block=prev_block,
        )
        data = cast(List[JSONLike], res["data"])

        assert len(res) == 1, "one zero transfer should exist"
        assert (
            data[0]["sender"] == self.deployer_crypto.address
        ), f"{data[0]['sender']} should be the sender"
        assert data[0]["block_number"] is not None, "tx is still pending"

    def test_get_owners(self) -> None:
        """Test the owners are as expected."""
        owners = self.contract.get_owners(
            ledger_api=self.ledger_api,
            contract_address=cast(str, self.contract_address),
        )["owners"]
        assert owners == self.owners()


@skip_docker_tests
class TestRawSafeTransaction(BaseContractTestHardHatSafeNet):
    """Test `get_raw_safe_transaction`"""

    ledger_api: EthereumApi

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
        assert list(signatures_by_owners.keys()) == self.owners()

        tx = self._get_raw_safe_tx(
            sender_address=sender.address,
            value=value,
            data=data,
            signatures_by_owners=signatures_by_owners,
            to_address=receiver.address,
        )
        assert all(key in tx.keys() for key in EXPECTED_TX_KEYS), "Missing key"

        tx_signed = sender.sign_transaction(tx)
        tx_hash = self.ledger_api.send_signed_transaction(tx_signed)
        assert tx_hash is not None, "Tx hash is `None`"

        verified = self._verify_safe_tx(
            tx_hash, value, data, receiver.address, signatures_by_owners
        )
        assert verified, f"Not verified: {verified}"

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

    # mock `get_transaction` and `get_transaction_receipt` using a copy of a real reverted tx and its receipt
    @mock.patch.object(
        Eth,
        "get_transaction",
        return_value=AttributeDict(
            {
                "accessList": [],
                "blockHash": HexBytes(
                    "0x8543592f08d1d9e6d722ba9d600270d7e7789ecc9b66f27ca81b104df9c5dd4a"
                ),
                "blockNumber": 31190129,
                "chainId": "0x89",
                "from": "0x5eF6567079c6c26d8ebf61AC0716163367E9B3cf",
                "gas": 270000,
                "gasPrice": 36215860217,
                "hash": HexBytes(
                    "0x09d5be525caea564b2d4fd31af424c8f0414a9b270937a1bee29167a883e6ce5"
                ),
                "input": "0x6a7612020000000000000000000000003d9e92b0fe7673dda3d7c33b9ff302768a03de190000000000000000000"
                "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
                "000000000000014000000000000000000000000000000000000000000000000000000000000000000000000000000"
                "00000000000000000000000000000000000000000000001d4c0000000000000000000000000000000000000000000"
                "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
                "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
                "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000002000"
                "0000000000000000000000000000000000000000000000000000000000000846b0bac970000000000000000000000"
                "000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000"
                "000000000004000000000000000000000000000000000000000000000000000000000001df5000000000000000000"
                "00000000000000000000000000000487da3583c85e1e0000000000000000000000000000000000000000000000000"
                "000000000000000000000000000000000000000000000000000000000000000000000000104c292f99a14d354c669"
                "3f9037a4a3d09c85c8ad5f1ab4de79bbc8bab845560f797f385ecbe77e90245b7b45e218a2c56fec17c9d38729264"
                "83d0ed800df46daa71c3afaa87b5959d644cd0d311a93acb398ec4f9d4c545c54ea6f4adbaa3e99dd9668f948eb64"
                "10f1b2105e2f6ca762badf17539d9221cef7af55a244c6ae3c6b401cfd01fe829d711a372b9d8ad5b91e0956a4da1"
                "6929d04a2581b10f9f4599899b625c367bef18656c90efcf9d9ee5063860774f08517488b05ef5090acd31aa9d91b"
                "7df8080d69fdddfe9b326f3ae0cb95227e21d2d265b6a83861998dd9e91fb980415e78c2bb0b10dbe3b4d7bead977"
                "2f32fa26b738c5670aa69ee9d09973ea2b81c00000000000000000000000000000000000000000000000000000000",
                "maxFeePerGas": 36215860217,
                "maxPriorityFeePerGas": 36215860202,
                "nonce": 2231,
                "r": HexBytes(
                    "0x5d5d369d5fc30c5604d974761d41b08118120eb94fd65a827bab1f6ea558d67c"
                ),
                "s": HexBytes(
                    "0x12f68826bd41989335e62d43fd36547fe171ad536b99bc93766622438d3f8355"
                ),
                "to": "0x37ba5291A5bE8cbE44717a0673fe2c5a45B4B6A8",
                "transactionIndex": 28,
                "type": "0x2",
                "v": 1,
                "value": 0,
            }
        ),
    )
    @mock.patch.object(
        EthereumApi,
        "get_transaction_receipt",
        return_value={
            "blockHash": "0x8543592f08d1d9e6d722ba9d600270d7e7789ecc9b66f27ca81b104df9c5dd4a",
            "blockNumber": 31190129,
            "contractAddress": None,
            "cumulativeGasUsed": 5167853,
            "effectiveGasPrice": 36215860217,
            "from": "0x5eF6567079c6c26d8ebf61AC0716163367E9B3cf",
            "gasUsed": 48921,
            "logs": [
                {
                    "address": "0x0000000000000000000000000000000000001010",
                    "blockHash": "0x8543592f08d1d9e6d722ba9d600270d7e7789ecc9b66f27ca81b104df9c5dd4a",
                    "blockNumber": 31190129,
                    "data": "0x00000000000000000000000000000000000000000000000000064b5dcc9920c1000000000000000000000000"
                    "00000000000000000000000032116d529b00f7490000000000000000000000000000000000000000000004353d"
                    "1a5e0a73394e1e000000000000000000000000000000000000000000000000320b21f4ce67d688000000000000"
                    "0000000000000000000000000000000004353d20a9683fd26edf",
                    "logIndex": 115,
                    "removed": False,
                    "topics": [
                        "0x4dfe1bbbcf077ddc3e01291eea2d5c70c2b422b415d95645b9adcfd678cb1d63",
                        "0x0000000000000000000000000000000000000000000000000000000000001010",
                        "0x0000000000000000000000005ef6567079c6c26d8ebf61ac0716163367e9b3cf",
                        "0x000000000000000000000000f0245f6251bef9447a08766b9da2b07b28ad80b0",
                    ],
                    "transactionHash": "0x09d5be525caea564b2d4fd31af424c8f0414a9b270937a1bee29167a883e6ce5",
                    "transactionIndex": 28,
                }
            ],
            "logsBloom": "0x0000000000000000000000000000000000000000000000000000000000000000000000000000800000000000000"
            "000000000800000000000000000000000000000008000000000000000000000000080000000000000000000010000"
            "000000000000000000000000000000000000000000000000000000008000000000000000000000008000000000000"
            "000000000000000000000000000000000000088000020000000000000000000000000000000000000000000000000"
            "000000000000400000000000000000000100000000000000000000000000000010000000000000000000000000000"
            "0000000800000000000000000000000000000000000100000",
            "status": 0,
            "to": "0x37ba5291A5bE8cbE44717a0673fe2c5a45B4B6A8",
            "transactionHash": "0x09d5be525caea564b2d4fd31af424c8f0414a9b270937a1bee29167a883e6ce5",
            "transactionIndex": 28,
            "type": "0x2",
            "revert_reason": "execution reverted: GS026",
        },
    )
    def test_verify_reverted(self, *_: Any) -> None:
        """Test verify for reverted tx."""
        assert self.contract_address is not None
        res = self.contract.verify_tx(
            ledger_api=self.ledger_api,
            contract_address=self.contract_address,
            tx_hash="test",
            owners=("",),
            to_address=crypto_registry.make(
                EthereumCrypto.identifier, private_key_path=ETHEREUM_KEY_PATH_1
            ).address,
            value=0,
            data=b"",
            signatures_by_owner={},
        )
        assert not res["verified"], "Should not be verified"


@skip_docker_tests
class TestOwnerManagement(BaseContractTestHardHatSafeNet):
    """Test owner management related ."""

    ledger_api: EthereumApi

    def test_remove(self) -> None:  # pylint: disable=too-many-locals
        """Test owner removal."""
        assert self.contract_address is not None
        owner_to_be_removed = self.owners()[2]
        threshold = max(self.threshold() - 1, 1)
        value = 0
        data_str = self.contract.get_remove_owner_data(
            ledger_api=self.ledger_api,
            contract_address=self.contract_address,
            owner=owner_to_be_removed,
            threshold=threshold,
        ).get("data")
        data = bytes.fromhex(data_str[2:])  # strip 0x before converting to bytes

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
            to_address=self.contract_address,
            value=value,
            data=data,
        )["tx_hash"]
        b_tx_hash = binascii.unhexlify(cast(str, tx_hash)[2:])
        signatures_by_owners = {
            crypto.address: crypto.sign_message(b_tx_hash, is_deprecated_mode=True)[2:]
            for crypto in cryptos
        }
        assert list(signatures_by_owners.keys()) == self.owners()

        tx = self._get_raw_safe_tx(
            sender_address=sender.address,
            value=value,
            data=data,
            to_address=self.contract_address,
            signatures_by_owners=signatures_by_owners,
        )
        assert all(key in tx.keys() for key in EXPECTED_TX_KEYS), "Missing key"

        prev_block = cast(int, self.ledger_api.api.eth.get_block_number()) + 1
        tx_signed = sender.sign_transaction(tx)
        tx_hash = self.ledger_api.send_signed_transaction(tx_signed)

        assert tx_hash is not None, "Tx hash is `None`"

        verified = self._verify_safe_tx(
            tx_hash, value, data, self.contract_address, signatures_by_owners
        )
        assert verified, f"Not verified: {verified}"
        time.sleep(1)
        remove_events = self.contract.get_removed_owner_events(
            ledger_api=self.ledger_api,
            contract_address=self.contract_address,
            removed_owner=owner_to_be_removed,
            from_block=prev_block,
        ).get("data")

        assert remove_events is not None, "a RemovedOwner event was expected"
        assert len(remove_events) == 1, "1 RemovedOwner event was expected"
        assert (
            remove_events[0].get("owner") == owner_to_be_removed
        ), "a different owner than expected was removed"

    def test_swap(self) -> None:  # pylint: disable=too-many-locals
        """Test owner swapping."""
        assert self.contract_address is not None
        old_owner = self.owners()[1]
        new_owner = KEY_PAIRS[-1][0]
        value = 0
        data_str = self.contract.get_swap_owner_data(
            ledger_api=self.ledger_api,
            contract_address=self.contract_address,
            old_owner=old_owner,
            new_owner=new_owner,
        ).get("data")
        data = bytes.fromhex(data_str[2:])  # strip 0x before converting to bytes

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
            to_address=self.contract_address,
            value=value,
            data=data,
        )["tx_hash"]
        b_tx_hash = binascii.unhexlify(cast(str, tx_hash)[2:])
        signatures_by_owners = {
            crypto.address: crypto.sign_message(b_tx_hash, is_deprecated_mode=True)[2:]
            for crypto in cryptos
        }
        assert list(signatures_by_owners.keys()) == self.owners()

        tx = self._get_raw_safe_tx(
            sender_address=sender.address,
            to_address=self.contract_address,
            value=value,
            data=data,
            signatures_by_owners=signatures_by_owners,
        )
        assert all(key in tx.keys() for key in EXPECTED_TX_KEYS), "Missing key"

        prev_block = cast(int, self.ledger_api.api.eth.get_block_number()) + 1
        tx_signed = sender.sign_transaction(tx)
        tx_hash = self.ledger_api.send_signed_transaction(tx_signed)

        assert tx_hash is not None, "Tx hash is `None`"

        verified = self._verify_safe_tx(
            tx_hash, value, data, self.contract_address, signatures_by_owners
        )
        assert verified, f"Not verified: {verified}"
        time.sleep(1)
        remove_events = self.contract.get_removed_owner_events(
            ledger_api=self.ledger_api,
            contract_address=self.contract_address,
            removed_owner=old_owner,
            from_block=prev_block,
        ).get("data")

        assert remove_events is not None, "a RemovedOwner event was expected"
        assert len(remove_events) == 1, "1 RemovedOwner event was expected"
        assert (
            remove_events[0].get("owner") == old_owner
        ), "a different owner than expected was removed"
