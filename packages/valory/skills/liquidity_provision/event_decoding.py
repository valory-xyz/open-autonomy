import web3
import sys
import json

root_dir = "/home/david/Valory/repos/contracts-amm"

abi_files = {
    "ERC20PresetFixedSupply": f"{root_dir}/node_modules/@openzeppelin/contracts/build/contracts/ERC20PresetFixedSupply.json",
    "UniswapV2Pair": f"{root_dir}/artifacts/third_party/v2-core/contracts/UniswapV2Pair.sol/UniswapV2Pair.json",
    "WETH": f"{root_dir}/third_party/canonical-weth/build/contracts/WETH9.json",
    "UniswapV2Router02": f"{root_dir}/artifacts/third_party/v2-periphery/contracts/UniswapV2Router02.sol/UniswapV2Router02.json",
    "UniswapV2ERC20": f"{root_dir}/artifacts/third_party/v2-core/contracts/UniswapV2ERC20.sol/UniswapV2ERC20.json",
}

contracts = {
    # "gnosis_safe": {"address": "0x9fE46736679d2D9a65F0992F2272dE9f3c7fa6e0", "abi_file": ""},
    # "gnosis_safe_L2": {"address": "0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512", "abi_file": ""},
    # "gnosis_safe_proxy_factory": {"address": "0x5FbDB2315678afecb367f032d93F642f64180aa3", "abi_file": ""},
    # "gnosis_multisend": {"address": "0x2279B7A0a67DB372996a5FaB50D91eAA73d2eBe6", "abi_file": ""},
    # "safe_proxy": {"address": "0x67C828DC58df857618c88994a4bA6c15f05ebf36", "abi_file": ""},
    # "uniswap_factory": {"address": "0xB7f8BC63BbcaD18155201308C8f3540b07f84F5e", "abi_file": ""},
    "uniswap_router02": {"address": "0xA51c1fc2f0D1a1b8494Ed1FE312d7C3a78Ed91C0", "abi_file": abi_files["UniswapV2Router02"]},
    "A": {"address": "0x0DCd1Bf9A1b36cE34237eEaFef220932846BCD82", "abi_file": abi_files["ERC20PresetFixedSupply"]},
    "B": {"address": "0x9A676e781A523b5d0C0e43731313A708CB607508", "abi_file": abi_files["ERC20PresetFixedSupply"]},
    "LP": {"address": "0x50cd56fb094f8f06063066a619d898475dd3eede", "abi_file": abi_files["UniswapV2ERC20"]},
    "WETH": {"address": "0xDc64a140Aa3E981100a9becA4E685f962f0cF6C9", "abi_file": abi_files["WETH"]},
    "A-WETH": {"address": "0x86A6C37D3E868580a65C723AAd7E0a945E170416", "abi_file": abi_files["UniswapV2Pair"]},
    "B-WETH": {"address": "0x3430fe46bfE23b1fafDe4F7c78481051F7c0E01F", "abi_file": abi_files["UniswapV2Pair"]},
    "A-B": {"address": "0x50CD56fb094F8f06063066a619D898475dD3EedE", "abi_file": abi_files["UniswapV2Pair"]},
}

hardhat_endpoint = "http://127.0.0.1:8545"


if __name__ == "__main__":

    w3 = web3.Web3(web3.Web3.HTTPProvider(hardhat_endpoint))

    if not w3.isConnected():
        print("Not connected!")
        sys.exit()

    tx_hash = "0xd27c8eafeb85a8d94250c0d8ff422a8722fc864bfaa26f3293941776bdc6cb06"
    tx_receipt = w3.eth.get_transaction_receipt(tx_hash)

    contract_key = "LP"
    with open(contracts[contract_key]["abi_file"]) as f:
        token_abi = json.load(f)["abi"]
        contract = w3.eth.contract(address=w3.toChecksumAddress(contracts[contract_key]["address"]), abi=token_abi)

        rich_logs = contract.events.Transfer().processReceipt(tx_receipt)

        for log in rich_logs:
            print(log['args']) # Getting 1000 and 1004 values here. What's that 1004?