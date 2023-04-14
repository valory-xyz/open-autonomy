Tools for minting software packages in the [Autonolas Protocol](https://docs.autonolas.network/protocol/).

This command group consists of a number of functionalities to mint components, agents and services in the [Autonolas Protocol](https://docs.autonolas.network/protocol/). These commands are the CLI alternative to mint packages using the [Autonolas Protocol web app](https://protocol.autonolas.network/). See the appropriate subcommands for more information.

!!! info

    You can specify how you wish to sing the on-chain transactions produced by these commands: either with **a private key stored in a file**, or with a **hardware wallet**. In this latter case, ensure that you have configured properly the drivers for your hardware wallet.

## Options

`--use-ethereum`
: Use the Ethereum chain profile to interact with the Autonolas Protocol registry contracts. This option requires that you define the following environment variable:

    - `ETHEREUM_CHAIN_RPC` : RPC endpoint for the Ethereum mainnet chain.

`--use-goerli`
: Use the Görli chain profile to interact with the Autonolas Protocol registry contracts. This option requires that you define the following environment variable:

    - `GOERLI_CHAIN_RPC` : RPC endpoint for the Görli testnet chain.

`--use-custom-chain`
: Use the custom-chain chain profile to interact with the Autonolas Protocol registry contracts. This option requires that you define the following environment variables (see the [Autonolas Protocol](https://docs.autonolas.network/protocol/) documentation for more information):

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
: Use the local chain profile to interact with the Autonolas Protocol registry contracts. This option requires that you have a local Hardhat node with the required contracts deployed.

!!! note

    The options `--use-ethereum`, `--use-goerli`, `--use-custom-chain` and `--use-local` are mutually exclusive.

`--skip-hash-check`
: Skip hash check when verifying dependencies on chain.

## `autonomy mint protocol` / `contract` / `connection` / `skill`

Mint a protocol, contract, connection or skill in the Autonolas Protocol.

### Usage

```bash
autonomy mint protocol [OPTIONS] PACKAGE_PATH
autonomy mint contract [OPTIONS] PACKAGE_PATH
autonomy mint connection [OPTIONS] PACKAGE_PATH
autonomy mint skill [OPTIONS] PACKAGE_PATH
```
### Options

`--key FILE`
: Use a private key from a file to sign the transactions.

`--hwi`
: Use a hardware wallet to sign the transactions.

`--password PASSWORD`
: Password for the key file.

`-d, --dependencies DEPENDENCY_ID`
: Dependencies for the package.

`--nft IPFS_HASH_OR_IMAGE_PATH`
: IPFS hash or path to the NFT image for the NFT image representing the package. Note that if you are using a local chain this option is not required.

`--owner TEXT`
: Owner address of the package.

### Examples

Mint the `hello_world_abci` {{fsm_app}} skill with dependencies 11 and 42 in a custom chain:

```bash
autonomy mint --use-custom-chain skill -d 11 -d 42 --nft <nft_ipfs_hash_or_image_path> ./packages/valory/skills/hello_world_abci --key my_key.txt
```

Same as above, but using a hardware wallet:

```bash
autonomy mint --use-custom-chain skill -d 11 -d 42 --nft <nft_ipfs_hash_or_image_path> ./packages/valory/skills/hello_world_abci --hwi
```

## `autonomy mint agent`

Mint an agent in the Autonolas Protocol.
### Usage

```bash
autonomy mint agent [OPTIONS] PACKAGE_PATH
```

### Options

`--key FILE`
: Use a private key from a file to sign the transactions.

`--hwi`
: Use a hardware wallet to sign the transactions.

`--password PASSWORD`
: Password for the key file.

`-d, --dependencies DEPENDENCY_ID`
: Dependencies for the package. In order to be minted, agent packages require at least one dependency.

`--nft NFT_HASH`
: IPFS hash for the NFT image representing the package. Note that if you are using a local chain this option is not required.

`--owner TEXT`
: Owner address of the package.

### Examples

Mint the `hello_world` agent with dependency 43 in the Ethereum main chain:

```bash
autonomy mint --use-ethereum agent -d 43 --nft <nft_ipfs_hash_or_image_path> ./packages/valory/agents/hello_world --key my_key.txt
```

Same as above, but using a hardware wallet:

```bash
autonomy mint --use-ethereum agent -d 43 --nft <nft_ipfs_hash_or_image_path> ./packages/valory/agents/hello_world --hwi
```

## `autonomy mint service`

Mint a service in the Autonolas Protocol.
### Usage

```bash
autonomy mint service [OPTIONS] PACKAGE_PATH
```

### Options
  
`--key FILE`
: Use a private key from a file to sign the transactions.

`--hwi`
: Use a hardware wallet to sign the transactions.

`--password PASSWORD`
: Password for the key file.

`--nft IPFS_HASH_OR_IMAGE_PATH`
: IPFS hash or path to the NFT image for the NFT image representing the package. Note that if you are using a local chain this option is not required.

`--owner TEXT`
: Owner address of the package.

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
autonomy mint --use-ethereum service -a 84 -n 4 -c 10000000 --threshold 3 --nft <nft_ipfs_hash_or_image_path> ./packages/valory/services/hello_world --key my_key.txt
```

Same as above, but using a hardware wallet:

```bash
autonomy mint --use-ethereum service -a 84 -n 4 -c 10000000 --threshold 3 --nft <nft_ipfs_hash_or_image_path> ./packages/valory/services/hello_world --hwi
```

!!! note

    You can specify more than one type of canonical agent in a service by appropriately defining the triplets `-a`, `-n` and `-c` for each canonical agent ID.