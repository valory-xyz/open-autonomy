# Deployment guide

This guide follows the ropsten oracle example. Modify as relevant for other deployments.

For DO only:

```bash
ssh root@178.62.4.138
```


# Prerequisites

- Skaffold `>=v1.33.0`
- Docker
- Docker-Compose
- Python `>=3.7`

Install the virtual environment:

```bash
make new_env
```

# Step 1

First we need to build the images used for the deployment.

Images are built & tagged by scaffold based on an environment variable `$VERSION`.

This is done from the root directory.

```bash
make clean
export VERSION=0.1.0
rsync -avu packages/ deployments/Dockerfiles/open_aea/packages
skaffold build --build-concurrency=0 --push=false
```

# Step 2

Now we have our images, we need to build the deployment to use them.


```bash
pipenv shell
python deployments/click_create.py build-deployment --deployment-type docker-compose  --valory-app oracle_ropsten --keys-file-path deployments/keys/ropsten_keys.txt
```
We can additionally specify a file path as so;

```bash
pipenv shell
python deployments/click_create.py build-deployment \
  --deployment-type docker-compose  \
  --keys-file-path deployments/keys/ropsten_keys.txt \
  --deployment-file-path deployments/deployment_specifications/price_estimation_ropsten.yaml 
```


```output
To configure tendermint for deployment please run: 

docker run --rm -v $(pwd)/deployments/build/build:/tendermint:Z --entrypoint=/usr/bin/tendermint valory/consensus-algorithms-tendermint:0.1.0 testnet --config /etc/tendermint/config-template.toml --v 4 --o . --hostname=node0 --hostname=node1 --hostname=node2 --hostname=node3

Generated Deployment!


Application:          oracle_ropsten
Type:                 docker-compose
Agents:               4
Network:              ropsten
Build Length          9887
```

# Step 3

We have build our deployment docker-compose file.
Next we need to go ahead and configure tendermint to setup the validators.
We use the docker command generated in the previous step to do this; 

```bash
docker run --rm -v $(pwd)/deployments/build/build:/tendermint:Z --entrypoint=/usr/bin/tendermint valory/consensus-algorithms-tendermint:0.1.0 testnet --config /etc/tendermint/config-template.toml --v 4 --o . --hostname=node0 --hostname=node1 --hostname=node2 --hostname=node3
```

```output
I[2022-03-20|20:53:10.377] Generated private validator                  module=main keyFile=node0/config/priv_validator_key.json stateFile=node0/data/priv_validator_state.json
I[2022-03-20|20:53:10.384] Generated node key                           module=main path=node0/config/node_key.json
I[2022-03-20|20:53:10.391] Generated genesis file                       module=main path=node0/config/genesis.json
I[2022-03-20|20:53:10.456] Generated private validator                  module=main keyFile=node1/config/priv_validator_key.json stateFile=node1/data/priv_validator_state.json
I[2022-03-20|20:53:10.464] Generated node key                           module=main path=node1/config/node_key.json
I[2022-03-20|20:53:10.472] Generated genesis file                       module=main path=node1/config/genesis.json
I[2022-03-20|20:53:10.559] Generated private validator                  module=main keyFile=node2/config/priv_validator_key.json stateFile=node2/data/priv_validator_state.json
I[2022-03-20|20:53:10.571] Generated node key                           module=main path=node2/config/node_key.json
I[2022-03-20|20:53:10.580] Generated genesis file                       module=main path=node2/config/genesis.json
I[2022-03-20|20:53:10.649] Generated private validator                  module=main keyFile=node3/config/priv_validator_key.json stateFile=node3/data/priv_validator_state.json
I[2022-03-20|20:53:10.665] Generated node key                           module=main path=node3/config/node_key.json
I[2022-03-20|20:53:10.678] Generated genesis file                       module=main path=node3/config/genesis.json
Successfully initialized 4 node directories
```
# Step 4 (only required for deployments with hardhat network)

We now need to spin up a local hardhat node so that we have a chain to interact with.

This is done in a seperate terminal via docker as so;
```bash
docker run -p 8545:8545 -it valory/consensus-algorithms-hardhat:0.1.0
```


# Step 5

Now that we have our deployment built, we can actually run it.

```bash
cd deployments/build
docker-compose up --force-recreate
```

# Step 6

Retrieve logs

```bash
docker ps
docker logs ID > node_${i}.txt
```

or

```bash
for i in {1..4}; do scp root@178.62.4.138:node_${i}.txt node_${i}.txt; done
```


## Developer mode

In developer mode, the aea docker-image is overwritten and instead launches the aea with watcher.py
On any changes to components within both the packages directory or the open-aea repository the watcher.py will;

- stop the running aea
- fingerprint the packages
- prune tendermint 
- restart tendermint
- restart the aea

Without actually requiring a rebuild of the images!

There are 2 ways of entering into an interactive development environment.

The easiest, is to make use of the convenience commands;

### Quick Dev Mode
```bash
export OPEN_AEA_REPO_DIR=../open-aea
make run-oracle-dev 
```

The 2nd method is more manual and demonstrates the exact steps required to clean and build the images.

### Manual Mode

```bash
export VERSION=dev
make build-images
```
This will build and tag the development Dockerfile in deployments/Dockerfiles.


To then build a deployment for developer mode, nothing extra other than the environment variable is needed.

i.e. We build the deployment;
```bash
 python deployments/click_create.py build-deployment --valory-app oracle_hardhat --deployment-type docker-compose --configure-tendermint
```
To run the development deployment
```bash
cd deployments/build
docker-compose up --force-recreate
```


