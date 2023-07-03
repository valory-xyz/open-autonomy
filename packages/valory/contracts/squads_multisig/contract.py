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
from enum import IntEnum
from typing import Any

from aea.common import JSONLike
from aea.configurations.base import PublicId
from aea.contracts.base import Contract
from aea.crypto.base import LedgerApi


Pubkey = Any  # defined in solders.pubkey
Program = Any  # defined in anchorpy
Instruction = Any  # defined in solders.instruction


class SquadsMultisig(Contract):
    """The scaffold contract class for a smart contract."""

    class SquadsMultisigAuthorityIndex(IntEnum):
        """Squads multisig authority index list."""

        INTERNAL = 0
        VAULT = 1
        SECONDARY = 2
        PROGRAM_UPGRADE = 3

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
    def get_multisig_account(
        cls,
        ledger_api: LedgerApi,
        program: Program,
        multisig_pda: Pubkey,
    ) -> Any:
        """
        Get multisig account.

        Returns an object containing metadata for a squads multisig account.

        :param ledger_api: The ledger API object.
        :type ledger_api: LedgerApi
        :param program: The program instance.
        :type program: Program
        :param multisig_pda: The public key of the multisig account (Not the vault address).
        :type multisig_pda: Pubkey
        :return: The decoded multisig account information.
        :rtype: Any
        """
        account_info = ledger_api.api.get_account_info(pubkey=multisig_pda)
        # TODO
        # discriminator = _account_discriminator(self._idl_account.name)
        # if discriminator != data[:ACCOUNT_DISCRIMINATOR_SIZE]:
        #     msg = f"Account {address} has an invalid discriminator"
        #     raise AccountInvalidDiscriminator(msg)
        return program.account["Ms"]._coder.accounts.decode(account_info.value.data)

    @classmethod
    def get_tx_index(
        cls,
        ledger_api: LedgerApi,
        program: Program,
        multisig_pda: Pubkey,
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
        account_data = cls.get_multisig_account(
            ledger_api=ledger_api, program=program, multisig_pda=multisig_pda
        )
        return account_data.transaction_index

    @classmethod
    def get_transaction_account(
        cls, ledger_api: LedgerApi, program: Program, tx_pda: Pubkey
    ) -> Any:
        """
        Get transaction account object.

        Returns an decode multisig transaction account object.

        :param ledger_api: The ledger API.
        :type ledger_api: LedgerApi
        :param program: The program instance.
        :type program: Program
        :param tx_pda: The public key of the transaction account.
        :type tx_pda: Pubkey
        :return: The transaction account information.
        :rtype: Any
        """
        account_info = ledger_api.api.get_account_info(pubkey=tx_pda)
        # TODO
        # discriminator = _account_discriminator(self._idl_account.name)
        # if discriminator != data[:ACCOUNT_DISCRIMINATOR_SIZE]:
        #     msg = f"Account {address} has an invalid discriminator"
        #     raise AccountInvalidDiscriminator(msg)
        return program.account["MsTransaction"]._coder.accounts.decode(
            account_info.value.data
        )

    @classmethod
    def get_ix_index(
        cls, ledger_api: LedgerApi, program: Program, tx_pda: Pubkey
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
        account_data = cls.get_transaction_account(
            ledger_api=ledger_api, program=program, tx_pda=tx_pda
        )
        return account_data.instruction_index

    @classmethod
    def get_instruction_account(
        cls, ledger_api: LedgerApi, program: Program, ix_pda: Pubkey
    ) -> Any:
        """
        Get instruction account.

        Returns an object containing decoded data from a instruction account.

        :param ledger_api: The ledger API.
        :type ledger_api: LedgerApi
        :param program: The program instance.
        :type program: Program
        :param ix_pda: The public key of the instruction account.
        :type ix_pda: Pubkey
        :return: The instruction account information.
        :rtype: Any
        """
        account_info = ledger_api.api.get_account_info(pubkey=ix_pda)
        # TODO
        # discriminator = _account_discriminator(self._idl_account.name)
        # if discriminator != data[:ACCOUNT_DISCRIMINATOR_SIZE]:
        #     msg = f"Account {address} has an invalid discriminator"
        #     raise AccountInvalidDiscriminator(msg)
        return program.account["MsInstruction"]._coder.accounts.decode(
            account_info.value.data
        )

    @classmethod
    def get_tx_pda(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        tx_index: int,
        multisig_pda: Pubkey,
        program_id: Pubkey,
    ) -> Pubkey:
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
        :return: The transaction PDA.
        :rtype: Pubkey
        """
        return Pubkey.find_program_address(
            seeds=[
                "squad".encode(encoding="utf-8"),
                bytes(multisig_pda),
                int(str(tx_index), 10).to_bytes(byteorder="little", length=4),
                "transaction".encode(encoding="utf-8"),
            ],
            program_id=program_id,
        )

    @classmethod
    def create_transaction_tx(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        authority_index: int,
        multisig_pda: Pubkey,
        creator: Pubkey,
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
        creator = ledger_api.to_keypair(creator)  # TODO: To be implemented on plugin
        program: Program = ledger_api.get_contract_instance(
            contract_interface=cls.contract_interface,
            contract_address=str(contract_address),
        ).get("program")
        program.provider.wallet = creator.entity

        tx_index = cls.get_tx_index(
            ledger_api=ledger_api, program=program, multisig_pda=multisig_pda
        )
        next_tx_index = tx_index + 1
        tx_pda, _ = cls.get_tx_pda(
            multisig_pda,
            next_tx_index,
            ledger_api.to_pubkey(contract_address),  # TODO: To be implemented on plugin
        )
        method_name = "create_transaction"
        data = [authority_index]
        accounts = {
            "multisig": multisig_pda,
            "transaction": tx_pda,
            "creator": creator.pubkey(),
            "system_program": ledger_api.system_program,  # TODO: To be implemented on plugin
        }
        remaining_accounts = None
        solders_tx = program.transaction[method_name](
            *data,
            ctx=ledger_api.create_context(  # TODO: To be implemented on plugin
                accounts=accounts, remaining_accounts=remaining_accounts
            ),
            payer=creator.entity,
            blockhash=ledger_api.recent_block_hash(),  # TODO: To be implemented on plugin
        )
        return ledger_api.serialize_to_dict(
            solders_tx
        )  # TODO: To be implemented on plugin

    @classmethod
    def add_instruction_tx(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        tx_pda: Pubkey,
        multisig_pda: Pubkey,
        creator: Pubkey,
        ix: Instruction,
    ) -> JSONLike:
        """Attach instruction"""
        creator = ledger_api.to_keypair(creator)  # TODO: To be implemented on plugin
        program: Program = ledger_api.get_contract_instance(
            contract_interface=cls.contract_interface,
            contract_address=str(contract_address),
        ).get("program")
        program.provider.wallet = creator.entity

        # Prepare instruction index, pda

        ix_index = cls.get_ix_index(
            ledger_api=ledger_api,
            program=program,
            tx_pda=tx_pda,
        )
        next_ix_index = ix_index + 1
        ix_pda, _ = cls.get_ix_pda(
            tx_pda=tx_pda,
            ix_index=next_ix_index,
            program_id=ledger_api.to_pubkey(
                contract_address
            ),  # TODO: To be implemented on plugin
        )

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
        method_name = "add_instruction"
        data = [incoming_is]
        accounts = {
            "multisig": multisig_pda,
            "transaction": tx_pda,
            "instruction": ix_pda,
            "creator": creator.pubkey(),  # Correct
            "system_program": ledger_api.system_program,  # TODO: To be implemented on plugin
        }
        remaining_accounts = None
        solders_tx = program.transaction[method_name](
            *data,
            ctx=ledger_api.create_context(  # TODO: To be implemented on plugin
                accounts=accounts, remaining_accounts=remaining_accounts
            ),
            payer=creator.entity,
            blockhash=ledger_api.recent_block_hash(),  # TODO: To be implemented on plugin
        )
        return ledger_api.serialize_to_dict(
            solders_tx
        )  # TODO: To be implemented on plugin

    @classmethod
    def activate_transaction_tx(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        multisig_pda: Pubkey,
        tx_pda: Pubkey,
        creator: Pubkey,
    ) -> JSONLike:
        """Activate transaction."""
        creator = ledger_api.to_keypair(creator)  # TODO: To be implemented on plugin
        program: Program = ledger_api.get_contract_instance(
            contract_interface=cls.contract_interface,
            contract_address=str(contract_address),
        ).get("program")
        program.provider.wallet = creator.entity

        method_name = "activate_transaction"
        data = []
        accounts = {
            "multisig": multisig_pda,
            "transaction": tx_pda,
            "creator": creator.pubkey(),  # Correct
        }
        remaining_accounts = None
        solders_tx = program.transaction[method_name](
            *data,
            ctx=ledger_api.create_context(  # TODO: To be implemented on plugin
                accounts=accounts, remaining_accounts=remaining_accounts
            ),
            payer=creator.entity,
            blockhash=ledger_api.recent_block_hash(),  # TODO: To be implemented on plugin
        )
        return ledger_api.serialize_to_dict(
            solders_tx
        )  # TODO: To be implemented on plugin

    @classmethod
    def approve_transaction_tx(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        multisig_pda: Pubkey,
        tx_pda: Pubkey,
        creator: Pubkey,
    ) -> JSONLike:
        """Approve transaction."""
        creator = ledger_api.to_keypair(creator)  # TODO: To be implemented on plugin
        program: Program = ledger_api.get_contract_instance(
            contract_interface=cls.contract_interface,
            contract_address=str(contract_address),
        ).get("program")
        program.provider.wallet = creator.entity

        method_name = "approve_transaction"
        data = []
        accounts = {
            "multisig": multisig_pda,
            "transaction": tx_pda,
            "member": creator.pubkey(),
        }
        remaining_accounts = None
        solders_tx = program.transaction[method_name](
            *data,
            ctx=ledger_api.create_context(  # TODO: To be implemented on plugin
                accounts=accounts, remaining_accounts=remaining_accounts
            ),
            payer=creator.entity,
            blockhash=ledger_api.recent_block_hash(),  # TODO: To be implemented on plugin
        )
        return ledger_api.serialize_to_dict(
            solders_tx
        )  # TODO: To be implemented on plugin

    @classmethod
    def execute_transaction_tx(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        multisig_pda: Pubkey,
        tx_pda: Pubkey,
    ) -> JSONLike:
        """Execute transaction."""
        creator = ledger_api.to_keypair(creator)  # TODO: To be implemented on plugin
        program: Program = ledger_api.get_contract_instance(
            contract_interface=cls.contract_interface,
            contract_address=str(contract_address),
        ).get("program")
        program.provider.wallet = creator.entity

        ixs = []
        tx_account = cls.get_transaction_account(
            ledger_api=ledger_api,
            program=program,
            tx_pda=tx_pda,
        )
        for idx in range(1, tx_account.instruction_index + 1):
            ix_pda, _ = cls.get_ix_pda(
                tx_pda=tx_pda,
                ix_index=idx,
                program_id=ledger_api.to_pubkey(
                    contract_address
                ),  # TODO: To be implemented on plugin
            )
            ix_account = cls.get_instruction_account(
                ledger_api=ledger_api, program=program, ix_pda=ix_pda
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

        method_name = "execute_transaction"
        data = [bytes(list(range(len(keys))))]
        accounts = {
            "multisig": multisig_pda,
            "transaction": tx_pda,
            "member": creator.pubkey(),
        }
        remaining_accounts = [
            ledger_api.to_account_meta(**key)  # TODO: To be implemented on plugin
            for key in keys.values()
        ]
        solders_tx = program.transaction[method_name](
            *data,
            ctx=ledger_api.create_context(  # TODO: To be implemented on plugin
                accounts=accounts, remaining_accounts=remaining_accounts
            ),
            payer=creator.entity,
            blockhash=ledger_api.recent_block_hash(),  # TODO: To be implemented on plugin
        )
        return ledger_api.serialize_to_dict(
            solders_tx
        )  # TODO: To be implemented on plugin
