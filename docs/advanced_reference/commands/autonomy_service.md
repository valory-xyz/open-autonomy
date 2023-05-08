Tools to manage services minted in the [Autonolas Protocol](https://docs.autonolas.network/protocol/).

This command group consists of a number of functionalities to manage the life cycle of services that have been minted in the [Autonolas Protocol](https://docs.autonolas.network/protocol/).

!!! info

    You can specify how you wish to sign the on-chain transactions produced by these commands: either with **a private key stored in a file**, or with a **hardware wallet**. In this latter case, ensure that you have configured properly the drivers for your hardware wallet.

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

## `autonomy service activate`

Activate a service minted in the Autonolas Protocol.

### Usage

```bash
autonomy service activate [OPTIONS] SERVICE_ID
```

### Options

`--key FILE`
: Use a private key from a file to sign the transactions.

`--hwi`
: Use a hardware wallet to sign the transactions.

`--password PASSWORD`
: Password for the key file.

### Examples

To activate a service with ID 42 in the Autonolas Protocol:

```bash
autonomy service activate 42 --key my_key.txt
```

Same as above, but using a hardware wallet:

``bash
autonomy service activate 42 --hwi
```

## `autonomy service register`

Register an agent instance in a service minted and activated in the Autonolas Protocol.
### Usage

```bash
autonomy service register [OPTIONS] SERVICE_ID
```

### Options

`--key FILE`
: Use a private key from a file to sign the transactions.

`--hwi`
: Use a hardware wallet to sign the transactions.

`-i, --instance AGENT_ADDRESS`
: Agent instance address.

`-a, --agent-id AGENT_ID`
: Canonical agent ID.

`--password PASSWORD`
: Password for the key file.

### Examples

To register an agent instance of canonical agent ID 56 with address `0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266` on the service with ID 42 in the protocol:

```bash
autonomy service register -i 0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266 -a 56 42 --key my_key.txt
```

Same as above, but using a hardware wallet:

```bash
autonomy service register -i 0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266 -a 56 42 --hwi
```

When providing the agent instance address make sure that the address you provide is funded.

## `autonomy service deploy`

Deploy a service in the Autonolas Protocol.

This command can be executed after all agent slots have been registered in the corresponding service.

### Usage

```bash
autonomy service deploy [OPTIONS] SERVICE_ID
```
### Options

`--key FILE`
: Use a private key from a file to sign the transactions.

`--hwi`
: Use a hardware wallet to sign the transactions.

`-d, --deployment-payload PAYLOAD`
: Deployment payload value.

`--password PASSWORD`
: Password for the key file.

### Examples

To deploy a service with ID 42 in the Autonolas Protocol:

```bash
autonomy service deploy 42 --key my_key.txt
```

Same as above, but using a hardware wallet:

```bash
autonomy service deploy 42 --hwi
```