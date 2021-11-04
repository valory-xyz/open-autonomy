# Consensus algorithms

This repository contains the [Valory](https://www.valory.xyz/) stack, a set of distributed consensus
technologies built on top of the [open AEA framework](https://github.com/valory-xyz/open-aea) to facilitate the creation of dynamic, decentralised applications that depend on off-chain components.

As opposed to tradicional smart contracts, Valory apps go beyond simple, purely reactive applications and can show complex, proactive behaviours that contain off-chain logic without giving up on decentralization.


## Requirements

- Python >= 3.6
- [Tendermint](https://docs.tendermint.com/master/introduction/install.html)
- [IPFS node](https://docs.ipfs.io/install/command-line/#official-distributions) `v0.6.0`


## Setting the repository

- Clone the repository, and recursively clone the submodules:

      git clone --recursive git@github.com:valory-xyz/consensus-algorithms.git

  Note: to update the Git submodules later:

      git submodule update --init --recursive

- Create and launch a virtual environment. Also, run this during development, everytime you need to re-create and launch the virtual environment and update the dependencies:

      make new_env && pipenv shell


- Build the Hardhat project:

      cd third_party/safe-contracts && yarn


## Getting started

Have a look at the [price estimation](https://github.com/valory-xyz/consensus-algorithms/tree/main/examples/price_estimation) example.