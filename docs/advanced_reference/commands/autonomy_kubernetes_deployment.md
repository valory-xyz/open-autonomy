# Launching a Kubernetes Cluster of Services

This guide explains how to launch a Kubernetes cluster of services using the `autonomy` CLI tool.

## Prerequisites

Before you begin, ensure you have:
- Open Autonomy framework installed
- Kubernetes tools installed:
  - [kubectl](https://kubernetes.io/docs/tasks/tools/)
  - [Docker Engine](https://docs.docker.com/engine/install/)
  - [Skaffold](https://skaffold.dev/docs/install/#standalone-binary) `>= 1.39.1`
- A service package ready for deployment

## Preparing for Deployment

### 1. Fetch the Service

If you haven't already, fetch your service:
```bash
autonomy fetch valory/hello_world:0.1.0 --service --remote
```

### 2. Create Keys Configuration

Create a `keys.json` file with your agent keys:
```json
[
    [
        {
            "address": "agent1_address",
            "private_key": "agent1_private_key",
            "ledger": "ethereum"
        }
    ],
    [
        {
            "address": "agent2_address",
            "private_key": "agent2_private_key",
            "ledger": "ethereum"
        }
    ]
]
```

## Building the Kubernetes Deployment

### 1. Build the Deployment

Use the `autonomy deploy build` command with the `--kubernetes` flag:
```bash
autonomy deploy build keys.json --kubernetes
```

This creates a deployment environment in the `./abci_build_*` directory with:
```
abci_build_*/
├── agent_keys/          # Agent key configurations
├── nodes/               # Tendermint node configurations
├── persistent_data/     # Persistent storage
└── kubernetes/          # Kubernetes manifests
```

### 2. Review Kubernetes Configuration

The generated Kubernetes manifests include:
- Deployments for each agent
- Services for network communication
- ConfigMaps for configuration
- PersistentVolumeClaims for storage

## Launching the Cluster

### 1. Start the Deployment

Navigate to the build directory and run:
```bash
cd abci_build_*
autonomy deploy run
```


### 2. Monitor Deployment

Check deployment status:
```bash
kubectl get pods
kubectl get services
```

View logs:
```bash
kubectl logs <pod-name>
```

## Managing the Deployment

### Scaling

To scale the number of agents:
1. Update `keys.json` with additional agent keys
2. Rebuild the deployment with the new configuration

### Monitoring

Monitor service health:
```bash
kubectl describe pods
kubectl get events
```

### Troubleshooting

Common issues and solutions:

1. Pod Startup Failures
   - Check logs: `kubectl logs <pod-name>`
   - Verify resources: `kubectl describe pod <pod-name>`

2. Network Issues
   - Check services: `kubectl get services`
   - Verify network policies

3. Configuration Problems
   - Review ConfigMaps: `kubectl get configmaps`
   - Check mounted volumes

## Best Practices

1. Security
   - Use secrets for sensitive data
   - Implement network policies
   - Regular key rotation

2. Resource Management
   - Set resource limits
   - Monitor resource usage
   - Use horizontal pod autoscaling

3. Maintenance
   - Regular backups
   - Update strategies
   - Monitoring and alerting

## Next Steps

After deploying your service:
- [Monitor service performance](./monitor_service.md)
- [Upgrade service components](./upgrade_service.md)
- [Configure service parameters](./configure_service.md)

## Additional Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Open Autonomy Deployment Reference](../api/cli/deploy.md)
- [Service Configuration Guide](../key_concepts/service_config.md)
