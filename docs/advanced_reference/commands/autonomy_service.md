Tools to manage services minted in the {{ autonolas_protocol }}.

This command group consists of a number of functionalities to manage [the life cycle of services](https://docs.autonolas.network/protocol/life_cycle_of_a_service/) that have been minted in the {{ autonolas_protocol }}.

!!! info

    You can specify how you wish to sign the on-chain transactions produced by these commands: either with **a private key stored in a file**, or with a **hardware wallet**. In this latter case, ensure that you have configured properly the drivers for your hardware wallet.

## Options

`--dry-run`
: Perform a dry run for the transaction.

`--use-ethereum`
: Use the Ethereum chain profile to interact with the Autonolas Protocol registry contracts. This option requires that you define the following environment variable:

    - `ETHEREUM_CHAIN_RPC` : RPC endpoint for the Ethereum mainnet chain.

`--use-goerli`
: Use the Görli chain profile to interact with the Autonolas Protocol registry contracts. This option requires that you define the following environment variable:

    - `GOERLI_CHAIN_RPC` : RPC endpoint for the Görli testnet chain.

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

    The options `--use-ethereum`, `--use-goerli`, `--use-custom-chain` and `--use-local` are mutually exclusive.

`-t, --timeout FLOAT`
: Timeout for on-chain interactions

`-r, --retries INTEGER`
: Max retries for on-chain interactions

`--sleep FLOAT`
: Sleep period between retries

## `autonomy service info`

Print service information.

### Usage

```bash
autonomy service info SERVICE_ID
```

### Examples

```bash
$ autonomy service info 3

+---------------------------+----------------------------------------------+
|         Property          |                    Value                     |
+===========================+==============================================+
| Service State             | DEPLOYED                                     |
+---------------------------+----------------------------------------------+
| Security Deposit          | 1000                                         |
+---------------------------+----------------------------------------------+
| Multisig Address          | 0x0000000000000000000000000000000000000000   |
+---------------------------+----------------------------------------------+
| Cannonical Agents         | 1                                            |
+---------------------------+----------------------------------------------+
| Max Agents                | 4                                            |
+---------------------------+----------------------------------------------+
| Threshold                 | 3                                            |
+---------------------------+----------------------------------------------+
| Number Of Agent Instances | 4                                            |
+---------------------------+----------------------------------------------+
| Registered Instances      | - 0x0000000000000000000000000000000000000000 |
|                           | - 0x0000000000000000000000000000000000000000 |
|                           | - 0x0000000000000000000000000000000000000000 |
|                           | - 0x0000000000000000000000000000000000000000 |
+---------------------------+----------------------------------------------+
```

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

`--token ERC20_TOKEN_ADDRESS`
: ERC20 token to use for activating the service. You must specify the same token used when minting the service. See the [`autonomy mint service`](./autonomy_mint.md#autonomy-mint-service) command.

`--password PASSWORD`
: Password for the key file.

### Examples

To activate a service with ID 42 in the Autonolas Protocol:

```bash
autonomy service activate 42 --key my_key.txt
```

Same as above, but using a hardware wallet:

```bash
autonomy service activate 42 --hwi
```

If an ERC20 token was used as bonding token when the service was minted, then you have to provide the same token address using the `--token` flag:

```bash
autonomy service activate 42 --key my_key.txt --token <token_address>
```

Make sure your account holds enough funds for activating the service:

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

`--token ERC20_TOKEN_ADDRESS`
: ERC20 token to use as bond for the agent instances. You must specify the same token used when minting the service. See the [`autonomy mint service`](./autonomy_mint.md#autonomy-mint-service) command.

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

If an ERC20 token was used as bonding token when the service was minted, then you have to provide the same token address using the `--token` flag:

```bash
autonomy service register -i 0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266 -a 56 42 --hwi --token <token_address>
```

Make sure your account holds enough funds to pay for the agent bonds.

## `autonomy service deploy`

Deploy a service in the Autonolas Protocol.

This command can be executed after all agent slots have been registered in the corresponding service.

### Usage

```bash
autonomy service deploy [OPTIONS] SERVICE_ID
```
### Options

`--reuse-multisig`
: Reuse `mutlisig` from previous deployment.

`--key FILE`
: Use a private key from a file to sign the transactions.

`--hwi`
: Use a hardware wallet to sign the transactions.

`-f, --fallback-handler ADDRESS`
: Fallback handler address for the gnosis safe multisig.

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

## `autonomy service terminate`

Terminate a service.

This command can be executed after the service is activated.

### Usage

```bash
autonomy service terminate [OPTIONS] SERVICE_ID
```
### Options

`--key FILE`
: Use a private key from a file to sign the transactions.

`--hwi`
: Use a hardware wallet to sign the transactions.

`--password PASSWORD`
: Password for the key file.

### Examples

To terminate the service with ID 42 in the Autonolas Protocol:

```bash
autonomy service terminate 42 --key my_key.txt
```

Same as above, but using a hardware wallet:

```bash
autonomy service terminate 42 --hwi
```

## `autonomy service unbond`

Unbond a service.

This command can be executed after the service is terminated.

### Usage

```bash
autonomy service unbond [OPTIONS] SERVICE_ID
```
### Options

`--key FILE`
: Use a private key from a file to sign the transactions.

`--hwi`
: Use a hardware wallet to sign the transactions.

`--password PASSWORD`
: Password for the key file.

### Examples

To unbond a service with ID 42 in the Autonolas Protocol:

```bash
autonomy service unbond 42 --key my_key.txt
```

Same as above, but using a hardware wallet:

```bash
autonomy service unbond 42 --hwi
```
