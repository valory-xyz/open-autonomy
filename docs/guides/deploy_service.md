Deploying a service with the {{open_autonomy}} framework requires that you have an already available service configuration, which you could be a service created from scratch, fetched from the [IPFS](https://ipfs.io/), or already registered in the on-chain protocol.

## What you will learn

In this guide, you will learn how to:

* Create a local deployment for testing purposes of
  * a service stored in your machine.
  * a service available in the on-chain registry.
* Create a cloud deployment of a service.

Before starting this guide, ensure that your machine satisfies the framework requirements and that you have followed the [set up guide](./set_up.md). As a result you should have a Pipenv workspace folder.

## Local deployment

Local deployments of a service are recommended to test your service before you publish it to a remote registry. Open a terminal and follow the steps below.

1. **Build the agents' image.** Navigate to the local folder of the service that you want to deploy, that is, the folder containing the `service.yaml` file, and build the Docker image of the service agents:

    ```bash
    cd <service_folder>
    autonomy build-image
    ```

    After the command finishes building the image, you can see that it has been created by executing:

    ```bash
    docker image ls | grep <service_agent_name>
    ```

2. **Prepare the keys file.** Prepare a JSON file `keys.json` containing the wallet address and the private key for each of the agents that make up the service.

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

3. **Build the deployment.** Within the service folder, execute the command below to build the service deployment.

    ```bash
    autonomy deploy build keys.json --aev -ltm
    ```

    This will create a deployment environment within the `./abci_build` folder with the following structure:

    ```bash
    abci_build/
    ├── agent_keys
    │   ├── agent_0
    │   ├── agent_1
    │   ├── agent_2
    │   └── agent_3
    ├── nodes
    │   ├── node0
    │   ├── node1
    │   ├── node2
    │   └── node3
    ├── persistent_data
    │   ├── benchmarks
    │   ├── logs
    │   ├── tm_state
    │   └── venvs
    └── docker-compose.yaml
    ```

4. **Run the service.** Navigate to the deployment environment folder (`./abci_build`) and run the deployment locally.

    ```bash
    cd abci_build
    autonomy deploy run
    ```

    You can cancel the local execution by pressing `Ctrl-C`.

## On-chain deployment

The {{open_autonomy}} framework provides a convenient interface for services that are [registered in the on-chain protocol](./register_packages_on_chain.md##register-a-service).

  1. **Find the service ID.** Explore the [services section](https://protocol.autonolas.network/agents) of the protocol frontend, and note the ID of the service that you want to deploy. The service must be in [Deployed state](https://docs.autonolas.network/protocol/life_cycle_of_a_service/#deployed).

  2. **Execute the service deployment.** Execute the following command

    ```bash
    autonomy deploy from-token <ID> keys.json --use-goerli
    ```
    where `keys.json` contains the addresses and keys of (some of) the registered agents in the service.

!!! warning "Important"
    When deploying a service registered on-chain, the framework automatically overrides a number of configuration arguments (under `setup`) in the agent containers with the values registered in the on-chain protocol:

    === "skill.yaml"

    ```yaml
    (...)
    models:
      params:
        args:
          setup:
            all_participants: # Overridden with the registered values
            safe_contract_address: # Overridden with the registered values
            consensus_threshold: # Overridden with the registered values
    ```

## Cloud deployment

!!! info
    This section will be added soon.
