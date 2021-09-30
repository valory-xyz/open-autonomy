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
import re
import secrets
from typing import Any, Dict, List, Optional, Tuple, cast

from aea.common import JSONLike
from aea.configurations.base import PublicId
from aea.contracts.base import Contract
from aea.crypto.base import LedgerApi
from aea_ledger_ethereum import EthereumApi
from eth_typing import ChecksumAddress, HexAddress, HexStr, URI
from gnosis.eth import EthereumClient
from gnosis.eth.constants import NULL_ADDRESS
from gnosis.eth.contracts import get_proxy_factory_contract, get_safe_V1_3_0_contract
from gnosis.safe import ProxyFactory, Safe, SafeTx
from hexbytes import HexBytes
from web3 import HTTPProvider
from web3.types import Nonce, TxParams, Wei


PUBLIC_ID = PublicId.from_str("valory/gnosis_safe:0.1.0")

_logger = logging.getLogger(
    f"aea.packages.{PUBLIC_ID.author}.contracts.{PUBLIC_ID.name}.contract"
)


SAFE_CONTRACT = "0xd9Db270c1B5E3Bd161E8c8503c55cEABeE709552"
DEFAULT_CALLBACK_HANDLER = "0xf48f2B2d2a534e402487b3ee7C18c33Aec0Fe5e4"
PROXY_FACTORY_CONTRACT = "0xa6B71E26C5e0845f74c812102Ca7114b6a896AB2"
MULTISEND_CONTRACT = "0xA238CBeb142c10Ef7Ad8442C6D1f9E89e07e7761"
MULTISEND_CALL_ONLY_CONTRACT = "0x40A2aCCbd92BCA938b02010E17A5b8929b49130D"


def keccak256(input_: bytes) -> bytes:
    """Compute hash."""
    return bytes(bytearray.fromhex(EthereumApi.get_hash(input_)[2:]))


def _get_nonce() -> int:
    """Generate a nonce for the Safe deployment."""
    return secrets.SystemRandom().randint(0, 2 ** 256 - 1)


def checksum_address(agent_address: str) -> ChecksumAddress:
    """Get the checksum address."""
    return ChecksumAddress(HexAddress(HexStr(agent_address)))


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
        tx_params, contract_address = cls._get_deploy_transaction(
            ledger_api,
            deployer_address,
            owners=owners,
            threshold=threshold,
            salt_nonce=salt_nonce,
        )
        result = dict(cast(Dict, tx_params))
        # piggyback the contract address
        result["contract_address"] = contract_address
        return result

    @classmethod
    def _get_deploy_transaction(  # pylint: disable=too-many-locals,too-many-arguments
        cls,
        ledger_api: LedgerApi,
        deployer_address: str,
        owners: List[str],
        threshold: int,
        salt_nonce: Optional[int] = None,
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

        :return: transaction params and contract address
        """
        salt_nonce = salt_nonce if salt_nonce is not None else _get_nonce()
        salt_nonce = cast(int, salt_nonce)
        to_address = NULL_ADDRESS
        data = b""
        payment_token = NULL_ADDRESS
        payment = 0
        payment_receiver = NULL_ADDRESS

        ledger_api = cast(EthereumApi, ledger_api)
        uri = cast(URI, cast(HTTPProvider, ledger_api.api.provider).endpoint_uri)
        ethereum_client = EthereumClient(uri)

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
            ethereum_client.get_network().name,
            account_address,
            ether_account_balance,
        )

        if not ethereum_client.w3.eth.getCode(
            safe_contract_address
        ) or not ethereum_client.w3.eth.getCode(proxy_factory_address):
            raise ValueError("Network not supported")

        _logger.info(
            "Creating new Safe with owners=%s threshold=%s "
            "fallback-handler=%s salt-nonce=%s",
            owners,
            threshold,
            fallback_handler,
            salt_nonce,
        )
        safe_contract = (  # pylint: disable=assignment-from-no-return
            get_safe_V1_3_0_contract(ethereum_client.w3, safe_contract_address)
        )
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

        proxy_factory = ProxyFactory(proxy_factory_address, ethereum_client)
        nonce = ethereum_client.get_nonce_for_account(account_address)
        tx_params, contract_address = cls._build_tx_deploy_proxy_contract_with_nonce(
            proxy_factory,
            safe_contract_address,
            account_address,
            safe_creation_tx_data,
            salt_nonce,
            nonce=nonce,
        )
        return tx_params, contract_address

    @classmethod
    def _build_tx_deploy_proxy_contract_with_nonce(  # pylint: disable=too-many-arguments
        cls,
        proxy_factory: ProxyFactory,
        master_copy: str,
        address: str,
        initializer: bytes,
        salt_nonce: int,
        gas: Optional[int] = None,
        gas_price: Optional[int] = None,
        nonce: Optional[int] = None,
    ) -> Tuple[TxParams, str]:
        """
        Deploy proxy contract via Proxy Factory using `createProxyWithNonce` (create2)

        :param proxy_factory: the ProxyFactory object
        :param address: Ethereum address
        :param master_copy: Address the proxy will point at
        :param initializer: Data for safe creation
        :param salt_nonce: Uint256 for `create2` salt
        :param gas: Gas
        :param gas_price: Gas Price
        :param nonce: Nonce
        :return: Tuple(tx-hash, tx, deployed contract address)
        """
        proxy_factory_contract = (  # pylint: disable=assignment-from-no-return
            get_proxy_factory_contract(
                proxy_factory.ethereum_client.w3, proxy_factory.address
            )
        )
        create_proxy_fn = proxy_factory_contract.functions.createProxyWithNonce(
            master_copy, initializer, salt_nonce
        )

        tx_parameters = TxParams({"from": address})
        contract_address = create_proxy_fn.call(tx_parameters)

        if gas_price is not None:
            tx_parameters["gasPrice"] = Wei(gas_price)

        if gas is not None:
            tx_parameters["gas"] = Wei(gas)

        if nonce is not None:
            tx_parameters["nonce"] = Nonce(nonce)

        transaction_dict = create_proxy_fn.buildTransaction(tx_parameters)
        # Auto estimation of gas does not work. We use a little more gas just in case
        transaction_dict["gas"] = Wei(transaction_dict["gas"] + 50000)
        return transaction_dict, contract_address

    @classmethod
    def get_raw_safe_transaction_hash(  # pylint: disable=too-many-arguments
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        to_address: str,
        value: int,
        data: bytes,
    ) -> JSONLike:
        """
        Get the hash of the raw Safe transaction

        :param ledger_api: the ledger API object
        :param contract_address: the contract address
        :param to_address: the tx recipient address
        :param value: the ETH value of the transaction
        :param data: the data of the transaction
        :return: the hash of the raw Safe transaction
        """
        safe_tx = cls._get_safe_tx(
            ledger_api, contract_address, to_address, value, data
        )
        return dict(tx_hash=safe_tx.safe_tx_hash.hex())

    @classmethod
    def _get_safe_tx(  # pylint: disable=too-many-arguments
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        to_address: str,
        value: int,
        data: bytes,
    ) -> SafeTx:
        """Get the Safe transaction object."""
        ledger_api = cast(EthereumApi, ledger_api)
        uri = cast(URI, cast(HTTPProvider, ledger_api.api.provider).endpoint_uri)
        ethereum_client = EthereumClient(uri)
        safe = Safe(
            ChecksumAddress(HexAddress(HexStr(contract_address))),
            ethereum_client,
        )
        safe_tx = safe.build_multisig_tx(to_address, value, data)
        return safe_tx

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
    ) -> JSONLike:
        """
        Get the raw Safe transaction

        :param ledger_api: the ledger API object
        :param contract_address: the contract address
        :param sender_address: the address of the sender
        :param owners: the sequence of owners
        :param to_address: the tx recipient address
        :param value: the ETH value of the transaction
        :param data: the data of the transaction
        :param signatures_by_owner: mapping from owners to signatures
        :return: the raw Safe transaction
        """
        sorted_owners = sorted(owners, key=str.lower)
        final_signature = b""
        for signer in sorted_owners:
            if signer not in signatures_by_owner:
                continue
            signature = signatures_by_owner[signer]
            signature_bytes = binascii.unhexlify(signature)
            final_signature += signature_bytes

        safe_tx = cls._get_safe_tx(
            ledger_api, contract_address, to_address, value, data
        )
        safe_tx.signatures = final_signature
        safe_tx.call(sender_address)

        tx_gas_price = safe_tx.gas_price or safe_tx.w3.eth.gas_price
        tx_parameters = {
            "from": sender_address,
            "gasPrice": tx_gas_price,
        }
        transaction_dict = safe_tx.w3_tx.buildTransaction(tx_parameters)
        transaction_dict["gas"] = Wei(
            max(transaction_dict["gas"] + 75000, safe_tx.recommended_gas())
        )
        transaction_dict["nonce"] = safe_tx.w3.eth.get_transaction_count(
            safe_tx.w3.toChecksumAddress(sender_address)
        )

        return transaction_dict

    @classmethod
    def verify_contract(
        cls, ledger_api: LedgerApi, contract_address: str, solc_version: str
    ) -> bool:
        """
        Verify the contract's bytecode

        :param ledger_api: the ledger API object
        :param contract_address: the contract address
        :param solc_version: solc version with which the contract was compiled
        :return: the verified status
        """
        ledger_api = cast(EthereumApi, ledger_api)
        blockchain_bytecode = cls._extract_bytecode_contract(
            ledger_api.api.eth.get_code(contract_address).hex()[2:],  # strip leading 0x
            solc_version,
        )
        compiled_bytecode = cls._extract_bytecode_contract("", solc_version)  # FIX
        return blockchain_bytecode == compiled_bytecode

    @classmethod
    def _extract_bytecode_contract(
        cls, bytecode: str, solc_version: str
    ) -> Optional[str]:
        """
        Strip all contract's metadata

        :param bytecode: the contract's bytecode
        :param solc_version: solc version with which the contract was compiled
        :return: the contract with all metadata stripped or None if it failed
        """
        _, solc_minor, solc_patch, _ = cls._version_extractor(solc_version)
        contract_end = bytecode.index("a165627a7a72305820")

        if solc_minor is None or solc_patch is None:
            return None
        if solc_minor >= 4 and solc_patch >= 22:
            contract_start = bytecode.rindex("6080604052")
            return bytecode[contract_start:contract_end]
        if solc_minor >= 4 and solc_patch >= 7:
            contract_start = bytecode.rindex("6060604052")
            return bytecode[contract_start:contract_end]
        return bytecode

    @classmethod
    def _version_extractor(
        cls, solc_version: str
    ) -> Tuple[Optional[int], Optional[int], Optional[int], Optional[str]]:
        """
        Extracts version numbers from a string in the format "v0.4.16+commit.d7661dd9"

        :param solc_version: solc version with which the contract was compiled
        :return: the version numbers: major, minor, patch, [commit]
        """
        major, minor, patch, commit = None, None, None, None
        version_regex = r"v([0-9]+)\.([0-9]+)\.([0-9]+)([+-]commit\.[a-zA-Z0-9]+)?"
        match = re.match(version_regex, solc_version)

        if match:
            major, minor, patch = [int(i) for i in match.groups()[:3]]
            if len(match.groups()) > 3:
                commit = match.groups()[3].split(".")[-1]

        return major, minor, patch, commit
