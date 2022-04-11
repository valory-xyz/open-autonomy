# Valory Application Deployment

Tooling has been provided to allow for the automatic generation of deployments via deployment specifications.

Valory application deployments can be built on the fly.


```bash
python deployments/click_create.py build-deployment --help
```
output 
```
    Usage: click_create.py build-deployment [OPTIONS]
    
      Build the agent and its components.
    
    Options:
      --valory-app TEXT               [required]
      --deployment-type [docker-compose|kubernetes]
                                      [required]
      --configure-tendermint
      --help                          Show this message and exit.

```

In order to build a deployment from scratch.

    sudo make clean
    make build-images
    python deployments/click_create.py build-deployment \
        --valory-app oracle_hardhat \
        --deployment-type docker-compose \
        --configure-tendermint

Once the script is run, a build configuration will be output to;

    ./deployments/build/$BUILD.yaml

This can then be launched using the appropriate tool.

For example, to launch a deployment using docker-compose.
    
    cd deployments/build/
    docker-compose up --force-recreate

This will spawn:

- a network of 4 Tendermint nodes, each one trying to connect to
  a separate ABCI application instance;
- 4 AEAs, each one running an instance of the ABCI application,
  and a finite-state machine behaviour to interact with
  the round phases.

The following is the output of a single AEA (you can use `docker logs --follow`):
```
info: Building package (connection, valory/abci:0.1.0)...
info: Running command '/usr/bin/python3 check_dependencies.py /home/ubuntu/price_estimation/.build/connection/valory/abci'...
info: Command '/usr/bin/python3 check_dependencies.py /home/ubuntu/price_estimation/.build/connection/valory/abci' succeded with output:
info: Warning:  'tendermint' is required by the abci connection, but it is not installed, or it is not accessible from the system path.
Build completed!
warning: [price_estimation] The kwargs={'consensus': OrderedDict([('max_participants', 4)]), 'convert_id': 'USD', 'currency_id': 'BTC', 'initial_delay': 5.0, 'tendermint_url': 'http://node0:26657'} passed to params have not been set!
warning: [price_estimation] The kwargs={'api_key': None, 'source_id': 'coingecko'} passed to price_api have not been set!
    _     _____     _
   / \   | ____|   / \
  / _ \  |  _|    / _ \
 / ___ \ | |___  / ___ \
/_/   \_\|_____|/_/   \_\

v1.0.2

Starting AEA 'price_estimation' in 'async' mode...
info: [price_estimation] ABCI Handler: setup method called.
info: [price_estimation] Start processing messages...
info: [price_estimation] Entered in the 'registration' behaviour state
info: [price_estimation] transaction signing was successful.
info: [price_estimation] 'registration' behaviour state is done
info: [price_estimation] Entered in the 'observation' behaviour state
info: [price_estimation] Got observation of BTC price in USD: 43876.0
info: [price_estimation] transaction signing was successful.
info: [price_estimation] 'observation' behaviour state is done
info: [price_estimation] Entered in the 'estimate' behaviour state
info: [price_estimation] Using observations [44217.09, 44406.04, 44189.115714582986, 43876.0] to compute the estimate.
info: [price_estimation] Got estimate of BTC price in USD: 44172.06142864574
info: [price_estimation] transaction signing was successful.
info: [price_estimation] 'estimate' behaviour state is done
info: [price_estimation] Consensus reached on estimate: 44172.06142864574
```

From the logs, you can see the different behaviours of the
finite-state machine behaviour: `registration`, `observation`,
and `estimate` states. Moreover,
you can see that the observation of this agent
has been considered in the set of observation shared
among all the AEAs (`Using observations: ...`).
Finally, the consensus is reached among all the AEAs
on the BTC/USD estimate `44172.06142864574`,
which is a simple average of the set of observations.

An analogous output is produced by other AEAs.
Here it is reported the output of another AEA
that participated in the same round:

```
info: Building package (connection, valory/abci:0.1.0)...
info: Running command '/usr/bin/python3 check_dependencies.py /home/ubuntu/price_estimation/.build/connection/valory/abci'...
info: Command '/usr/bin/python3 check_dependencies.py /home/ubuntu/price_estimation/.build/connection/valory/abci' succeded with output:
info: Warning:  'tendermint' is required by the abci connection, but it is not installed, or it is not accessible from the system path.
Build completed!
warning: [price_estimation] The kwargs={'consensus': OrderedDict([('max_participants', 4)]), 'convert_id': 'USD', 'currency_id': 'BTC', 'initial_delay': 5.0, 'tendermint_url': 'http://node1:26657'} passed to params have not been set!
warning: [price_estimation] The kwargs={'api_key': '2142662b-985c-4862-82d7-e91457850c2a', 'source_id': 'ftx'} passed to price_api have not been set!
    _     _____     _
   / \   | ____|   / \
  / _ \  |  _|    / _ \
 / ___ \ | |___  / ___ \
/_/   \_\|_____|/_/   \_\

v1.0.2

Starting AEA 'price_estimation' in 'async' mode...
info: [price_estimation] ABCI Handler: setup method called.
info: [price_estimation] Start processing messages...
info: [price_estimation] Entered in the 'registration' behaviour state
info: [price_estimation] transaction signing was successful.
info: [price_estimation] 'registration' behaviour state is done
info: [price_estimation] Entered in the 'observation' behaviour state
info: [price_estimation] Got observation of BTC price in USD: 44189.115714582986
info: [price_estimation] transaction signing was successful.
info: [price_estimation] 'observation' behaviour state is done
info: [price_estimation] Entered in the 'estimate' behaviour state
info: [price_estimation] Using observations [44217.09, 44406.04, 44189.115714582986, 43876.0] to compute the estimate.
info: [price_estimation] Got estimate of BTC price in USD: 44172.06142864574
info: [price_estimation] transaction signing was successful.
info: [price_estimation] 'estimate' behaviour state is done
info: [price_estimation] Consensus reached on estimate: 44172.06142864574
```

 
## Building & tagging local images

    export VERSION=0.1.0
    make build-images


Conceptually, the image to be used within a deployment should contain all required dependencies and packages.

Configuration of containers and agents is done via environment variables.

### Required Dependencies

- [Skaffold](https://skaffold.dev/docs/install/): Deployment Orchestration
- [Kind](https://kind.sigs.k8s.io/docs/user/quick-start/#installation): Local Cluster deployment and management.
- [Kubectl](https://kubernetes.io/docs/tasks/tools/): kubernetes cli tool
- [Docker](https://docs.docker.com/get-docker/): Container backend

### Quick Cluster Deploy
```
make localcluster-start
make localcluster-deploy
```

## Cluster Development

### To Configure Local Cluster

1. create a local cluster and save the kubeconfig locally
```bash
# build cluster and get kubeconfig
kind create cluster
```
2. login to docker
```bash
docker login -u valory
```
3. deploy registry credentials to the cluster
```bash
kubectl create secret generic regcred \
            --from-file=.dockerconfigjson=/home/$(whoami)/.docker/config.json \
            --type=kubernetes.io/dockerconfigjson
```
4. set skaffold configuration to use a remote registry
```bash
skaffold config set local-cluster false
```
5. (optional) deploy monitoring and dashboard
```bash
# create dashboard user and deploy dashboard configuration
kubectl create serviceaccount dashboard-admin-sa
kubectl create clusterrolebinding dashboard-admin-sa --clusterrole=cluster-admin --serviceaccount=default:dashboard-admin-sa
skaffold run --profile dashboard

# launch dashboard app in firefox
./kubernetes_configs/setup_dashboard.sh
```
6. optional retrieve the token for the dashboard
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

### tear down
```
kind delete cluster
```


## Deployment on Ropsten

Ensure accurate configuration, in particular, swap folder names of `configure_agents` and `configure_agents_ropsten` (`mv configure_agents configure_agents_old` and `mv configure_agents_ropsten configure_agents`). Then run `make localnet-start` from within the node: `ssh root@178.62.4.138`

```bash
count=0
docker ps --format {{"'{{ .ID}}'"}} --filter='ancestor=valory/price_estimation:0.1.0' | while read -r line ; do docker logs "$line" > node_${count}.txt; (( count++ )); done
```

To find exceptions in logs, e.g. `docker logs 1629f5bd397d | grep "Traceback (most recent call last):"`

To save logs to file: `docker logs d425a72bada2 > node_4.txt`

To copy files to local machine: `for i in {1..4}; do scp root@178.62.4.138:node_${i}.txt node_${i}.txt; done`


