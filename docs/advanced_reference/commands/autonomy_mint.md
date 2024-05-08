Tools for minting software packages in the {{ autonolas_protocol }}.

This command group consists of a number of functionalities to mint components, agents and services in the {{ autonolas_protocol }}. These commands are the CLI alternative to mint packages using the {{ autonolas_protocol_registry_dapp }}. See the appropriate subcommands for more information.

!!! info

    You can specify how you wish to sign the on-chain transactions produced by these commands: either with **a private key stored in a file**, or with a **hardware wallet**. In this latter case, ensure that you have configured properly the drivers for your hardware wallet.

## Options

`--dry-run`
: Perform a dry run for the transaction.

`--use-celo`                      
:   Use the `Celo` chain profile to interact with the Autonolas Protocol registry contracts.

`--use-base-sepolia`              
:   Use the `Base Sepolia` profile to interact with the Autonolas Protocol registry contracts.

`--use-base`                      
:   Use the `Base` chain profile to interact with the Autonolas Protocol registry contracts.

`--use-optimistic-sepolia`        
:   Use the `Optimistic Sepolia` chain profile to interact with the Autonolas Protocol registry contracts.

`--use-optimistic`                
:   Use the `Optimistic` chain profile to interact with the Autonolas Protocol registry contracts.

`--use-arbitrum-sepolia`          
:   Use the `Arbitrum Sepolia` chain profile to interact with the Autonolas Protocol registry contracts.

`--use-arbitrum-one`              
:   Use the `Arbitrum One` chain profile to interact with the Autonolas Protocol registry contracts.

`--use-chiado`                    
:   Use the `Chiado` chain profile to interact with the Autonolas Protocol registry contracts.

`--use-gnosis`                    
:   Use the `Gnosis` chain profile to interact with the Autonolas Protocol registry contracts.

`--use-polygon-mumbai`            
:   Use the `Polygon Mumbai` chain profile to interact with the Autonolas Protocol registry contracts.

`--use-polygon`                   
:   Use the `Polygon` chain profile to interact with the Autonolas Protocol registry contracts.

`--use-ethereum`
:   Use the `Ethereum` chain profile to interact with the Autonolas Protocol registry contracts.

`--use-goerli`                    
:   Use the `Goerli` chain profile to interact with the Autonolas Protocol registry contracts.

To use these chain profile, you will have to export an environment variable for RPC in `<CHAIN_NAME>_CHAIN_RPC` format. For example if you want to use `ethereum`, you will have to export `ETHEREUM_CHAIN_RPC` and for `polygon-mumbai` it would be `POLYGON_MUMBAI_CHAIN_RPC`

`--use-custom-chain`
: Use the custom-chain profile to interact with the Autonolas Protocol registry contracts. This profile requires that you define some parameters and [contract addresses](../on_chain_addresses.md) as environment variables (see also the {{ autonolas_protocol }} documentation for more information):

    - `CUSTOM_CHAIN_RPC` : RPC endpoint for the custom chain.
    - `CUSTOM_CHAIN_ID` : chain ID.
    - `CUSTOM_COMPONENT_REGISTRY_ADDRESS` : Custom Component Registry contract address.
    - `CUSTOM_AGENT_REGISTRY_ADDRESS` : Custom Agent Registry contract address.
    - `CUSTOM_REGISTRIES_MANAGER_ADDRESS` : Custom Registries Manager contract address.
    - `CUSTOM_SERVICE_MANAGER_ADDRESS` : Custom Service Manager contract address.
    - `CUSTOM_SERVICE_REGISTRY_ADDRESS` : Custom Service Registry contract address.
    - `CUSTOM_GNOSIS_SAFE_PROXY_FACTORY_ADDRESS` : Custom Gnosis Safe multisig contract address.
    - `CUSTOM_GNOSIS_SAFE_SAME_ADDRESS_MULTISIG_ADDRESS` : Custom Gnosis Safe Same Address Multisig address.
    - `CUSTOM_SERVICE_REGISTRY_TOKEN_UTILITY_ADDRESS` : Custom Service Registry Token Utility address.
    - `CUSTOM_MULTISEND_ADDRESS` : Custom Multisend address.

!!! note
    For L2 chains you are only required to set
    - `CUSTOM_SERVICE_MANAGER_ADDRESS`,
    - `CUSTOM_SERVICE_REGISTRY_ADDRESS`,
    - `CUSTOM_GNOSIS_SAFE_PROXY_FACTORY_ADDRESS`,
    - `CUSTOM_GNOSIS_SAFE_SAME_ADDRESS_MULTISIG_ADDRESS` and
    - `CUSTOM_MULTISEND_ADDRESS`.

`--use-local`
: Use the local chain profile to interact with the Autonolas Protocol registry contracts. This option requires that you have a local Hardhat node with the required contracts deployed.

!!! note

    The chain profile flags are mutually exclusive.

`-t, --timeout FLOAT`
: Timeout for on-chain interactions

`-r, --retries INTEGER`
: Max retries for on-chain interactions

`--sleep FLOAT`
: Sleep period between retries

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

`--nft IPFS_HASH_OR_IMAGE_PATH`
: IPFS hash or path to the image for the NFT representing the package. Note that if you are using a local chain this option is not required.

`--owner OWNER_ADDRESS`
: Owner address of the package.

`--update TOKEN_ID`
: Update the existing minted token with the latest package hash.

### Examples

Mint the `abstract_abci` skill in a local chain:

```bash
autonomy mint --use-local skill --key my_key.txt --nft <nft_ipfs_hash_or_image_path> --owner <owner_address> ./packages/valory/skills/abstract_abci
```

Same as above, but using a hardware wallet:

```bash
autonomy mint --use-local skill --hwi --nft <nft_ipfs_hash_or_image_path> --owner <owner_address> ./packages/valory/skills/abstract_abci
```

Update the minted `abstract_abci` skill using

```bash
autonomy mint --use-local skill --key my_key.txt --nft <nft_ipfs_hash_or_image_path> --owner <owner_address> ./packages/valory/skills/abstract_abci --update <token_id>
```

Perform a dry run

```bash
autonomy mint --dry-run protocol ./packages/valory/protocols/abci --key key.txt
```

Output

```bash
=== Dry run output ===
Method: RegistriesManagerContract.get_create_transaction
Contract: 0x...
Kwargs: 
    owner: 0x...
    component_type: UnitType.COMPONENT
    metadata_hash: 0x...
    sender: 0x...
    §ncies: []
Transaction: 
    chainId: 31337
    nonce: 0
    value: 0
    gas: 16000
    maxFeePerGas: 4000000000
    maxPriorityFeePerGas: 3000000000
    to: 0x...
    data: 0x...
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

`--nft NFT_HASH_OR_IMAGE_PATH`
: IPFS hash or path to the image for the NFT representing the package. Note that if you are using a local chain this option is not required.

`--owner OWNER_ADDRESS`
: Owner address of the package.

`--update TOKEN_ID`
: Update the already minted agent with on-chain `TOKEN_ID` with the current package hash.

### Examples

Mint the `hello_world` agent in the Ethereum main chain:

```bash
autonomy mint --use-ethereum agent --key my_key.txt --nft <nft_ipfs_hash_or_image_path> --owner <owner_address> ./packages/valory/agents/hello_world
```

Same as above, but using a hardware wallet:

```bash
autonomy mint --use-ethereum agent --hwi --nft <nft_ipfs_hash_or_image_path> --owner <owner_address> ./packages/valory/agents/hello_world
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

`--owner OWNER_ADDRESS`
: Owner address of the package.

`-a, --agent-id AGENT_ID`
: Canonical agent ID.

`-n, --number-of-slots NUM_SLOTS`
: Number of agent instances for the canonical agent.

`-c, --cost-of-bond COST_BOND_WEI`
: Cost of bond for the agent (Wei).

`--threshold`
: Threshold for the minimum number of agents required to run the service. The threshold has to be at least $\lceil(2N + 1) / 3\rceil$, where $N$ is total number of the agents in the service.

`--token ERC20_TOKEN_ADDRESS`
: ERC20 token for securing the service.

`--update TOKEN_ID`
: Update the already minted service with on-chain `TOKEN_ID` with the current package hash.

### Examples

Mint the `hello_world` service with 4 instances of canonical agent ID 3, cost of bond 10000000000000000 Wei per agent and a threshold of 3 agents, in the Ethereum main chain:

```bash
autonomy mint --use-ethereum service --key my_key.txt --nft <nft_ipfs_hash_or_image_path> --owner <owner_address> --agent-id 3 --number-of-slots 4 --cost-of-bond 10000000000000000 --threshold 3 ./packages/valory/services/hello_world
```

Same as above, but using a hardware wallet:

```bash
autonomy mint --use-ethereum service --hwi --nft <nft_ipfs_hash_or_image_path> --owner <owner_address> --agent-id 3 --number-of-slots 4 --cost-of-bond 10000000000000000 --threshold 3 ./packages/valory/services/hello_world
```

!!! note

    You can specify more than one type of canonical agent in a service by appropriately defining the triplets `--agent-id`, `--number-of-slots` and `--cost-of-bond` for each canonical agent ID.


You can also use a custom ERC20 token as token to secure the service. Use the `--token` flag to provide the address of the token of your choice:

```bash
autonomy mint --use-ethereum service --key my_key.txt --nft <nft_ipfs_hash_or_image_path> --owner <owner_address> --agent-id 3 --number-of-slots 4 --cost-of-bond 10000000000000000 --threshold 3 ./packages/valory/services/hello_world --token <erc20_token_address>
```

!!! warning "Important"

    If you have minted a service using a custom ERC20 token, then you have to use the same token activate the service and to register the agent instances.