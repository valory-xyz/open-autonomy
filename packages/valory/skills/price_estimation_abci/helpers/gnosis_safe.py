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

"""
This module contains Gnosis Safe utilities.

Taken from:
    https://github.com/gnosis/safe-cli/blob/contracts_v1.3.0/safe_creator.py

"""
import logging
import secrets
from typing import List, Optional, Tuple, cast

from eth_typing import URI
from gnosis.eth import EthereumClient
from gnosis.eth.constants import NULL_ADDRESS
from gnosis.eth.contracts import get_proxy_factory_contract, get_safe_V1_3_0_contract
from gnosis.safe import ProxyFactory
from hexbytes import HexBytes

# Note: addresses of deployment of master contracts are deterministic
from web3.auto import w3
from web3.types import Nonce, TxParams, Wei

from packages.valory.skills.price_estimation_abci.helpers.base import checksum_address


SAFE_CONTRACT = "0xd9Db270c1B5E3Bd161E8c8503c55cEABeE709552"
DEFAULT_CALLBACK_HANDLER = "0xf48f2B2d2a534e402487b3ee7C18c33Aec0Fe5e4"
PROXY_FACTORY_CONTRACT = "0xa6B71E26C5e0845f74c812102Ca7114b6a896AB2"
MULTISEND_CONTRACT = "0xA238CBeb142c10Ef7Ad8442C6D1f9E89e07e7761"
MULTISEND_CALL_ONLY_CONTRACT = "0x40A2aCCbd92BCA938b02010E17A5b8929b49130D"


def _get_nonce() -> int:
    """Generate a nonce for the Safe deployment."""
    return secrets.SystemRandom().randint(0, 2 ** 256 - 1)


def get_deploy_safe_tx(  # pylint: disable=too-many-locals
    ethereum_node_url: str,
    sender: str,
    owners: List[str],
    threshold: int,
    salt_nonce: Optional[int] = None,
) -> Tuple[TxParams, str]:
    """
    Get the deployment transaction of the new Safe.

    :param ethereum_node_url: Ethereum node url
    :param sender: public key of the sender of the transaction
    :param owners: a list of public keys
    :param threshold: the signature threshold
    :param salt_nonce: Use a custom nonce for the deployment. Defaults to random nonce.

    :return: transaction params and contract address
    """
    node_url: URI = URI(ethereum_node_url)
    salt_nonce = salt_nonce if salt_nonce is not None else _get_nonce()
    salt_nonce = cast(int, salt_nonce)
    to_address = NULL_ADDRESS
    data = b""
    payment_token = NULL_ADDRESS
    payment = 0
    payment_receiver = NULL_ADDRESS

    if len(owners) < threshold:
        raise ValueError("Threshold cannot be bigger than the number of unique owners")

    safe_contract_address = SAFE_CONTRACT
    proxy_factory_address = PROXY_FACTORY_CONTRACT
    fallback_handler = DEFAULT_CALLBACK_HANDLER
    ethereum_client = EthereumClient(node_url)

    account_address = checksum_address(sender)
    account_balance: int = ethereum_client.get_balance(account_address)
    if not account_balance:
        raise ValueError("Client does not have any funds")

    ether_account_balance = round(
        ethereum_client.w3.fromWei(account_balance, "ether"), 6
    )
    logging.info(
        "Network %s - Sender %s - Balance: %sΞ",
        ethereum_client.get_network().name,
        account_address,
        ether_account_balance,
    )

    if not ethereum_client.w3.eth.getCode(
        safe_contract_address
    ) or not ethereum_client.w3.eth.getCode(proxy_factory_address):
        raise ValueError("Network not supported")

    logging.info(
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
    tx_params, contract_address = _build_tx_deploy_proxy_contract_with_nonce(
        proxy_factory,
        safe_contract_address,
        account_address,
        safe_creation_tx_data,
        salt_nonce,
    )
    return tx_params, contract_address


def _build_tx_deploy_proxy_contract_with_nonce(  # pylint: disable=too-many-arguments
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
    transaction_dict["nonce"] = w3.eth.get_transaction_count(address)
    return transaction_dict, contract_address
