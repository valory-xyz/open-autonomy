# Quick Start

The purpose of this quick start is to get you up and running with the {{open_autonomy}} framework for agent service development as quickly as possible.
The overall pipeline with the framework is summarized in the figure below:

<figure markdown>
![](./images/pipeline.svg)
<figcaption>Overall pipeline to deploy an agent service with the Open Autonomy framework</figcaption>
</figure>

The dashed arrows in the figure denote the "entry points" for a developer in the pipeline. For example, if the developer is satisfied with some agent available in the agent registry, then they can skip the first step about defining agent components, and fetch that agent directly. We will give more detail about the pipeline below.



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

Follow the steps indicated in the diagram to define and build and deploy locally an example agent service.
In this case, we consider the [Hello World agent service](https://docs.autonolas.network/service_example/), which is a service for demonstration purposes.

The steps defined in the figure above are materialized as follows:

1. **Component provision:** The developer ensures that the agent components are available, either by programming them from scratch using the {{open_aea}} framework, or fetching them from the Component Registry. Each agent service needs one or more underlying {{fsm_app}}(s) that define the service business logic. The {{open_autonomy}} framework contains packages with base classes that help define {{fsm_app}}s.
    - In our case, we don't need to provision or define any component, since we will fetch an agent from the registry in the next step.
2. **Agent definition:** The developer ensures that the agents that make up the service are available, either by defining them  using the {{open_aea}} framework, or by fetching them from the Agent Registry.
    - Execute the following commands:
    ```bash
    aea init --reset --author default_author --ipfs --remote
    aea fetch valory/hello_world:0.1.0:QmcZVfH6de4Mfg28a7SKRrVJMkvPcPqhP1wfcn6pkeQoLi --remote
    cd hello_world
    aea install
    aea generate-key ethereum
    aea add-key ethereum
    ```
    This will retrieve the Hello World agent. You can optionally also execute `aea run` to test a single instance of the agent.
3. **Service definition:** The developer produces a service definition based on the corresponding agents, or it fetches a service from the Service Registry.
    - Execute
    ```bash
    make clean
    autonomy deploy build image valory/hello_world --dependencies
    autonomy deploy build image valory/hello_world
    autonomy deploy build deployment valory/hello_world deployments/keys/keys.json
    ```
4. **Service deployment:** Once the service is defined, the developer can use the {{open_autonomy}} CLI to deploy the service.
    - Execute
    ```bash
    cd hello_world_build/
    docker-compose up --force-recreate
    ```


## Deploy a local agent service

3. Get, build and install your agent

5. Run your agent. More info on this hello world example on the [Example of a service](https://docs.autonolas.network/service_example/) section.
```bash
aea run
```
