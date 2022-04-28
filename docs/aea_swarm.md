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

