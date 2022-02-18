# Deployment guide

# Prerequisites

- Skaffold `>=v1.33.0`
- Docker
- Python `>=3.7`

Install and enter the virtual environment:

```bash
make new_env
pipenv shell
```

# Step 1

First we need to build the images used for the deployment.

Images are built & tagged by scaffold based on an environment variable `$VERSION`.

This is done from the root directory.

```bash
export VERSION=0.1.0
rsync -avu packages/ deployments/Dockerfiles/open_aea/packages
skaffold build --build-concurrency=0 --push=false
```

# Step 2

Now we have our images, we need to build the deployment to use them.


```bash
python deployments/create_deployment.py \
    -t docker-compose \
    -app oracle_hardhat
```

```output
Generated Deployment!


Application:          oracle_hardhat
Type:                 docker-compose
Agents:               2
Network:              hardhat
Build Length          3419

To configure tendermint for specified Deployment please run: 

docker run --rm -v $(pwd)/deployments/build/build:/tendermint:Z --entrypoint=/usr/bin/tendermint valory/consensus-algorithms-tendermint:0.1.0 testnet --config /etc/tendermint/config-template.toml --v 2 --o . --hostname=node0 --hostname=node1
```

# Step 3

We have build our deployment docker-compose file.
Next we need to go ahead and configure tendermint to setup the validators.
We use the docker command generated in the previous step to do this; 

```bash
docker run --rm -v $(pwd)/deployments/build/build:/tendermint:Z --entrypoint=/usr/bin/tendermint valory/consensus-algorithms-tendermint:0.1.0 testnet --config /etc/tendermint/config-template.toml --v 2 --o . --hostname=node0 --hostname=node1
```

```output
I[2022-02-03|12:56:52.911] Found private validator                      module=main keyFile=node0/config/priv_validator_key.json stateFile=node0/data/priv_validator_state.json
I[2022-02-03|12:56:52.911] Found node key                               module=main path=node0/config/node_key.json
I[2022-02-03|12:56:52.911] Found genesis file                           module=main path=node0/config/genesis.json
I[2022-02-03|12:56:52.911] Found private validator                      module=main keyFile=node1/config/priv_validator_key.json stateFile=node1/data/priv_validator_state.json
I[2022-02-03|12:56:52.911] Found node key                               module=main path=node1/config/node_key.json
I[2022-02-03|12:56:52.911] Found genesis file                           module=main path=node1/config/genesis.json
Successfully initialized 2 node directories
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


