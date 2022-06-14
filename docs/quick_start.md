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
touch Pipfile && pipenv --python 3.10 && pipenv shell
```

2. Install {{open_autonomy}}
```bash
pip install open-autonomy
```

3. Get packages
```bash
svn checkout  https://github.com/valory-xyz/open-autonomy/trunk/packages packages
```

4. Build and install your agent
```bash
cd hello_world
aea generate-key ethereum
aea add-key ethereum
aea install
```

5. Setup a tendermint testnet
```bash
tendermint init
```

6. Run your agent. More info on this hello world example on the [get started](https://davidminarsch.github.io/temp-docs-valory/get_started/) section.
```bash
aea run
```
