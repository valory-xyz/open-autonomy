The purpose of this guide is to provide a step-by-step instructions on how to install the {{open_autonomy}} framework and use a number of CLI commands to run a [Hello World agent service](../hello_world_agent_service.md) as a local deployment. More concretely, in this guide, you will end up running:

  - 4 Docker containers implementing the 4 agents of the service, and
  - 4 Docker containers implementing one Tendermint node for each agent.

Having completed this guide, you can take a look at the [overview of the development process](./overview_of_the_development_process.md) with the {{open_autonomy}} framework, and continue with the rest of the guides in this section.


## Requirements

Ensure that your machine satisfies the following requirements:

- [Python](https://www.python.org/) `>= 3.7` (recommended `>= 3.10`)
- [Pip](https://pip.pypa.io/en/stable/installation/)
- [Pipenv](https://pipenv.pypa.io/en/latest/install/) `>=2021.x.xx`
- [Docker Engine](https://docs.docker.com/engine/install/)
- [Docker Compose](https://docs.docker.com/compose/install/)


## Setup
1. Create a workspace folder:
```bash
mkdir my_workspace
cd my_workspace
```

2. Setup the environment. Remember to use the Python version you have installed. Here we are using 3.10 as reference:
```bash
touch Pipfile && pipenv --python 3.10 && pipenv shell
```

3. Install the {{open_autonomy}} framework:
```bash
pip install open-autonomy
```

4. Initialize the framework to work with the remote [IPFS](https://ipfs.io) registry. This means that when the framework will be fetching a component, it will do so from the [IPFS](https://ipfs.io):
    ```bash
    autonomy init --remote --ipfs
    ```

    !!!info
        The InterPlanetary File System ([IPFS](https://ipfs.io)) is a protocol, hypermedia and file sharing peer-to-peer network for storing and sharing data in a global, distributed file system. {{open_autonomy}} can use components stored in the [IPFS](https://ipfs.io), or stored locally.

## Deploy a local agent service

!!! note
    On **MacOS** and **Windows**, running Docker containers requires having Docker Desktop running as well. If you're using one of those operating systems, remember to start Docker Desktop
    before you run agent services.


Now, we are in position to use the {{open_autonomy}} CLI to fetch the agent service from the remote registry, and deploy it locally.

1. Use the CLI to fetch the [Hello World agent service](../hello_world_agent_service.md). This will connect to the remote registry and download the service specification to the `hello_world` folder:
    ```bash
    autonomy fetch valory/hello_world:0.1.0:bafybeihrng5d73bsctkjilgc2lxkn4ditsbf3c7vqmt6wpi45zglq42i2e --service
    cd hello_world
    ```


2. Prepare a JSON file `keys.json` containing the addresses and keys of the four agents that make up the agent service. Below you have some sample keys for testing:

    !!! warning "Important"
        Use these keys for testing purposes only. **Never use these keys in a production environment or for personal use.**

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


3. Build the Docker image of the service agents:
    ```bash
    autonomy build-image
    ```
    After the command finishes building it, you can see that it has created the image by executing:
    ```bash
    docker image ls | grep hello_world
    ```

4. Build the deployment setup for the service:
    ```bash
    autonomy deploy build keys.json
    ```

5. The build configuration will be located in `./abci_build`. Run the deployment using
    ```bash
    cd abci_build
    autonomy deploy run
    ```

    This will deploy the [Hello World agent service](../hello_world_agent_service.md) locally with four agents connected to four Tendermint nodes.

    At this point you should see a (verbose) output of the agent logs, which should look something like this:
    ```bash
    (...)

    abci0    | [2022-01-01 00:00:00,000] [INFO] [agent] arrived block with timestamp: 2022-00-00 00:00:00.000000
    abci0    | [2022-01-01 00:00:00,000] [INFO] [agent] current AbciApp time: 2022-00-00 00:00:00.000000
    abci0    | [2022-01-01 00:00:00,000] [INFO] Created a new local deadline for the next `begin_block` request from the Tendermint node: 2022-00-00 00:00:00.000000
    abci2    | [2022-01-01 00:00:00,000] [INFO] [agent] 'select_keeper' round is done with event: Event.DONE
    abci2    | [2022-01-01 00:00:00,000] [INFO] [agent] scheduling timeout of 30.0 seconds for event Event.ROUND_TIMEOUT with deadline 2022-00-00 00:00:00.000000
    abci2    | [2022-01-01 00:00:00,000] [INFO] [agent] Entered in the 'print_message' round for period 2
    abci2    | [2022-01-01 00:00:00,000] [INFO] [agent] Entered in the 'print_message' behaviour
    abci2    | Agent agent (address 0x976EA74026E726554dB657fA54763abd0C3a0aa9) in period 2 says: HELLO WORLD!
    abci2    | [2022-01-01 00:00:00,000] [INFO] [agent] printed_message=Agent agent (address 0x976EA74026E726554dB657fA54763abd0C3a0aa9) in period 2 says: HELLO WORLD!

    (...)
    ```


6. The logs of a single agent or node can then be inspected with, e.g.,
    ```bash
    docker logs {container_id} --follow
    ```
    where `{container_id}` refers to the Docker container ID for either an agent
    (`abci0`, `abci1`, `abci2` and `abci3`) or a Tendermint node (`node0`, `node1`, `node2` and `node3`).

    Try to inspect the service agent logs yourself and identify when they say "HELLO WORLD!"
