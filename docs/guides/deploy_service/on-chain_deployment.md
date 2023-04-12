On-chain deployment refers to the process of deploying a service that has been [published and minted](../publish_mint_packages.md) in the [Autonolas Protocol](https://docs.autonolas.network/protocol/). The framework provides a convenient CLI tools for deploying such services automatically.

!!! warning "Important"
    On-chain deployments will automatically override a number of configuration arguments in the {{fsm_app}} skill, within the the agent containers, with values read on-chain. Namely:

    === "skill.yaml"

    ```yaml
    (...)
    models:
      params:
        args:
          setup:
            all_participants: # Overridden with the registered values
            safe_contract_address: # Overridden with the registered values
            consensus_threshold: # Overridden with the registered values
    ```

Execute the deployment as follows:

1. **Find the service ID.** Explore the [services section](https://protocol.autonolas.network/agents) of the protocol frontend, and note the token ID of the service that you want to deploy. The service must be in [Deployed state](https://docs.autonolas.network/protocol/life_cycle_of_a_service/#deployed).

2. **Prepare the keys file.** Prepare a JSON file `keys.json` containing the wallet address and the private key for each of the agents that you wish to deploy in the local machine.

    ???+ example "Example of a `keys.json` file"

        <span style="color:red">**WARNING: Use this file for testing purposes only. Never use the keys or addresses provided in this example in a production environment or for personal use.**</span>

        ```json title="keys.json"
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

2. **Deploy the service.** Execute the following command:

    ```bash
    autonomy deploy from-token <ID> keys.json --use-goerli # (1)!
    ```

    1. `--use-goerli` indicates that the service is registered in the Görli testnet. Check out the [`autonomy deploy from-token`](../../../advanced_reference/commands/autonomy_deploy/#autonomy-deploy-from-token) command documentation to learn more about its parameters and options.

    The deployment will be run for as many agents as keys are defined in the `keys.json` file.
