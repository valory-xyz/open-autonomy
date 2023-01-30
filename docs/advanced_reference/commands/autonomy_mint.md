Tools for minting components on-chain.

This command group consists of a number of functionalities to mint components, agents and services to work with the on-chain protocol. See the appropriate subcommands for more information.

## Options

`--use-ethereum`
: Use the Ethereum chain profile to interact with the on-chain registry contracts. This option requires that you define the following environment variable:

    - `ETHEREUM_CHAIN_RPC` : RPC endpoint for the Ethereum mainnet chain.

`--use-goerli`
: Use the Görli chain profile to interact with the on-chain registry contracts. This option requires that you define the following environment variable:

    - `GOERLI_CHAIN_RPC` : RPC endpoint for the Görli testnet chain.

`--use-custom-chain`
: Use the custom-chain chain profile to interact with the on-chain registry contracts. This option requires that you define the following environment variables (see the [Autonolas Protocol section](https://docs.autonolas.network/protocol/) for more information):

    - `CUSTOM_CHAIN_RPC` : RPC endpoint for the custom chain.
    - `CUSTOM_CHAIN_ID` : Chain ID.
    - `CUSTOM_COMPONENT_REGISTRY_ADDRESS` : custom Component Registry
 contract address.
    - `CUSTOM_AGENT_REGISTRY_ADDRESS` : custom Agent Registry contract address.
    - `CUSTOM_REGISTRIES_MANAGER_ADDRESS` : custom Registries Manager contract address.
    - `CUSTOM_SERVICE_MANAGER_ADDRESS` : custom Service Manager contract address.
    - `CUSTOM_SERVICE_REGISTRY_ADDRESS` : custom Service Registry contract address.
    - `CUSTOM_GNOSIS_SAFE_MULTISIG_ADDRESS` : custom Gnosis Safe multisig contract address.

`--use-local`
: Use the local chain profile to interact with the on-chain registry contracts. This option requires that you have a local Hardhat node with the required contracts deployed.

!!! note

    The options `--use-ethereum`, `--use-goerli`, `--use-custom-chain` and `--use-local` are mutually exclusive.

`--skip-hash-check`
: Skip hash check when verifying dependencies on chain.

## `autonomy mint protocol` / `contract` / `connection` / `skill`

Mint a protocol, contract, connection or skill in the on-chain protocol.

### Usage

```bash
autonomy mint protocol [OPTIONS] PACKAGE_PATH KEYS_FILE
autonomy mint contract [OPTIONS] PACKAGE_PATH KEYS_FILE
autonomy mint connection [OPTIONS] PACKAGE_PATH KEYS_FILE
autonomy mint skill [OPTIONS] PACKAGE_PATH KEYS_FILE
```
### Options

`--password PASSWORD`
: Password for the key file.

`-d, --dependencies DEPENDENCY_ID`
: Dependencies for the package.

`--nft NFT_HASH`
: IPFS hash for the NFT image representing the package. Note that if you are using a local chain this option is not required.

### Examples

Mint the `hello_world_abci` {{fsm_app}} skill with dependencies 11 and 42 in a custom chain:

```bash
autonomy mint --use-custom-chain skill -d 11 -d 42 --nft <nft_ipfs_hash> ./packages/valory/skills/hello_world_abci my_keys_file
```

## `autonomy mint agent`

Mint an agent in the on-chain protocol.
### Usage

```bash
autonomy mint agent [OPTIONS] PACKAGE_PATH KEYS_FILE
```

### Options

`--password PASSWORD`
: Password for the key file.

`-d, --dependencies DEPENDENCY_ID`
: Dependencies for the package. In order to be minted, agent packages require at least one dependency.

`--nft NFT_HASH`
: IPFS hash for the NFT image representing the package. Note that if you are using a local chain this option is not required.

### Examples

Mint the `hello_world` agent with dependency 43 in the Ethereum main chain:

```bash
autonomy mint --use-ethereum agent -d 43 --nft <nft_ipfs_hash> ./packages/valory/agents/hello_world my_keys_file
```

## `autonomy mint service`

Mint a service in the on-chain protocol.
### Usage

```bash
autonomy mint service [OPTIONS] PACKAGE_PATH KEYS_FILE
```

### Options
  
`--password PASSWORD`
: Password for the key file.

`--nft NFT_HASH`
: IPFS hash for the NFT image representing the package. Note that if you are using a local chain this option is not required.

`-a, --agent-id AGENT_ID`
: Canonical agent ID.

`-n, --number-of-slots NUM_SLOTS`
: Number of agent instances for the canonical agent.

`-c, --cost-of-bond COST_BOND`
: Cost of bond for the agent (Wei).

`--threshold`
: Threshold for the minimum number of agents required to run the service. The threshold has to be at least $\lceil(2N + 1) / 3\rceil$, where $N$ is total number of the agents in the service.

### Examples

Mint the `hello_world` service with 4 instances of canonical agent ID 84, cost of bond 10000000 Wei and a threshold of 3 agents, in the Ethereum main chain:

```bash
autonomy mint --use-ethereum service -a 84 -n 4 -c 10000000 --threshold 3 --nft <nft_ipfs_hash> ./packages/valory/services/hello_world my_keys_file
```

!!! note

    You can specify more than one type of canonical agent in a service by appropriately defining the triplets `-a`, `-n` and `-c` for each canonical agent ID.