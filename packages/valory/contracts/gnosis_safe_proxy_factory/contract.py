# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2023 Valory AG
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

"""This module contains the class to connect to an Gnosis Safe Proxy Factory contract."""
import logging
from typing import Any, Optional, Tuple, cast

from aea.common import JSONLike
from aea.configurations.base import PublicId
from aea.contracts.base import Contract
from aea.crypto.base import LedgerApi
from aea_ledger_ethereum import EthereumApi
from web3.types import Nonce, TxParams, Wei


PUBLIC_ID = PublicId.from_str("valory/gnosis_safe_proxy_factory:0.1.0")
MIN_GAS = 1
# see https://github.com/valory-xyz/open-autonomy/pull/1209#discussion_r950129886
GAS_ESTIMATE_ADJUSTMENT = 50_000


_logger = logging.getLogger(
    f"aea.packages.{PUBLIC_ID.author}.contracts.{PUBLIC_ID.name}.contract"
)

PROXY_FACTORY_CONTRACT = "0xa6B71E26C5e0845f74c812102Ca7114b6a896AB2"


class GnosisSafeProxyFactoryContract(Contract):
    """The Gnosis Safe Proxy Factory contract."""

    contract_id = PUBLIC_ID

    @classmethod
    def get_raw_transaction(
        cls, ledger_api: LedgerApi, contract_address: str, **kwargs: Any
    ) -> Optional[JSONLike]:
        """Get the raw transaction."""
        raise NotImplementedError  # pragma: nocover

    @classmethod
    def get_raw_message(
        cls, ledger_api: LedgerApi, contract_address: str, **kwargs: Any
    ) -> Optional[bytes]:
        """Get raw message."""
        raise NotImplementedError  # pragma: nocover

    @classmethod
    def get_state(
        cls, ledger_api: LedgerApi, contract_address: str, **kwargs: Any
    ) -> Optional[JSONLike]:
        """Get state."""
        raise NotImplementedError  # pragma: nocover

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
        return super().get_deploy_transaction(ledger_api, deployer_address, **kwargs)

    @classmethod
    def build_tx_deploy_proxy_contract_with_nonce(  # pylint: disable=too-many-arguments,too-many-locals
        cls,
        ledger_api: EthereumApi,
        proxy_factory_address: str,
        master_copy: str,
        address: str,
        initializer: bytes,
        salt_nonce: int,
        gas: int = MIN_GAS,
        gas_price: Optional[int] = None,
        max_fee_per_gas: Optional[int] = None,
        max_priority_fee_per_gas: Optional[int] = None,
        nonce: Optional[int] = None,
    ) -> Tuple[TxParams, str]:
        """
        Deploy proxy contract via Proxy Factory using `createProxyWithNonce` (create2)

        :param ledger_api: ledger API object
        :param proxy_factory_address: the address of the proxy factory
        :param address: Ethereum address
        :param master_copy: Address the proxy will point at
        :param initializer: Data for safe creation
        :param salt_nonce: Uint256 for `create2` salt
        :param gas: Gas
        :param gas_price: Gas Price
        :param max_fee_per_gas: max
        :param max_priority_fee_per_gas: max
        :param nonce: Nonce
        :return: Tuple(tx-hash, tx, deployed contract address)
        """
        proxy_factory_contract = cls.get_instance(ledger_api, proxy_factory_address)

        create_proxy_fn = proxy_factory_contract.functions.createProxyWithNonce(
            master_copy, initializer, salt_nonce
        )

        tx_parameters = TxParams({"from": address})
        contract_address = create_proxy_fn.call(tx_parameters)

        if gas_price is not None:
            tx_parameters["gasPrice"] = Wei(gas_price)  # pragma: nocover

        if max_fee_per_gas is not None:
            tx_parameters["maxFeePerGas"] = Wei(max_fee_per_gas)  # pragma: nocover

        if max_priority_fee_per_gas is not None:
            tx_parameters["maxPriorityFeePerGas"] = Wei(  # pragma: nocover
                max_priority_fee_per_gas
            )

        if (
            gas_price is None
            and max_fee_per_gas is None
            and max_priority_fee_per_gas is None
        ):
            tx_parameters.update(ledger_api.try_get_gas_pricing())

        # we set a value to avoid triggering the gas estimation during `buildTransaction` below
        tx_parameters["gas"] = Wei(max(gas, MIN_GAS))

        if nonce is not None:
            tx_parameters["nonce"] = Nonce(nonce)

        transaction_dict = create_proxy_fn.build_transaction(tx_parameters)
        gas_estimate = (
            ledger_api._try_get_gas_estimate(  # pylint: disable=protected-access
                transaction_dict
            )
        )
        # see https://github.com/valory-xyz/open-autonomy/pull/1209#discussion_r950129886
        transaction_dict["gas"] = (
            Wei(max(gas_estimate + GAS_ESTIMATE_ADJUSTMENT, gas))
            if gas_estimate is not None
            else Wei(gas)
        )
        return transaction_dict, contract_address

    @classmethod
    def verify_contract(
        cls, ledger_api: EthereumApi, contract_address: str
    ) -> JSONLike:
        """
        Verify the contract's bytecode

        :param ledger_api: the ledger API object
        :param contract_address: the contract address
        :return: the verified status
        """
        ledger_api = cast(EthereumApi, ledger_api)
        deployed_bytecode = ledger_api.api.eth.get_code(contract_address).hex()
        local_bytecode = cls.contract_interface["ethereum"]["deployedBytecode"]
        verified = deployed_bytecode == local_bytecode
        return dict(verified=verified)
