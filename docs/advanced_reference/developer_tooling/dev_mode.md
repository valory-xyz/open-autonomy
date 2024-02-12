The {{open_autonomy}} framework comes with *developer mode* (`dev` mode) tooling to enable faster service developing and debugging. The `dev` mode supports running agent services with a number of functionalities enabled:

* **Hot reload**, which enables hot code swapping and reflects changes on the agent code as well as on the local `open-aea` repository without rebuilding or restarting the containers manually.
* **Hardhat Instance**, which enables the inclusion of a pre-configured Hardhat Instance image in the deployment, which can be used as a test blockchain.
* **ACN Instance**, which enables inclusion of a pre-configured ACN Instance image, which can be used to test various agent communication functionalities, for example establishing the Tendermint network at the startup.
* **Execution replay** of a previous agent in the service.
* **Benchmark** the performance of an agent service.

Before starting this guide, ensure that your machine satisfies the framework requirements and that you have followed the [set up guide](../../guides/set_up.md). As a result you should have a Pipenv workspace folder.

## Build and run an agent service in `dev` mode

1. **Fetch the service.** Fetch the Price Oracle service from the remote registry.

    ```bash
    autonomy fetch valory/oracle_hardhat:0.1.0:<hash> --service
    ```

2. **Build the agents' image.** Navigate to the local folder of the service, and build the Docker image of the service agents in `dev` mode.

    ```bash
    cd oracle_hardhat
    autonomy build-image --dev
    ```

    After the command finishes building the image, you can see that it has been created by executing:

    ```bash
    docker image ls | grep oracle_hardhat
    ```

3. **Prepare the keys file.** Within the service folder, prepare a JSON file `keys.json` containing the wallet address and the private key for each of the agents that make up the service.

    ??? example "Example of a `keys.json` file"

        <span style="color:red">**WARNING: Use this file for testing purposes only. Never use the keys or addresses provided in this example in a production environment or for personal use.**</span>

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

4. **Build the deployment.** Within the service folder, execute the command below to build the service deployment in `dev` mode, including a pre-configured Hardhat instance.

    ```bash
    autonomy deploy build keys.json --dev --packages-dir ~/git/open-autonomy/packages --open-autonomy-dir ~/git/open-aea/ --open-aea-dir ~/git/open-autonomy/ --use-hardhat -ltm
    ```

    You must modify the paths in the command above appropriately, pointing to:

    * the path to the local registry (/packages directory),
    * the path to the local {{open_autonomy_repository}},
    * the path to the local {{open_aea_repository}}.

    This will create a deployment environment in `dev` mode within the `./abci_build` folder.

5. **Run the service.** Navigate to the deployment environment folder (`./abci_build`) and run the deployment locally.

    ```bash
    cd abci_build
    autonomy deploy run
    ```

	You can cancel the local execution at any time by pressing ++ctrl+c++.

## Hot reload

Once the agents are running, you can make changes to the agent's code as well as the local {{open_aea_repository}}, and it will trigger the service restart.

The trigger is caused by any Python file closing in either the `open-autonomy/packages` or the `open-aea/` directory. So even if you haven't made any change and still want to restart the service, just open any Python file press `Ctrl+S` or save it from the file menu and it will trigger the restart.


## Hardhat instance

By default the command that builds the service deployment (`autonomy deploy build`) only includes the agent nodes and the Tendermint nodes. If you want to include a local Hardhat node as a test blockchain for the ledger connection, you can do so by using the `--use-hardhat` flag in that command.

The deployment setup will include a Hardhat node (image `valory/open-autonomy-hardhat`) using `hardhat` as container name. Therefore, in order to use this node, you must set a [service-level override](../../configure_service/service_configuration_file.md#service-level-overrides) so that the `valory/ledger` connection address is set to `http://hardhat:8545`.
You can achieve this by editing the service configuration file `service.yaml` as follows:

```yaml title="service.yaml"
# (...)
---
public_id: valory/ledger:0.1.0
type: connection
config:
  ledger_apis:
    ethereum:
      address: ${LEDGER_RPC:str:http://hardhat:8545}
```

Alternatively, you can leave the default `service.yaml` and export an environment variable:

```yaml title="service.yaml"
# (...)
---
public_id: valory/ledger:0.1.0
type: connection
config:
  ledger_apis:
    ethereum:
      address: ${LEDGER_RPC:str:http://localhost:8545}
```

```bash
export LEDGER_RPC = http://hardhat:8545
```

If you require specific custom contracts to test your service, read the [guide to include custom contracts](https://github.com/valory-xyz/autonolas-registries/blob/main/docs/running_with_custom_contracts.md).

## ACN instance

You can also include an ACN node for agent communication using the `--use-acn` flag in `autonomy deploy build`.

The deployment setup will include an ACN node (image `valory/open-acn-node`) using `acn` as container name. Similarly as above, in order to use this node you must set a [service-level override](../../configure_service/service_configuration_file.md#service-level-overrides) so that the `valory/p2p_libp2p_client` connection parameters are set to the appropriate values.
You can achieve this by editing the service configuration file `service.yaml` as follows:

```yaml title="service.yaml"
# (...)
---
public_id: valory/p2p_libp2p_client:0.1.0
type: connection
config:
  nodes:
  - uri: acn:11000
    public_key: 03c74dbfbe7bbc1b42429f78778017a3cd7eaf9d59d1634c9505a3f7c1a9350e71
cert_requests:
- identifier: acn
  ledger_id: ethereum
  message_format: '{public_key}'
  not_after: '2025-01-01'
  not_before: '2024-01-01'
  public_key: 03c74dbfbe7bbc1b42429f78778017a3cd7eaf9d59d1634c9505a3f7c1a9350e71
  save_path: .certs/acn_cosmos_11000.txt
is_abstract: false
```
