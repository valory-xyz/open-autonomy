Fetch an agent or agent service from a registry.

## Usage
```bash
autonomy fetch [OPTIONS] PUBLIC_ID_OR_HASH
```

## Options
```
--remote
```
:   To use a remote registry.

```
--local
```
:   To use a local registry.

```
--alias TEXT
```
:   Provide a local alias for the agent or service.

```
--agent
```
:   Specify the package type as agent (default).

```
--service
```
:   Specify the package type as service.

```
--help
```
:   Show the help message and exit.


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

Fetch the agent service `hello_world` from a remote registry ([IPFS](https://ipfs.io)):
```bash
autonomy fetch valory/hello_world:0.1.0:bafybeibp2iiojzyykcbkadqdszd35laq2ub34eovyghrsr33t2vrxmk2r4 --service --remote
```
