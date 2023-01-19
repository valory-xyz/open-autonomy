# `autonomy service`

Tools to manage on chain services. Once you have a service and the required components minted on chain, you can start with the service deployment process using the service manager.

### Options

`--use-ethereum`
: Use `ethereum` chain profile to interact with the contracts.

`--use-goerli`
: Use `goerli` chain profile to interact with the contracts.

`--use-custom-chain`
: Use custom-chain chain profile to interact with the contracts.

`--use-local`
: Use local chain profile to interact with the contracts.

`--skip-hash-check`
: Skip hash check when verifying dependencies on chain

To understand how to use various chain profiles refer to `Chain Selection` section on the `autonomy mint` command documentation.

## `autonomy service activate`

### Usage

`autonomy service activate [OPTIONS] SERVICE_ID KEYS`

### Options

`--password TEXT`
: Password for key pair

### Examples

To activate a service which is already minted on chain run

`autonomy service activate SERVICE_ID PATH_TO_FUNDED_KEY`

Make sure the key you provide is the same as the one you used to mint the service.

## `autonomy service register`

### Usage

`autonomy service register [OPTIONS] SERVICE_ID KEYS`

### Options

`-i, --instance TEXT`
: Agent instance address

`-a, --agent-id INTEGER`
: Agent ID

`--password TEXT`
: Password for key pair

### Examples

To register an instance with agent ID 1 run

`autonomy service register -i 0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266 -a 1`

> Note: address used here is taken from a hardhat deployment

This will add the provided address as the instance for the agent id 1 for the given service. When providing the instance address make sure that the address you provide is funded, is not the same as the service owner and has not already been registered in any other service.

## `autonomy service deploy`

### Usage

`autonomy service deploy [OPTIONS] SERVICE_ID KEYS`

### Options

`-d, --deployment-payload`
: Deployment payload value

### Examples

To deploy a service just run the command in the given usage format.