# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2024 Valory AG
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

import json
from collections import OrderedDict
from enum import Enum, IntEnum
from typing import Any, Dict, List, Optional, Tuple, Union

from aea.common import JSONLike
from aea.configurations.base import PublicId
from aea.contracts.base import Contract
from aea.crypto.base import LedgerApi
from solders.system_program import transfer  # pylint: disable=import-error


Pubkey = Any  # defined in solders.pubkey
Keypair = Any  # defined in solders.keypair
Program = Any  # defined in anchorpy
Instruction = Any  # defined in solders.instruction


class SquadsMultisigAuthorityIndex(IntEnum):
    """Squads multisig authority index list."""

    INTERNAL = 0
    VAULT = 1
    SECONDARY = 2
    PROGRAM_UPGRADE = 3


class MultisigAccountType(Enum):
    """Squads multisig account types."""

    MS = "Ms"
    MS_TRANSACTION = "MsTransaction"
    MS_INSTRUCTION = "MsInstruction"

    def __str__(self) -> str:
        """String represenation."""
        return self._value_  # pylint: disable=no-member


class TransactionStatus(IntEnum):
    """Transaction status"""

    Draft = 0  # Transaction default state
    Active = 1  # Transaction is live and ready
    ExecuteReady = 2  # Transaction has been approved and is pending execution
    Executed = 3  # Transaction has been executed
    Rejected = 4  # Transaction has been rejected
    Cancelled = 5  # Transaction has been cancelled


def pubkey_container_to_list(container: Any) -> List[str]:
    """Convert pubkey container to list of pubkey strings."""
    return list(map(str, container))


def account_meta_container_to_list(container: Any) -> List[Dict[str, Any]]:
    """Convert pubkey container to list of pubkey strings."""
    return [
        {
            "pubkey": str(ac.pubkey),
            "is_signer": ac.is_signer,
            "is_writable": ac.is_writable,
        }
        for ac in container
    ]


def ms_account_to_dict(state: Any) -> Dict[str, Any]:
    """Deserialize multisig account state to a python dictionary."""
    return {
        "threshold": state.threshold,
        "authority_index": state.authority_index,
        "transaction_index": state.transaction_index,
        "ms_change_index": state.ms_change_index,
        "bump": state.bump,
        "create_key": str(state.create_key),
        "allow_external_execute": state.allow_external_execute,
        "keys": pubkey_container_to_list(container=state.keys),
    }


def ms_tx_account_to_dict(state: Any) -> Dict[str, Any]:
    """Deserialize multisig transaction account state to a python dictionary."""
    return {
        "creator": str(state.creator),
        "ms": str(state.ms),
        "transaction_index": state.transaction_index,
        "authority_index": state.authority_index,
        "authority_bump": state.authority_bump,
        "status": state.status.index,
        "instruction_index": state.instruction_index,
        "bump": state.bump,
        "approved": pubkey_container_to_list(state.approved),
        "rejected": pubkey_container_to_list(state.rejected),
        "cancelled": pubkey_container_to_list(state.cancelled),
        "executed_index": state.executed_index,
    }


def ms_ix_account_to_dict(state: Any) -> Dict[str, Any]:
    """Deserialize multisig instruction account to a python dictionary."""
    return {
        "program_id": str(state.program_id),
        "keys": account_meta_container_to_list(state.keys),
        "data": list(state.data),
        "instruction_index": state.instruction_index,
        "bump": state.bump,
        "executed": state.executed,
    }


ACCOUNT_STATE_SERIALIZERS = {
    MultisigAccountType.MS: ms_account_to_dict,
    MultisigAccountType.MS_TRANSACTION: ms_tx_account_to_dict,
    MultisigAccountType.MS_INSTRUCTION: ms_ix_account_to_dict,
}

# Same for mainnet, devnet, testnet
SQUADS_MULTISIG_ADDRESS = "SMPLecH534NA9acpos4G6x7uf3LWbCAwZQE9e8ZekMu"

# Note: When loading contract instances on the ethereum contract packages we use `contract_address`
# argument as the contract addres for the instance being loaded, but in case of squads multisig
# the main contract is defined a factory/proxy. Which means you cannot directly interact with a
# multisig, you'll have to go through the factory contract. So when loading the contract/program
# instance use the `SQUADS_MULTISIG_ADDRESS` (Check the `get_program_state` method for an exmaple).


class SquadsMultisig(Contract):
    """The scaffold contract class for a smart contract."""

    contract_id = PublicId.from_str("valory/squads_multisig:0.1.0")

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
    def get_program_instance(cls, ledger_api: LedgerApi) -> Program:
        """
        Load multisig program instance.

        :param ledger_api: Ledger API instance.
        :return: Program instance for the squads multisig
        """
        program: Program = ledger_api.get_contract_instance(
            contract_interface=cls.contract_interface[ledger_api.identifier],
            contract_address=SQUADS_MULTISIG_ADDRESS,
        ).get("program")
        return program

    @classmethod
    def get_account_state(
        cls,
        ledger_api: LedgerApi,
        contract_address: Pubkey,
        account_type: Union[MultisigAccountType, str],
        program: Optional[Program] = None,
    ) -> JSONLike:
        """
        Get multisig account.

        Returns an object containing metadata for a squads multisig account.

        :param ledger_api: The ledger API object.
        :type ledger_api: LedgerApi
        :param program: The program instance.
        :type program: Program
        :param pda: The public key of the multisig account (Not the vault address).
        :type pda: Pubkey
        :return: The decoded multisig account information.
        :rtype: Any
        """
        account_type = MultisigAccountType(str(account_type))
        contract_address = ledger_api.to_pubkey(contract_address)
        account_info = ledger_api.api.get_account_info(pubkey=contract_address)
        program = program or cls.get_program_instance(ledger_api=ledger_api)
        state = program.account[  # pylint: disable=protected-access
            account_type.value
        ]._coder.accounts.decode(account_info.value.data)
        serializer = ACCOUNT_STATE_SERIALIZERS[account_type]
        return serializer(state=state)

    @classmethod
    def current_tx_index(
        cls,
        ledger_api: LedgerApi,
        contract_address: Pubkey,
        program: Optional[Program] = None,
    ) -> Dict[str, int]:
        """
        Get the current transaction index of a multisig.

        :param ledger_api: The ledger API.
        :type ledger_api: LedgerApi
        :param program: The program instance.
        :type program: Program
        :param multisig_pda: The public key of the multisig account (Not the vault address).
        :type multisig_pda: Pubkey
        :return: The transaction index for the account.
        :rtype: int
        """
        contract_address = ledger_api.to_pubkey(contract_address)
        program = program or cls.get_program_instance(ledger_api=ledger_api)
        account_data = cls.get_account_state(
            ledger_api=ledger_api,
            contract_address=contract_address,
            account_type=MultisigAccountType.MS,
            program=program,
        )
        return {"data": account_data["transaction_index"]}

    @classmethod
    def next_tx_index(
        cls,
        ledger_api: LedgerApi,
        contract_address: Pubkey,
        program: Optional[Program] = None,
    ) -> JSONLike:
        """
        Get the next transaction index of a multisig.

        :param ledger_api: The ledger API.
        :type ledger_api: LedgerApi
        :param program: The program instance.
        :type program: Program
        :param multisig_pda: The public key of the multisig account (Not the vault address).
        :type multisig_pda: Pubkey
        :return: The transaction index for the account.
        :rtype: int
        """
        index = 1 + cls.current_tx_index(
            ledger_api=ledger_api,
            contract_address=contract_address,
            program=program,
        ).pop("data")
        return dict(data=index)

    @classmethod
    def current_ix_index(
        cls,
        ledger_api: LedgerApi,
        contract_address: Pubkey,
        program: Optional[Program] = None,
    ) -> Dict[str, int]:
        """
        Get instruction index for a transaction.

        :param ledger_api: The ledger API.
        :type ledger_api: LedgerApi
        :param program: The program instance.
        :type program: Program
        :param tx_pda: The public key of the transaction account.
        :type tx_pda: Pubkey
        :return: The instruction index for the transaction.
        :rtype: int
        """
        contract_address = ledger_api.to_pubkey(contract_address)
        program = program or cls.get_program_instance(ledger_api=ledger_api)
        account_data = cls.get_account_state(
            ledger_api=ledger_api,
            contract_address=contract_address,
            account_type=MultisigAccountType.MS_TRANSACTION,
            program=program,
        )
        return {"data": account_data["instruction_index"]}

    @classmethod
    def next_ix_index(
        cls,
        ledger_api: LedgerApi,
        contract_address: Pubkey,
        program: Optional[Program] = None,
    ) -> Dict[str, int]:
        """
        Get the next transaction index of a multisig.

        :param ledger_api: The ledger API.
        :type ledger_api: LedgerApi
        :param program: The program instance.
        :type program: Program
        :param multisig_pda: The public key of the multisig account (Not the vault address).
        :type multisig_pda: Pubkey
        :return: The transaction index for the account.
        :rtype: int
        """
        next_ix = 1 + cls.current_ix_index(
            ledger_api=ledger_api,
            contract_address=contract_address,
            program=program,
        ).pop("data")
        return {"data": next_ix}

    @classmethod
    def get_tx_pda(
        cls,
        ledger_api: LedgerApi,
        contract_address: Pubkey,
        tx_index: int,
    ) -> JSONLike:
        """
        Get transaction PDA (Program Derived Address).

        :param ledger_api: The ledger API.
        :type ledger_api: LedgerApi
        :param contract_address: The address of the contract.
        :type contract_address: str
        :param tx_index: The index of the transaction.
        :type tx_index: int
        :param multisig_pda: The public key of the multisig account.
        :type multisig_pda: Pubkey
        :param program_id: The public key of the program.
        :type program_id: Pubkey
        :return: The transaction PDA and nonce.
        :rtype: Tuple[Pubkey, int]
        """
        contract_address = ledger_api.to_pubkey(contract_address)
        program_id = ledger_api.to_pubkey(SQUADS_MULTISIG_ADDRESS)
        seeds = [
            "squad".encode(encoding="utf-8"),
            bytes(contract_address),  # type: ignore
            int(str(tx_index), 10).to_bytes(byteorder="little", length=4),
            "transaction".encode(encoding="utf-8"),
        ]
        data = str(ledger_api.pda(seeds=seeds, program_id=program_id))
        return dict(data=data)

    @classmethod
    def get_ix_pda(
        cls,
        ledger_api: LedgerApi,
        contract_address: Pubkey,
        ix_index: int,
    ) -> Dict[str, Tuple[Pubkey, int]]:
        """Create TX PDA"""
        contract_address = ledger_api.to_pubkey(contract_address)
        program_id = ledger_api.to_pubkey(SQUADS_MULTISIG_ADDRESS)
        return {
            "data": ledger_api.pda(
                seeds=[
                    "squad".encode(encoding="utf-8"),
                    bytes(contract_address),  # type: ignore
                    int(str(ix_index), 10).to_bytes(byteorder="little", length=1),
                    "instruction".encode(encoding="utf-8"),
                ],
                program_id=program_id,
            )
        }

    @classmethod
    def create_transaction_ix(  # pylint: disable=too-many-arguments
        cls,
        ledger_api: LedgerApi,
        contract_address: Pubkey,
        authority_index: int,
        creator: Pubkey,
        tx_pda: Optional[Pubkey] = None,
    ) -> JSONLike:
        """
        Create instruction set for creating a transaction.

        :param ledger_api: The ledger API.
        :type ledger_api: LedgerApi
        :param contract_address: The address of the contract.
        :type contract_address: str
        :param program: The program instance.
        :type program: Program
        :param multisig_pda: The public key of the multisig account.
        :type multisig_pda: Pubkey
        :param authority_index: The index of the authority.
        :type authority_index: int
        :return: The created transaction tx.
        :rtype: JSONLike
        """
        creator = ledger_api.to_pubkey(creator)
        contract_address = ledger_api.to_pubkey(contract_address)
        program = cls.get_program_instance(ledger_api=ledger_api)
        if tx_pda is None:
            tx_pda = cls.get_tx_pda(
                ledger_api=ledger_api,
                contract_address=contract_address,
                tx_index=cls.next_tx_index(
                    ledger_api=ledger_api,
                    contract_address=contract_address,
                    program=program,
                ).pop("data"),
            )
        tx_pda = ledger_api.to_pubkey(tx_pda)
        ix = ledger_api.build_instruction(
            contract_instance=program,
            method_name="create_transaction",
            data=[authority_index],
            accounts={
                "multisig": contract_address,
                "transaction": tx_pda,
                "creator": creator,
                "system_program": ledger_api.system_program,
            },
            remaining_accounts=None,
        )
        return {"recent_blockhash": ledger_api.latest_hash, "ixs": [ix]}

    @classmethod
    def add_instruction_ix(  # pylint: disable=too-many-arguments
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        tx_pda: Pubkey,
        creator: Pubkey,
        ix: Instruction,
        index: Optional[int] = None,
    ) -> JSONLike:
        """Attach instruction"""
        tx_pda = ledger_api.to_pubkey(tx_pda)
        contract_address = ledger_api.to_pubkey(contract_address)
        creator = ledger_api.to_pubkey(creator)
        program = cls.get_program_instance(ledger_api=ledger_api)
        index = index or cls.next_ix_index(
            ledger_api=ledger_api,
            contract_address=contract_address,
            program=program,
        ).pop("data")
        ix_pda = cls.get_ix_pda(
            ledger_api=ledger_api,
            contract_address=tx_pda,
            ix_index=index,
        ).pop("data")
        ix = ledger_api.deserialize_ix(ix)
        incoming_is = program.type["IncomingInstruction"](
            program_id=ix.program_id,
            keys=[
                program.type["MsAccountMeta"](
                    pubkey=account.pubkey,
                    is_signer=account.is_signer,
                    is_writable=account.is_writable,
                )
                for account in ix.accounts
            ],
            data=ix.data,
        )
        ix = ledger_api.build_instruction(
            contract_instance=program,
            method_name="add_instruction",
            data=[incoming_is],
            accounts={
                "multisig": contract_address,
                "transaction": tx_pda,
                "instruction": ix_pda,
                "creator": creator,
                "system_program": ledger_api.system_program,
            },
        )
        return {"recent_blockhash": ledger_api.latest_hash, "ixs": [ix]}

    @classmethod
    def activate_transaction_ix(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        tx_pda: Pubkey,
        creator: Pubkey,
    ) -> JSONLike:
        """Create instruction set for activating a transaction."""
        contract_address = ledger_api.to_pubkey(contract_address)
        tx_pda = ledger_api.to_pubkey(tx_pda)
        creator = ledger_api.to_pubkey(creator)
        program = cls.get_program_instance(ledger_api=ledger_api)
        ix = ledger_api.build_instruction(
            contract_instance=program,
            method_name="activate_transaction",
            data=[],
            accounts={
                "multisig": contract_address,
                "transaction": tx_pda,
                "creator": creator,
            },
        )
        return {"recent_blockhash": ledger_api.latest_hash, "ixs": [ix]}

    @classmethod
    def create_new_transaction_ix(  # pylint: disable=too-many-arguments
        cls,
        ledger_api: LedgerApi,
        contract_address: Pubkey,
        authority_index: int,
        creator: Pubkey,
        ixs: List[Instruction],
        tx_pda: Optional[Pubkey] = None,
    ) -> JSONLike:
        """Create instruction set for creating and activating the transaction with given list of instruction."""
        creator = ledger_api.to_pubkey(creator)
        contract_address = ledger_api.to_pubkey(contract_address)
        program = cls.get_program_instance(ledger_api=ledger_api)
        if tx_pda is not None:
            tx_pda = ledger_api.to_pubkey(tx_pda)
        else:
            tx_pda = cls.get_tx_pda(
                ledger_api=ledger_api,
                contract_address=contract_address,
                tx_index=cls.next_tx_index(
                    ledger_api=ledger_api,
                    contract_address=contract_address,
                    program=program,
                ).pop("data"),
            )

        tx_ixs = []
        create_ix = cls.create_transaction_ix(
            ledger_api=ledger_api,
            contract_address=contract_address,
            authority_index=authority_index,
            creator=creator,
            tx_pda=tx_pda,
        )

        tx_ixs += create_ix["ixs"]
        for index, ix in enumerate(ixs):
            attach_ix = cls.add_instruction_ix(
                ledger_api=ledger_api,
                contract_address=contract_address,
                tx_pda=tx_pda,
                creator=creator,
                ix=ix,
                index=(index + 1),
            )
            tx_ixs += attach_ix["ixs"]

        activate_ix = cls.activate_transaction_ix(
            ledger_api=ledger_api,
            contract_address=contract_address,
            tx_pda=tx_pda,
            creator=creator,
        )
        tx_ixs += activate_ix["ixs"]
        return {"recent_blockhash": ledger_api.latest_hash, "ixs": tx_ixs}

    @classmethod
    def approve_transaction_ix(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        tx_pda: Pubkey,
        member: Pubkey,
    ) -> JSONLike:
        """Create instruction set for approving a transaction."""
        contract_address = ledger_api.to_pubkey(contract_address)
        tx_pda = ledger_api.to_pubkey(tx_pda)
        member = ledger_api.to_pubkey(member)
        program = cls.get_program_instance(ledger_api=ledger_api)
        ix = ledger_api.build_instruction(
            contract_instance=program,
            method_name="approve_transaction",
            data=[],
            accounts={
                "multisig": contract_address,
                "transaction": tx_pda,
                "member": member,
            },
        )
        return {"recent_blockhash": ledger_api.latest_hash, "ixs": [ix]}

    @classmethod
    def execute_transaction_ix(  # pylint: disable=too-many-arguments, too-many-locals
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        tx_pda: Pubkey,
        member: Pubkey,
    ) -> JSONLike:
        """Create instruction set for executing a transaction."""
        contract_address = ledger_api.to_pubkey(contract_address)
        tx_pda = ledger_api.to_pubkey(tx_pda)
        member = ledger_api.to_pubkey(member)
        program = cls.get_program_instance(ledger_api=ledger_api)
        ixs = []
        tx_account = cls.get_account_state(
            ledger_api=ledger_api,
            contract_address=tx_pda,
            account_type=MultisigAccountType.MS_TRANSACTION,
            program=program,
        )
        for idx in range(1, tx_account["instruction_index"] + 1):
            ix_pda = cls.get_ix_pda(
                ledger_api=ledger_api,
                contract_address=tx_pda,
                ix_index=idx,
            ).pop("data")
            ix_account = cls.get_account_state(
                ledger_api=ledger_api,
                contract_address=ix_pda,
                account_type=MultisigAccountType.MS_INSTRUCTION,
                program=program,
            )
            ixs.append({"pubkey": ix_pda, "account": ix_account})
        keys = OrderedDict()
        for ix in ixs:
            keys[ix["pubkey"]] = {
                "pubkey": ix["pubkey"],
                "is_signer": False,
                "is_writable": False,
            }
            keys[ledger_api.system_program] = {
                "pubkey": ledger_api.system_program,
                "is_signer": False,
                "is_writable": False,
            }
            for key in ix["account"]["keys"]:
                keys[key["pubkey"]] = {
                    "pubkey": key["pubkey"],
                    "is_signer": False,
                    "is_writable": key["is_writable"],
                }
        ix = ledger_api.build_instruction(
            contract_instance=program,
            method_name="execute_transaction",
            data=[bytes(list(range(len(keys))))],
            accounts={
                "multisig": contract_address,
                "transaction": tx_pda,
                "member": member,
            },
            remaining_accounts=[
                ledger_api.to_account_meta(**key) for key in keys.values()
            ],
        )
        return {"recent_blockhash": ledger_api.latest_hash, "ixs": [ix]}

    @classmethod
    def get_transfer_tx(  # pylint: disable=unused-argument
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        from_pubkey: str,
        to_pubkey: str,
        lamports: int,
    ) -> JSONLike:
        """Get transfer tx."""
        transfer_tx = transfer(
            params=dict(
                from_pubkey=ledger_api.to_pubkey(from_pubkey),
                to_pubkey=ledger_api.to_pubkey(to_pubkey),
                lamports=lamports,
            )
        ).to_json()
        return dict(data=json.loads(transfer_tx))
