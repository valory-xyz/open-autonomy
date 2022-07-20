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

Ensure your machine satisfies the following requirements:

- Python `>= 3.7` (recommended `>= 3.10`)
- [Tendermint](https://docs.tendermint.com/master/introduction/install.html) `==0.34.19`
- [Pipenv](https://pipenv.pypa.io/en/latest/install/) `>=2021.x.xx`

## Setup

1. Setup the environment
```bash
export OPEN_AEA_IPFS_ADDR="/dns/registry.autonolas.tech/tcp/443/https"
touch Pipfile && pipenv --python 3.10 && pipenv shell
```

2. Install {{open_autonomy}}
```bash
pip install open-autonomy
```

## Deploy a local agent service

Follow the steps indicated below to download a demonstration agent service from the Service Registry, and deploy it locally using Docker Compose.
In this case, we consider the [Hello World agent service](https://docs.autonolas.network/service_example/).

1. Prepare a JSON file `keys.json` containing the addresses and keys of the four agents that make up the [Hello World agent service](https://docs.autonolas.network/service_example/). Below you have some sample keys for testing:
    ```json
    [
        {
            "address": "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
            "private_key": "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
        },
        {
            "address": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
            "private_key": "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d"
        },
        {
            "address": "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC",
            "private_key": "0x5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a"
        },
        {
            "address": "0x90F79bf6EB2c4f870365E785982E1f101E93b906",
            "private_key": "0x7c852118294e51e653712a81e05800f419141751be58f605c371e15141b007a6"
        }
    ]
    ```


2. Use the CLI to townload and build the images to deploy the [Hello World agent service](https://docs.autonolas.network/service_example/):
    ```bash
      autonomy deploy build deployment valory/hello_world:bafybeidlqr3bwzb2zxxxt7fcgrucjx6kbnqdynr77slybnampvjenuic2i keys.json
    ```
    The command above generates the required images to run the agent service using the keys provided in the `keys.json` file. In this case, we are accessing the service definition located in the Service Registry.

    !!!note
        It is also possible to generate a deployment using a local service definition. See the [CLI section](./autonomy.md) for the complete details.

3. The build configuration will be located in `./abci_build`. Execute `docker-compose` as indicated below. This will deploy a local [Hello World agent service](https://docs.autonolas.network/service_example/) with four agents connected to four Tendermint nodes.
    ```bash
    cd abci_build
    docker-compose up --force-recreate
    ```

4. The logs of a single agent or node can then be inspected with, e.g.,
    ```bash
    docker logs {container_id} --follow
    ```
