This guide will show an example of how dev mode execution replay works, based on the [Price oracle service](../../demos/price_oracle_intro.md).  The example below shows how to replay agent runs from Tendermint dumps.

### Run a local Hardhat node
1. Open a terminal and run a local [HardHat](https://hardhat.org/) node that will emulate a blockchain node. For convenience, we provide a Docker image in [Docker Hub](https://hub.docker.com/) that can be run by executing:
    ```bash
    docker run -p 8545:8545 -it valory/open-autonomy-hardhat:0.1.0
    ```

### Run the service locally
Execute the next steps in a separate terminal.

1. Fetch the `oracle_hardhat` service and navigate to the service folder.
   ```bash
   autonomy fetch valory/oracle_polygon:0.1.0:bafybeie6zryhy7v3fb4mwlu3br4brfxva4m5j2fyldbclq2v3d6modmewm --service
   cd oracle_hardhat
   ```
   
3. Build the Docker image of the service agents in dev mode:
    ```bash
    autonomy build-image --dev
    ```
    After the command finishes building the image, you can see that it has been created by executing:
    ```bash
    docker image ls | grep oar-oracle
    ```

4. Prepare a JSON file `keys.json` containing the wallet address and the private key for each of the agents that make up the service.

    ??? example "Example of a `keys.json` file"

        Find below an example of the structure of a `keys.json` file.

        <span style="color:red">**WARNING: Use this file for testing purposes only. Never use the keys or addresses provided in this example in a production environment or for personal use.**</span>

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


4. Build the deployment setup for the service:
    ```bash
    autonomy deploy build --dev --force --packages-dir PATH_TO_PACKAGES_DIR keys.json 
    ```

5. Navigate to the deployment environment folder (`./abci_build`) and run the deployment locally using
    ```bash
    cd abci_build
    mkdir -p persistent_data/logs
    mkdir -p persistent_data/venvs
    sudo chown -R 1000:1000 -R persistent_data/logs
    sudo chown -R 1000:1000 -R persistent_data/venvs   
    autonomy deploy run
    ```

### Replay the service execution

1. Wait until at least one period (`reset_and_pause` round) has occurred. This is because the Tendermint server will only dump Tendermint data on resets. Once you have a data dump, you can stop the local execution by pressing `Ctrl-C`.

2. Run
   ```bash
   autonomy replay tendermint
   ```
   This will spawn a Tendermint network with the available dumps.

3. Now  you can run replays for particular agents using
   ```bash
   autonomy replay agent AGENT_NUM
   ```
   where `AGENT_NUM` is a number between `0` and the number of available agents `-1`. E.g., to run the replay for the first agent, run
   ```bash
   autonomy replay agent 0
   ```
