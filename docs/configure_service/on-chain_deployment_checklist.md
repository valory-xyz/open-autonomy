This section details a requirement checklist that need to be satisfied so that your agent service can be properly deployed on-chain.

## Required {{fsm_app}} skill models

Ensure that your skill extends the following classes in the `models.py` file:

``` python
packages.valory.skills.abstract_round_abci.models.BenchmarkTool
packages.valory.skills.abstract_round_abci.models.BaseParams
```

You can define custom arguments for the skill, if required.

=== "Without custom arguments"

    ``` python
    from packages.valory.skills.abstract_round_abci.models import BenchmarkTool
    from packages.valory.skills.abstract_round_abci.models import BaseParams

    # (...)

    YourBenchmarkTool = BenchmarkTool
    YourSkillParams = BaseParams
    ```

=== "With custom arguments"

    ``` python
    from packages.valory.skills.abstract_round_abci.models import BenchmarkTool
    from packages.valory.skills.abstract_round_abci.models import BaseParams

    # (...)

    YourBenchmarkTool = BenchmarkTool

    class YourSkillParams(BaseParams):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self.your_custom_arg_1: str = self._ensure("your_custom_arg_1", kwargs, str)
            self.your_custom_arg_2: str = self._ensure("your_custom_arg_2", kwargs, str)            
            
            # (...)

            super().__init__(*args, **kwargs)
    ```

## Required arguments and overrides

Ensure that your {{fsm_app}} skill, agent and service configuration files (`skill.yaml`, `aea-config.yaml`, and `service.yaml`, respectively) define the appropriate arguments and overrides:

`skill.yaml`
:   Must define default/placeholder values for the arguments associated to the `YourSkillParams` class.

`aea-config.yaml`
:   Must define overrides for `valory/abci` connection, `valory/ledger` connection, `valory/p2p_libp2p_client` connection, and your {{fsm_app}} skill. Environment variables used for agent-level overrides can use the simplified syntax `${<type>:<default_value>}`.

`service.yaml`
:   Must define overrides for `valory/ledger` connection and your {{fsm_app}} skill (optionally, also for `valory/p2p_libp2p_client` connection). Environment variables used for service-level overrides use the syntax `${<env_var_name>:<type>:<default_value>}`. They will be [exported](../configure_service/service_configuration_file.md#export-to-environment-variables) as their upper case JSON path in the agent Docker container.
See also the [service level overrides](../configure_service/service_configuration_file.md#service-level-overrides) and [multiple overrides](../configure_service/service_configuration_file.md#multiple-overrides) sections for more information.

=== "skill.yaml"

    ``` yaml
    name: <your_skill_name>
    author: <author>
    version: <version>
    type: skill    
    # (...)
    models:
      benchmark_tool:
        args:
          log_dir: /logs
        class_name: YourBenchmarkTool

      params:
        args:
          setup:
            all_participants:
            - '0x0000000000000000000000000000000000000000'
            safe_contract_address: '0x0000000000000000000000000000000000000000'
            consensus_threshold: null            
          tendermint_url: http://localhost:26657
          tendermint_com_url: http://localhost:8080
          service_registry_address: null
          share_tm_config_on_startup: false
          on_chain_service_id: null
          # (...)
        class_name: YourSkillParams
    ```

=== "aea-config.yaml"

    ``` yaml
    # (...)
    ---
    public_id: valory/abci:0.1.0
    type: connection
    config:
      target_skill_id: <author>/<your_skill_name>:<version>
      host: ${ABCI_HOST:str:localhost}
      port: ${ABCI_PORT:int:26658}
      use_tendermint: ${ABCI_USE_TENDERMINT:bool:false}
    
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
     - uri: ${P2P_URI:str:acn.staging.autonolas.tech:9005}
       public_key: ${P2P_PUBLIC_KEY:str:02d3a830c9d6ea1ae91936951430dee11f4662f33118b02190693be835359a9d77}
     - uri: ${P2P_URI:str:acn.staging.autonolas.tech:9006}
       public_key: ${P2P_PUBLIC_KEY:str:02e741c62d706e1dcf6986bf37fa74b98681bc32669623ac9ee6ff72488d4f59e8}
    cert_requests:
    - identifier: acn
      ledger_id: ethereum
      message_format: '{public_key}'
      not_after: '2025-01-01'
      not_before: '2024-01-01'
      public_key: ${P2P_PUBLIC_KEY:str:02d3a830c9d6ea1ae91936951430dee11f4662f33118b02190693be835359a9d77}
      save_path: .certs/acn_cosmos_9005.txt

    ---
    public_id: <author>/<your_skill_name>:<version>
    type: skill    
    models:
      benchmark_tool:
        args:
          log_dir: ${str:/benchmarks}

      params:
        args:
          setup:
            all_participants: ${list:[]}
            safe_contract_address: ${str:'0x0000000000000000000000000000000000000000'}
            consensus_threshold: ${int:null}
          tendermint_url: ${str:http://localhost:26657}
          tendermint_com_url: ${str:http://localhost:8080}
          service_registry_address: ${str:null}
          share_tm_config_on_startup: ${bool:false}
          on_chain_service_id: ${int:null}
          # (...)
    ```

=== "service.yaml"

    ``` yaml
    # (...)
    ---
    public_id: valory/ledger:0.19.0
    type: connection
    config:
      ledger_apis:
        ethereum:
          address: ${ETHEREUM_ADDRESS:str:http://localhost:8545}
          chain_id: ${ETHEREUM_CHAIN_ID:int:31337}
          poa_chain: ${ETHEREUM_POA_CHAIN:bool:false}
          default_gas_price_strategy: ${DEFAULT_GAS_PRICE_STRATEGY:str:eip1559}
 
    ---
    public_id: <author>/<your_skill_name>:<version>
    type: skill    
    models:
      benchmark_tool:
        args:
          log_dir: ${LOG_DIR:str:/benchmarks}

      params:
        args:
          setup:
            all_participants: ${ALL_PARTICIPANTS:list:["0x...","0x...","0x...","0x..."]}      
            safe_contract_address: ${SAFE_CONTRACT_ADDRESS:str:0x...}
            consensus_threshold: ${CONSENSUS_THRESHOLD:int:null}
          tendermint_url: ${str:http://localhost:26657}
          tendermint_com_url: ${str:http://localhost:8080}
          service_registry_address: ${SERVICE_REGISTRY_ADDRESS:str:0x...}
          share_tm_config_on_startup: ${SHARE_TM_CONFIG_ON_STARTUP:bool:false}
          on_chain_service_id: ${ON_CHAIN_SERVICE_ID:int:1}
          # (...)
    ```
!!! warning "Important"
    Recall that when [deploying an on-chain service](../guides/deploy_service.md#on-chain-deployment) using `autonomy deploy from-token`, a number of arguments (under `setup`) are overridden with the values registered in the Autonolas Protocol:
    ```yaml title="service.yaml"
    # (...)
    models:
      params:
        args:
          setup:
            all_participants: # Overridden with the registered values
            safe_contract_address: # Overridden with the registered values
            consensus_threshold: # Overridden with the registered values
    ```

    For local deployments, the argument `consensus_threshold` can take the value:

    * `null`: then the framework will automatically calculate `consensus_threshold` as $\lceil (2N+1)/3 \rceil$, where $N=$`len(all_participants)`.
    * Any value $M$ such that $\lceil (2N+1)/3 \rceil \leq M \leq N$.
    
    Otherwise, the framework will raise an error and the app will not start. 

## Publish and mint packages

Ensure that your components, agent and service packages are published to the IPFS registry:

* [Push your components](../guides/publish_fetch_packages.md#push-a-component-on-a-registry) using the `autonomy push` command.
* [Publish your agents](../guides/publish_fetch_packages.md#publish-an-agent-on-a-registry) using the `autonomy publish` command.
* [Publish your services](../guides/publish_fetch_packages.md#publish-a-service-on-a-registry) using the `autonomy publish` command.

Ensure that your components, agents and service packages are [minted on-chain in the Autonolas Protocol](../guides/publish_mint_packages.md).


## Check the deployment readiness of the service using

```
$ autonomy analyse service --public-id PUBLIC_ID
```

or if you want to check deployment readiness of an on-chain service

```
$ autonomy analyse service --token-id TOKEN_ID
```

## Publish Docker images (optional)

You can build the Docker images for the service using the `autonomy build-image` command. Alternatively, the images are built automatically when the service is deployed using `autonomy deploy from-token` command

If you want to use an image with a stable hash or a stable version of a runtime image, you can provide the hash/version using `--image-version` on the `autonomy deploy build` command.

Ensure that the image exists before running the deployment:

```bash
docker pull <author>/oar_runtime_<service_name>:<ipfs_hash_service_agent>
```

