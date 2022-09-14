<h1 align="center">
    <b>Open Autonomy Framework</b>
</h1>

<p align="center">
  <a href="https://pypi.org/project/open-autonomy/">
    <img alt="PyPI" src="https://img.shields.io/pypi/v/open-autonomy">
  </a>
  <a href="https://pypi.org/project/open-autonomy/">
    <img alt="PyPI - Python Version" src="https://img.shields.io/pypi/pyversions/open-autonomy">
  </a>
  <a>
    <img alt="PyPI - Wheel" src="https://img.shields.io/pypi/wheel/open-autonomy">
  </a>
  <a href="https://github.com/valory-xyz/open-autonomy/blob/main/LICENSE">
    <img alt="License" src="https://img.shields.io/pypi/l/open-autonomy">
  </a>
  <a href="https://pypi.org/project/open-autonomy/">
    <img alt="Downloads" src="https://img.shields.io/pypi/dm/open-autonomy">
  </a>
</p>
<p align="center">
  <a href="https://github.com/valory-xyz/open-autonomy/actions/workflows/main_workflow.yml">
    <img alt="Sanity checks and tests" src="https://github.com/valory-xyz/open-autonomy/workflows/main_workflow/badge.svg?branch=main">
  </a>
  <a href="">
    <img alt="Codecov" src="https://img.shields.io/codecov/c/github/valory-xyz/open-autonomy">
  </a>
  <a href="https://img.shields.io/badge/lint-flake8-blueviolet">
    <img alt="flake8" src="https://img.shields.io/badge/lint-flake8-yellow" >
  </a>
  <a href="https://github.com/python/mypy">
    <img alt="mypy" src="https://img.shields.io/badge/static%20check-mypy-blue">
  </a>
  <a href="https://github.com/psf/black">
    <img alt="Black" src="https://img.shields.io/badge/code%20style-black-black">
  </a>
  <a href="https://github.com/PyCQA/bandit">
    <img alt="mypy" src="https://img.shields.io/badge/security-bandit-lightgrey">
  </a>
</p>

Open Autonomy is a framework for the creation of Agent Services: off-chain services which run as a multi-agent-system (MAS)  and are replicated on a temporary consensus gadget (blockchain) while being crypto-economically secured on a public blockchain, hence offering robustness, transparency and decentralization off-chain.

As opposed to traditional smart contracts, Valory apps go beyond simple, purely on-chain logic without giving up on decentralization.

## Get started developing autonomous services

1. Create and launch a clean virtual environment with Python 3.10 (any Python `>=` 3.7 works):

       pipenv --python 3.10 && pipenv shell

2. Install the package from [PyPI](https://pypi.org/project/open-autonomy/):

       pip install open-autonomy


3. Then, build your services as described in the [docs](https://docs.autonolas.network/).


## For developers contributing to the framework: Install from Source

- Ensure your machine satisfies the following requirements:

    - Python `>= 3.7`
    - [Tendermint](https://docs.tendermint.com/master/introduction/install.html) `==0.34.19`
    - [IPFS node](https://docs.ipfs.io/install/command-line/#official-distributions) `==v0.6.0`
    - [Pip](https://pip.pypa.io/en/stable/installation/)
    - [Pipenv](https://pipenv.pypa.io/en/latest/install/) `>=2021.x.xx`
    - [Go](https://go.dev/doc/install) `==1.17.7`
    - [Kubectl](https://kubernetes.io/docs/tasks/tools/)
    - [Docker Engine](https://docs.docker.com/engine/install/)
    - [Docker Compose](https://docs.docker.com/compose/install/)
    - [Skaffold](https://skaffold.dev/docs/install/#standalone-binary) `>= 1.39.1`
    - [Gitleaks](https://github.com/zricethezav/gitleaks/releases/latest)

- Clone the repository:

      git clone git@github.com:valory-xyz/open-autonomy.git

- Pull pre-built images:

      docker pull valory/autonolas-registries:latest
      docker pull valory/contracts-amm:latest
      docker pull valory/safe-contract-net:latest

- Create and launch a virtual environment. Also, run this during development,
every time you need to re-create and launch the virtual environment and update
the dependencies:

      make new_env && pipenv shell

## Cite

If you are using our software in a publication, please
consider to cite it with the following BibTex entry:

```
@misc{open-autonomy,
  Author = {David Minarsch and Marco Favorito and Viraj Patel and Adamantios Zaras and David Vilela Freire and Michiel Karrenbelt and 8baller and Ardian Abazi},
  Title = {Open Autonomy Framework},
  Year = {2021},
}
```
