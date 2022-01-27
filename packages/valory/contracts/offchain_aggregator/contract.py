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

"""This module contains the class to connect to an Offchain Aggregator contract."""
import logging
from typing import Any, Optional, cast

from aea.common import JSONLike
from aea.configurations.base import PublicId
from aea.contracts.base import Contract
from aea.crypto.base import LedgerApi
from aea_ledger_ethereum import EthereumApi
from eth_abi import encode_abi


DEPLOYED_BYTECODE = "0x608060405234801561001057600080fd5b50600436106101005760003560e01c80637284e41611610097578063b5ab58dc11610066578063b5ab58dc1461033e578063b633620c1461035b578063e5fe457714610378578063feaf968c146103d357610100565b80637284e41614610263578063814118341461026b5780638205bf6a146102c35780639a6fc8f5146102cb57610100565b806354fd4d50116100d357806354fd4d50146101d9578063668a0f02146101e15780636b0bac97146101e957806370da2f671461025b57610100565b8063181f5a771461010557806322adbc7814610182578063313ce567146101a157806350d25bcd146101bf575b600080fd5b61010d6103db565b6040805160208082528351818301528351919283929083019185019080838360005b8381101561014757818101518382015260200161012f565b50505050905090810190601f1680156101745780820380516001836020036101000a031916815260200191505b509250505060405180910390f35b61018a6103fb565b6040805160179290920b8252519081900360200190f35b6101a961041f565b6040805160ff9092168252519081900360200190f35b6101c7610443565b60408051918252519081900360200190f35b6101c761046a565b6101c761046f565b610259600480360360208110156101ff57600080fd5b81019060208101813564010000000081111561021a57600080fd5b82018360208201111561022c57600080fd5b8035906020019184600183028401116401000000008311171561024e57600080fd5b509092509050610482565b005b61018a610a60565b61010d610a84565b610273610b1a565b60408051602080825283518183015283519192839290830191858101910280838360005b838110156102af578181015183820152602001610297565b505050509050019250505060405180910390f35b6101c7610b88565b6102f4600480360360208110156102e157600080fd5b503569ffffffffffffffffffff16610bb9565b604051808669ffffffffffffffffffff1681526020018581526020018481526020018381526020018269ffffffffffffffffffff1681526020019550505050505060405180910390f35b6101c76004803603602081101561035457600080fd5b5035610cf8565b6101c76004803603602081101561037157600080fd5b5035610d32565b610380610d72565b604080516fffffffffffffffffffffffffffffffff19909616865263ffffffff909416602086015260ff9092168484015260170b606084015267ffffffffffffffff166080830152519081900360a00190f35b6102f4610e2c565b6060604051806060016040528060228152602001610f1160229139905090565b7f0000000000000000000000000000000000000000000000000de0b6b3a764000081565b7f000000000000000000000000000000000000000000000000000000000000001281565b60008054600160b01b900463ffffffff16815260016020526040902054601790810b900b90565b600481565b600054600160b01b900463ffffffff1690565b61048c8282610ea3565b36146104df576040805162461bcd60e51b815260206004820152601960248201527f7472616e736d6974206d65737361676520746f6f206c6f6e6700000000000000604482015290519081900360640190fd5b6104e7610eab565b60408051608080820183526000549081901b6fffffffffffffffffffffffffffffffff19168252600160801b810464ffffffffff166020830152600160a81b810460ff1682840152600160b01b900463ffffffff16606082015282528390839081101561055357600080fd5b50602081810135601790810b810b900b90830152356040820181905281515160589190911b906fffffffffffffffffffffffffffffffff198083169116146105e2576040805162461bcd60e51b815260206004820152601560248201527f636f6e666967446967657374206d69736d617463680000000000000000000000604482015290519081900360640190fd5b604082015182516020015164ffffffffff80831691161061064a576040805162461bcd60e51b815260206004820152600c60248201527f7374616c65207265706f72740000000000000000000000000000000000000000604482015290519081900360640190fd5b610652610ed2565b336000908152600260209081526040918290208251808401909352805460ff8082168552919284019161010090910416600181111561068d57fe5b600181111561069857fe5b90525090506001816020015160018111156106af57fe5b1480156106f057506003816000015160ff16815481106106cb57fe5b60009182526020909120015473ffffffffffffffffffffffffffffffffffffffff1633145b610741576040805162461bcd60e51b815260206004820152601860248201527f756e617574686f72697a6564207472616e736d69747465720000000000000000604482015290519081900360640190fd5b50825164ffffffffff909116602091820152820151601790810b7f0000000000000000000000000000000000000000000000000de0b6b3a764000090910b13801591506107b857507f00000000000000000000000000000000000000000000d3c21bcecceda100000060170b816020015160170b13155b6107f35760405162461bcd60e51b8152600401808060200182810382526023815260200180610f336023913960400191505060405180910390fd5b80516060908101805163ffffffff6001918201811690925260408051808201825260208087018051601790810b845267ffffffffffffffff4281168486019081528a518a01518916600090815297855296869020945185549751909116600160c01b0290820b77ffffffffffffffffffffffffffffffffffffffffffffffff9081167fffffffffffffffff0000000000000000000000000000000000000000000000009098169790971790961695909517909255865186015191518388015184519190950b815233918101919091528083019390935290519216927f15896539366eeb36325b327019dbcaa42700cca9b3e61881c197705255ce667e92918290030190a280516060015160408051428152905160009263ffffffff16917f0109fc6f55cf40689f02fbaad7af7fe7bbac8a3d2186600afc7d3e10cac60271919081900360200190a380600001516060015163ffffffff16816020015160170b7f0559884fd3a460db3073b7fc896cc77986f16e378210ded43186175bf646fc5f426040518082815260200191505060405180910390a3518051600080546020840151604085015160609095015163ffffffff16600160b01b027fffffffffffff00000000ffffffffffffffffffffffffffffffffffffffffffff60ff909616600160a81b027fffffffffffffffffffff00ffffffffffffffffffffffffffffffffffffffffff64ffffffffff909316600160801b027fffffffffffffffffffffff0000000000ffffffffffffffffffffffffffffffff60809790971c6fffffffffffffffffffffffffffffffff199095169490941795909516929092171692909217929092161790555050565b7f00000000000000000000000000000000000000000000d3c21bcecceda100000081565b60048054604080516020601f6002600019610100600188161502019095169490940493840181900481028201810190925282815260609390929091830182828015610b105780601f10610ae557610100808354040283529160200191610b10565b820191906000526020600020905b815481529060010190602001808311610af357829003601f168201915b5050505050905090565b60606003805480602002602001604051908101604052809291908181526020018280548015610b1057602002820191906000526020600020905b815473ffffffffffffffffffffffffffffffffffffffff168152600190910190602001808311610b54575050505050905090565b60008054600160b01b900463ffffffff16815260016020526040902054600160c01b900467ffffffffffffffff1690565b600080600080600063ffffffff8669ffffffffffffffffffff1611156040518060400160405280600f81526020017f4e6f20646174612070726573656e74000000000000000000000000000000000081525090610c945760405162461bcd60e51b81526004018080602001828103825283818151815260200191508051906020019080838360005b83811015610c59578181015183820152602001610c41565b50505050905090810190601f168015610c865780820380516001836020036101000a031916815260200191505b509250505060405180910390fd5b50610c9d610ed2565b5050505063ffffffff8316600090815260016020908152604091829020825180840190935254601781810b810b810b808552600160c01b90920467ffffffffffffffff1693909201839052949594900b939092508291508490565b600063ffffffff821115610d0e57506000610d2d565b5063ffffffff8116600090815260016020526040902054601790810b900b5b919050565b600063ffffffff821115610d4857506000610d2d565b5063ffffffff16600090815260016020526040902054600160c01b900467ffffffffffffffff1690565b600080808080333214610dcc576040805162461bcd60e51b815260206004820152601460248201527f4f6e6c792063616c6c61626c6520627920454f41000000000000000000000000604482015290519081900360640190fd5b50506000805463ffffffff600160b01b8204811683526001602052604090922054608082901b96600160801b909204600881901c909316955064ffffffffff9092169350601782900b9250600160c01b90910467ffffffffffffffff1690565b60008054600160b01b900463ffffffff1690808080610e49610ed2565b5050505063ffffffff8216600090815260016020908152604091829020825180840190935254601781810b810b810b808552600160c01b90920467ffffffffffffffff1693909201839052939493900b9290915081908490565b604401919050565b6040518060600160405280610ebe610ee9565b815260006020820181905260409091015290565b604080518082019091526000808252602082015290565b6040805160808101825260008082526020820181905291810182905260608101919091529056fe5665727953696d706c654f6666636861696e41676772656761746f7220302e302e316f62736572766174696f6e206973206f7574206f66206d696e2d6d61782072616e6765a264697066735822122020fbd6e5016e409c337e3dfcb85a4de6bd8f9e449577714deadf5e4bde2a905364736f6c63430007010033"
PUBLIC_ID = PublicId.from_str("valory/offchain_aggregator:0.1.0")

_logger = logging.getLogger(
    f"aea.packages.{PUBLIC_ID.author}.contracts.{PUBLIC_ID.name}.contract"
)


class OffchainAggregatorContract(Contract):
    """The Offchain Aggregator contract."""

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
        return super().get_deploy_transaction(ledger_api, deployer_address, **kwargs)

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
        # local_bytecode = cls.contract_interface["ethereum"]["deployedBytecode"]  # noqa:  E800
        verified = deployed_bytecode == DEPLOYED_BYTECODE
        return dict(verified=verified)

    @classmethod
    def get_transmit_data(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        epoch_: int,
        round_: int,
        amount_: int,
    ) -> JSONLike:
        """
        Handler method for the 'get_active_project' requests.

        Implement this method in the sub class if you want
        to handle the contract requests manually.

        :param ledger_api: the ledger apis.
        :param contract_address: the contract address.
        :param epoch_: the epoch
        :param round_: the round
        :param amount_: the amount
        :return: the tx  # noqa: DAR202
        """
        instance = cls.get_instance(ledger_api, contract_address)
        report = cls.get_report(epoch_, round_, amount_)
        data = instance.encodeABI(fn_name="transmit", args=[report])
        return {"data": bytes.fromhex(data[2:])}  # type: ignore

    @classmethod
    def get_latest_transmission_details(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
    ) -> JSONLike:
        """
        Handler method for the 'get_active_project' requests.

        Implement this method in the sub class if you want
        to handle the contract requests manually.

        :param ledger_api: the ledger apis.
        :param contract_address: the contract address.
        :return: the tx  # noqa: DAR202
        """
        contract_instance = cls.get_instance(ledger_api, contract_address)

        detail = ledger_api.contract_method_call(
            contract_instance,
            "latestTransmissionDetails",
        )
        if detail is None:
            return {"epoch_": 0, "round_": 0}  # pragma: nocover
        epoch_ = detail[1]
        round_ = detail[2]
        return {"epoch_": epoch_, "round_": round_}

    @classmethod
    def get_report(
        cls,
        epoch_: int,
        round_: int,
        amount_: int,
    ) -> bytes:
        """
        Get report serialised.

        :param epoch_: the epoch
        :param round_: the round
        :param amount_: the amount
        :return: the tx  # noqa: DAR202
        """
        left_pad = "0" * 22
        TEMP_CONFIG = 0
        config_digest = TEMP_CONFIG.to_bytes(16, "big").hex()
        epoch_hex = epoch_.to_bytes(4, "big").hex()
        round_hex = round_.to_bytes(1, "big").hex()
        raw_report = left_pad + config_digest + epoch_hex + round_hex
        report = encode_abi(["bytes32", "int192"], [bytes.fromhex(raw_report), amount_])
        return report

    @classmethod
    def transmit(  # pylint: disable=too-many-arguments
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        epoch_: int,
        round_: int,
        amount_: int,
        **kwargs: Any,
    ) -> Optional[JSONLike]:
        """
        Handler method for the 'get_active_project' requests.

        Implement this method in the sub class if you want
        to handle the contract requests manually.

        :param ledger_api: the ledger apis.
        :param contract_address: the contract address.
        :param epoch_: the epoch
        :param round_: the round
        :param amount_: the amount
        :param kwargs: the kwargs
        :return: the tx  # noqa: DAR202
        """
        contract_instance = cls.get_instance(ledger_api, contract_address)
        report = cls.get_report(epoch_, round_, amount_)

        return ledger_api.build_transaction(
            contract_instance=contract_instance,
            method_name="transmit",
            method_args={"_report": report},
            tx_args=kwargs,
        )

    @classmethod
    def latest_round_data(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
    ) -> Optional[JSONLike]:
        """
        Get data from the latest round.

        :param ledger_api: the ledger apis.
        :param contract_address: the contract address.
        :return: the data
        """
        contract_instance = cls.get_instance(ledger_api, contract_address)

        return ledger_api.contract_method_call(
            contract_instance,
            "latestRoundData",
        )
