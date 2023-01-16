The {{open_autonomy}} framework comes with *dev mode* tooling to enable faster service developing and debugging. The dev mode supports running agent services with a number of functionalities enabled:

* **Hot reload,** which enables hot code swapping and reflects changes on the agent code as well as on the local `open-aea` repository without rebuilding or restarting the containers manually.
* **Execution replay** of a previous agent in the service.
* **Benchmark** the performance of an agent service.


Before starting this guide, ensure that your machine satisfies the framework requirements and that you have followed the [set up guide](../../guides/set_up.md). As a result you should have a Pipenv workspace folder.

## Build and run an agent service in dev mode

This example is based on the Price Oracle service. The service requires a local Hardhat node. Open a dedicated terminal and run:

```bash
docker run -p 8545:8545 -it valory/open-autonomy-hardhat:0.1.0
```

Execute the next steps in a separate terminal.

1. **Fetch the service.** Fetch the Price Oracle service from the remote registry.

    ```bash
    autonomy fetch valory/oracle_hardhat:0.1.0:bafybeieo2gmyuut6chwnonutmcxo75wz7mpjxtim6c2naaarqpp5wa46ge --service
    ```

2. **Build the agents' image.** Navigate to the local folder of the service, and build the Docker image of the service agents in dev mode.

    ```bash
    cd oracle_hardhat
    autonomy build-image --dev
    ```

    After the command finishes building the image, you can see that it has been created by executing:

    ```bash
    docker image ls | grep oracle_hardhat
    ```

3. **Prepare the keys file.** Within the service folder, prepare a JSON file `keys.json` containing the wallet address and the private key for each of the agents that make up the service.

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

4. **Build the deployment.** Within the service folder, execute the command below to build the service deployment in dev mode.

    ```bash
    autonomy deploy build keys.json --dev --packages-dir ~/git/open-autonomy/packages --open-autonomy-dir ~/git/open-aea/ --open-aea-dir ~/git/open-autonomy/
    ```

    You must modify the paths in the command above aproppriately, pointing to:

    * the path to the local registry (/packages directory),
    * the path to the local {{open_autonomy_repository}},
    * the path to the local {{open_aea_repository}}.

    This will create a deployment environment in dev mode within the `./abci_build` folder.

5. **Run the service.** Navigate to the deployment environment folder (`./abci_build`) and run the deployment locally.

    ```bash
    cd abci_build
    autonomy deploy run
    ```

    You can cancel the local execution by pressing `Ctrl-C`.

## Hot reload

Once the agents are running, you can make changes to the agent's code as well as the local {{open_aea_repository}}, and it will trigger the service restart.

The trigger is caused by any Python file closing in either the `open-autonomy/packages` or the `open-aea/` directory. So even if you haven't made any change and still want to restart the service, just open any Python file press `Ctrl+S` or save it from the file menu and it will trigger the restart.
