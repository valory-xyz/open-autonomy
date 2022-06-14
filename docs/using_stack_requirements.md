# Requirements and Set-Up

In order to set up the {{open_autonomy}} framework for development or running the examples provided, ensure that your machine satisfies the following requirements:

- Python `>= 3.7`
- Yarn `>=1.22.xx`
- Node `>=v12.xx`
- [Tendermint](https://docs.tendermint.com/master/introduction/install.html) `==0.34.11`
- [IPFS node](https://docs.ipfs.io/install/command-line/#official-distributions) `==v0.6.0`
- [Pipenv](https://pipenv.pypa.io/en/latest/install/) `>=2021.x.xx`

## For developers using the framework: Get started developing

1. Create and launch a clean virtual environment with Python 3.10 (any Python `>=` 3.7 works):
```bash
pipenv --python 3.10 && pipenv shell
```

2. Install the package from [PyPI](https://pypi.org/project/open-autonomy/):
```bash
pip install open-autonomy
```

3. Then, build your services as described in the [docs](https://docs.autonolas.network/).


## For developers contributing to the framework: Install from Source

- Clone the repository, and recursively clone the submodules:
```bash
git clone --recursive git@github.com:valory-xyz/open-autonomy.git
```

      Note: to update the Git submodules later:
      ```bash
      git submodule update --init --recursive
      ```

- Build the Hardhat projects:
```bash
cd third_party/safe-contracts && yarn install
cd ../..
cd third_party/contracts-amm && yarn install
cd ../..
```

- Create and launch a virtual environment. Also, run this during development,
every time you need to re-create and launch the virtual environment and update
the dependencies:
```bash
make new_env && pipenv shell
```
