# Price Oracle - Introduction

The goal of this demo is to demonstrate an agent service that provides an estimation
of the Bitcoin price (USD) based on observations coming from different data sources,
e.g., CoinMarketCap, CoinGecko, Binance and Coinbase.
Each agent collects an observation from one of the data sources above and
shares it with the rest of the agents through the consensus gadget (Tendermint).
Once all the observations are settled, each agent
computes locally a deterministic function that aggregates the observations made by all the 
agents, and obtains an estimate of the Bitcoin price. In this demo, we consider the 
average of the observed values. 
The local estimates made by all the agents are shared, and
a consensus is reached when one estimate
reaches $\lceil(2n + 1) / 3\rceil$ of the total voting power committed
on the consensus gadget.
Once the consensus on an estimate has been reached, a multi-signature transaction
with $\lceil(2n + 1) / 3\rceil$ of the participants' signatures is settled on the
Ethereum chain, which is emulated by a local Hardhat node in the demo.


## Architecture of the Demo

This demo is composed of:

- A [HardHat](https://hardhat.org/) node (emulating an Ethereum blockchain).
- A set of four [Tendermint](https://tendermint.com/) nodes (`node0`, `node1`, `node2`, `node3`).
- A set of four AEAs (`abci0`, `abci1`, `abci2`, `abci3`), in one-to-one connection with their corresponding Tendermint 
node.

<figure markdown>
![](./images/oracle_diagram.svg)
<figcaption>Price oracle demo architecture</figcaption>
</figure>


{% include 'requirements.md' %}


## Running the Demo

The steps below will guide you to create a Pipenv enviroment for the demo,
download the price oracle agent service definition from the Service Registry
and build a deployment that will run locally.

1. Open a terminal and create a workspace folder, e.g.,
```bash
mkdir my_demo
cd my_demo
```

2. Within the workspace folder, setup the environment:
```bash
export VERSION=0.1.0
export OPEN_AEA_IPFS_ADDR="/dns/registry.autonolas.tech/tcp/443/https"
touch Pipfile && pipenv --python 3.10 && pipenv shell
```

3. Install {{open_autonomy}} on the created environment:
```bash
pip install open-autonomy
```

4. Inside the workspace folder, create a JSON file `keys.json` containing the addresses and keys of the four agents that are 
   part of this demo. Below you have a sample `keys.json` file that you can use for testing:
    ```json
    [
      {
          "address": "0x15d34AAf54267DB7D7c367839AAf71A00a2C6A65",
          "private_key": "0x47e179ec197488593b187f80a00eb0da91f1b9d0b13f8733639f19c30a34926a"
      },
      {
          "address": "0x9965507D1a55bcC2695C58ba16FB37d819B0A4dc",
          "private_key": "0x8b3a350cf5c34c9194ca85829a2df0ec3153be0318b5e2d3348e872092edffba"
      },
      {
          "address": "0x976EA74026E726554dB657fA54763abd0C3a0aa9",
          "private_key": "0x92db14e403b83dfe3df233f83dfa3a0d7096f21ca9b0d6d6b8d88b2b4ec1564e"
      },
      {
          "address": "0x14dC79964da2C08b23698B3D3cc7Ca32193d9955",
          "private_key": "0x4bbbf85ce3377467afe5d46f804f221813b2bb87f24d81f60f1fcdbf7cbf4356"
      }
    ]
    ```

5. Use the {{open_autonomy}} CLI to download and build the agent images:
    ```bash
      autonomy deploy build deployment valory/oracle_hardhat:bafybeibhv2ziivbnj3sgfzjjtvqbsvt3fvra4texc3lx4snqxo6lbmq2le keys.json
    ```
    This command above downloads the price oracle agent service definition from the Service Registry, and generates the required Docker images to run it using the keys provided in the `keys.json` file.
    
6. Open a second terminal and run a local [HardHat](https://hardhat.org/) node that will emulate a blockchain node. For convenience, we provide a Docker image in [Docker Hub](https://hub.docker.com/) that can be run by executing:
    ```bash
    docker run -p 8545:8545 -it valory/open-autonomy-hardhat:0.1.0
    ```

7. Now, we are in position to execute the agent service. Return to the workspace terminal.
The build configuration will be located in `./abci_build`. Execute [Docker Compose](https://docs.docker.com/compose/install/) as indicated below. This will deploy a local price oracle agent service with four agents connected to four [Tendermint](https://tendermint.com/) nodes.
    ```bash
    cd abci_build
    docker-compose up --force-recreate
    ```

8. The logs of a single agent or [Tendermint](https://tendermint.com/) node can then be inspected in another terminal with, e.g.,
    ```bash
    docker logs <container_id> --follow
    ```
    where `<container_id>` refers to the Docker container ID for either an agent
    (`abci0`, `abci1`, `abci2` and `abci3`) or a Tendermint node (`node0`, `node1`, `node2` and `node3`).
    
    
Once you have successfully run the demo, you can explore its [technical details](price_oracle_technical_details.md), and 
take a look at the [composition of FSMs](price_oracle_fsms.md) that make up the agents' {{fsm_app}}.

