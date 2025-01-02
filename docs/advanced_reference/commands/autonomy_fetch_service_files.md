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

### Example: Fetching the Hello World Service

1. From a local registry:
```bash
autonomy fetch valory/hello_world:0.1.0 --service --local
```

2. From a remote registry:
```bash
autonomy fetch valory/hello_world:0.1.0 --service --remote
```

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
