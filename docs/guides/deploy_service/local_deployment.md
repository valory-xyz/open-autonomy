Local service deployments are usually executed for testing services under active development. You can use such deployments to test your service before you mint it in the [Autonolas Protocol](https://docs.autonolas.network/protocol/). Local deployments are based on Docker Compose. We exemplify this process using the `hello_world` service as an example.

1. **Fetch the service.** In the workspace folder, fetch the service from the corresponding registry:

    === "Local registry"
        <!-- TODO FIXME: packages lock + push all should not be necessary here, but otherwise it cannot build the image. -->
        ```bash
        autonomy packages lock
        autonomy push-all
        autonomy fetch valory/hello_world:0.1.0 --service --local
        ```

    === "Remote registry"
        ```bash
        autonomy fetch valory/hello_world:0.1.0:bafybeicdjvpwloho3okcf7d3kmidxvkqdosnfnq47s2e5j277epi2ndjie --service
        ```

2. **Build the agents' image.** Navigate to the service runtime folder that you have just created and build the Docker image of the agents of the service:

    ```bash
    cd hello_world
    autonomy build-image #(1)!
    ```

    1. Check out the [`autonomy build-image`](../../../advanced_reference/commands/autonomy_build-image) command documentation to learn more about its parameters and options.

    After the command finishes, you can check that the image has been created by executing:

    ```bash
    docker image ls | grep <agent_name>
    ```

    Recall that you can find the `agent_name` within the service configuration file `service.yaml`.

3. **Prepare the keys file.** Prepare a JSON file `keys.json` containing the wallet address and the private key for each of the agents that make up the service.

    ???+ example "Example of a `keys.json` file"

        <span style="color:red">**WARNING: Use this file for testing purposes only. Never use the keys or addresses provided in this example in a production environment or for personal use.**</span>

        ```json title="keys.json"
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

4. **Build the deployment.** Within the service runtime folder, execute the command below to build the service deployment:

    ```bash
    rm -rf abci_build #(1)!
    autonomy deploy build keys.json -ltm #(2)!
    ```

    1. Delete previous deployments, if necessary.
    2. `-ltm` stands for "use local Tendermint node". Check out the [`autonomy deploy build`](../../../advanced_reference/commands/autonomy_deploy/#autonomy-deploy-build) command documentation to learn more about its parameters and options.

    This will create a deployment environment within the `./abci_build` folder with the following structure:

    ```bash
    abci_build/
    ├── agent_keys
    │   ├── agent_0
    │   ├── agent_1
    │   |   ...
    │   └── agent_N
    ├── nodes
    │   ├── node0
    │   ├── node1
    │   |   ...
    │   └── nodeN
    ├── persistent_data
    │   ├── benchmarks
    │   ├── logs
    │   ├── tm_state
    │   └── venvs
    └── docker-compose.yaml
    ```

5. **Run the service.** Navigate to the deployment environment folder (`./abci_build`) and run the deployment locally.

    ```bash
    cd abci_build
    autonomy deploy run #(1)!
    ```

    1. Check out the [`autonomy deploy run`](../../advanced_reference/commands/autonomy_deploy/#autonomy-deploy-run) command documentation to learn more about its parameters and options.

    This will spawn in the local machine:

    * $N$ agents, each one running an instance of the corresponding {{fsm_app}}.
    * a network of $N$ Tendermint nodes, one per agent.

    The logs of a single agent or Tendermint node can be inspected in a separate terminal using `docker logs <container_id> --follow`.

    You can cancel the local execution at any time by pressing ++ctrl+c++.
