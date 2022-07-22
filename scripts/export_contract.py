import json

with open("/home/david/Descargas/IUniswapV2ERC20.json", "r") as abi_file:
    abi = json.load(abi_file)
    # print(abi)


functions = list(filter(
    lambda x: x["type"] == "function" and not x["name"].isupper(),  # skip DOMAIN_SEPARATOR, PERMIT_TYPEHASH
    abi["abi"]
))

functions = {f["name"]: f for f in functions}

# print([i["name"] for i in functions])

print(functions)