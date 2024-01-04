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

**Open Autonomy** is a framework for the creation of **agent services**: off-chain
autonomous services which run as a multi-agent-system (MAS) and offer enhanced functionalities
on-chain. Agent services expand the range of operations that traditional
smart contracts provide, making it possible to execute **arbitrarily complex operations**
(such as machine-learning algorithms). Most importantly, agent services are
**decentralized**, **trust-minimized**, **transparent**, and **robust**.


## Get started developing agent services

Read the [Open Autonomy documentation](https://docs.autonolas.network/open-autonomy/) to learn more about agent services. Follow the [set up](https://docs.autonolas.network/open-autonomy/guides/set_up/) and [quick start](https://docs.autonolas.network/open-autonomy/guides/quick_start/) guides to start building your own services.


## For developers contributing to the framework: install from source

- Ensure your machine satisfies the following requirements:

    - Python `>= 3.8`
    - [Tendermint](https://docs.tendermint.com/v0.34/introduction/install.html) `==0.34.19`
    - [IPFS node](https://docs.ipfs.io/install/command-line/#official-distributions) `==v0.6.0`
    - [Pip](https://pip.pypa.io/en/stable/installation/)
    - [Pipenv](https://pipenv.pypa.io/en/latest/installation.html) `>=2021.x.xx`
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
      docker pull valory/acn-node:latest
      docker pull valory/contracts-amm:latest
      docker pull valory/safe-contract-net:latest
      docker pull valory/slow-tendermint-server:0.1.0

- Create and launch a virtual environment. Also, run this during development,
every time you need to re-create and launch the virtual environment and update
the dependencies:

      make new_env && pipenv shell

  > :information_source: Note: we are using [atheris](https://github.com/google/atheris) in order to perform fuzzy testing.
  > The dependency is not listed in the `Pipfile` because it is not supported on Windows.
  > If you need to run or implement a fuzzy test, please manually install the dependency.
  > If you are developing on Mac, please follow the extra steps described [here](https://github.com/google/atheris#mac).

- Fetch packages:

      autonomy packages sync --update-packages

## Cite

If you are using our software in a publication, please
consider to cite it with the following BibTex entry:

```
@misc{open-autonomy,
  Author = {David Minarsch and Marco Favorito and Viraj Patel and Adamantios Zaras and David Vilela Freire and Michiel Karrenbelt and 8baller and Ardian Abazi and Yuri Turchenkov and José Moreira Sánchez},
  Title = {Open Autonomy Framework},
  Year = {2021},
}
```
