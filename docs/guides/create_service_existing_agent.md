The typical use case that this guide intends to illustrate is where a service owner wants to use existing agents to run its own service
with a custom configuration. For example, an oracle service customized to serve data of their interest.


##What you will learn
In this guide, we will show how to:

  - Create a service definition using an already available agent on the  [IPFS](https://ipfs.io/).
  - Test the service using a local deployment.
  - Publish the service on the [IPFS](https://ipfs.io/).
  - Register the service in the on-chain protocol. We will be using the [Görli testnet](https://goerli.net/).
  - Deploy the registered service.

If you recall the [overview of the development process](./overview_of_the_development_process.md), this roughly consists in steps 4, 5, and 6. For illustration purposes, we will also be using the agents from the [Hello World agent service](../demos/hello_world_demo.md) and we will create a new (but functionally equivalent) "Hello World 2 agent service".

Before starting this guide, ensure that your machine satisfies the framework requirements and that you have followed the [set up guide](./set_up.md). As a result you should have a Pipenv workspace folder.

## Step-by-step instructions

1. **Identify the IPFS hash of the agent.** This can be some agent with the desired functionality for which you already know the hash, or you can browse it in the repository of a published agent. For this example, we consider the `hello_world` agent, whose hash is

    ```
    valory/hello_world:0.1.0:bafybeicealdcbxjdejskntddizntwqmlpyxa2ujaxnw2cgy73x3swldwcq
    ```

    You can browse the agent contents stored in the IPFS [here](https://gateway.autonolas.tech/ipfs/bafybeicealdcbxjdejskntddizntwqmlpyxa2ujaxnw2cgy73x3swldwcq/hello_world/).

    !!! note
        Future releases of the {{open_autonomy}} framework will provide convenient commands to browse and discover existing registered components. For now, we assume that we already know the IPFS hash of the agent.

        You can also check the [package list](../package_list.md) of {{open_autonomy}}, where you can find a number of sample agents.

2. **Create the service definition.** Create an empty folder with the service name (e.g., `hello_world_2_service`). Inside that folder, create a `README.md` file, where you can write a description of the service, and a service definition file `service.yaml`, where the agent IPFS hash must be specified. You will need the [IPFS](https://ipfs.io/) hash of the agent to populate the `servie.yaml` file:

    ```bash
    mkdir hello_world_2_service
    cd hello_world_2_service
    touch README.md
    touch service.yaml
    ```

    ??? example "Example of a `service.yaml` file"
        As its name suggests, the service definition file `service.yaml` is where
        the parameters of the agent service are defined, including the particular agent that composes the service. Here is an example of a `service.yaml` file:
        ```yaml
        name: hello_world_2_service
        author: your_name
        version: 0.1.0
        description: This is the Hello World 2 service.
        aea_version: '>=1.0.0, <2.0.0'
        license: Apache-2.0
        fingerprint:
          README.md: bafybeiapubcoersqnsnh3acia5hd7otzt7kjxekr6gkbrlumv6tkajl6jm
        fingerprint_ignore_patterns: []
        agent: valory/hello_world:0.1.0:bafybeicealdcbxjdejskntddizntwqmlpyxa2ujaxnw2cgy73x3swldwcq
        number_of_agents: 4
        ---
        benchmark_persistence_params:
          args: &id001
            log_dir: /benchmarks
        public_id: valory/hello_world_abci:0.1.0
        type: skill
        models:
          0:
          - benchmark_tool:
              args: *id001
          1:
          - benchmark_tool:
              args: *id001
          2:
          - benchmark_tool:
              args: *id001
          3:
          - benchmark_tool:
              args: *id001
        ---
        public_id: valory/ledger:0.19.0
        type: connection
        config:
          ledger_apis:
            ethereum:
              address: http://host.docker.internal:8545
              chain_id: 31337
              poa_chain: false
              default_gas_price_strategy: eip1559
        ```

        Most of the parameters in the YAML file are self-explanatory, but let us briefly discuss some of them:

        - `fingerprint`: this field contains the IPFS hash for all the files inside the service folder, except the `service.yaml` itself. To get the IPFS hash of a given file you can use the `autonomy hash` command, for example,
        ```bash
        autonomy hash one README.md
        ```

        - `fingerprint_ignore_patterns`: filename patterns whose matches will be ignored.
        - `agent`: references the agent that the service is going to use, in the format `public_id:ipfs_hash`.

        Following the mandatory parameters of the service definition, there is a number of parameter overrides following the operator `---`, which set parameters for the agent components. In this case, the service is setting values for some parameters parameters in the `hello_world_abci` skill, and in the `ledger` connection. For now, you can safely ignore that part of the `service.yaml`file.

3. **Use a local deployment to test the service.** This is the recommended approach in order to test your agent service before you publish it to the IPFS. Follow the instructions in the [local deployment guide](./deploy_service.md#local-deployment) to run the local deployment. Note that this process should be somewhat familiar to you if you have followed the [quick start guide](./quick_start.md).


4. **Publish the service.** This will make the service available for other developers to fetch and use it. This step is also required if you want to register the service in the on-chain registry. Follow the instructions in the [IPFS service publication guide](./publish_service.md) to have your service published.

5. **Register the service on-chain.** By registering the service in the on-chain registry you ensure that it is crypto-economically secured through the on-chain protocol. Follow the instructions in the [on-chain service registration guide](./register_packages_on_chain.md#register-a-service).


6. **Deploy the registered service.** Finally, you can try to run a deployment for the on-chain service that you just have registered. Follow the [on-chain deployment guide](./deploy_service.md#on-chain-deployment) to have your service up and running.
