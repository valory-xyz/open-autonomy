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

from collections import OrderedDict
from enum import Enum, IntEnum
from typing import Any, Optional, Tuple

from aea.common import JSONLike
from aea.configurations.base import PublicId
from aea.contracts.base import Contract
from aea.crypto.base import LedgerApi


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
    def get_program_instance(
        cls,
        ledger_api: LedgerApi,
        contract_address: Pubkey,
    ) -> Program:
        """Get program instance."""
        program: Program = ledger_api.get_contract_instance(
            contract_interface=cls.contract_interface[ledger_api.identifier],
            contract_address=contract_address,
        ).get("program")
        return program

    @classmethod
    def get_account_state(
        cls,
        ledger_api: LedgerApi,
        contract_address: Pubkey,
        pda: Pubkey,
        account_type: MultisigAccountType,
        program: Optional[Program] = None,
    ) -> Any:
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
        pda = ledger_api.to_pubkey(pda)
        account_info = ledger_api.api.get_account_info(pubkey=pda)
        program = program or cls.get_program_instance(
            ledger_api=ledger_api, contract_address=contract_address
        )
        return program.account[  # pylint: disable=protected-access
            account_type.value
        ]._coder.accounts.decode(account_info.value.data)

    @classmethod
    def current_tx_index(
        cls,
        ledger_api: LedgerApi,
        contract_address: Pubkey,
        multisig_pda: Pubkey,
        program: Optional[Program] = None,
    ) -> int:
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
        multisig_pda = ledger_api.to_pubkey(multisig_pda)
        program = program or cls.get_program_instance(
            ledger_api=ledger_api, contract_address=contract_address
        )
        account_data = cls.get_account_state(
            ledger_api=ledger_api,
            contract_address=contract_address,
            pda=multisig_pda,
            account_type=MultisigAccountType.MS,
            program=program,
        )
        return account_data.transaction_index

    @classmethod
    def current_ix_index(
        cls,
        ledger_api: LedgerApi,
        contract_address: Pubkey,
        tx_pda: Pubkey,
        program: Optional[Program] = None,
    ) -> int:
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
        tx_pda = ledger_api.to_pubkey(tx_pda)
        program = program or cls.get_program_instance(
            ledger_api=ledger_api, contract_address=contract_address
        )
        account_data = cls.get_account_state(
            ledger_api=ledger_api,
            contract_address=contract_address,
            pda=tx_pda,
            account_type=MultisigAccountType.MS_TRANSACTION,
            program=program,
        )
        return account_data.instruction_index

    @classmethod
    def get_tx_pda(
        cls,
        ledger_api: LedgerApi,
        contract_address: Pubkey,
        tx_index: int,
        multisig_pda: Pubkey,
    ) -> Tuple[Pubkey, int]:
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
        multisig_pda = ledger_api.to_pubkey(multisig_pda)
        program_id = ledger_api.to_pubkey(contract_address)
        return ledger_api.pda(
            seeds=[
                "squad".encode(encoding="utf-8"),
                bytes(multisig_pda),  # type: ignore
                int(str(tx_index), 10).to_bytes(byteorder="little", length=4),
                "transaction".encode(encoding="utf-8"),
            ],
            program_id=program_id,
        )

    @classmethod
    def get_ix_pda(
        cls,
        ledger_api: LedgerApi,
        contract_address: Pubkey,
        ix_index: int,
        tx_pda: Pubkey,
    ) -> Tuple[Pubkey, int]:
        """Create TX PDA"""
        tx_pda = ledger_api.to_pubkey(tx_pda)
        program_id = ledger_api.to_pubkey(contract_address)
        return ledger_api.pda(
            seeds=[
                "squad".encode(encoding="utf-8"),
                bytes(tx_pda),  # type: ignore
                int(str(ix_index), 10).to_bytes(byteorder="little", length=1),
                "instruction".encode(encoding="utf-8"),
            ],
            program_id=program_id,
        )

    @classmethod
    def create_transaction_ix(  # pylint: disable=too-many-arguments
        cls,
        ledger_api: LedgerApi,
        contract_address: Pubkey,
        authority_index: int,
        multisig_pda: Pubkey,
        creator: Pubkey,
        tx_pda: Optional[Pubkey] = None,
    ) -> JSONLike:
        """
        Create transaction tx.

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
        multisig_pda = ledger_api.to_pubkey(multisig_pda)
        program = cls.get_program_instance(
            ledger_api=ledger_api, contract_address=contract_address
        )

        if tx_pda is not None:
            tx_pda = ledger_api.to_pubkey(tx_pda)
        else:
            next_tx_index = (
                cls.current_tx_index(
                    ledger_api=ledger_api,
                    contract_address=contract_address,
                    multisig_pda=multisig_pda,
                    program=program,
                )
                + 1
            )
            tx_pda, _ = cls.get_tx_pda(
                ledger_api=ledger_api,
                contract_address=contract_address,
                tx_index=next_tx_index,
                multisig_pda=multisig_pda,
            )
        remaining_accounts = None
        ix = ledger_api.build_instruction(
            contract_instance=program,
            method_name="create_transaction",
            data=[authority_index],
            accounts={
                "multisig": multisig_pda,
                "transaction": tx_pda,
                "creator": creator,
                "system_program": ledger_api.system_program,
            },
            remaining_accounts=remaining_accounts,
        )
        return {"recent_blockhash": ledger_api.latest_hash, "ixs": [ix]}

    @classmethod
    def add_instruction_ix(  # pylint: disable=too-many-arguments
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        tx_pda: Pubkey,
        multisig_pda: Pubkey,
        creator: Pubkey,
        ix: Instruction,
        ix_index: Optional[int] = None,
    ) -> JSONLike:
        """Attach instruction"""
        tx_pda = ledger_api.to_pubkey(tx_pda)
        multisig_pda = ledger_api.to_pubkey(multisig_pda)
        creator = ledger_api.to_pubkey(creator)
        program = cls.get_program_instance(
            ledger_api=ledger_api,
            contract_address=contract_address,
        )
        ix_index = (
            (ix_index - 1)
            if ix_index is not None
            else cls.current_ix_index(
                ledger_api=ledger_api,
                contract_address=contract_address,
                tx_pda=tx_pda,
                program=program,
            )
        )
        next_ix_index = ix_index + 1
        ix_pda, _ = cls.get_ix_pda(
            ledger_api=ledger_api,
            contract_address=contract_address,
            ix_index=next_ix_index,
            tx_pda=tx_pda,
        )
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
                "multisig": multisig_pda,
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
        multisig_pda: Pubkey,
        tx_pda: Pubkey,
        creator: Pubkey,
    ) -> JSONLike:
        """Activate transaction."""
        multisig_pda = ledger_api.to_pubkey(multisig_pda)
        tx_pda = ledger_api.to_pubkey(tx_pda)
        creator = ledger_api.to_pubkey(creator)
        program = cls.get_program_instance(
            ledger_api=ledger_api,
            contract_address=contract_address,
        )
        ix = ledger_api.build_instruction(
            contract_instance=program,
            method_name="activate_transaction",
            data=[],
            accounts={
                "multisig": multisig_pda,
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
        multisig_pda: Pubkey,
        creator: Pubkey,
        ix: Instruction,
    ) -> JSONLike:
        """Create instruction set for creating and activating the transaction with given list of instruction."""
        creator = ledger_api.to_pubkey(creator)
        multisig_pda = ledger_api.to_pubkey(multisig_pda)
        program = cls.get_program_instance(
            ledger_api=ledger_api, contract_address=contract_address
        )
        next_tx_index = (
            cls.current_tx_index(
                ledger_api=ledger_api,
                contract_address=contract_address,
                multisig_pda=multisig_pda,
                program=program,
            )
            + 1
        )
        tx_pda, _ = cls.get_tx_pda(
            ledger_api=ledger_api,
            contract_address=contract_address,
            tx_index=next_tx_index,
            multisig_pda=multisig_pda,
        )

        ixs = []
        create_ix = cls.create_transaction_ix(
            ledger_api=ledger_api,
            contract_address=contract_address,
            authority_index=authority_index,
            multisig_pda=multisig_pda,
            creator=creator,
            tx_pda=tx_pda,
        )
        ixs += create_ix["ixs"]

        attach_ix = cls.add_instruction_ix(
            ledger_api=ledger_api,
            contract_address=contract_address,
            tx_pda=tx_pda,
            multisig_pda=multisig_pda,
            creator=creator,
            ix=ix,
            ix_index=1,
        )
        ixs += attach_ix["ixs"]

        activate_ix = cls.activate_transaction_ix(
            ledger_api=ledger_api,
            contract_address=contract_address,
            multisig_pda=multisig_pda,
            tx_pda=tx_pda,
            creator=creator,
        )
        ixs += activate_ix["ixs"]

        return {"recent_blockhash": ledger_api.latest_hash, "ixs": ixs}

    @classmethod
    def approve_transaction_ix(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        multisig_pda: Pubkey,
        tx_pda: Pubkey,
        creator: Pubkey,
    ) -> JSONLike:
        """Approve transaction."""
        multisig_pda = ledger_api.to_pubkey(multisig_pda)
        tx_pda = ledger_api.to_pubkey(tx_pda)
        creator = ledger_api.to_pubkey(creator)
        program = cls.get_program_instance(
            ledger_api=ledger_api,
            contract_address=contract_address,
        )
        ix = ledger_api.build_instruction(
            contract_instance=program,
            method_name="approve_transaction",
            data=[],
            accounts={
                "multisig": multisig_pda,
                "transaction": tx_pda,
                "member": creator,
            },
        )
        return {"recent_blockhash": ledger_api.latest_hash, "ixs": [ix]}

    @classmethod
    def execute_transaction_ix(  # pylint: disable=too-many-arguments, too-many-locals
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        multisig_pda: Pubkey,
        tx_pda: Pubkey,
        creator: Pubkey,
    ) -> JSONLike:
        """Execute transaction."""
        multisig_pda = ledger_api.to_pubkey(multisig_pda)
        tx_pda = ledger_api.to_pubkey(tx_pda)
        creator = ledger_api.to_pubkey(creator)
        program = cls.get_program_instance(
            ledger_api=ledger_api, contract_address=contract_address
        )

        ixs = []
        tx_account = cls.get_account_state(
            ledger_api=ledger_api,
            contract_address=contract_address,
            pda=tx_pda,
            account_type=MultisigAccountType.MS_TRANSACTION,
            program=program,
        )
        for idx in range(1, tx_account.instruction_index + 1):
            ix_pda, _ = cls.get_ix_pda(
                ledger_api=ledger_api,
                contract_address=contract_address,
                ix_index=idx,
                tx_pda=tx_pda,
            )
            ix_account = cls.get_account_state(
                ledger_api=ledger_api,
                contract_address=contract_address,
                pda=ix_pda,
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
            for key in ix["account"].keys:
                keys[key.pubkey] = {
                    "pubkey": key.pubkey,
                    "is_signer": False,
                    "is_writable": key.is_writable,
                }

        ix = ledger_api.build_instruction(
            contract_instance=program,
            method_name="execute_transaction",
            data=[bytes(list(range(len(keys))))],
            accounts={
                "multisig": multisig_pda,
                "transaction": tx_pda,
                "member": creator,
            },
            remaining_accounts=[
                ledger_api.to_account_meta(**key) for key in keys.values()
            ],
        )
        return {"recent_blockhash": ledger_api.latest_hash, "ixs": [ix]}
