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

"""This module contains the class to connect to an Gnosis Safe contract."""
import binascii
import logging
import secrets
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union, cast

from aea.common import JSONLike
from aea.configurations.base import PublicId
from aea.contracts.base import Contract
from aea.crypto.base import LedgerApi
from aea_ledger_ethereum import EthereumApi
from eth_typing import ChecksumAddress, HexAddress, HexStr
from hexbytes import HexBytes
from packaging.version import Version
from py_eth_sig_utils.eip712 import encode_typed_data
from requests import HTTPError
from web3.exceptions import SolidityError, TransactionNotFound
from web3.types import BlockIdentifier, Nonce, TxData, TxParams, Wei

from packages.valory.contracts.gnosis_safe_proxy_factory.contract import (
    GnosisSafeProxyFactoryContract,
)


PUBLIC_ID = PublicId.from_str("valory/gnosis_safe:0.1.0")
MIN_GAS = MIN_GASPRICE = 1
# see https://github.com/safe-global/safe-eth-py/blob/6c0e0d80448e5f3496d0d94985bca239df6eb399/gnosis/safe/safe_tx.py#L354
GAS_ADJUSTMENT = 75_000

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
        ledger_api = cast(EthereumApi, ledger_api)
        tx_params, contract_address = cls._get_deploy_transaction(
            ledger_api, deployer_address, owners=owners, threshold=threshold, **kwargs
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
        gas: int = 0,
        gas_price: Optional[int] = None,
        max_fee_per_gas: Optional[int] = None,
        max_priority_fee_per_gas: Optional[int] = None,
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
        :param max_fee_per_gas: max
        :param max_priority_fee_per_gas: max
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
        account_balance: int = ledger_api.api.eth.get_balance(account_address)
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

        if not ledger_api.api.eth.get_code(
            safe_contract_address
        ) or not ledger_api.api.eth.get_code(proxy_factory_address):
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
                {"gas": MIN_GAS, "gasPrice": MIN_GASPRICE}  # type: ignore
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
            max_fee_per_gas=max_fee_per_gas,
            max_priority_fee_per_gas=max_priority_fee_per_gas,
        )
        return tx_params, contract_address

    @classmethod
    def get_raw_safe_transaction_hash(  # pylint: disable=too-many-arguments,too-many-locals
        cls,
        ledger_api: EthereumApi,
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

        Note, because safe_nonce is included in the tx_hash the agents implicitly agree on the order of txs if they agree on a tx_hash.

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
            chain_id = ledger_api.api.eth.chain_id

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
    def _get_packed_signatures(
        cls, owners: Tuple[str], signatures_by_owner: Dict[str, str]
    ) -> bytes:
        """Get the packed signatures."""
        sorted_owners = sorted(owners, key=str.lower)
        signatures = b""
        for signer in sorted_owners:
            if signer not in signatures_by_owner:
                continue  # pragma: nocover
            signature = signatures_by_owner[signer]
            signature_bytes = binascii.unhexlify(signature)
            signatures += signature_bytes
        # Packed signature data ({bytes32 r}{bytes32 s}{uint8 v})
        return signatures

    @classmethod
    def get_raw_safe_transaction(  # pylint: disable=too-many-arguments,too-many-locals
        cls,
        ledger_api: EthereumApi,
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
        safe_gas_price: int = 0,
        gas_token: str = NULL_ADDRESS,
        refund_receiver: str = NULL_ADDRESS,
        gas_price: Optional[int] = None,
        nonce: Optional[Nonce] = None,
        max_fee_per_gas: Optional[int] = None,
        max_priority_fee_per_gas: Optional[int] = None,
        old_price: Optional[Dict[str, Wei]] = None,
        fallback_gas: int = 0,
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
        :param safe_gas_price: Gas price that should be used for the payment calculation
        :param gas_token: Token address (or `0x000..000` if ETH) that is used for the payment
        :param refund_receiver: Address of receiver of gas payment (or `0x000..000`  if tx.origin).
        :param gas_price: gas price
        :param nonce: the nonce
        :param max_fee_per_gas: max
        :param max_priority_fee_per_gas: max
        :param old_price: the old gas price params in case that we are trying to resubmit a transaction.
        :param fallback_gas: (external) gas to spend when base_gas and safe_tx_gas are zero and no gas estimation is possible.
        :return: the raw Safe transaction
        """
        sender_address = ledger_api.api.toChecksumAddress(sender_address)
        to_address = ledger_api.api.toChecksumAddress(to_address)
        ledger_api = cast(EthereumApi, ledger_api)
        signatures = cls._get_packed_signatures(owners, signatures_by_owner)
        safe_contract = cls.get_instance(ledger_api, contract_address)

        w3_tx = safe_contract.functions.execTransaction(
            to_address,
            value,
            data,
            operation,
            safe_tx_gas,
            base_gas,
            safe_gas_price,
            gas_token,
            refund_receiver,
            signatures,
        )
        # see https://github.com/safe-global/safe-eth-py/blob/6c0e0d80448e5f3496d0d94985bca239df6eb399/gnosis/safe/safe_tx.py#L354
        configured_gas = (
            base_gas + safe_tx_gas + GAS_ADJUSTMENT
            if base_gas != 0 or safe_tx_gas != 0
            else MIN_GAS
        )
        tx_parameters: Dict[str, Union[str, int]] = {
            "from": sender_address,
            "gas": configured_gas,
        }
        actual_nonce = ledger_api.api.eth.get_transaction_count(
            ledger_api.api.toChecksumAddress(sender_address)
        )
        if actual_nonce != nonce:
            nonce = actual_nonce
            old_price = None
        if gas_price is not None:
            tx_parameters["gasPrice"] = gas_price
        if max_fee_per_gas is not None:
            tx_parameters["maxFeePerGas"] = max_fee_per_gas  # pragma: nocover
        if max_priority_fee_per_gas is not None:  # pragma: nocover
            tx_parameters["maxPriorityFeePerGas"] = max_priority_fee_per_gas
        if (
            gas_price is None
            and max_fee_per_gas is None
            and max_priority_fee_per_gas is None
        ):
            tx_parameters.update(ledger_api.try_get_gas_pricing(old_price=old_price))
        # note, the next line makes an eth_estimateGas call iff gas is not set!
        transaction_dict = w3_tx.buildTransaction(tx_parameters)
        if configured_gas != 1:
            transaction_dict["gas"] = Wei(configured_gas)
        else:
            gas_estimate = (
                ledger_api._try_get_gas_estimate(  # pylint: disable=protected-access
                    transaction_dict
                )
            )
            transaction_dict["gas"] = (
                Wei(gas_estimate) if gas_estimate is not None else fallback_gas
            )
        transaction_dict["nonce"] = nonce  # pragma: nocover
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
        deployed_bytecode = ledger_api.api.eth.get_code(contract_address).hex()
        # we cannot use cls.contract_interface["ethereum"]["deployedBytecode"] because the
        # contract is created via a proxy
        local_bytecode = SAFE_DEPLOYED_BYTECODE
        verified = deployed_bytecode == local_bytecode
        return dict(verified=verified)

    @classmethod
    def verify_tx(  # pylint: disable=too-many-arguments,too-many-locals
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        tx_hash: str,
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
        safe_version: Optional[str] = None,
    ) -> JSONLike:
        """
        Verify a tx hash exists on the blockchain.

        Currently, the implementation is an overkill as most of the verification is implicit by the acceptance of the transaction in the Safe.

        :param ledger_api: the ledger API object
        :param contract_address: the contract address
        :param tx_hash: the transaction hash
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
        :param safe_version: Safe version 1.0.0 renamed `baseGas` to `dataGas`. Safe version 1.3.0 added `chainId` to the `domainSeparator`. If not provided, it will be retrieved from network
        :return: the verified status
        """
        to_address = ledger_api.api.toChecksumAddress(to_address)
        ledger_api = cast(EthereumApi, ledger_api)
        safe_contract = cls.get_instance(ledger_api, contract_address)
        signatures = cls._get_packed_signatures(owners, signatures_by_owner)

        if safe_version is None:
            safe_version = safe_contract.functions.VERSION().call(
                block_identifier="latest"
            )
        # Safes >= 1.0.0 Renamed `baseGas` to `dataGas`
        safe_version_ = Version(safe_version)
        base_gas_name = "baseGas" if safe_version_ >= Version("1.0.0") else "dataGas"

        try:
            _logger.info(f"Trying to get transaction and receipt from hash {tx_hash}")
            transaction = ledger_api.api.eth.get_transaction(tx_hash)
            receipt = ledger_api.get_transaction_receipt(tx_hash)
            _logger.info(
                f"Received transaction: {transaction}, with receipt: {receipt}."
            )
            if receipt is None:
                raise ValueError  # pragma: nocover
        except (TransactionNotFound, ValueError):  # pragma: nocover
            return dict(verified=False, status=-1)

        expected = dict(
            contract_address=contract_address,
            to_address=to_address,
            value=value,
            data=data,
            operation=operation,
            safe_tx_gas=safe_tx_gas,
            base_gas=base_gas,
            gas_price=gas_price,
            gas_token=gas_token,
            refund_receiver=refund_receiver,
            signatures=signatures,
        )
        decoded: Tuple[Any, Dict] = (None, {})
        diff: Dict = {}
        try:
            decoded = safe_contract.decode_function_input(transaction["input"])
            actual = dict(
                contract_address=transaction["to"],
                to_address=decoded[1]["to"],
                value=decoded[1]["value"],
                data=decoded[1]["data"],
                operation=decoded[1]["operation"],
                safe_tx_gas=decoded[1]["safeTxGas"],
                base_gas=decoded[1][base_gas_name],
                gas_price=decoded[1]["gasPrice"],
                gas_token=decoded[1]["gasToken"],
                refund_receiver=decoded[1]["refundReceiver"],
                signatures=decoded[1]["signatures"],
            )
            diff = {k: (v, actual[k]) for k, v in expected.items() if v != actual[k]}
            verified = (
                receipt["status"]
                and "execTransaction" in str(decoded[0])
                and len(diff) == 0
            )
        except (TransactionNotFound, KeyError, ValueError):  # pragma: nocover
            verified = False
        return dict(
            verified=verified,
            status=receipt["status"],
            transaction=transaction,
            actual=decoded,  # type: ignore
            expected=expected,
            diff=diff,
        )

    @classmethod
    def revert_reason(  # pylint: disable=unused-argument
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        tx: TxData,
    ) -> JSONLike:
        """Check the revert reason of a transaction.

        :param ledger_api: the ledger API object.
        :param contract_address: the contract address
        :param tx: the transaction for which we want to get the revert reason.

        :return: the revert reason message.
        """
        ledger_api = cast(EthereumApi, ledger_api)

        # build a new transaction to replay:
        replay_tx = {
            "to": tx["to"],
            "from": tx["from"],
            "value": tx["value"],
            "data": tx["input"],
        }

        try:
            # replay the transaction locally:
            ledger_api.api.eth.call(replay_tx, tx["blockNumber"] - 1)
        except SolidityError as e:
            # execution reverted exception
            return dict(revert_reason=repr(e))
        except HTTPError as e:  # pragma: nocover
            # http exception
            raise e
        else:
            # given tx not reverted
            raise ValueError(f"The given transaction has not been reverted!\ntx: {tx}")

    @classmethod
    def get_safe_nonce(cls, ledger_api: EthereumApi, contract_address: str) -> JSONLike:
        """
        Retrieve the safe's nonce

        :param ledger_api: the ledger API object
        :param contract_address: the contract address
        :return: the safe nonce
        """
        safe_contract = cls.get_instance(ledger_api, contract_address)
        safe_nonce = safe_contract.functions.nonce().call(block_identifier="latest")
        return dict(safe_nonce=safe_nonce)

    @classmethod
    def get_ingoing_transfers(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        from_block: Optional[str] = None,
        to_block: Optional[str] = "latest",
    ) -> JSONLike:
        """
        A list of transfers into the contract.

        :param ledger_api: the ledger API object
        :param contract_address: the contract address,
        :param from_block: from which block to start tje search
        :param to_block: at which block to end the search
        :return: list of transfers
        """
        safe_contract = cls.get_instance(ledger_api, contract_address)

        if from_block is None:
            logging.info(
                "'from_block' not provided, checking for transfers to the safe contract in the last 50 blocks."
            )
            current_block = ledger_api.api.eth.get_block("latest")["number"]
            from_block = hex(max(0, current_block - 50))  # check in the last ~10 min

        safe_filter = safe_contract.events.SafeReceived.createFilter(
            fromBlock=from_block, toBlock=to_block
        )
        all_entries = safe_filter.get_all_entries()

        return {
            "data": list(
                map(
                    lambda entry: {
                        "sender": entry["args"]["sender"],
                        "amount": int(entry["args"]["value"]),
                        "blockNumber": entry["blockNumber"],
                    },
                    all_entries,
                )
            )
        }

    @classmethod
    def get_balance(cls, ledger_api: EthereumApi, contract_address: str) -> JSONLike:
        """
        Retrieve the safe's balance

        :param ledger_api: the ledger API object
        :param contract_address: the contract address
        :return: the safe balance (in wei)
        """
        return dict(balance=ledger_api.get_balance(address=contract_address))

    @classmethod
    def get_amount_spent(  # pylint: disable=unused-argument
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        tx_hash: str,
    ) -> JSONLike:
        """
        Get the amount of ether spent in a tx.

        :param ledger_api: the ledger API object
        :param contract_address: the contract address (not used)
        :param tx_hash: the settled tx hash
        :return: the safe balance (in wei)
        """
        tx_receipt = ledger_api.get_transaction_receipt(tx_hash)
        tx = ledger_api.get_transaction(tx_hash)

        tx_value = int(tx["value"])
        gas_price = int(tx["gasPrice"])
        gas_used = int(tx_receipt["gasUsed"])
        total_spent = tx_value + (gas_price * gas_used)

        return dict(amount_spent=total_spent)

    @classmethod
    def get_safe_txs(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        from_block: BlockIdentifier = "earliest",
        to_block: BlockIdentifier = "latest",
    ) -> JSONLike:
        """
        Get all the safe tx hashes.

        :param ledger_api: the ledger API object
        :param contract_address: the contract address (not used)
        :param from_block: from which block to search for events
        :param to_block: to which block to search for events
         :return: the safe txs
        """

        ledger_api = cast(EthereumApi, ledger_api)
        factory_contract = cls.get_instance(ledger_api, contract_address)
        entries = factory_contract.events.ExecutionSuccess.createFilter(
            fromBlock=from_block,
            toBlock=to_block,
        ).get_all_entries()

        return dict(
            txs=list(
                map(
                    lambda entry: dict(
                        tx_hash=entry.transactionHash.hex(),
                        block_number=entry.blockNumber,
                    ),
                    entries,
                )
            )
        )
