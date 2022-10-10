The Autonolas ecosystem has an **on-chain protocol** that provides primitives to create, operate and secure agent services on a blockchain. It also provides a mechanism that incentivizes their creation and rewards developers and service operators proportionally for their efforts to support the growth of the Autonolas ecosystem.

The **on-chain registry** is a collection of ERC721 smart contracts (eventually deployed on all major blockchains) that handle the life cycle of **packages** (that is, agent components, agents and agent services) within the on-chain protocol. These contracts store a representation of the code developed in the form of an NFT.

Therefore, registering a package in the on-chain registry is the required step so that they can be used in the on-chain protocol.

The on-chain protocol can be accessed through the {{on_chain_frontend}}.

## What will you learn
In this guide, you will learn how to:

  * Register agent components, agents and agent services in the on-chain registry.
  * Manage the life cycle of an agent service on-chain.

## Requirements
This guide is based in the on-chain registry currently deployed in the [Görli testnet](https://goerli.net/). Ensure that you have:

  * A **[Görli testnet](https://goerli.net/) wallet address** (e.g., [Metamask](https://metamask.io/)) with some GörliETH funds in it. You can use, for example, a [Görli POW faucet](https://goerli-faucet.pk910.de/) to earn some free GörliETH.
  * The remote registry **package hash** of the already published completed package that you want to register on-chain. See the corresponding guides in case you are in doubt on how to create and publish a package in a remote registry.
  * An **NFT image URL**. This image will be used to represent the NFT on marketplaces such as [OpenSea](https://opensea.io/). You can use [this sample image URL](https://gateway.autonolas.tech/ipfs/Qmbh9SQLbNRawh9Km3PMEDSxo77k1wib8fYZUdZkhPBiev) for testing purposes.
  * If you are registering an agent service, you will also need the **wallet addresses of the agents** that are part of the service.


## Register an agent component
!!! info
    This section will be added soon.


## Register an agent
!!! info
    This section will be added soon.


## Register a service
Before continuing, ensure that you meet the [requirements](#requirements) stated above.

  1. **Connect your wallet.** Access the {{on_chain_frontend}}, and connect your [Metamask](https://metamask.io/) wallet.

  2. **Find the agent's canonical ID.** Explore the [agents section](https://protocol.autonolas.network/agents), and note the ID of the agent that make up your service. If your service is composed of different agents, you must note the IDs of all of them.

  3. **Fill in the service data.** Navigate to the [services section](https://protocol.autonolas.network/services), and press the button _Register_.
  There are some data that need to be input in this form, whereas additional metadata needs to be filled by pressing the button _Generate Hash & File_:

      1. **Owner Address.** Your wallet address (or whoever you want to declare the owner of the service), starting by `0x...`.
      2. **Generate the metadata file.** By pressing the button _Generate Hash & File_ you need to input further data:

          - **Name.** A name for the service.
          - **Description.** A description of the service.
          - **Version.** The service version number, for example, 0.1.0.
          - **Package hash.** This is the remote registry package hash starting by `bafybei...` that you obtained when published the service on a remote service.
          - **NFT Image URL.** An URL pointing to an image. You can use [this sample image URL](https://gateway.autonolas.tech/ipfs/Qmbh9SQLbNRawh9Km3PMEDSxo77k1wib8fYZUdZkhPBiev) for testing purposes.

          By pressing _Save File & Generate Hash_ a metadada file with this information will be automatically generated in the remote IPFS registry. You will notice that the hash will be populated in the service registration form.

      3. **Canonical agent Ids.** Comma-separated list of agent ID(s) which the service requires. These are the ID(s) that you found in an earlier step above.

      4. **No. of slots to canonical agent Ids.** Specify the number of agent instances for each agent ID listed above.

      5. **Cost of agent instance bond.** Specify (in wei units) what is the bond per each agent instance  joining the service. If you are using it for testing purposes, we suggest that you use a small value (e.g., 1000000000000000 GörliWei = 0.001 GörliETH).

      6. **Threshold.** Specify the threshold of agents required to sign.

  4. Press the button _Submit_. Your  [Metamask](https://metamask.io/) wallet will ask you to approve the transaction.

Once the transaction is settled on-chain, you should see a message indicating that the service has been registered successfully, and you should see that it is in agent **pre-registration** state. Congratulations! Your service is now registered to work with the on-chain protocol.
