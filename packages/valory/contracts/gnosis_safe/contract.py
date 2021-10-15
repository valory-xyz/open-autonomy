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

"""This module contains the class to connect to an Gnosis Safe contract."""
import binascii
import logging
import secrets
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, cast

from aea.common import JSONLike
from aea.configurations.base import PublicId
from aea.contracts.base import Contract
from aea.crypto.base import LedgerApi
from aea_ledger_ethereum import EthereumApi
from eth_typing import ChecksumAddress, HexAddress, HexStr
from hexbytes import HexBytes
from packaging.version import Version
from py_eth_sig_utils.eip712 import encode_typed_data
from web3.exceptions import TransactionNotFound
from web3.types import TxParams, Wei


PUBLIC_ID = PublicId.from_str("valory/gnosis_safe:0.1.0")

_logger = logging.getLogger(
    f"aea.packages.{PUBLIC_ID.author}.contracts.{PUBLIC_ID.name}.contract"
)

NULL_ADDRESS: str = "0x" + "0" * 40
SAFE_CONTRACT = "0xd9Db270c1B5E3Bd161E8c8503c55cEABeE709552"
DEFAULT_CALLBACK_HANDLER = "0xf48f2B2d2a534e402487b3ee7C18c33Aec0Fe5e4"
PROXY_FACTORY_CONTRACT = "0xa6B71E26C5e0845f74c812102Ca7114b6a896AB2"
SAFE_DEPLOYED_BYTECODE = "0x608060405273ffffffffffffffffffffffffffffffffffffffff600054167fa619486e0000000000000000000000000000000000000000000000000000000060003514156050578060005260206000f35b3660008037600080366000845af43d6000803e60008114156070573d6000fd5b3d6000f3fea2646970667358221220d1429297349653a4918076d650332de1a1068c5f3e07c5c82360c277770b955264736f6c63430007060033"


def _get_nonce() -> int:
    """Generate a nonce for the Safe deployment."""
    return secrets.SystemRandom().randint(0, 2 ** 256 - 1)


def checksum_address(agent_address: str) -> ChecksumAddress:
    """Get the checksum address."""
    return ChecksumAddress(HexAddress(HexStr(agent_address)))


class SafeOperation(Enum):
    """Operation types."""

    CALL = 0
    DELEGATE_CALL = 1
    CREATE = 2


class GnosisSafeContract(Contract):
    """The Gnosis Safe contract."""

    contract_id = PUBLIC_ID

    @classmethod
    def get_raw_transaction(
        cls, ledger_api: LedgerApi, contract_address: str, **kwargs: Any
    ) -> Optional[JSONLike]:
        """Get the Safe transaction."""
        raise NotImplementedError

    @classmethod
    def get_raw_message(
        cls, ledger_api: LedgerApi, contract_address: str, **kwargs: Any
    ) -> Optional[bytes]:
        """Get raw message."""
        raise NotImplementedError

    @classmethod
    def get_state(
        cls, ledger_api: LedgerApi, contract_address: str, **kwargs: Any
    ) -> Optional[JSONLike]:
        """Get state."""
        raise NotImplementedError

    @classmethod
    def get_deploy_transaction(
        cls, ledger_api: LedgerApi, deployer_address: str, **kwargs: Any
    ) -> Optional[JSONLike]:
        """
        Get deploy transaction.

        :param ledger_api: ledger API object.
        :param deployer_address: the deployer address.
        :param kwargs: the keyword arguments.
        :return: an optional JSON-like object.
        """
        owners = kwargs.pop("owners")
        threshold = kwargs.pop("threshold")
        salt_nonce = kwargs.pop("salt_nonce", None)
        gas = kwargs.pop("gas", None)
        gas_price = kwargs.pop("gas_price", None)
        ledger_api = cast(EthereumApi, ledger_api)
        tx_params, contract_address = cls._get_deploy_transaction(
            ledger_api,
            deployer_address,
            owners=owners,
            threshold=threshold,
            salt_nonce=salt_nonce,
            gas=gas,
            gas_price=gas_price,
        )
        result = dict(cast(Dict, tx_params))
        # piggyback the contract address
        result["contract_address"] = contract_address
        return result

    @classmethod
    def _get_deploy_transaction(  # pylint: disable=too-many-locals,too-many-arguments
        cls,
        ledger_api: EthereumApi,
        deployer_address: str,
        owners: List[str],
        threshold: int,
        salt_nonce: Optional[int] = None,
        gas: Optional[int] = None,
        gas_price: Optional[int] = None,
    ) -> Tuple[TxParams, str]:
        """
        Get the deployment transaction of the new Safe.

        Taken from:
            https://github.com/gnosis/safe-cli/blob/contracts_v1.3.0/safe_creator.py

        :param ledger_api: Ethereum APIs.
        :param deployer_address: public key of the sender of the transaction
        :param owners: a list of public keys
        :param threshold: the signature threshold
        :param salt_nonce: Use a custom nonce for the deployment. Defaults to random nonce.
        :param gas: gas cost
        :param gas_price: Gas price that should be used for the payment calculation

        :return: transaction params and contract address
        """
        salt_nonce = salt_nonce if salt_nonce is not None else _get_nonce()
        salt_nonce = cast(int, salt_nonce)
        to_address = NULL_ADDRESS
        data = b""
        payment_token = NULL_ADDRESS
        payment = 0
        payment_receiver = NULL_ADDRESS

        if len(owners) < threshold:
            raise ValueError(
                "Threshold cannot be bigger than the number of unique owners"
            )

        safe_contract_address = SAFE_CONTRACT
        proxy_factory_address = PROXY_FACTORY_CONTRACT
        fallback_handler = DEFAULT_CALLBACK_HANDLER

        account_address = checksum_address(deployer_address)
        account_balance: int = ledger_api.api.eth.getBalance(account_address)
        if not account_balance:
            raise ValueError("Client does not have any funds")

        ether_account_balance = round(
            ledger_api.api.fromWei(account_balance, "ether"), 6
        )
        _logger.info(
            "Network %s - Sender %s - Balance: %sΞ",
            ledger_api.api.net.version,
            account_address,
            ether_account_balance,
        )

        if not ledger_api.api.eth.getCode(
            safe_contract_address
        ) or not ledger_api.api.eth.getCode(proxy_factory_address):
            raise ValueError("Network not supported")  # pragma: nocover

        _logger.info(
            "Creating new Safe with owners=%s threshold=%s "
            "fallback-handler=%s salt-nonce=%s",
            owners,
            threshold,
            fallback_handler,
            salt_nonce,
        )
        safe_contract = cls.get_instance(ledger_api, safe_contract_address)
        safe_creation_tx_data = HexBytes(
            safe_contract.functions.setup(
                owners,
                threshold,
                to_address,
                data,
                fallback_handler,
                payment_token,
                payment,
                payment_receiver,
            ).buildTransaction(  # type: ignore
                {"gas": 1, "gasPrice": 1}  # type: ignore
            )[
                "data"
            ]
        )

        nonce = (
            ledger_api._try_get_transaction_count(  # pylint: disable=protected-access
                account_address
            )
        )
        if nonce is None:
            raise ValueError("No nonce returned.")  # pragma: nocover
        # TOFIX: lazy import until contract dependencies supported in AEA
        from packages.valory.contracts.gnosis_safe_proxy_factory.contract import (  # pylint: disable=import-outside-toplevel
            GnosisSafeProxyFactoryContract,
        )

        (
            tx_params,
            contract_address,
        ) = GnosisSafeProxyFactoryContract.build_tx_deploy_proxy_contract_with_nonce(
            ledger_api,
            proxy_factory_address,
            safe_contract_address,
            account_address,
            safe_creation_tx_data,
            salt_nonce,
            nonce=nonce,
            gas=gas,
            gas_price=gas_price,
        )
        return tx_params, contract_address

    @classmethod
    def get_raw_safe_transaction_hash(  # pylint: disable=too-many-arguments,too-many-locals
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        to_address: str,
        value: int,
        data: bytes,
        operation: int = SafeOperation.CALL.value,
        safe_tx_gas: int = 0,
        base_gas: int = 0,
        gas_price: int = 0,
        gas_token: str = NULL_ADDRESS,
        refund_receiver: str = NULL_ADDRESS,
        safe_nonce: Optional[int] = None,
        safe_version: Optional[str] = None,
        chain_id: Optional[int] = None,
    ) -> JSONLike:
        """
        Get the hash of the raw Safe transaction.

        Adapted from https://github.com/gnosis/gnosis-py/blob/69f1ee3263086403f6017effa0841c6a2fbba6d6/gnosis/safe/safe_tx.py#L125

        :param ledger_api: the ledger API object
        :param contract_address: the contract address
        :param to_address: the tx recipient address
        :param value: the ETH value of the transaction
        :param data: the data of the transaction
        :param operation: Operation type of Safe transaction
        :param safe_tx_gas: Gas that should be used for the Safe transaction
        :param base_gas: Gas costs for that are independent of the transaction execution
            (e.g. base transaction fee, signature check, payment of the refund)
        :param gas_price: Gas price that should be used for the payment calculation
        :param gas_token: Token address (or `0x000..000` if ETH) that is used for the payment
        :param refund_receiver: Address of receiver of gas payment (or `0x000..000`  if tx.origin).
        :param safe_nonce: Current nonce of the Safe. If not provided, it will be retrieved from network
        :param safe_version: Safe version 1.0.0 renamed `baseGas` to `dataGas`. Safe version 1.3.0 added `chainId` to the `domainSeparator`. If not provided, it will be retrieved from network
        :param chain_id: Ethereum network chain_id is used in hash calculation for Safes >= 1.3.0. If not provided, it will be retrieved from the provided ethereum_client
        :return: the hash of the raw Safe transaction
        """
        safe_contract = cls.get_instance(ledger_api, contract_address)
        if safe_nonce is None:
            safe_nonce = safe_contract.functions.nonce().call(block_identifier="latest")
        if safe_version is None:
            safe_version = safe_contract.functions.VERSION().call(
                block_identifier="latest"
            )
        if chain_id is None:
            chain_id = ledger_api.api.eth.chainId

        data_ = HexBytes(data).hex()

        # Safes >= 1.0.0 Renamed `baseGas` to `dataGas`
        safe_version_ = Version(safe_version)
        base_gas_name = "baseGas" if safe_version_ >= Version("1.0.0") else "dataGas"

        structured_data = {
            "types": {
                "EIP712Domain": [
                    {"name": "verifyingContract", "type": "address"},
                ],
                "SafeTx": [
                    {"name": "to", "type": "address"},
                    {"name": "value", "type": "uint256"},
                    {"name": "data", "type": "bytes"},
                    {"name": "operation", "type": "uint8"},
                    {"name": "safeTxGas", "type": "uint256"},
                    {"name": base_gas_name, "type": "uint256"},
                    {"name": "gasPrice", "type": "uint256"},
                    {"name": "gasToken", "type": "address"},
                    {"name": "refundReceiver", "type": "address"},
                    {"name": "nonce", "type": "uint256"},
                ],
            },
            "primaryType": "SafeTx",
            "domain": {
                "verifyingContract": contract_address,
            },
            "message": {
                "to": to_address,
                "value": value,
                "data": data_,
                "operation": operation,
                "safeTxGas": safe_tx_gas,
                base_gas_name: base_gas,
                "gasPrice": gas_price,
                "gasToken": gas_token,
                "refundReceiver": refund_receiver,
                "nonce": safe_nonce,
            },
        }

        # Safes >= 1.3.0 Added `chainId` to the domain
        if safe_version_ >= Version("1.3.0"):
            # EIP712Domain(uint256 chainId,address verifyingContract)
            structured_data["types"]["EIP712Domain"].insert(  # type: ignore
                0, {"name": "chainId", "type": "uint256"}
            )
            structured_data["domain"]["chainId"] = chain_id  # type: ignore

        return dict(tx_hash=HexBytes(encode_typed_data(structured_data)).hex())

    @classmethod
    def get_raw_safe_transaction(  # pylint: disable=too-many-arguments,too-many-locals
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        sender_address: str,
        owners: Tuple[str],
        to_address: str,
        value: int,
        data: bytes,
        signatures_by_owner: Dict[str, str],
        operation: int = SafeOperation.CALL.value,
        safe_tx_gas: int = 0,
        base_gas: int = 0,
        gas_price: int = 0,
        gas_token: str = NULL_ADDRESS,
        refund_receiver: str = NULL_ADDRESS,
        safe_nonce: Optional[int] = None,
        safe_version: Optional[str] = None,
    ) -> JSONLike:
        """
        Get the raw Safe transaction

        :param ledger_api: the ledger API object
        :param contract_address: the contract address
        :param sender_address: the address of the sender
        :param owners: the sequence of owners
        :param to_address: Destination address of Safe transaction
        :param value: Ether value of Safe transaction
        :param data: Data payload of Safe transaction
        :param signatures_by_owner: mapping from owners to signatures
        :param operation: Operation type of Safe transaction
        :param safe_tx_gas: Gas that should be used for the Safe transaction
        :param base_gas: Gas costs for that are independent of the transaction execution
            (e.g. base transaction fee, signature check, payment of the refund)
        :param gas_price: Gas price that should be used for the payment calculation
        :param gas_token: Token address (or `0x000..000` if ETH) that is used for the payment
        :param refund_receiver: Address of receiver of gas payment (or `0x000..000`  if tx.origin).
        :param safe_nonce: Current nonce of the Safe. If not provided, it will be retrieved from network
        :param safe_version: Safe version 1.0.0 renamed `baseGas` to `dataGas`. Safe version 1.3.0 added `chainId` to the `domainSeparator`. If not provided, it will be retrieved from network
        :return: the raw Safe transaction
        """
        ledger_api = cast(EthereumApi, ledger_api)
        sorted_owners = sorted(owners, key=str.lower)
        signatures = b""
        for signer in sorted_owners:
            if signer not in signatures_by_owner:
                continue  # pragma: nocover
            signature = signatures_by_owner[signer]
            signature_bytes = binascii.unhexlify(signature)
            signatures += signature_bytes
        # Packed signature data ({bytes32 r}{bytes32 s}{uint8 v})

        safe_contract = cls.get_instance(ledger_api, contract_address)

        if safe_nonce is None:
            safe_nonce = safe_contract.functions.nonce().call(block_identifier="latest")
        if safe_version is None:
            safe_version = safe_contract.functions.VERSION().call(
                block_identifier="latest"
            )

        w3_tx = safe_contract.functions.execTransaction(
            to_address,
            value,
            data,
            operation,
            safe_tx_gas,
            base_gas,
            gas_price,
            gas_token,
            refund_receiver,
            signatures,
        )
        tx_gas_price = gas_price or ledger_api.api.eth.gasPrice
        tx_parameters = {
            "from": sender_address,
            "gasPrice": tx_gas_price,
        }
        transaction_dict = w3_tx.buildTransaction(tx_parameters)
        transaction_dict["gas"] = Wei(
            max(transaction_dict["gas"] + 75000, base_gas + safe_tx_gas + 75000)
        )
        transaction_dict["nonce"] = ledger_api.api.eth.getTransactionCount(
            ledger_api.api.toChecksumAddress(sender_address)
        )
        return transaction_dict

    @classmethod
    def verify_contract(cls, ledger_api: LedgerApi, contract_address: str) -> JSONLike:
        """
        Verify the contract's bytecode

        :param ledger_api: the ledger API object
        :param contract_address: the contract address
        :return: the verified status
        """
        ledger_api = cast(EthereumApi, ledger_api)
        deployed_bytecode = ledger_api.api.eth.getCode(contract_address).hex()
        # we cannot use cls.contract_interface["ethereum"]["deployedBytecode"] because the
        # contract is created via a proxy
        local_bytecode = SAFE_DEPLOYED_BYTECODE
        verified = deployed_bytecode == local_bytecode
        return dict(verified=verified)

    @classmethod
    def verify_tx(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,  # pylint: disable=unused-argument
        tx_hash: str,
    ) -> JSONLike:
        """
        Verify a tx hash exists on the blockchain.

        :param ledger_api: the ledger API object
        :param contract_address: the contract address
        :param tx_hash: the transaction hash
        :return: the verified status
        """
        ledger_api = cast(EthereumApi, ledger_api)

        try:
            transaction = ledger_api.api.eth.getTransaction(tx_hash)
            receipt = ledger_api.get_transaction_receipt(tx_hash)
            if receipt is None:
                raise ValueError  # pragma: nocover
            verified = transaction["to"] == contract_address and receipt["status"]
            # TOFIX: verify input field in tx
            return dict(verified=verified)
        except (TransactionNotFound, ValueError):  # pragma: nocover
            return dict(verified=False)
