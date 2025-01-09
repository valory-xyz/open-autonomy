# Open Autonomy CLI Overview

This page provides a quick reference to commonly used CLI commands in the Open Autonomy framework. Each command has a brief description and basic usage example, with links to more detailed documentation.

## Core Commands

### autonomy analyse
Analyse an agent service, including ABCI app specifications, docstrings, logs, and more.

```bash
# Check FSM specifications
autonomy analyse fsm-specs

# Analyse logs from a directory
autonomy analyse logs --from-dir ./logs --agent agent1
```

[Detailed analyse documentation](./advanced_reference/commands/autonomy_analyse.md)

### autonomy deploy
Deploy an agent service using various deployment backends (Docker, Kubernetes, or localhost).

```bash
# Build deployment setup
autonomy deploy build keys.json --docker

# Run deployment
autonomy deploy run deployment_dir/
```

[Detailed deploy documentation](./advanced_reference/commands/autonomy_deploy.md)

### autonomy develop
Development tools for agent services.

```bash
# Run service registry contracts locally
autonomy develop service-registry-network
```

[Detailed develop documentation](./advanced_reference/commands/autonomy_develop.md)

### autonomy fetch
Fetch an agent or service from a registry.

```bash
# Fetch a package
autonomy fetch valory/service:0.1.0
```

[Detailed fetch documentation](./advanced_reference/commands/autonomy_fetch.md)

### autonomy hash
Hashing utilities for packages.

```bash
# Generate IPFS hashes for all packages
autonomy hash all

# Get hash for a specific file
autonomy hash hash-file path/to/file
```

[Detailed hash documentation](./advanced_reference/commands/autonomy_hash.md)

### autonomy mint
Mint components and services on-chain.

```bash
# Mint a service
autonomy mint service --service path/to/service --key path/to/key.json
```

[Detailed mint documentation](./advanced_reference/commands/autonomy_mint.md)

### autonomy publish
Publish agent or service packages to the registry.

```bash
# Publish current package
autonomy publish
```

[Detailed publish documentation](./advanced_reference/commands/autonomy_publish.md)

### autonomy push-all
Push all available packages to a registry.

```bash
# Push all packages
autonomy push-all --packages-dir ./packages
```

[Detailed push-all documentation](./advanced_reference/commands/autonomy_push_all.md)

### autonomy replay
Replay tools for agent services.

```bash
# Replay specific agent
autonomy replay agent 0 --build path/to/build

# Run tendermint
autonomy replay tendermint --build path/to/build
```

[Detailed replay documentation](./advanced_reference/commands/autonomy_replay.md)

### autonomy service
Manage on-chain services.

```bash
# Get service info
autonomy service info SERVICE_ID

# Activate service
autonomy service activate SERVICE_ID --key path/to/key.json

# Deploy service
autonomy service deploy SERVICE_ID --key path/to/key.json
```

[Detailed service documentation](./advanced_reference/commands/autonomy_service.md)

## Additional Information

- Most commands support the `--help` flag for detailed usage information
- Commands that interact with blockchains typically require a key file
- Many commands have additional options for customization and configuration
- See the [detailed command reference](./advanced_reference/commands/autonomy_analyse.md) for complete documentation of each command

## Common Options

Many commands share common options:

- `--registry`: Specify the registry to use (default: remote)
- `--chain`: Select blockchain network (e.g., ethereum, polygon)
- `--key`: Path to key file for blockchain transactions
- `--password`: Password for encrypted key files
- `--help`: Show help message and exit