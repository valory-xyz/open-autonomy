# Deployment guide

This guide follows the ropsten oracle example. Modify as relevant for other deployments.

For DO only:

```bash
ssh root@178.62.4.138
```


# Prerequisites

- Skaffold `==v1.33.0`
- Docker
- Docker-Compose
- Python `>=3.7`

Install Skaffold to manage containers & tagging:

```bash
curl -Lo skaffold https://storage.googleapis.com/skaffold/releases/v1.33.0/skaffold-linux-amd64 && \
sudo install skaffold /usr/local/bin/
```

Install the virtual environment:

```bash
make new_env
pipenv shell
```

Optionally, clean up images & build cache to ensure no artefacts (check with `docker system df` for disc space usage):

```bash
docker rm -vf $(docker ps -aq)
docker rmi -f $(docker images -aq)
docker builder prune --all
rm -rf deployments/persistent_data/logs/aea_*.txt
rm -rf deployments/persistent_data/logs/node_*.txt
```

Ensure, there exists a folder `deployments/persistent_data/logs` with full permissions: `chmod 777 deployments/persistent_data/logs`.

# Step 1

First we need to build the images used for the deployment.

Images are built & tagged by a python script which uses calls Skaffold based on an environment variable `$VERSION`.

This is done from the root directory.

The first time we run the application, we must also build and tag the dependency images. 

These images are used for tendermint and for the local hardhat image.

```bash
swarm deploy build image valory/oracle_hardhat --dependencies
```

```output
Building image with:
        Profile: dependencies
        ServiceId: valory/oracle_hardhat:latest

[Skaffold] Generating tags...
[Skaffold] - valory/open-autonomy-tendermint -> valory/open-autonomy-tendermint:0.1.0
[Skaffold] - valory/open-autonomy-hardhat -> valory/open-autonomy-hardhat:0.1.0
[Skaffold] Checking cache...
[Skaffold] - valory/open-autonomy-tendermint: Found Locally
[Skaffold] - valory/open-autonomy-hardhat: Found Locally
....
```

Now we have our base dependencies, we can build the application specific dependencies.

```bash
swarm deploy build image valory/oracle_hardhat
```

From this command, we receive the below output showing custom images being built and tagged for the specified Valory app and version.

```output
Building image with:
        Profile: prod
        ServiceId: valory/oracle_hardhat:latest

[Skaffold] Generating tags...
[Skaffold] - valory/open-autonomy-open-aea -> valory/open-autonomy-open-aea:oracle-0.1.0
[Skaffold] Checking cache...
[Skaffold] - valory/open-autonomy-open-aea: Found Locally
...
```

# Step 2

Now we have our images, we need to build the deployment to use them.

```bash
swarm deploy build deployment valory/oracle_hardhat deployments/keys/hardhat_keys.json 
```


```output
[Tendermint] I[2022-05-16|10:25:44.897] Generated private validator                  module=main keyFile=node0/config/priv_validator_key.json stateFile=node0/data/priv_validator_state.json
[Tendermint] I[2022-05-16|10:25:44.897] Generated node key                           module=main path=node0/config/node_key.json
[Tendermint] I[2022-05-16|10:25:44.897] Generated genesis file                       module=main path=node0/config/genesis.json
[Tendermint] I[2022-05-16|10:25:44.900] Generated private validator                  module=main keyFile=node1/config/priv_validator_key.json stateFile=node1/data/priv_validator_state.json
[Tendermint] I[2022-05-16|10:25:44.900] Generated node key                           module=main path=node1/config/node_key.json
[Tendermint] I[2022-05-16|10:25:44.900] Generated genesis file                       module=main path=node1/config/genesis.json
[Tendermint] I[2022-05-16|10:25:44.903] Generated private validator                  module=main keyFile=node2/config/priv_validator_key.json stateFile=node2/data/priv_validator_state.json
[Tendermint] I[2022-05-16|10:25:44.903] Generated node key                           module=main path=node2/config/node_key.json
[Tendermint] I[2022-05-16|10:25:44.904] Generated genesis file                       module=main path=node2/config/genesis.json
[Tendermint] I[2022-05-16|10:25:44.907] Generated private validator                  module=main keyFile=node3/config/priv_validator_key.json stateFile=node3/data/priv_validator_state.json
[Tendermint] I[2022-05-16|10:25:44.907] Generated node key                           module=main path=node3/config/node_key.json
[Tendermint] I[2022-05-16|10:25:44.907] Generated genesis file                       module=main path=node3/config/genesis.json
[Tendermint] Successfully initialized 4 node directories
[Tendermint] 

Generated Deployment!


Type:                 docker-compose
Agents:               4
Network:              hardhat
Build Length          9167
```

# Step 3 (only required for deployments with hardhat network)

We now need to spin up a local hardhat node so that we have a chain to interact with.

This is done in a separate terminal via docker as so;
```bash
docker run -p 8545:8545 -it valory/open-autonomy-hardhat:0.1.0
```


# Step 4

Now that we have our deployment built, we can actually run it.

```bash
cd abci_build/
docker-compose up --force-recreate
```

# Step 5

Retrieve logs

```bash
docker ps
docker logs ID > abci${i}.txt
```

or

```bash
for i in {0..3}; do ssh root@178.62.4.138 "docker logs abci${i} > abci${i}.txt"; done
for i in {0..3}; do ssh root@178.62.4.138 "docker logs node${i} > node${i}.txt"; done
for i in {0..3}; do scp root@178.62.4.138:abci${i}.txt abci${i}.txt; done
for i in {0..3}; do scp root@178.62.4.138:node${i}.txt node${i}.txt; done
```

or

```bash
for i in {0..3}; do scp root@178.62.4.138:open-autonomy/abci_build/persistent_data/logs/aea_${i}.txt abci${i}.txt; done
for i in {0..3}; do scp root@178.62.4.138:open-autonomy/abci_build/persistent_data/logs/node_${i}.txt node${i}.txt; done
```

and run script for checking path

```bash
swarm analyse abci logs abci${i}.txt
```

# Step 6

Stop

```bash
cd abci_build/
docker-compose kill
```

## Developer mode

In developer mode, the aea docker-image is overwritten and instead launches the aea with `watcher.py`
On any changes to components within both the packages directory or the open-aea repository the `watcher.py` will;

- stop the running aea
- fingerprint the packages
- prune tendermint 
- restart tendermint
- restart the aea

Without actually requiring a rebuild of the images!

Developer mode will also store much more granular information allowing the developer to replay the application state.

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
swarm deploy build image --dev PUBLIC_ID_OR_HASH
```
Images are built and tagged on an application by application basis. This is so that Valory images are pre-installed with the necessary dependencies to allow fast start up in production.

This will build and tag the development Dockerfile in deployments/Dockerfiles.

To then build a deployment for developer mode, nothing extra other than the environment variable is needed.

i.e. We build the deployment;
```bash
swarm deploy build deployment --dev PUBLIC_ID_OR_HASH KEYS_FILE
```
To run the development deployment
```bash
cd deployments/build
docker-compose up --force-recreate
```
# Logs 

## Persistent in docker-compose

By default, the logs from AEA's and their nodes are stored within; When running the application in Development mode, the application will store additional data within the persistent data directory:

```bash
ls abci_build/persistent_data/
```
```output
benchmarks  logs  tm_state  venvs
```

- benchmarking - This directory contains benchmarking data from the running agents.
- tm_state - This directory contains the tendermint message state from the running agents, allowing replay of the application.
- venvs - This directory contains shared virtual environments.


# Background info:

File tree (from level `abci_build/nodes`):

``` bash
abci_build/nodes/
└── node0
    ├── config
    │   ├── config.toml # general validator config
    │   ├── genesis.json # the genesis file with all the validators in it      node_key.json  
    │   ├── node_key.json # the key file of the node
    │   └── priv_validator_key.json # the key file of the validator
    └── data 
        └── priv_validator_state.json # contains the configuration of the state at startup
```

The network configuration is passed directly to the node.

Example genesis file:
``` json
{
  "genesis_time": "2022-04-07T17:24:42.830360304Z",
  "chain_id": "chain-9sL6vh",
  "initial_height": "0",
  "consensus_params": {
    "block": {
      "max_bytes": "22020096",
      "max_gas": "-1",
      "time_iota_ms": "1000"
    },
    "evidence": {
      "max_age_num_blocks": "100000",
      "max_age_duration": "172800000000000",
      "max_bytes": "1048576"
    },
    "validator": {
      "pub_key_types": [
        "ed25519"
      ]
    },
    "version": {}
  },
  "validators": [
    {
      "address": "1496C02B6A7243B791EED40BD507BDDF46748F0A",
      "pub_key": {
        "type": "tendermint/PubKeyEd25519",
        "value": "rRqP11v8hil6dTYLgZHz8e7CbCEwF0O23OOp8ZyF9PM="
      },
      "power": "1",
      "name": "node0"
    },
    {
      "address": "585ADCC6C87222505715F5C24A598D5EE9D947E5",
      "pub_key": {
        "type": "tendermint/PubKeyEd25519",
        "value": "1UDW597G1MBYDZ5WvklFxAkbBCkaGCMeipdnvll33ds="
      },
      "power": "1",
      "name": "node1"
    },
    {
      "address": "8E67A1A005E3E7DBAC769C38B718C51382876BDA",
      "pub_key": {
        "type": "tendermint/PubKeyEd25519",
        "value": "SjoyI8ZFsnFro0sw9mfVkH0YLd0MCv5gqlGFq++G5E8="
      },
      "power": "1",
      "name": "node2"
    },
    {
      "address": "D4D28787301A651F1F1985C4CAA03C723DA9179F",
      "pub_key": {
        "type": "tendermint/PubKeyEd25519",
        "value": "w9x8PXCMxRvnORBsLGckhA+S8g8xFmi5vGOK7roptvM="
      },
      "power": "1",
      "name": "node3"
    }
  ],
  "app_hash": ""
}
```
