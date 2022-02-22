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
python deployments/click_create.py build-deployment --deployment-type docker-compose  --valory-app oracle_ropsten --keys-file-path deployments/deployment_specifications/ropsten_keys.txt
```
We can additionally specify a file path as so;

```bash
pipenv shell
python deployments/click_create.py build-deployment \
  --deployment-type docker-compose --configure-tendermint \
  --deployment-file-path deployments/deployment_specifications/counter.yaml 
```


```output
To configure tendermint for deployment please run: 

docker run --rm -v $(pwd)/deployments/build/build:/tendermint:Z --entrypoint=/usr/bin/tendermint valory/consensus-algorithms-tendermint:0.1.0 testnet --config /etc/tendermint/config-template.toml --v 4 --o . --hostname=node0 --hostname=node1 --hostname=node2 --hostname=node3

Generated Deployment!


Application:          price_estimation_hardhat
Type:                 docker-compose
Agents:               4
Network:              ropsten
Build Length          8785
```

# Step 3

We have build our deployment docker-compose file.
Next we need to go ahead and configure tendermint to setup the validators.
We use the docker command generated in the previous step to do this; 

```bash
docker run --rm -v $(pwd)/deployments/build/build:/tendermint:Z --entrypoint=/usr/bin/tendermint valory/consensus-algorithms-tendermint:0.1.0 testnet --config /etc/tendermint/config-template.toml --v 4 --o . --hostname=node0 --hostname=node1 --hostname=node2 --hostname=node3
```

```output
I[2022-02-19|10:19:04.387] Generated private validator                  module=main keyFile=node0/config/priv_validator_key.json stateFile=node0/data/priv_validator_state.json
I[2022-02-19|10:19:04.396] Generated node key                           module=main path=node0/config/node_key.json
I[2022-02-19|10:19:04.405] Generated genesis file                       module=main path=node0/config/genesis.json
I[2022-02-19|10:19:04.459] Generated private validator                  module=main keyFile=node1/config/priv_validator_key.json stateFile=node1/data/priv_validator_state.json
I[2022-02-19|10:19:04.467] Generated node key                           module=main path=node1/config/node_key.json
I[2022-02-19|10:19:04.475] Generated genesis file                       module=main path=node1/config/genesis.json
I[2022-02-19|10:19:04.527] Generated private validator                  module=main keyFile=node2/config/priv_validator_key.json stateFile=node2/data/priv_validator_state.json
I[2022-02-19|10:19:04.534] Generated node key                           module=main path=node2/config/node_key.json
I[2022-02-19|10:19:04.545] Generated genesis file                       module=main path=node2/config/genesis.json
I[2022-02-19|10:19:04.604] Generated private validator                  module=main keyFile=node3/config/priv_validator_key.json stateFile=node3/data/priv_validator_state.json
I[2022-02-19|10:19:04.612] Generated node key                           module=main path=node3/config/node_key.json
I[2022-02-19|10:19:04.617] Generated genesis file                       module=main path=node3/config/genesis.json
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


