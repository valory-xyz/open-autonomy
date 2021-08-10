# Consensus algorithms

Distributed consensus meets the AEA framework.

## Preliminaries

- Create and launch a virtual environment with Python 3.8 (any Python `>=` 3.6 works):

      pipenv --python 3.8 && pipenv shell

- Install the package from source:

      pip install .

- [Install Tendermint](https://docs.tendermint.com/master/introduction/install.html)


## During development:

- Install development dependencies:

      pipenv install --dev --skip-lock

- Install [IPFS node](https://docs.ipfs.io/install/command-line/#official-distributions) `v0.6.0`