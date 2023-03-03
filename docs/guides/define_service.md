Given an existing agent, either developed by yourself on the previous step, or fetch from the remote registry, the next step consists in defining the agent service and tuning its configuration options.

<figure markdown>
![](../images/development_process_define_service.svg)
<figcaption>Part of the development process covered in this guide</figcaption>
</figure>

## What you will learn

In this guide, you will learn how to define the agent service itself, and how to define what agent will the service be using.

Before starting this guide, ensure that your machine satisfies the framework requirements and that you have followed the [set up guide](./set_up.md). As a result you should have a Pipenv workspace folder.

## Step-by-step instructions

To create a service with an existing agent published on a local or remote repository you need to identify the **public ID** and the **package hash** of the agent. It can be some agent that you have developed, or you can reuse an existing agent from a repository.
You can browse the [list of packages](../package_list.md) available in the default remote IPFS registry.
For this example, we consider the `valory/hello_world` agent, used in the [Hello World service](../demos/hello_world_demo.md), whose public ID and hash are

```
valory/hello_world:0.1.0:bafybeicealdcbxjdejskntddizntwqmlpyxa2ujaxnw2cgy73x3swldwcq
```

You can view the agent contents stored in the IPFS registry [here](https://gateway.autonolas.tech/ipfs/bafybeicealdcbxjdejskntddizntwqmlpyxa2ujaxnw2cgy73x3swldwcq/hello_world/).

!!! note
    Future releases of the {{open_autonomy}} framework will provide convenient commands to browse and discover existing registered components. For now, we assume that we already know the IPFS hash of the agent.

1. **Create the  the service.** In the workspace folder, create an empty folder with the service name. Within this folder, create:

    * a `README.md` file, where you can write a description of the service, and
    * a service configuration file `service.yaml`, where you will indicate the [IPFS](https://ipfs.io/) hash of the agent.

    ```bash
    mkdir your_service
    cd your_service
    touch README.md
    touch service.yaml
    ```

2. **Define the service configuration file.** The service configuration file `service.yaml` is where the parameters of the agent service are defined, including the particular agent that composes the service.
You must populate the contents of the `service.yaml`. There are a number of mandatory parameters that you need to provide, as well as the service-level overrides. Learn more about the details of [the service configuration file](./service_configuration_file.md) in the next section.

    ???+ example "Example of a service configuration file `service.yaml`"
        Below you can find an example of the `service.yaml` for the [Hello World service](../demos/hello_world_demo.md).
        ```yaml
        name: hello_world
        author: valory
        version: 0.1.0
        description: A simple demonstration of a simple ABCI application
        aea_version: '>=1.0.0, <2.0.0'
        license: Apache-2.0
        fingerprint:
          README.md: <ipfs_hash>
        fingerprint_ignore_patterns: []
        agent: valory/hello_world:0.1.0:<ipfs_hash>
        number_of_agents: 4
        ---
        extra:
          benchmark_persistence_params:
            args: &id002
              log_dir: /benchmarks
          params_args:
            args:
              setup: &id001
                all_participants:
                - '0x0000000000000000000000000000000000000000'
                safe_contract_address: '0x0000000000000000000000000000000000000000'
                consensus_threshold: null
        public_id: valory/hello_world_abci:0.1.0
        type: skill
        0:
          models:
            params:
              args:
                service_registry_address: null
                share_tm_config_on_startup: false
                on_chain_service_id: null
                setup: *id001
                hello_world_message: ${HELLO_WORLD_STRING_0:str:HELLO_WORLD! (from Agent 0)}
            benchmark_tool:
              args: *id002
        1:
          models:
            params:
              args:
                service_registry_address: null
                share_tm_config_on_startup: false
                on_chain_service_id: null
                setup: *id001
                hello_world_message: ${HELLO_WORLD_STRING_1:str:HELLO_WORLD! (from Agent 1)}
            benchmark_tool:
              args: *id002
        2:
          models:
            params:
              args:
                service_registry_address: null
                share_tm_config_on_startup: false
                on_chain_service_id: null
                setup: *id001
                hello_world_message: ${HELLO_WORLD_STRING_2:str:HELLO_WORLD! (from Agent 2)}
            benchmark_tool:
              args: *id002
        3:
          models:
            params:
              args:
                service_registry_address: null
                share_tm_config_on_startup: false
                on_chain_service_id: null
                setup: *id001
                hello_world_message: ${HELLO_WORLD_STRING_3:str:HELLO_WORLD! (from Agent 3)}
            benchmark_tool:
              args: *id002
        ---
        public_id: valory/ledger:0.19.0
        type: connection
        config:
          ledger_apis:
            ethereum:
              address: ${SERVICE_HELLO_WORLD_RPC:str:http://host.docker.internal:8545}
              chain_id: 31337
              poa_chain: false
              default_gas_price_strategy: eip1559
        ```

3. **Use a local deployment to test the service.** This is the recommended approach in order to test your agent service before you publish it to a remote registry. Follow the instructions in the [local deployment guide](./deploy_service.md#local-deployment) to run the local deployment. Note that this process should be somewhat familiar to you if you have followed the [quick start guide](./quick_start.md).

4. **Publish the service.** Once you have finished coding and testing the service, [pubish it on the local and/or remote registry](./publish_fetch_packages.md#publish-a-service-on-a-registry). Note down the service public ID and the package hash:

    === "Publish to the remote registry"

        ```bash
        autonomy publish
        ```

    === "Publish to the remote registry"

        ```bash
        (This section will be updated soon)
        ```
