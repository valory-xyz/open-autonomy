#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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
Read the full transaction history and show the ERC20 transfer events in a human-readable format for a set of known accounts.

To run with a Hardhat integration test, set a breakpoint before the test ends to avoid the local chain being destroyed and Hardhat stopped.
"""
import json
import sys
from enum import Enum
from typing import Optional, cast

from hexbytes import HexBytes
from web3 import Web3
from web3.logs import IGNORE


HARDHAT_ENDPOINT = "http://127.0.0.1:8545"
HARDHAT_DEFAULT_MNEMONIC = "test test test test test test test test test test test junk"
ERC20_ABI = "../third_party/contracts-amm/node_modules/@openzeppelin/contracts/build/contracts/ERC20PresetFixedSupply.json"


class Color(Enum):
    """Standard terminal color codes."""

    GREEN = "\033[32m"
    RESET = "\033[39m"


# These Hardhat addresses are assigned in the contracts-amm deployment.
hardhat_account_indices_to_names = {
    0: "token_A_issuer",
    1: "token_B_issuer",
    10: "safe_owner_1",
    11: "safe_owner_2",
    12: "safe_owner_3",
    13: "safe_owner_4",
}

# Known addresses from out Hardhat deployment
# It would be nice to have automatic derivation for these ones as we do for Hardhat default accounts.
account_names_to_addresses = {
    "gnosis_safe": "0x9fE46736679d2D9a65F0992F2272dE9f3c7fa6e0",
    "gnosis_safe_L2": "0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512",
    "gnosis_safe_proxy_factory": "0x5FbDB2315678afecb367f032d93F642f64180aa3",
    "gnosis_multisend": "0x2279B7A0a67DB372996a5FaB50D91eAA73d2eBe6",
    "safe_proxy": "0x67C828DC58df857618c88994a4bA6c15f05ebf36",
    "uniswap_factory": "0xB7f8BC63BbcaD18155201308C8f3540b07f84F5e",
    "uniswap_router02": "0xA51c1fc2f0D1a1b8494Ed1FE312d7C3a78Ed91C0",
    "token_A": "0x0DCd1Bf9A1b36cE34237eEaFef220932846BCD82",
    "token_B": "0x9A676e781A523b5d0C0e43731313A708CB607508",
    "token_LP": "0x50cd56fb094f8f06063066a619d898475dd3eede",
    "token_WETH": "0xDc64a140Aa3E981100a9becA4E685f962f0cF6C9",
    "A_WETH_pool": "0x86A6C37D3E868580a65C723AAd7E0a945E170416",
    "B_WETH_pool": "0x3430fe46bfE23b1fafDe4F7c78481051F7c0E01F",
    "minter": "0x0000000000000000000000000000000000000000",
    "safe": "0x68FCdF52066CcE5612827E872c45767E5a1f6551",
    "defaultFallbackHandlerContractName": "0xCf7Ed3AccA5a467e9e704C703E8D87F634fB0Fc9",
    "SimulateTxAccessor": "0x5FC8d32690cc91D4c39d9d3abcBD16989F875707",
    "CompatibilityFallbackHandler": "0x0165878A594ca255338adfa4d48449f69242Eb8F",
    "CreateCall": "0xa513E6E4b8f2a923D98304ec87F64353C4D5C853",
    "MultiSendCallOnly": "0x8A791620dd6260079BF849Dc5567aDC3F2FdC318",
    "SignMessageLib": "0x610178dA211FEF7D417bC0e6FeD39F05609AD788",
}


def get_tx_tag(tx_logs: dict) -> str:
    """Identifies known transactions as ENTER_POOL, EXIT_POOL or SWAP_BACK.

    :param tx_logs: the transfer logs
    :return: the transaction tag
    """
    for log in tx_logs:
        if "errors" not in log:

            # If a tx has a LP_token transfer from the minter to the safe we flag it as ENTER_POOL
            if (
                log["args"]["from"] == account_names_to_addresses["minter"]
                and log["args"]["to"] == account_names_to_addresses["safe"]
                and log["address"] == account_names_to_addresses["token_LP"]
            ):
                return (
                    Color.GREEN.value + "ENTER_POOL" + Color.RESET.value
                )  # Using standard colored output

            # If a tx has a LP_token transfer from the safe to the LP pool we flag it as EXIT_POOL
            if (
                log["args"]["from"] == account_names_to_addresses["safe"]
                and log["args"]["to"] == account_names_to_addresses["token_LP"]
                and log["address"] == account_names_to_addresses["token_LP"]
            ):
                return (
                    Color.GREEN.value + "EXIT_POOL" + Color.RESET.value
                )  # Using standard colored output

            # If a tx has a token_A transfer from the pool to the safe we flag it as SWAP_BACK
            if (
                log["args"]["from"] == account_names_to_addresses["safe"]
                and log["args"]["to"] == account_names_to_addresses["A_WETH_pool"]
                and log["address"] == account_names_to_addresses["token_A"]
            ):
                return (
                    Color.GREEN.value + "SWAP_BACK" + Color.RESET.value
                )  # Using standard colored output

    return "N/A"


def get_address_name(address: Optional[str]) -> str:
    """Return the address name for known accounts.

    :param address: the address
    :return: the aaddress name
    """
    if address is None:
        return "none"
    address = cast(str, Web3.toChecksumAddress(address))
    return (
        addresses_to_account_names[address]
        if address in addresses_to_account_names
        else address
    )


if __name__ == "__main__":

    # Connect to HardHat
    w3 = Web3(Web3.HTTPProvider(HARDHAT_ENDPOINT))

    if not w3.isConnected():
        print("Not connected!")
        sys.exit()

    # Enable features to derive addresses
    w3.eth.account.enable_unaudited_hdwallet_features()

    # Checksum the addresses
    for acount_name in account_names_to_addresses.keys():
        account_names_to_addresses[acount_name] = Web3.toChecksumAddress(
            account_names_to_addresses[acount_name]
        )

    # Add the 20 Hardhat default accounts to known addresses
    for i in range(20):
        account = w3.eth.account.from_mnemonic(
            HARDHAT_DEFAULT_MNEMONIC, account_path=f"m/44'/60'/0'/0/{i}"
        )
        acount_name = (
            hardhat_account_indices_to_names[i]
            if i in hardhat_account_indices_to_names
            else f"hardhat_address_{i}"
        )
        account_names_to_addresses[acount_name] = Web3.toChecksumAddress(
            account.address
        )

    # Create the dict address -> account name
    addresses_to_account_names = {v: k for k, v in account_names_to_addresses.items()}

    # Load the ERC20 contract
    with open(ERC20_ABI, encoding="utf-8") as abi_file:
        erc_20_token_abi = json.load(abi_file)["abi"]
        erc_20_contract = w3.eth.contract(
            address=w3.toChecksumAddress(account_names_to_addresses["token_A"]),
            abi=erc_20_token_abi,
        )

    # Get all transactions and receipts in all blocks
    last_block_number = w3.eth.get_block("latest")["number"]

    table_header = f"{'FROM':<18}      {'TO':<18}  {'TOKEN VALUE':<14} {'TOKEN':<16}"

    for i in range(last_block_number + 1):
        block = w3.eth.get_block(i)

        for tx_hash in block["transactions"]:
            tx = w3.eth.get_transaction(cast(HexBytes, tx_hash))
            tx_receipt = w3.eth.get_transaction_receipt(cast(HexBytes, tx_hash))

            if tx_receipt is None:
                raise ValueError

            # Get the ERC20 transfer logs
            transfer_logs = erc_20_contract.events.Transfer().processReceipt(
                tx_receipt, IGNORE
            )

            # Identify known transactions
            tx_tag = get_tx_tag(transfer_logs)

            # Print the transaction info
            from_address = get_address_name(tx["from"])  # type: ignore
            to_address = get_address_name(tx["to"])  # type: ignore

            print()
            print(f"{'-'*75} Transaction {tx_hash.hex()}")  # type: ignore
            print(
                f"{table_header} from: {from_address}  | to: {to_address}  |  ETH value: {tx.value}"  # type: ignore
            )
            print(f"{' '*75} nonce: {tx.nonce}  |  block: {i}  |  tag: {tx_tag}")  # type: ignore
            print(
                f"{' '*75} gas used: {tx_receipt['gasUsed']}  |  gas limit: {tx.gas}  |  gas price: {tx.gasPrice}"  # type: ignore
            )

            # Print the tranfer events
            for tx_log in transfer_logs:
                if "errors" not in tx_log:
                    from_address = get_address_name(tx_log["args"]["from"])
                    to_address = get_address_name(tx_log["args"]["to"])
                    token = get_address_name(tx_log["address"])
                    value = tx_log["args"]["value"]
                    print(
                        f"{from_address:<18} ->   {to_address:<18}: {value:<14} {token:<16}"
                    )
