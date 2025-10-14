Tools to manage AI agents minted in the {{ autonolas_protocol }}.

This command group consists of a number of functionalities to manage [the life cycle of AI agents](https://stack.olas.network/protocol/life_cycle_of_a_service/) that have been minted in the {{ autonolas_protocol }}.

!!! info

    You can specify how you wish to sign the on-chain transactions produced by these commands: either with **a private key stored in a file**, or with a **hardware wallet**. In this latter case, ensure that you have configured properly the drivers for your hardware wallet.

## Options

`--dry-run`
: Perform a dry run for the transaction.

`--use-celo`
: Use the Celo chain profile to interact with the Autonolas Protocol registry contracts.

`--use-base`
: Use the Base chain profile to interact with the Autonolas Protocol registry contracts.

`--use-optimism`
: Use the Optimism chain profile to interact with the Autonolas Protocol registry contracts.

`--use-arbitrum-one`
: Use the Arbitrum One chain profile to interact with the Autonolas Protocol registry contracts.

`--use-gnosis`
: Use the Gnosis chain profile to interact with the Autonolas Protocol registry contracts.

`--use-polygon`
: Use the Polygon chain profile to interact with the Autonolas Protocol registry contracts.

`--use-ethereum`
: Use the Ethereum chain profile to interact with the Autonolas Protocol registry contracts.

To use these chain profiles, you have to export an environment variable that defines the RPC endpoint in the format `<CHAIN_NAME>_CHAIN_RPC`. For example, if you want to use Ethereum (`--use-ethereum`), you have to export `ETHEREUM_CHAIN_RPC`.

`--use-custom-chain`
: Use the custom-chain profile to interact with the Autonolas Protocol registry contracts. This profile requires that you define some parameters and [contract addresses](../on_chain_addresses.md) as environment variables (see also the {{ autonolas_protocol }} documentation for more information):

    - `CUSTOM_CHAIN_RPC` : RPC endpoint for the custom chain.
    - `CUSTOM_CHAIN_ID` : chain ID.
    - `CUSTOM_COMPONENT_REGISTRY_ADDRESS`
    - `CUSTOM_AGENT_REGISTRY_ADDRESS`
    - `CUSTOM_REGISTRIES_MANAGER_ADDRESS`
    - `CUSTOM_SERVICE_MANAGER_ADDRESS`
    - `CUSTOM_SERVICE_REGISTRY_ADDRESS`
    - `CUSTOM_GNOSIS_SAFE_PROXY_FACTORY_ADDRESS`<sup>&#8224;</sup>
    - `CUSTOM_GNOSIS_SAFE_SAME_ADDRESS_MULTISIG_ADDRESS`<sup>&#8224;</sup>
    - `CUSTOM_SAFE_MULTISIG_WITH_RECOVERY_MODULE_ADDRESS`<sup>&#8225;</sup>
    - `CUSTOM_RECOVERY_MODULE_ADDRESS`<sup>&#8225;</sup>
    - `CUSTOM_SERVICE_REGISTRY_TOKEN_UTILITY_ADDRESS`
    - `CUSTOM_MULTISEND_ADDRESS`

    !!! note
        For L2 chains you are only required to set

        - `CUSTOM_SERVICE_MANAGER_ADDRESS`
        - `CUSTOM_SERVICE_REGISTRY_ADDRESS`
        - `CUSTOM_GNOSIS_SAFE_PROXY_FACTORY_ADDRESS`<sup>&#8224;</sup>
        - `CUSTOM_GNOSIS_SAFE_SAME_ADDRESS_MULTISIG_ADDRESS`<sup>&#8224;</sup>
        - `CUSTOM_SAFE_MULTISIG_WITH_RECOVERY_MODULE_ADDRESS`<sup>&#8225;</sup>
        - `CUSTOM_RECOVERY_MODULE_ADDRESS`<sup>&#8225;</sup>
        - `CUSTOM_MULTISEND_ADDRESS`

    <sup>&#8224;</sup> Required only if `--use-recovery` is not specified.

    <sup>&#8225;</sup> Required only if `--use-recovery` is specified.

`--use-local`
: Use the local chain profile to interact with the Autonolas Protocol registry contracts. This option requires that you have a local Hardhat node with the required contracts deployed.

!!! note

    The chain profile flags (`--use-ethereum`, etc.) are mutually exclusive.

`--use-recovery`
: Use a multisig with a recovery module when deploying or redeploying the AI agent. This module allows ownership of the AI agent multisig to be transferred to the AI agent owner if the agent instances have not done so. This functionality is only available during the [*Pre-Registration*](https://docs.olas.network/protocol/life_cycle_of_a_service/#pre-registration) phase and is executed automatically when [activating](#autonomy-service-activate) the AI agent. See notes <sup>&#8224;</sup> and <sup>&#8225;</sup> above.

`-t, --timeout FLOAT`
: Timeout for on-chain interactions

`-r, --retries INTEGER`
: Max retries for on-chain interactions

`--sleep FLOAT`
: Sleep period between retries

## `autonomy service info`

Print AI agent information.

### Usage

```bash
autonomy service info AI_AGENT_ID
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

Activate an AI agent minted in the Autonolas Protocol.

### Usage

```bash
autonomy service activate [OPTIONS] AI_AGENT_ID
```

### Options

`--key FILE`
: Use a private key from a file to sign the transactions.

`--hwi`
: Use a hardware wallet to sign the transactions.

`--token ERC20_TOKEN_ADDRESS`
: ERC20 token to use for activating the AI agent. You must specify the same token used when minting the AI agent. See the [`autonomy mint service`](./autonomy_mint.md#autonomy-mint-service) command.

`--password PASSWORD`
: Password for the key file.

### Examples

To activate an AI agent with ID 42 in the Autonolas Protocol:

```bash
autonomy service activate 42 --key my_key.txt
```

Same as above, but using a hardware wallet:

```bash
autonomy service activate 42 --hwi
```

If an ERC20 token was used as bonding token when the AI agent was minted, then you have to provide the same token address using the `--token` flag:

```bash
autonomy service activate 42 --key my_key.txt --token <token_address>
```

Make sure your account holds enough funds for activating the AI agent:

## `autonomy service register`

Register an agent instance in an AI agent minted and activated in the Autonolas Protocol.

### Usage

```bash
autonomy service register [OPTIONS] AI_AGENT_ID
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
: ERC20 token to use as bond for the agent instance. You must specify the same token used when minting the AI agent. See the [`autonomy mint service`](./autonomy_mint.md#autonomy-mint-service) command.

`--password PASSWORD`
: Password for the key file.

### Examples

To register an agent instance of blueprint ID 56 with address `0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266` on the AI agent with ID 42 in the protocol:

```bash
autonomy service register -i 0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266 -a 56 42 --key my_key.txt
```

Same as above, but using a hardware wallet:

```bash
autonomy service register -i 0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266 -a 56 42 --hwi
```

When providing the agent instance address make sure that the address you provide is funded.

If an ERC20 token was used as bonding token when the AI agent was minted, then you have to provide the same token address using the `--token` flag:

```bash
autonomy service register -i 0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266 -a 56 42 --hwi --token <token_address>
```

Make sure your account holds enough funds to pay for the agent instance bonds.

## `autonomy service deploy`

Deploy an AI agent in the Autonolas Protocol.

This command can be executed after all agent instance slots have been registered in the corresponding AI agent.

### Usage

```bash
autonomy service deploy [OPTIONS] AI_AGENT_ID
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

To deploy an AI agent with ID 42 in the Autonolas Protocol:

```bash
autonomy service deploy 42 --key my_key.txt
```

Same as above, but using a hardware wallet:

```bash
autonomy service deploy 42 --hwi
```

## `autonomy service terminate`

Terminate an AI agent.

This command can be executed after the AI agent is activated.

### Usage

```bash
autonomy service terminate [OPTIONS] AI_AGENT_ID
```
### Options

`--key FILE`
: Use a private key from a file to sign the transactions.

`--hwi`
: Use a hardware wallet to sign the transactions.

`--password PASSWORD`
: Password for the key file.

### Examples

To terminate the AI agent with ID 42 in the Autonolas Protocol:

```bash
autonomy service terminate 42 --key my_key.txt
```

Same as above, but using a hardware wallet:

```bash
autonomy service terminate 42 --hwi
```

## `autonomy service unbond`

Unbond an AI agent.

This command can be executed after the AI agent is terminated.

### Usage

```bash
autonomy service unbond [OPTIONS] AI_AGENT_ID
```
### Options

`--key FILE`
: Use a private key from a file to sign the transactions.

`--hwi`
: Use a hardware wallet to sign the transactions.

`--password PASSWORD`
: Password for the key file.

### Examples

To unbond an AI agent with ID 42 in the Autonolas Protocol:

```bash
autonomy service unbond 42 --key my_key.txt
```

Same as above, but using a hardware wallet:

```bash
autonomy service unbond 42 --hwi
```

## `autonomy service recover-multisig`

Recover the AI agent multisig.

This command allows the AI agent owner to reclaim the multisig wallet from the
previous deployment if it was not properly transferred by the agent instances after
AI agent termination.

AI agent multisig recovery is only possible if:
    - The original deployment was performed with the `--use-recovery-module` flag.
    - The AI agent is currently in the `PRE_REGISTRATION` state (i.e., all operators have unbonded).

### Usage

```bash
autonomy service recover-multisig [OPTIONS] AI_AGENT_ID
```
### Options

`--key FILE`
: Use a private key from a file to sign the transactions.

`--hwi`
: Use a hardware wallet to sign the transactions.

`--password PASSWORD`
: Password for the key file.

### Examples

To recover the multisig of AI agent with ID 42 in the Autonolas Protocol:

```bash
autonomy service recover-multisig 42 --key my_key.txt
```

Same as above, but using a hardware wallet:

```bash
autonomy service recover-multisig 42 --hwi
```
