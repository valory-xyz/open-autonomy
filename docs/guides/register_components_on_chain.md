To complete all the steps in this guide, you should have a [Görli testnet](https://goerli.net/) wallet address (e.g., [Metamask](https://metamask.io/)) with some GörliETH funds in it.



# Registering a service

5. **Register a service.** Now it's time to interact with the on-chain protocol through a deployed smart contract in the [Görli testnet](https://goerli.net/). We will be using a convenient protocol front-end to interact with the contract.

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
