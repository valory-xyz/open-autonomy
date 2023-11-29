# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023 valory
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

from typing import Any

from aea.common import JSONLike
from aea.configurations.base import PublicId
from aea.contracts.base import Contract
from aea.crypto.base import LedgerApi


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
    def get_approve_tx(  # pylint: disable=too-many-arguments
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
