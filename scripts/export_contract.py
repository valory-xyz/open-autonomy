import json
from cookiecutter.main import cookiecutter
from typing import Dict, Tuple
from datetime import date

type_equivalence = {
    "address": "str",
    "uint256": "int",
    "bytes32": "bytes",
    "uint8": "int",
    "bool": "bool",
}



def extract_functions_from_build(contract_build_path: str) -> Tuple[Dict, Dict]:
    with open(contract_build_path, "r") as abi_file:
        abi = json.load(abi_file)

        functions = list(filter(
            lambda x: x["type"] == "function" and not x["name"].isupper(),  # skip DOMAIN_SEPARATOR, PERMIT_TYPEHASH
            abi["abi"]
        ))

        read_functions = {f["name"]: {i["name"]: type_equivalence[i["type"]] for i in f["inputs"]} for f in functions if f["stateMutability"] == "view"}
        write_functions = {f["name"]: {i["name"]: type_equivalence[i["type"]] for i in f["inputs"]} for f in functions if f["stateMutability"] not in ("view", "pure")}
        return read_functions, write_functions


def generate_package(project_config, output_dir) -> None:
    cookiecutter(
        template='contract_template/',
        extra_context=project_config,  # overwrite config
        output_dir=output_dir,
        overwrite_if_exists=True,
        no_input=True,  # avoid prompt
    )

def main():

    CONTRACT_NAME = "uniswap_v2_erc20_exported"
    CONTRACT_VENDOR = "valory"
    CONTRACT_BUILD_PATH = "/home/david/Descargas/IUniswapV2ERC20.json"
    OUTPUT_DIR = "/home/david/Descargas/"


    read_functions, write_functions = extract_functions_from_build(CONTRACT_BUILD_PATH)

    project_config = {
        "project_slug": CONTRACT_NAME,
        "contract_name": CONTRACT_NAME,
        "contract_vendor": CONTRACT_VENDOR,
        "class_name": "UniswapV2ERC20Contract",
        "read_functions": read_functions,
        "write_functions": write_functions,
        "year": date.today().year,
    }

    generate_package(project_config, OUTPUT_DIR)


if __name__ == "__main__":
    main()