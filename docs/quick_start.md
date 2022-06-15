# Quick Start

The purpose of this quick start is to get you up and running with the {{open_autonomy}} framework for agent service development as quickly as possible.

## Requirements

Ensure your machine satisfies the following requirements:

- Python `>= 3.7`
- [Tendermint](https://docs.tendermint.com/master/introduction/install.html) `==0.34.11`
- [Pipenv](https://pipenv.pypa.io/en/latest/install/) `>=2021.x.xx`

## Setup

1. Setup the environment
```bash
export OPEN_AEA_IPFS_ADDR="/dns/registry.autonolas.tech/tcp/443/https"
touch Pipfile && pipenv --python 3.10 && pipenv shell
```

2. Install {{open_autonomy}}
```bash
pip install open-autonomy
```

3. Get, build and install your agent
```bash
aea init --reset --author default_author --ipfs --remote
aea fetch valory/hello_world:QmRXo6bdg5M91LAvFRSc19dtsuzfeh4c9Ub8VFfGrobGcg --remote
cd hello_world
aea install
aea generate-key ethereum
aea add-key ethereum
```

4. Run your agent. More info on this hello world example on the [get started](https://docs.autonolas.network/get_started/) section.
```bash
aea run
```
