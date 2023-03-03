The [Autonolas Protocol](https://docs.autonolas.network/protocol/) provides primitives to create, operate and secure agent services on-chain. It also provides a mechanism that incentivizes their creation and rewards developers and service operators proportionally for their efforts to support the growth of the Autonolas ecosystem.

<figure markdown>
![](../images/development_process_mint_packages_on_chain.svg)
<figcaption>Part of the development process covered in this guide</figcaption>
</figure>

The [Autonolas Protocol](https://docs.autonolas.network/protocol/) comprises the **on-chain registry**, a collection of ERC721 smart contracts that manage the registration of software packages (components, agents and services). The registry stores a representation of the packages minted in the form of NFTs.
Minting packages on-chain is a requirement to secure and use them in the [Autonolas Protocol](https://docs.autonolas.network/protocol/).

You can mint packages using the [Autonolas Protocol web app](https://protocol.autonolas.network/) or the Open Autonomy CLI.

## What will you learn

In this guide, you will learn how to mint packages (components, agents and services) on-chain.

Before starting this guide, ensure that your machine satisfies the framework requirements and that you have followed the [set up guide](./set_up.md). As a result you should have a Pipenv workspace folder.
## Requirements

In order to mint a software package, you must ensure that you have:

* An **address** associated to either
    * a crypto wallet (e.g., [Metamask](https://metamask.io/) or a cold wallet), or
    * a multisig contract (like [Safe](https://safe.global/)) which allows to connect via [Wallet Connect](https://walletconnect.com/).
  
    In either case, the address must have funds for the chain that you wish to register the package.

* The **hash of the package** that you want to mint on-chain, and which must have been published into a remote registry.

    !!! info
        If you have followed the [guide to publish packages](./publish_fetch_packages.md), the package hash will be in the output of `autonomy push` and `autonomy publish`.

* An **NFT image URL**. This image will be used to represent the minted NFT for the package on marketplaces such as [OpenSea](https://opensea.io/). You can use [this sample image URL](https://gateway.autonolas.tech/ipfs/Qmbh9SQLbNRawh9Km3PMEDSxo77k1wib8fYZUdZkhPBiev) for testing purposes.

## Mint packages using the Autonolas Protocol web app

The [Autonolas Protocol web app](https://protocol.autonolas.network/) provides an intuitive GUI to mint components, agents and services, and manage the life cycle of services in the Autonolas ecosystem.

Read the [Autonolas Protocol docs](https://docs.autonolas.network/protocol/), and follow the corresponding instructions to get your software package minted on-chain as an NFT.

* [Mint a component.](https://docs.autonolas.network/protocol/mint_packages_on-chain/#mint-a-component)
* [Mint an agent.](https://docs.autonolas.network/protocol/mint_packages_on-chain/#mint-an-agent)
* [Mint a service.](https://docs.autonolas.network/protocol/mint_packages_on-chain/#mint-a-service)

## Mint packages using the CLI

You can also mint packages using the [`autonomy mint` command](../advanced_reference/cli/../commands/autonomy_mint.md).

!!! info
    This section will be added soon.
