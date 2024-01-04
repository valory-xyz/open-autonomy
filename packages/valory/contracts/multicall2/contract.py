# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023 Valory AG
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

"""This module contains a wrapper around Multicall2."""
import logging
from typing import Any, Callable, Dict, List, Tuple

from aea.common import JSONLike
from aea.configurations.base import PublicId
from aea.contracts.base import Contract
from aea.crypto.base import LedgerApi


PUBLIC_ID = PublicId.from_str("valory/multicall2:0.1.0")

_logger = logging.getLogger(
    f"aea.packages.{PUBLIC_ID.author}.contracts.{PUBLIC_ID.name}.contract"
)


class Multicall2Contract(Contract):
    """A wrapper for the MakerDAO Multicall2."""

    contract_id = PUBLIC_ID

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
        raise NotImplementedError  # pragma: nocover

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
        raise NotImplementedError  # pragma: nocover

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
        raise NotImplementedError  # pragma: nocover

    @classmethod
    def encode_function_call(
        cls,
        ledger_api: LedgerApi,
        contract_instance: Any,
        fn_name: str,
        args: List[Any],
    ) -> Tuple[Dict[str, Any], Callable]:
        """
        Encode a function call.

        To be used with Multicall2.aggregate().

        :param ledger_api: the ledger api.
        :param contract_instance: an insntace of the contract whose call is getting encoded.
        :param fn_name: the function name.
        :param args: the function arguments.
        :return: the target address, the data, and the output decoder function.
        """
        data = contract_instance.encodeABI(fn_name=fn_name, args=args)
        for elem in contract_instance.abi:
            if elem.get("name", "") == fn_name:
                output_types = elem["outputs"]
                normalized_output_types = [t["type"] for t in output_types]
                break

        def decoder(return_data: bytes) -> Any:
            """Decode the return data."""
            return ledger_api.api.codec.decode(normalized_output_types, return_data)

        decoder_fn = decoder
        target_address = contract_instance.address
        call = {
            "target": target_address,
            "callData": data,
        }
        return call, decoder_fn

    @classmethod
    def aggregate_and_decode(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        calls_and_decoders: List[Tuple[Dict[str, Any], Callable]],
    ) -> Tuple[int, List[Any]]:
        """
        Make aggregate call.

        :param ledger_api: the ledger apis.
        :param contract_address: the multicall address.
        :param calls_and_decoders: the calls and their corresponding output decoders.
        :return: block number and decoded outputs.
        """
        instance = cls.get_instance(ledger_api, contract_address)
        calls = [call[0] for call in calls_and_decoders]
        decoders = [call[1] for call in calls_and_decoders]
        res = instance.functions.aggregate(calls).call()
        block_number, call_responses = res[0], res[1]
        decoded_responses = [
            decoder(call_response)
            for decoder, call_response in zip(decoders, call_responses)
        ]
        block_number = ledger_api.api.eth.block_number
        return block_number, decoded_responses
