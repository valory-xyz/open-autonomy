# Requirements and Set-Up

In order to set up the {{valory_stack}} for development or running the examples provided, ensure that your machine satisfies the following requirements:

- [Python](https://www.python.org/) `>= 3.7`
- [Pipenv](https://pipenv.pypa.io/en/latest/install/) `>=2021.x.xx`
- [Yarn](https://yarnpkg.com/) `>=1.22.xx`
- [Node](https://nodejs.org/) `>=v12.xx`
- [Tendermint](https://docs.tendermint.com/master/introduction/install.html) `==0.34.11`
- [IPFS node](https://docs.ipfs.io/install/command-line/#official-distributions) `==v0.6.0`


If you are setting up the environment for the first time, follow these steps:

1. Clone the repository, and recursively clone the submodules:
      ```bash
      git clone --recursive git@github.com:valory-xyz/open-autonomy.git
      ```

2. Build the Hardhat projects:
      ```bash
      cd third_party/safe-contracts && yarn install
      cd ../..
      cd third_party/contracts-amm && yarn install
      cd ../..
      ```

3. Create and launch the virtual [Pipenv](https://pipenv.pypa.io/en/latest/install/) environment.
      ```bash
      make new_env && pipenv shell
      ```

If you already have the environment set up and you are updating the repository during development (e.g., pulling the main Git branch), we recommend that you follow these steps:

1. Update the Git submodules:
      ```bash
      git submodule update --init --recursive
      ```

2. If you are inside the [Pipenv](https://pipenv.pypa.io/en/latest/install/) environment, exit the environment:
      ```bash
      exit
      ```

3. Follow steps 2 and 3 above.
