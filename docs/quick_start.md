

# Quick Start

The purpose of this quick start is to get you up and running with the {{open_autonomy}} framework for agent service development as quickly as possible.
The overall pipeline with the framework is summarized in the figure below:

<figure markdown>
![](./images/pipeline.svg)
<figcaption>Overall pipeline to deploy an agent service with the Open Autonomy framework</figcaption>
</figure>

The steps defined in the figure above are materialized as follows:

1. **Component provision:** The developer ensures that the agent components are available, either by programming them from scratch using the {{open_aea}} framework, or fetching them from the Component Registry. Each agent service needs one or more underlying {{fsm_app}}(s) that define the service business logic. The {{open_autonomy}} framework contains packages with base classes that help define {{fsm_app}}s.

2. **Agent definition:** The developer ensures that the agents that make up the service are available, either by defining them  using the {{open_aea}} framework, or by fetching them from the Agent Registry.

3. **Service definition:** The developer produces a service definition based on the corresponding agents, or it fetches a service from the Service Registry. Agent operators register agent instances against the service.

4. **Service deployment:** Once the service is defined, the developer can use the {{open_autonomy}} CLI to deploy the service.

The dashed arrows in the figure denote the "entry points" for a developer in the pipeline. For example, if the developer is satisfied with some agent available in the agent registry, then they can skip the first step about defining agent components, and fetch that agent directly. We will give more detail about the pipeline below.

The goal of this quick start guide is to showcase steps 3-4 from the pipeline. That is, how to execute a (local) deployment of a demonstration service. We will cover the particularities of the components that make up agents in an agent service in other sections of the documentation.


## Requirements

Ensure that your machine satisfies the following requirements:

- [Python](https://www.python.org/) `>= 3.7` (recommended `>= 3.10`)
- [Pip](https://pip.pypa.io/en/stable/installation/)
- [Pipenv](https://pipenv.pypa.io/en/latest/install/) `>=2021.x.xx`
- [Docker Engine](https://docs.docker.com/engine/install/)
- [Docker Compose](https://docs.docker.com/compose/install/)


## Setup

1. Setup the environment. Remember to use the Python version you installed, here we use 3.10 as reference:
```bash
touch Pipfile && pipenv --python 3.10 && pipenv shell
```

2. Install {{open_autonomy_api}}:
```bash
pip install open-autonomy
```

3. Initialize the framework to work with the remote IPFS registry.
```bash
autonomy init --remote
```

## Deploy a Local Agent Service

!!! note
    On **MacOS** and **Windows**, running Docker containers requires having Docker Desktop running as well. If you're using one of those systems, remember to start Docker Desktop
    before you run agent services.


Follow the steps indicated below to download a demonstration agent service from the Service Registry, and deploy it locally using Docker Compose.
In this case, we consider the [Hello World agent service](./hello_world_agent_service.md).

1. Use the CLI to download the `valory/hello build` service. 
    ```bash
    autonomy fetch valory/hello_world:0.1.0:bafybeig7xzomdgsac76ooteaoyeibfanp36octjlaondrpmyx5yrpxdlwy --remote --service
    cd hello_world
    ```
    
2. Prepare a JSON file `keys.json` containing the addresses and keys of the four agents that make up the [Hello World agent service](./hello_world_agent_service.md). Below you have some sample keys for testing:

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


3. Build the required image
    ```bash
    autonomy build-image
    ```
    The command above generates the required images to run the agent service.

4. Build a deployment setup for the [Hello World agent service](./hello_world_agent_service.md):
    ```bash
    autonomy deploy build keys.json
    ```

    This will build the deployment setup required to run the service locally.
    !!!note
        It is also possible to generate a deployment using a local service definition. See the [CLI section](./autonomy.md) for the complete details.

5. The build configuration will be located in `./abci_build`. Run the deployment using
    ```bash
    cd abci_build
    autonomy deploy run
    ```

    This will deploy a local [Hello World agent service](./hello_world_agent_service.md) with four agents connected to four Tendermint nodes.

6. The logs of a single agent or node can then be inspected with, e.g.,
    ```bash
    docker logs {container_id} --follow
    ```
    where `{container_id}` refers to the Docker container ID for either an agent
    (`abci0`, `abci1`, `abci2` and `abci3`) or a Tendermint node (`node0`, `node1`, `node2` and `node3`).
