# Fetching and Viewing Service Files

This guide explains how to fetch and view the complete list of files from a service using the `autonomy` CLI tool.

## Prerequisites

Before you begin, ensure you have:
- Open Autonomy framework installed
- Access to either a local or remote registry
- Basic understanding of the Open Autonomy CLI

## Fetching Service Files

The `autonomy fetch` command allows you to download service files from either a local or remote registry.

### Basic Usage

```bash
autonomy fetch [OPTIONS] PUBLIC_ID_OR_HASH
```

### Common Options

- `--service`: Specify that you're fetching a service package
- `--remote`: Use a remote registry (IPFS)
- `--local`: Use a local registry
- `--alias`: Provide a local alias for the service

### Example: Fetching Services

1. From a local registry:
```bash
autonomy fetch valory/hello_world:0.1.0 --service --local
```

2. From a remote registry using package ID:
```bash
autonomy fetch valory/hello_world:0.1.0 --service --remote
```

3. Using IPFS hash:
```bash
autonomy fetch valory/service:QmHash123... --service
```

4. Using on-chain token ID:
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

## Viewing Service Files

After fetching a service, its files are stored in your local packages directory. Here's how to view them:

### Service Directory Structure

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

### Important Files

1. `service.yaml`: Contains service configuration and metadata
2. `contracts/`: Smart contracts used by the service
3. `protocols/`: Communication protocols for agent interactions
4. `skills/`: Core service functionality
5. `vendor/`: Third-party dependencies

### Listing Service Files

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
