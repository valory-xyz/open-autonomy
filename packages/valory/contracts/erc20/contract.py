# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023-2025 Valory AG
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

"""This module contains the scaffold contract definition."""

from typing import Any, Dict

from aea.common import JSONLike
from aea.configurations.base import PublicId
from aea.contracts.base import Contract
from aea.crypto.base import LedgerApi
from aea_ledger_ethereum import EthereumApi


class ERC20TokenContract(Contract):
    """ERC20 token contract."""

    contract_id = PublicId.from_str("valory/erc20:0.1.0")

    @classmethod
    def get_raw_transaction(
        cls, ledger_api: LedgerApi, contract_address: str, **kwargs: Any
    ) -> JSONLike:
        """
        Handler method for the 'GET_RAW_TRANSACTION' requests.

        Implement this method in the sub class if you want
        to handle the contract requests manually.

        :param ledger_api: the ledger apis.
        :param contract_address: the contract address.
        :param kwargs: the keyword arguments.
        :return: the tx  # noqa: DAR202
        """
        raise NotImplementedError

    @classmethod
    def get_raw_message(
        cls, ledger_api: LedgerApi, contract_address: str, **kwargs: Any
    ) -> bytes:
        """
        Handler method for the 'GET_RAW_MESSAGE' requests.

        Implement this method in the sub class if you want
        to handle the contract requests manually.

        :param ledger_api: the ledger apis.
        :param contract_address: the contract address.
        :param kwargs: the keyword arguments.
        :return: the tx  # noqa: DAR202
        """
        raise NotImplementedError

    @classmethod
    def get_state(
        cls, ledger_api: LedgerApi, contract_address: str, **kwargs: Any
    ) -> JSONLike:
        """
        Handler method for the 'GET_STATE' requests.

        Implement this method in the sub class if you want
        to handle the contract requests manually.

        :param ledger_api: the ledger apis.
        :param contract_address: the contract address.
        :param kwargs: the keyword arguments.
        :return: the tx  # noqa: DAR202
        """
        raise NotImplementedError

    @classmethod
    def get_approve_tx(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        spender: str,
        amount: int,
        sender: str,
        raise_on_try: bool = False,
    ) -> JSONLike:
        """Get approve tx."""
        instance = cls.get_instance(
            ledger_api=ledger_api,
            contract_address=contract_address,
        )
        tx = instance.functions.approve(spender, amount).build_transaction(
            {
                "from": sender,
                "gas": 1,
                "gasPrice": ledger_api.api.eth.gas_price,
                "nonce": ledger_api.api.eth.get_transaction_count(sender),
            }
        )
        return ledger_api.update_with_gas_estimate(
            transaction=tx,
            raise_on_try=raise_on_try,
        )

    @classmethod
    def get_events(  # pragma: nocover
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        event: str,
        receipt: JSONLike,
    ) -> JSONLike:
        """Process receipt for events."""
        contract_interface = cls.get_instance(
            ledger_api=ledger_api,
            contract_address=contract_address,
        )
        Event = getattr(contract_interface.events, event, None)
        if Event is None:
            return {"events": []}
        return {"events": Event().process_receipt(receipt)}

    @classmethod
    def check_balance(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        account: str,
    ) -> JSONLike:
        """Check the balance of the given account."""
        contract_instance = cls.get_instance(ledger_api, contract_address)
        balance_of = getattr(contract_instance.functions, "balanceOf")  # noqa
        token_balance = balance_of(account).call()
        wallet_balance = ledger_api.api.eth.get_balance(account)
        return dict(token=token_balance, wallet=wallet_balance)

    @classmethod
    def get_allowance(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        owner: str,
        spender: str,
    ) -> JSONLike:
        """Check the balance of the given account."""
        contract_instance = cls.get_instance(ledger_api, contract_address)
        allowance = contract_instance.functions.allowance(owner, spender).call()
        return dict(data=allowance)

    @classmethod
    def build_deposit_tx(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
    ) -> Dict[str, bytes]:
        """Build a deposit transaction."""
        contract_instance = cls.get_instance(ledger_api, contract_address)
        data = contract_instance.encode_abi("deposit")
        return {"data": bytes.fromhex(data[2:])}

    @classmethod
    def build_withdraw_tx(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        amount: int,
    ) -> Dict[str, bytes]:
        """Build a deposit transaction."""
        contract_instance = cls.get_instance(ledger_api, contract_address)
        data = contract_instance.encode_abi("withdraw", args=(amount,))
        return {"data": bytes.fromhex(data[2:])}

    @classmethod
    def build_approval_tx(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        spender: str,
        amount: int,
    ) -> Dict[str, bytes]:
        """Build an ERC20 approval."""
        contract_instance = cls.get_instance(ledger_api, contract_address)
        checksumed_spender = ledger_api.api.to_checksum_address(spender)
        data = contract_instance.encode_abi(
            "approve", args=(checksumed_spender, amount)
        )
        return {"data": bytes.fromhex(data[2:])}

    @classmethod
    def get_transfer_tx_data(  # pragma: nocover
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        receiver: str,
        amount: int,
    ) -> JSONLike:
        """Returns the transaction to transfer tokens."""
        contract_interface = cls.get_instance(
            ledger_api=ledger_api,
            contract_address=contract_address,
        )
        data = contract_interface.encode_abi(
            abi_element_identifier="transfer", args=[receiver, amount]
        )
        return dict(data=data)

    @classmethod
    def get_token_symbol(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
    ) -> JSONLike:
        """Check the balance of the given account."""
        contract_instance = cls.get_instance(ledger_api, contract_address)
        symbol = contract_instance.functions.symbol().call()
        return dict(data=symbol)

    @classmethod
    def get_total_supply(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
    ) -> JSONLike:
        """Get the total supply."""
        contract_instance = cls.get_instance(ledger_api, contract_address)
        total_supply = contract_instance.functions.totalSupply().call()
        return dict(data=total_supply)

    @classmethod
    def get_name(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
    ) -> JSONLike:
        """Get the total supply."""
        contract_instance = cls.get_instance(ledger_api, contract_address)
        name = contract_instance.functions.name().call()
        return dict(data=name)

    @classmethod
    def get_token_decimals(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
    ) -> JSONLike:
        """Get the token decimals."""
        contract_instance = cls.get_instance(ledger_api, contract_address)
        decimals = contract_instance.functions.decimals().call()
        return dict(data=decimals)

    @classmethod
    def build_transfer_tx(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        to_address: str,
        amount: int,
    ) -> Dict[str, bytes]:
        """Build an ERC20 transfer transaction."""
        contract_instance = cls.get_instance(ledger_api, contract_address)
        checksumed_to_address = ledger_api.api.to_checksum_address(to_address)
        data = contract_instance.encodeABI(
            "transfer", args=(checksumed_to_address, amount)
        )
        return {"data": bytes.fromhex(data[2:])}
