import solcx
import json

contractName = "GnosisSafe"
contractRelativePath = "contracts/GnosisSafe.sol"
contractAbsolutePath = f"/home/david/Downloads/{contractRelativePath}"
compiledContractPath = "/home/david/Downloads/contracts/GnosisSafe.json"
optimize = True

# Use this to install all solx versions
# for solc_version in solcx.get_installable_solc_versions():
#     solcx.install_solc(solc_version)

# Load compiled
contractJSON = {}
with open(compiledContractPath, 'r') as fil:
    contractJSON = json.loads(fil.read())

jsonBytecode = contractJSON["bytecode"][2:52]
jsonDeployedBytecode = contractJSON["deployedBytecode"][2:52]

print("608060405273ffffffffffffffffffffffffffffffffffffffff600054167fa blockchain code")
print(f"{jsonBytecode} json bytecode")
print(f"{jsonDeployedBytecode} json deployed bytecode\n")

# Compile
for solc_version in solcx.get_installed_solc_versions():
    if str(solc_version) < "0.7.0":
        continue

    compilation = solcx.compile_files(
        contractAbsolutePath,
        output_values=["abi", "bin-runtime"],
        solc_version=solc_version,
        optimize=optimize
    )

    keyA = f"{contractAbsolutePath}:{contractName}"
    keyB = f"{contractRelativePath}:{contractName}"
    contract_bytecode = ""

    if keyA in compilation:
        contract_bytecode = compilation[keyA]['bin-runtime']
    elif keyB in compilation:
        contract_bytecode = compilation[keyB]['bin-runtime']

    print(f"{contract_bytecode[:50]} compiled version {solc_version} optimize: {optimize}")
