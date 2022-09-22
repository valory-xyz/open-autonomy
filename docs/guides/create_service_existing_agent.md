The typical use case that this guide intends to illustrate is where a service owner wants to use existing agents to run its own service
with a custom configuration. For example, an oracle service customized to serve data of their interest.


##What you will learn
In this guide, we will show how to:

  - Create a service definition using an already available agent on the  [IPFS](https://ipfs.io/).
  - Test the service using a local deployment.
  - Publish the service on the [IPFS](https://ipfs.io/).
  - Register the service in the on-chain protocol. We will be using the [Görli testnet](https://goerli.net/).
  - Deploy the registered service.

If you recall the [overview of the development process](./overview_of_the_development_process.md), this roughly consists in steps 4, 5, and 6. For illustration purposes, we will also be using the agents from the [Hello World agent service](../hello_world_agent_service.md) and we will create a new (but functionally equivalent) "Hello World 2 agent service". To complete all the steps in this guide, you should have a [Görli testnet](https://goerli.net/) wallet address (e.g., [Metamask](https://metamask.io/)) with some GörliETH funds in it.

Before starting this guide, ensure that your machine satisfies the framework requirements and that you have followed the [set up guide](./set_up.md). As a result you should have a Pipenv workspace folder.

## Step-by-step instructions

1. **Identify the IPFS hash of the agent.** This can be some agent with the desired functionality for which you already know the hash, or you can browse it in the repository of a published agent. For this example, we consider the `hello_world` agent, whose hash is

    ```
    valory/hello_world:0.1.0:bafybeicealdcbxjdejskntddizntwqmlpyxa2ujaxnw2cgy73x3swldwcq
    ```

    If you want, you can browse the agent contents stored in the IPFS [here](https://gateway.autonolas.tech/ipfs/bafybeicealdcbxjdejskntddizntwqmlpyxa2ujaxnw2cgy73x3swldwcq/hello_world/).

    !!!note
        Future releases of the {{open_autonomy}} framework will provide convenient commands to browse and discover existing registered components. For now, we assume that we already know the IPFS hash of the agent.

2. **Create the service definition.** Create an empty folder with the service name (e.g., `hello_world_2_service`). Inside that folder, create a `README.md` file, where you can write a description of the service, and a service definition file `service.yaml`, where the agent IPFS hash must be specified:

    ```bash
    mkdir hello_world_2_service
    cd hello_world_2_service
    touch README.md
    touch service.yaml
    ```

    !!!info "The structure of the service definition file"
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
        public_id: valory/ledger:0.1.0
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

        - `fingerprint`: this field contains the IPFS hash for all the files inside the service folder, except the `service.yaml` itself.
        - `fingerprint_ignore_patterns`: filename patterns whose matches will be ignored.
        - `agent`: references the agent that the service is going to use, in the format `public_id:ipfs_hash`.

        Following the mandatory parameters of the service definition, there is a number of parameter overrides following the operator `---`, which set parameters for the agent components. In this case, the service is setting values for some parameters parameters in the `hello_world_abci` skill, and in the `ledger` connection. For now, you can safely ignore that part of the `service.yaml`file.

3. **Test the service using a local deployment.** This is the recommended approach in order to test your agent service before you publish it to the IPFS. Follow [these instructions](./deploy_service.md#step-by-step-instructions-local-deployment) to run the local deployment. Note that this process should be familiar to you if you have followed the [quick start](./quick_start.md) guide.


4. **Publish the service on the [IPFS](https://ipfs.io/).** This will make the service available for other developers to fetch it.

    Now publish the service by executing the following command within the service parent folder:

    ```bash
    autonomy publish --remote
    ```

    You should see an output similar to this:
    ```
    Published service package with
        PublicId: your_name/hello_world_2_service:0.1.0
        Package hash: bafybei01234567890abcdefghijklmnopqrstuvwxyz01234567890abcd
    ```
    Note down these values. You can browse how your service has been uploaded to the [IPFS](https://ipfs.io/)
    by accessing the gateway https://gateway.autonolas.tech/ipfs/`<hash>`, where `<hash>` is the IPFS hash value returned by the previous command.

5. **Register the service in the on-chain protocol.** Now it's time to interact with the on-chain protocol through a deployed smart contract in the [Görli testnet](https://goerli.net/). We will be using a convenient protocol front-end to interact with the contract.

    1. Make sure you have a [Metamask](https://metamask.io/) wallet with a [Görli testnet](https://goerli.net/) address and some funds on it.

    2. Access [the on-chain protocol frontend](https://protocol.autonolas.network/), and connect your [Metamask](https://metamask.io/) wallet.

    3. Navigate to the [agents section](https://protocol.autonolas.network/agents). You will find there that the Hello World agent is the agent with ID 1.

    4. Navigate to the [services section](https://protocol.autonolas.network/services), and press "Register". There are some data that need to be input in this form, whereas additional data is accessed through the "Generate Hash & File" button. Let's complete the main page first. You must insert:

        - Owner Address: your wallet address starting by `0x...`,
        - Canonical agent Ids: 1,
        - No. of slots to canonical agent Ids: 4,
        - Cost of agent instance bond: 0.01 GörliETH,
        - Threshold: 3.

    5. By pressing "Generate Hash & File" you need to input further data. Here is some example:

        - Name: Hello World 2 Service,
        - Description: This service says Hello World,
        - Version: 0.1.0,
        - Package hash: This is the hash starting by `bafybei...` you obtained when published the service on [IPFS](https://ipfs.io/).
        - NFT Image URL: An URL pointing to an image. You can use https://gateway.autonolas.tech/ipfs/Qmbh9SQLbNRawh9Km3PMEDSxo77k1wib8fYZUdZkhPBiev for testing purposes.


    6. Press "Save File & Generate Hash"
    7. Press "Submit". Your  [Metamask](https://metamask.io/) wallet will ask you to approve the transaction.


    You should see a message indicating that the service has been registered successfully. Congratulations! Your service is now registered and secured on-chain.

6. **Deploy the registered service.** Finally, you can try to run a deployment for the on-chain service that you just have registered. You will need a `keys.json` file, and the service token ID that you can find in
https://protocol.autonolas.network/services/. Execute the command

    ```bash
    autonomy deploy from-token ON_SERVICE_TOKEN_ID keys.json --use-goerli
    ```
    and you should be able to see your service running locally. We will discuss in more detail the deployment process in [this guide](./deploy_service.md).
