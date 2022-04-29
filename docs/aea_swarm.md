# AEA Swarm

AEA Swarm is a collection of tools from valory stack packaged into a CLI tool.

## Deploy

```
$ swarm deploy

Usage: swarm deploy [OPTIONS] COMMAND [ARGS]...

  Deploy an AEA project.

Options:
  --help  Show this message and exit.

Commands:
  build  Build the agent and its components.
```

### Build deployment environment.

```
$ swarm deploy build --help

Usage: swarm deploy build [OPTIONS] PUBLIC_ID KEYS_FILE

  Build the agent and its components.

Options:
  --o PATH            Path to output dir.
  --docker            Use docker as a backend.
  --kubernetes        Use docker as a kubernetes.
  --package-dir PATH  Path to packages folder (For local usage).
  --dev               Create development environment.
  --force             Remove existing build and overwrite with new one.
  --help              Show this message and exit.
```

To create an environment you'll need a deployment specefications file and a file containing keys with funds for the chain you want to use.

```
# create a docker deployment
$ swarm deploy build valory/oracle_hardhat deployments/keys/hardhat_keys.json
```

This will create a deployment environment with following directory structure

```
abci_build/
├── docker-compose.yaml
├── nodes
│   ├── node0
│   │   ├── config
│   │   └── data
│   ├── node1
│   │   ├── config
│   │   └── data
│   ├── node2
│   │   ├── config
│   │   └── data
│   └── node3
│       ├── config
│       └── data
└── persistent_data
    ├── dumps
    └── logs
```

To run this deployment go to the `abci_build` and run `docker-compose up`.

## Replay

Replay tools can be use the re run the agents using data dumps from previous runs.

**Note: Replay only works for deployments which were ran in dev mode**

```
$ swarm replay

Usage: swarm replay [OPTIONS] COMMAND [ARGS]...

  Replay tools.

Options:
  --help  Show this message and exit.

Commands:
  agent       Agent runner.
  tendermint  Tendermint runner.
```

### agent

```
$  swarm replay agent --help

Usage: swarm replay agent [OPTIONS] AGENT

  Agent runner.

Options:
  --build PATH     Path to build dir.
  --registry PATH  Path to registry folder.
  --help           Show this message and exit.
```

### tendermint

```
$ swarm replay tendermint --help

Usage: swarm replay tendermint [OPTIONS]

  Tendermint runner.

Options:
  --build PATH  Path to build directory.
  --help        Show this message and exit.
```


## Replay agents runs from Tendermint dumps

1. Run your preferred app in dev mode, for example run oracle in dev using `make run-oracle-dev` and in a separate terminal run `make run-hardhat`.

2. Wait until at least one reset (`reset_and_pause` round) has occurred, because the Tendermint server will only dump Tendermint data on resets. Once you have a data dump stop the app.

3. Run `swarm replay tendermint` . This will spawn a tendermint network with the available dumps.

4. Now  you can run replays for particular agents using `swarm replay agent AGENT_ID`. `AGENT_ID` is a number between `0` and the number of available agents `-1`. E.g. `swarm replay agent 0` will run the replay for the first agent.
