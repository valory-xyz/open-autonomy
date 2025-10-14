# Open Autonomy CLI Overview

This page provides a quick reference to commonly used CLI commands in the Open Autonomy framework. Each command has a brief description and basic usage example, with links to more detailed documentation.

## Core Commands

### autonomy analyse
Analyse an AI agent, including ABCI app specifications, docstrings, logs, and more.

[Detailed analyse documentation](./autonomy_analyse.md)

### autonomy deploy
Deploy an AI agent using various deployment backends (Docker, Kubernetes, or localhost).

[Detailed deploy documentation](./autonomy_deploy.md)

### autonomy develop
Development tools for AI agents.

[Detailed develop documentation](./autonomy_develop.md)

### autonomy fetch
Fetch an agent blueprint or AI agent from a registry.

[Detailed fetch documentation](./autonomy_fetch.md)

### autonomy mint
Mint components and AI agents on-chain.

[Detailed mint documentation](./autonomy_mint.md)

### autonomy push-all
Push all available packages to a registry.

[Detailed push-all documentation](./autonomy_push_all.md)

### autonomy replay
Replay tools for AI agents.

[Detailed replay documentation](./autonomy_replay.md)

### autonomy service
Manage on-chain AI agents.

[Detailed AI agent documentation](./autonomy_service.md)

## Additional Information

- Most commands support the `--help` flag for detailed usage information
- Commands that interact with blockchains typically require a key file
- Many commands have additional options for customization and configuration
- See the [detailed command reference](./autonomy_analyse.md) for complete documentation of each command

## Common Options

Many commands share common options:

- `--registry`: Specify the registry to use (default: remote)
- `--chain`: Select blockchain network (e.g., ethereum, polygon)
- `--key`: Path to key file for blockchain transactions
- `--password`: Password for encrypted key files
- `--help`: Show help message and exit