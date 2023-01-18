# `autonomy mint`

Toos to mint components on chain

### Options

`--use-ethereum`
: Use ethereum to chain profile to interact with the contracts.

`--use-goerli`
: Use goerli to chain profile to interact with the contracts.

`--use-custom-chain`
: Use custom-chain to chain profile to interact with the contracts.

`--use-local`
: Use local to chain profile to interact with the contracts.

`--skip-hash-check`
: Skip hash check when verifying dependencies on chain

### Chain selection

This command group contains tools for minting components, agents and service packages. You can specify what type of chain you want by providing a `--use-CHAINTYPE` flag. The current implementation provides 4 different types of chain to choose from `local`, `goerli`, `ethereum` and `custom` chain. 

If you use the local chain, make sure you have a local hardhat deployment with the required registry contracts deployed. If you want to use a custom chain you'll have to provide the chain parameters as the environment varibles.

Required variables if you want to use a custom chain

- `CUSTOM_COMPONENT_REGISTRY_ADDRESS` : custom `component_registry` contract address
- `CUSTOM_AGENT_REGISTRY_ADDRESS` : custom `agent_registry` contract address
- `CUSTOM_REGISTRIES_MANAGER_ADDRESS` : custom `registries_manager` contract address
- `CUSTOM_SERVICE_MANAGER_ADDRESS` : custom `service_manager` contract address
- `CUSTOM_SERVICE_REGISTRY_ADDRESS` : custom `service_registry` contract address
- `CUSTOM_GNOSIS_SAFE_MULTISIG_ADDRESS` : custom `gnosis_safe_multisig` contract address
- `CUSTOM_CHAIN_RPC` : RPC address
- `CUSTOM_CHAIN_ID` : Chain ID

In the same way, if you want to use chain other than custom and local you'll have to provide the RPC address as following environment variables.

- `GOERLI_CHAIN_RPC` : RPC endpoint for goerli testnet
- `ETHEREUM_CHAIN_RPC` : RPC endpoint for ethereum mainnet

## `autonomy mint protocol/contract/connection/skill`

### Usage

`autonomy mint COMPONENT_TYPE [OPTIONS] PACKAGE_PATH KEYS`

### Options

`--password TEXT`
: Password for key pair

`-d, --dependencies TEXT`
: Dependency for the package

`--nft TEXT`
: IPFS hash for the NFT image

### Examples

You can mint the component directly using `autonomy mint COMPONENT_TYPE PATH_TO_PACKAGE PATH_TO_FUNDED_KEYS`. Additionally you'll have to provide the dependencies if the component have any and an hash poiting to the `NFT` unique to the component. If you're using the local chain, the `NFT` is not required.

For example to mint a skill

`autonomy mint skill PATH_TO_SKILL PATH_TO_FUNDED_KEYS -d DEPENDENCY_ID --nft bafybeiggnad44tftcrenycru2qtyqnripfzitv5yume4szbkl33vfd4abm` 

> Note: the NFT hash used in the example is for demonstration purposes only

## `autonomy mint agent`

### Usage

`autonomy mint agent [OPTIONS] PACKAGE_PATH KEYS`

### Options

`--password TEXT`
: Password for key pair

`-d, --dependencies TEXT`
: Dependency for the package

`--nft TEXT`
: IPFS hash for the NFT image

### Examples

Unlike the components, the agent packages are required to have atleast one dependency to be minted. Otherwise the process is same.

## `autonomy mint service`

### Usage

`autonomy mint service [OPTIONS] PACKAGE_PATH KEYS`

### Options
  
`--password TEXT`
: Password for key pair

`--nft TEXT`
: IPFS hash for the NFT image

`-a, --agent-id INTEGER`
: Canonical agent ID

`-n, --number-of-slots INTEGER`
: Number of agent instances for the agent

`-c, --cost-of-bond INTEGER`
: Cost of bond for the agent (Wei)

`--threshold INTEGER`
: Threshold for the minimum numbers required torun the service

### Examples

Minting a service requires parameters other than the agent dependency, you will have to specify the number of slots and the cost of bond for that agent.

`autonomy mint skill PATH_TO_SKILL PATH_TO_FUNDED_KEYS -a 1 -n 4 -c 1000 --threshold 3 --nft bafybeiggnad44tftcrenycru2qtyqnripfzitv5yume4szbkl33vfd4abm` 

> Note: the NFT hash used in the example is for demonstration purposes only

Number of slots can be any number but the threshold needs to be greater than or equal to `ceil((n * 2 + 1) / 3)`, where `n` is total number of the agents in the service.
