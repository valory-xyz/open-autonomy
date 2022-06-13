# Valory Application Deployment

Tooling has been provided to allow for the automatic generation of deployments via deployment specifications.

Valory application deployments can be built on the fly.

## Generate deployment configuration

To learn about generating the deployment configuration, run the following command:

```bash
$ autonomy deploy build deployment --help

Usage: autonomy deploy build deployment [OPTIONS] PUBLIC_ID_OR_HASH KEYS_FILE

  Build deployment setup for n agents.

Options:
  --o PATH            Path to output dir.
  --n INTEGER         Number of agents.
  --docker            Use docker as a backend.
  --kubernetes        Use docker as a kubernetes.
  --packages-dir PATH  Path to packages folder (For local usage).
  --dev               Create development environment.
  --force             Remove existing build and overwrite with new one.
  --help              Show this message and exit.
  --password     Optional password for encrypted keys.
```

```bash
autonomy deploy build image --help

Usage: autonomy deploy build image [OPTIONS] PUBLIC_ID_OR_HASH

  Build image using skaffold.

Options:
  --packages-dir PATH   Path to packages folder (For local usage).
  --build-dir PATH     Path to build directory.
  --skaffold-dir PATH  Path to directory containing the skaffold config.
  --version TEXT       Image version
  --push               Push image after build.
  --dependencies       To use the dependencies profile.
  --prod               To use the prod profile.
  --dev                To use the dev profile.
  --cluster            To use the cluster profile.
  --help               Show this message and exit.
```

For example, in order to build a deployment from scratch for oracle abci, first ensure you have a clean build environment and then build the images:
```bash
make clean
autonomy deploy build image valory/oracle_hardhat --dependencies
autonomy deploy build image valory/oracle_hardhat
```

Next, run the command to generate the relevant build configuration:
```bash
autonomy deploy build deployment valory/oracle_hardhat deployments/keys/hardhat_keys.json
```

A build configuration will be output to `./abci_build`.

This can then be launched using the appropriate tool. For example, to launch a deployment using docker-compose.

```bash
cd abci_build/
docker-compose up --force-recreate
```

This will spawn:

- a network of `n` Tendermint nodes, each one trying to connect to a separate ABCI application instance;
- `n` AEAs, each one running an instance of the ABCI application, and a finite-state machine behaviour to interact with the round phases.

The logs of a single AEA or node can then be inspected with `docker logs {container_id} --follow`.

## Building & tagging local images

```bash
export VERSION=0.1.0
make build-images
```

Conceptually, the image to be used within a deployment should contain all required dependencies and packages.

Configuration of containers and agents is done via environment variables.

### Required Dependencies

- [Skaffold](https://skaffold.dev/docs/install/): Deployment Orchestration
- [Kind](https://kind.sigs.k8s.io/docs/user/quick-start/#installation): Local Cluster deployment and management.
- [Kubectl](https://kubernetes.io/docs/tasks/tools/): kubernetes cli tool
- [Docker](https://docs.docker.com/get-docker/): Container backend


## Cluster Deployment

In addition to Docker-Compose-based deployments, we support cluster deployments using Kubernetes.

### Quick Cluster Deploy

Run the following make targets for a quick deployment of the oracle:
```bash
make localcluster-start
```

### To Configure Local Cluster

1. Create a local cluster and save the kubeconfig locally
```bash
# build cluster and get kubeconfig
kind create cluster
```

2. Login to docker:
```bash
docker login -u valory
```

3. Deploy registry credentials to the cluster
```bash
kubectl create secret generic regcred \
            --from-file=.dockerconfigjson=/home/$(whoami)/.docker/config.json \
            --type=kubernetes.io/dockerconfigjson
```

4. Set skaffold configuration to use a remote registry
```bash
skaffold config set local-cluster false
```

5. (Optionally,) deploy monitoring and dashboard:
```bash
# create dashboard user and deploy dashboard configuration
kubectl create serviceaccount dashboard-admin-sa
kubectl create clusterrolebinding dashboard-admin-sa --clusterrole=cluster-admin --serviceaccount=default:dashboard-admin-sa
skaffold run --profile dashboard

# launch dashboard app in firefox
./kubernetes_configs/setup_dashboard.sh
```

6. (Optionally,) retrieve the token for the dashboard:
```bash
echo (kubectl describe secret (kubectl get secret | grep admin | awk '{print $1}') | grep token: | awk '{print $2}')
```

### To Deploy Poc

```bash
# deploy poc to cluster
skaffold run --profile minikube
```

### Dev mode

Watch for changes and automatically build tag and deploy and changes within the context of the build directories

```bash
# deploy poc to cluster
skaffold dev --profile minikube
```

### Tear down
```bash
kind delete cluster
```
