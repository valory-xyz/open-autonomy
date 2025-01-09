Fetch an agent or agent service from a registry using its public ID, hash, or token ID.
The `autonomy fetch` command allows you to download service files from either a local or remote registry.

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
:   Provide a local alias for the agent or service.

`--agent`
:   Specify the package type as agent (default).

`--service`
:   Specify the package type as service.

`--help`
:   Show the help message and exit.

`--use-celo`                      
:   Use the `Celo` chain profile to find the token with the given token ID.

`--use-base`                      
:   Use the `Base` chain profile to find the token with the given token ID.

`--use-optimistic`                
:   Use the `Optimistic` chain profile to find the token with the given token ID.

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
Fetch the agent `hello_world` from the local registry and assign the alias `my_hello_world_agent`:
```bash
autonomy fetch --local --alias my_hello_world_agent valory/hello_world:0.1.0
```

Fetch the agent `hello_world` from the default registry (initialized with `autonomy init`):
```bash
autonomy fetch valory/hello_world:0.1.0
```

Fetch the agent service `hello_world` from a local registry with an explicit path:
```bash
autonomy --registry-path=./packages fetch valory/hello_world:0.1.0 --service --local
```

Fetch the agent `hello_world` from a remote registry using package ID:
```bash
autonomy fetch valory/hello_world:0.1.0 --service --remote
```

Fetch the agent service `hello_world` from a remote registry using [IPFS](https://ipfs.io) hash:
```bash
autonomy fetch valory/hello_world:0.1.0:bafybeihl6j7ihkytk4t4ca2ffhctpzydwi6r4a354ubjasttuv2pw4oaci --service --remote
```

Fetch the agent service with the token ID `123` on Gnosis chain:
```bash
autonomy fetch 123 --use-gnosis
```

Fetch the agent service with the token ID `123` using on-chain token ID:
```bash
autonomy fetch 42 --service --chain ethereum
```

### Viewing Remote Registry Files

Before fetching a service, you can inspect its contents in the remote registry:

1. View service metadata:
```bash
# Using package ID
autonomy packages info valory/hello_world:0.1.0 --remote

# Using token ID
autonomy packages info 42 --chain ethereum
```

2. List available versions:
```bash
autonomy packages list --remote | grep hello_world
```

3. Inspect service configuration:
```bash
# Download and view service.yaml without fetching entire package
curl -L https://gateway.autonolas.tech/ipfs/<hash>/service.yaml
```

4. Browse IPFS contents:
If the service is stored on IPFS, you can browse its contents through:
- IPFS gateway: `https://gateway.autonolas.tech/ipfs/<hash>/`
- Local IPFS node (if running): `http://localhost:8080/ipfs/<hash>/`

### Viewing Service Files

After fetching a service, its files are stored in your local packages directory. Here's how to view them:

#### Service Directory Structure

The service files are organized in the following structure:
```
packages/
└── valory/
    └── hello_world/
        ├── service.yaml       # Service configuration
        ├── contracts/         # Smart contracts
        ├── protocols/         # Communication protocols
        ├── skills/           # Service skills
        └── vendor/           # Dependencies
```

#### Important Files

1. `service.yaml`: Contains service configuration and metadata
2. `contracts/`: Smart contracts used by the service
3. `protocols/`: Communication protocols for agent interactions
4. `skills/`: Core service functionality
5. `vendor/`: Third-party dependencies

#### Listing Service Files

To view all files in a fetched service:

1. Navigate to the service directory:
```bash
cd packages/valory/hello_world
```

2. List all files recursively:
```bash
ls -R
```

## Common Issues and Solutions

### Service Not Found
- Verify the service ID is correct
- Check registry connection
- Ensure you're using the correct registry flag (--local or --remote)

### Missing Dependencies
- Run `autonomy packages sync` to update local packages
- Check service requirements in `service.yaml`

### Permission Issues
- Verify write permissions in packages directory
- Run with appropriate permissions

## Next Steps

After fetching and viewing service files, you might want to:
- [Deploy the service](../../guides/deploy_service.md)
- [Configure the service](../../configure_service/service_configuration_file.md)
- [Launch a Kubernetes cluster](./autonomy_kubernetes_deployment.md)

## Additional Resources

- [Open Autonomy CLI Reference](../../api/cli/fetch.md)
- [Service Configuration Guide](../../configure_service/service_configuration_file.md)
- [Package Management Guide](../../guides/publish_fetch_packages.md)