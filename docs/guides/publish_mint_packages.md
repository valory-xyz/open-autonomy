Once you have finished developing and testing your service locally, it is time to publish the developed software packages on a remote registry (so that they become publicly available) and mint them in the [Autonolas Protocol](https://docs.autonolas.network/protocol/).

<figure markdown>
![](../images/development_process_publish_mint_packages.svg)
<figcaption>Part of the development process covered in this guide</figcaption>
</figure>

The [Autonolas Protocol](https://docs.autonolas.network/protocol/) provides primitives to create, operate and secure agent services on-chain. It also provides a mechanism that incentivizes their creation and rewards developers and service operators proportionally for their efforts to support the growth of the Autonolas ecosystem. The protocol comprises the **on-chain registry**, a collection of ERC721 smart contracts that manage the registration of software packages (components, agents and services). The registry stores a representation of the packages minted in the form of NFTs.
Minting packages on-chain is a requirement to secure and use them in the [Autonolas Protocol](https://docs.autonolas.network/protocol/).

You can mint packages using the [Autonolas Protocol web app](https://protocol.autonolas.network/) or the Open Autonomy CLI.

## What will you learn

This guide covers step 6 of the [development process](./overview_of_the_development_process.md). You will learn how to publish the software packages developed in the local registry (components, agents and services) to the remote registry, and how to mint them on-chain.

You must ensure that your machine satisfies the framework requirements and that you have [set up the framework](./set_up.md#set-up-the-framework) and [a local registry](./set_up.md#set-up-the-local-registry). As a result you should have a Pipenv workspace folder with a local registry (`./packages`) in it.

## Publish packages to the remote registry

If you have developed your components in the local registry, then the index file (`./packages/packages.json`) should contain a reference for them in the `dev` section, for example:

<!-- Use js instead of json lexer to support mkdocs-material comment features -->
```js
{
    "dev": {
        "service/your_name/your_service/0.1.0": "bafybei0000000000000000000000000000000000000000000000000000",
        "agent/your_name/your_agent/0.1.0": "bafybei0000000000000000000000000000000000000000000000000000",
        "skill/your_name/your_fsm_app/0.1.0": "bafybei0000000000000000000000000000000000000000000000000000"
        /* (1)! */
    },
    "third_party": {
        /* (2)! */
    }
}
```

1. Any other `dev` entries that you have go here. Entries must be comma-separated (`,`).
2. Any other `third_party` entries that you have go here. Entries must be comma-separated (`,`).

The easiest way to have your components published in the remote registry is by locking the packages in the local registry:

```bash
autonomy packages lock
```

and pushing them to the remote registry:

```bash
autonomy push-all
```

The former command will correct the hash values in component configuration files, as well as in the local registry index file. The latter will push all the components within `dev` to the remote registry. The output of the command will show an entry for each pushed component, which includes the package hash.

## Mint packages in the Autonolas Protocol

To mint a software package, it is required that its dependencies are also minted on-chain first. For example, you need that an agent is minted before minting the corresponding service, and you need that the agent components are minted before minting the agent.

To mint packages you need:

* An **address** associated to either
    * a crypto wallet (e.g., [Metamask](https://metamask.io/) or a cold wallet), or
    * a multisig contract (like [Safe](https://safe.global/)) which allows to connect via [Wallet Connect](https://walletconnect.com/).
  
    In either case, the address must have funds for the chain that you wish to mint the package on.

* The **hash of the package** that you want to mint, and which must have been published into a remote registry.

* An **NFT image URL**. This image will be used to represent the minted NFT for the package on marketplaces such as [OpenSea](https://opensea.io/). You can use [this sample image URL](https://gateway.autonolas.tech/ipfs/Qmbh9SQLbNRawh9Km3PMEDSxo77k1wib8fYZUdZkhPBiev) for testing purposes.

### Mint packages using the Autonolas Protocol web app

The [Autonolas Protocol web app](https://protocol.autonolas.network/) provides an intuitive GUI to mint components, agents and services, and manage the life cycle of services in the Autonolas ecosystem.

Read the [Autonolas Protocol docs](https://docs.autonolas.network/protocol/), and follow the corresponding instructions to get your software package minted:

* [Mint a component.](https://docs.autonolas.network/protocol/mint_packages_nfts/#mint-a-component)
* [Mint an agent.](https://docs.autonolas.network/protocol/mint_packages_nfts/#mint-an-agent)
* [Mint a service.](https://docs.autonolas.network/protocol/mint_packages_nfts/#mint-a-service)

### Mint packages using the CLI

You can also mint packages using the [`autonomy mint` command](../advanced_reference/cli/../commands/autonomy_mint.md).

!!! info
    This section will be added soon.
