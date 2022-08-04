import json
from cookiecutter.main import cookiecutter
from typing import Dict


def extract_functions_from_build(contract_build_path: str) -> Dict:
    with open(contract_build_path, "r") as abi_file:
        abi = json.load(abi_file)

        functions = list(filter(
            lambda x: x["type"] == "function" and not x["name"].isupper(),  # skip DOMAIN_SEPARATOR, PERMIT_TYPEHASH
            abi["abi"]
        ))

        functions = {f["name"]: f for f in functions}
        return functions


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

    functions = extract_functions_from_build(CONTRACT_BUILD_PATH)

    project_config = {
        "project_slug": CONTRACT_NAME,
        "contract_name": CONTRACT_NAME,
        "contract_vendor": CONTRACT_VENDOR,
        "functions": {
            "functionA": {},
            "functionB": {}
        }
    }

    generate_package(project_config, OUTPUT_DIR)


if __name__ == "__main__":
    main()