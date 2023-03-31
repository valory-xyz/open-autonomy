The next step consists in defining the service agent. All agents in the service share the same code base.
However, each operator can configure their agent instance. For example, in an oracle service,
each operator can define a different data provider.

<figure markdown>
![](../images/development_process_define_agent.svg)
<figcaption>Part of the development process covered in this guide</figcaption>
</figure>

## What you will learn

This guide covers step 3 of the [development process](./overview_of_the_development_process.md). You will learn how to define the service agent, how to add the {{fsm_app}}, and how to add other existing components required by your agent.

You must ensure that your machine satisfies the framework requirements and that you have [set up the framework](./set_up.md#set-up-the-framework) and [a local registry](./set_up.md#set-up-the-local-registry). As a result you should have a Pipenv workspace folder with a local registry (`./packages`) in it.

## Step-by-step instructions

In order to deploy and run a service you need an agent with a working {{fsm_app}}. We base this guide in a default {{fsm_app}} available in the remote registry, namely, the `hello_world_abci` {{fsm_app}}. As a result, we will define an agent implementing a functionality equivalent to the [Hello World service](../demos/hello_world_demo.md). You can, of course, use your own {{fsm_app}} to define your agent.

!!! warning "Important"

    If you have just [scaffolded an {{fsm_app}} in the previous step](./code_fsm_app_skill.md) but you didn't complete coding the business logic, then an agent that uses that {{fsm_app}} will fail to run. For this reason, we recommend that you use the `hello_world_abci` {{fsm_app}} in a first read of this guide.

1. **Ensure that the components required by your agent are in the local registry.** All the required components by your agent and their dependencies must be downloaded to the local registry. You can read [how to add missing components to the local registry](#).
If you have [set up the local registry](./set_up.md#set-up-the-local-registry) with the required components to follow these guides, you do not need to take any further action.

2. **Create the agent configuration file.** Create a folder for your agent in the local registry (`./packages`). Pay attention to the correct format of the folder:

    ```bash
    mkdir -p ./packages/your_name/agents/your_agent/
    ```

    Within the agent folder, create the agent configuration file `aea-config.yaml`:

    ```bash
    touch ./packages/your_name/agents/your_agent/aea-config.yaml
    ```

    This file must contain:

      * A number of mandatory parameters.

        !!! warning "Important"

            Ensure that `author` and `agent_name` match the path within the local registry.

      * A reference to the {{fsm_app}} skill.
      * References to other components required by the agent (or dependencies of the {{fsm_app}} skill), under the relevant sections.
      * Configuration overrides that specify values for component parameters. These overrides are separated by YAML document separators `---` and will be discussed in a further section.

    ???+ example "Example of an `aea-config.yaml` file"

        This is a complete example of an agent configuration file that uses the `hello_world_abci` {{fsm_app}} and overrides some required component parameters. 

        You will notice that there are a lot of parameters to be configured for the required components. For an initial read of this guide, you can ignore these parameters, but it is important that you identify how the references to the particular component parameter being overridden.

        ```yaml
        agent_name: your_agent
        author: your_name
        version: 0.1.0
        license: Apache-2.0
        description: Example of an agent.
        aea_version: '>=1.0.0, <2.0.0'
        fingerprint: {}
        fingerprint_ignore_patterns: []
        connections:
        - valory/abci:0.1.0:bafybeienpqzsym3rg7nnomd6mxgbt4didwd4wfj72oadde27trdmcgsu5y
        - valory/http_client:0.23.0:bafybeidykl4elwbcjkqn32wt5h4h7tlpeqovrcq3c5bcplt6nhpznhgczi
        - valory/ipfs:0.1.0:bafybeie46fu7mv64q72dwzoxg77zbiv3pzsigzjk3rehjpm47cf3y77mha
        - valory/ledger:0.19.0:bafybeighon6i2qfl2xrg7t3lbdzlkyo4v2a7ayvwso7m5w7pf2hvjfs2ma
        - valory/p2p_libp2p_client:0.1.0:bafybeidwcobzb7ut3efegoedad7jfckvt2n6prcmd4g7xnkm6hp6aafrva
        contracts: []
        protocols:
        - open_aea/signing:1.0.0:bafybeibqlfmikg5hk4phzak6gqzhpkt6akckx7xppbp53mvwt6r73h7tk4
        - valory/abci:0.1.0:bafybeig3dj5jhsowlvg3t73kgobf6xn4nka7rkttakdb2gwsg5bp7rt7q4
        - valory/http:1.0.0:bafybeifyoio7nlh5zzyn5yz7krkou56l22to3cwg7gw5v5o3vxwklibhty
        - valory/ipfs:0.1.0:bafybeihlgai5pbmkb6mjhvgy4gkql5uvpwvxbpdowczgz4ovxat6vajrq4
        skills:
        - valory/abstract_abci:0.1.0:bafybeigg5ofide2gxwgjvljjgpyy6ombby7ph6pg7erj3h6itduwpn6pqu
        - valory/abstract_round_abci:0.1.0:bafybeicn5utwviq46ubguok5rl5go4hb7oxluj7t6bja2ut4epjw2hevei
        - valory/hello_world_abci:0.1.0:bafybeigidqcurxh3r3m7vxjfv2d4tvcpzvkhwj7r7owacn6jymzik75k7i
        default_ledger: ethereum
        required_ledgers:
        - ethereum
        default_routing: {}
        connection_private_key_paths: {}
        private_key_paths: {}
        logging_config:
          version: 1
          disable_existing_loggers: false
          formatters:
            standard:
              format: '[%(asctime)s] [%(levelname)s] %(message)s'
          handlers:
            logfile:
              class: logging.FileHandler
              formatter: standard
              filename: ${LOG_FILE:str:log.txt}
              level: INFO
            console:
              class: logging.StreamHandler
              formatter: standard
              stream: ext://sys.stdout
          loggers:
            aea:
              handlers:
              - logfile
              - console
              propagate: true
        dependencies:
          open-aea-ledger-ethereum:
            version: ==1.31.0
          open-aea-test-autonomy:
            version: ==0.10.0.post2
        default_connection: null
        ---
        public_id: valory/hello_world_abci:0.1.0
        type: skill
        models:
          benchmark_tool:
            args:
              log_dir: ${str:/benchmarks}
          params:
            args:
              hello_world_message: ${str:HELLO_WORLD!}
              service_registry_address: ${str:null}
              share_tm_config_on_startup: ${bool:false}
              on_chain_service_id: ${int:null}
              setup:
                all_participants: ${list:[]}
                safe_contract_address: ${str:'0x0000000000000000000000000000000000000000'}
                consensus_threshold: ${int:null}
              tendermint_url: ${str:http://localhost:26657}
              tendermint_com_url: ${str:http://localhost:8080}
        ---
        public_id: valory/abci:0.1.0
        type: connection
        config:
          target_skill_id: valory/hello_world_abci:0.1.0
          host: ${str:localhost}
          port: ${int:26658}
          use_tendermint: ${bool:false}
        ---
        public_id: valory/ledger:0.19.0
        type: connection
        config:
          ledger_apis:
            ethereum:
              address: ${str:http://localhost:8545}
              chain_id: ${int:31337}
              poa_chain: ${bool:false}
              default_gas_price_strategy: ${str:eip1559}
        ---
        public_id: valory/p2p_libp2p_client:0.1.0
        type: connection
        config:
          nodes:
          - uri: ${str:acn.staging.autonolas.tech:9005}
            public_key: ${str:02d3a830c9d6ea1ae91936951430dee11f4662f33118b02190693be835359a9d77}
          - uri: ${str:acn.staging.autonolas.tech:9006}
            public_key: ${str:02e741c62d706e1dcf6986bf37fa74b98681bc32669623ac9ee6ff72488d4f59e8}
        cert_requests:
        - identifier: acn
          ledger_id: ethereum
          message_format: '{public_key}'
          not_after: '2023-01-01'
          not_before: '2022-01-01'
          public_key: ${str:02d3a830c9d6ea1ae91936951430dee11f4662f33118b02190693be835359a9d77}
          save_path: .certs/acn_cosmos_9005.txt
        - identifier: acn
          ledger_id: ethereum
          message_format: '{public_key}'
          not_after: '2023-01-01'
          not_before: '2022-01-01'
          public_key: ${str:02e741c62d706e1dcf6986bf37fa74b98681bc32669623ac9ee6ff72488d4f59e8}
          save_path: .certs/acn_cosmos_9006.txt
        is_abstract: true
        ```

3. **Create an entry for your agent in the local registry.** Add the corresponding entry to the local registry index file (`./packages/packages.json`). You must add the entry to the `dev` section, because it is a component being developed by you. You can use a placeholder for its hash value, as it will be corrected afterwards:

	<!-- Use js instead of json lexer to support mkdocs-material comment features -->
    ```js
    {
      "dev": {
        "agent/your_name/your_agent/0.1.0": "bafybei0000000000000000000000000000000000000000000000000000",
        /* (1)! */
      },
      "third_party": {
        /* (2)! */
      }
    }
    ```
    
    1. Any other `dev` entries that you have go here. Entries must be comma-separated (`,`).
    2. Any other `third_party` entries that you have go here. Entries must be comma-separated (`,`).

    Update the package hashes. The command below will correct any hash mismatch in the `aea-config.yaml` file, as well as in the local registry index file (`./packages/packages.json`):

    ```bash
    autonomy packages lock
    ```
