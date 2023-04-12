In addition to deployments based on Docker Compose, the framework also supports cluster deployments using Kubernetes.

## Building & tagging local images

```bash
export SERVICE_ID=author_name/service_name
export VERSION=0.1.0
autonomy build-image ${SERVICE_ID}
```

Conceptually, the image to be used within a deployment should contain all required dependencies and packages.

Configuration of containers and agents is done via environment variables.

## Quick cluster deploy

Run the following make targets for a quick deployment of the oracle:
```bash
svn export https://github.com/valory-xyz/open-autonomy/trunk/infrastructure
cd infrastructure
make localcluster-start
```

## Requirements

Besides the [framework requirements](../set_up.md#requirements), you will also need:

* [Skaffold](https://skaffold.dev/docs/install/): Deployment orchestration.
* [Kind](https://kind.sigs.k8s.io/docs/user/quick-start/#installation): Local cluster deployment and management.
* [Kubectl](https://kubernetes.io/docs/tasks/tools/): Kubernetes CLI tool.

## Configure a local cluster

1. Create a local cluster and save the kubeconfig locally

    ```bash
    # build cluster and get kubeconfig
    kind create cluster
    ```

1. Login to docker:
```bash
docker login -u valory
```

1. Deploy registry credentials to the cluster
```bash
kubectl create secret generic regcred \
            --from-file=.dockerconfigjson=/home/$(whoami)/.docker/config.json \
            --type=kubernetes.io/dockerconfigjson
```

1. Set skaffold configuration to use a remote registry
```bash
skaffold config set local-cluster false
```

1. (Optionally,) deploy monitoring and dashboard:
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

### To deploy poc

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
