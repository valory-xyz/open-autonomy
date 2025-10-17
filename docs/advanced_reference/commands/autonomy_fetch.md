Fetch an agent blueprint or AI agent from a registry using its public ID, hash, or token ID.
The `autonomy fetch` command allows you to download AI agent files from either a local or remote registry.

## Usage
```bash
autonomy fetch [OPTIONS] PUBLIC_ID_OR_HASH_OR_TOKEN_ID
```

## Options

`--remote`
:   To use a remote registry.

`--local`
:   To use a local registry.

`--alias` TEXT
:   Provide a local alias for the agent blueprint or AI agent.

`--agent`
:   Specify the package type as agent blueprint (default).

`--service`
:   Specify the package type as AI agent.

`--help`
:   Show the help message and exit.

`--use-celo`                      
:   Use the `Celo` chain profile to find the token with the given token ID.

`--use-base`                      
:   Use the `Base` chain profile to find the token with the given token ID.

`--use-optimism`                
:   Use the `Optimism` chain profile to find the token with the given token ID.

`--use-arbitrum-one`              
:   Use the `Arbitrum One` chain profile to find the token with the given token ID.

`--use-gnosis`                    
:   Use the `Gnosis` chain profile to find the token with the given token ID.

`--use-polygon`                   
:   Use the `Polygon` chain profile to find the token with the given token ID.

`--use-ethereum`
:   Use the `Ethereum` chain profile to find the token with the given token ID.

To use these chain profile, you will have to export an environment variable for RPC in `<CHAIN_NAME>_CHAIN_RPC` format. For example if you want to use `ethereum`, you will have to export `ETHEREUM_CHAIN_RPC`.

`--use-custom-chain`
: Use the custom-chain profile to find the token with the given token ID. This profile requires that you define some parameters and [contract addresses](../on_chain_addresses.md) as environment variables (see also the {{ autonolas_protocol }} documentation for more information):

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
: Use the local chain profile to find the token with the given token ID. This option requires that you have a local Hardhat node with the required contracts deployed.

!!! note

    The chain profile flags are mutually exclusive.


## Examples
Fetch the agent blueprint `hello_world` from the local registry and assign the alias `my_hello_world_agent`:
```bash
autonomy fetch --local --alias my_hello_world_agent valory/hello_world:0.1.0
```

Fetch the agent blueprint `hello_world` from the default registry (initialized with `autonomy init`):
```bash
autonomy fetch valory/hello_world:0.1.0
```

Fetch the AI agent `hello_world` from a local registry with an explicit path:
```bash
autonomy --registry-path=./packages fetch valory/hello_world:0.1.0 --service --local
```

Fetch the AI agent `hello_world` from a remote registry using [IPFS](https://ipfs.io) hash:
```bash
autonomy fetch valory/hello_world:0.1.0:bafybeib5a5qxpx7sq6kzqjuirp6tbrujwz5zvj25ot7nsu3tp3me3ikdhy --service --remote
```

Fetch the AI agent with the token ID `123` on Gnosis chain:
```bash
autonomy fetch 123 --use-gnosis
```

### Viewing Remote Registry Files

Before fetching an AI agent, you can inspect its contents in on IPFS through `https://gateway.autonolas.tech/ipfs/<hash>`

## Common Issues and Solutions

### AI agent Not Found
- Verify the AI agent ID is correct
- Check registry connection
- Ensure you're using the correct registry flag (--local or --remote)

### Missing Dependencies
- Run `autonomy packages sync` to update local packages
- Check AI agent requirements in `service.yaml`

### Permission Issues
- Verify write permissions in packages directory
- Run with appropriate permissions
