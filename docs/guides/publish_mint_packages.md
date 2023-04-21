Once you have finished developing and testing your service locally, it is time to publish the developed software packages on a remote registry (so that they become publicly available) and mint them in the [Autonolas Protocol](https://docs.autonolas.network/protocol/).

<figure markdown>
![](../images/development_process_publish_mint_packages.svg)
<figcaption>Part of the development process covered in this guide</figcaption>
</figure>

The [Autonolas Protocol](https://docs.autonolas.network/protocol/) provides primitives to create, operate and secure agent services on-chain. It also provides a mechanism that incentivizes their creation and rewards developers proportionally for their efforts to support the growth of the Autonolas ecosystem. The protocol comprises the **on-chain registry**, a collection of ERC721 smart contracts that manage the registration of software packages (components, agents and services). The registry stores a representation of the packages minted in the form of NFTs.
Minting packages on-chain is a requirement to secure and use them in the [Autonolas Protocol](https://docs.autonolas.network/protocol/).

You can mint packages using the [Autonolas Protocol web app](https://protocol.autonolas.network/) or the Open Autonomy CLI.

## What will you learn

This guide covers step 6 of the [development process](./overview_of_the_development_process.md). You will learn how to publish the software packages developed in the local registry (components, agents and services) to the remote registry, and how to mint them on-chain.

You must ensure that your machine satisfies the [framework requirements](./set_up.md#requirements), you have [set up the framework](./set_up.md#set-up-the-framework), and you have a local registry [populated with some default components](./set_up.md#populate-the-local-registry-for-the-guides). As a result you should have a Pipenv workspace folder with an initialized local registry (`./packages`) in it.

## Publish packages to the remote registry

If you have developed your components in the local registry, then the index file (`./packages/packages.json`) should contain a reference for them in the `dev` section, for example:

<!-- Use js instead of json lexer to support mkdocs-material comment features -->
```js title="packages.json"
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

The command `autonomy packages lock` will correct the hash values in component configuration files, as well as in the local registry index file. The command `autonomy push-all` will push all the components within `dev` to the remote registry. The output of the command will show an entry for each pushed component, which includes the package hash.

## Mint packages in the Autonolas Protocol

To mint a given software package, it is required that its dependencies are also minted on-chain first. For example, you need that an agent be minted before minting the corresponding service, and you need that the agent components are minted before minting the agent.

To mint packages you need:

* An **address** associated to either
    * a crypto wallet (e.g., [Metamask](https://metamask.io/) or a cold wallet), or
    * a multisig contract (like [Safe](https://safe.global/)) which allows to connect via [Wallet Connect](https://walletconnect.com/).
  
    In either case, the address must have funds for the chain that you wish to mint the package on.

* The **hash of the package** that you want to mint, and which must have been published into a remote registry.

* An **NFT image URL**. This image will be used to represent the minted NFT for the package on marketplaces such as [OpenSea](https://opensea.io/). You can use [this sample image URL](https://gateway.autonolas.tech/ipfs/Qmbh9SQLbNRawh9Km3PMEDSxo77k1wib8fYZUdZkhPBiev) for testing purposes.

Packages have to be minted satisfying their dependency hierarchy, that is, packages that depend on others must be minted afterwards. For example, this is the package dependency of the `hello_world` service:

### Using the Autonolas Protocol web app

The [Autonolas Protocol web app](https://protocol.autonolas.network/) is a front-end that provides an intuitive GUI to mint components, agents and services, and manage the life cycle of services in the Autonolas Protocol.

We refer you to the [Autonolas Protocol docs](https://docs.autonolas.network/protocol/), where you can find instructions on how to mint [components](https://docs.autonolas.network/protocol/mint_packages_nfts/#mint-a-component) (including the {{fsm_app}} skill), [agents](https://docs.autonolas.network/protocol/mint_packages_nfts/#mint-an-agent), and [services](https://docs.autonolas.network/protocol/mint_packages_nfts/#mint-a-service).

### Using the Open Autonomy CLI

You can also mint packages using the [`autonomy mint` command](../advanced_reference/cli/../commands/autonomy_mint.md).

In the example below we use a local, testing chain which contains the Autonolas Protocol registry contracts deployed (Docker image `valory/autonolas-registries`). We show how to mint all the components of the `hello_world` service using this testing environment.

!!! info

    If you want to mint packages on another chain, you must use the aproppriate flags for the command `autonomy mint`. For example, if you want to mint packages on the Autonolas Protocol deployed on Ethereum, you have to change the flag `--use-local` by `--use-ethereum` below. Read the documenation for the [`autonomy mint` command](../advanced_reference/commands/autonomy_mint.md) for more information.

1. **Start the local testing node.** On a separate terminal, run the `valory/autonolas-registries` Docker image:

    ```bash
    docker run -p 8545:8545 valory/autonolas-registries:latest
    ```

    Optionally, you can configure a software wallet (like Metamask) to explore the status of the Autonolas Protocol in this local, testing blockchain. Use the following parameters:

    * RPC URL: http://localhost:8545
    * Chain ID: 31337
    * Currency symbol: GO

    You can use a test account importing the private key `0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80`.

2. **Prepare the key file.** Prepare a file with a private key corresponding to a funded address in the chain.

    ```bash
    echo -n 0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80 > key.txt
    ```

3. **Mint the components.** Within the workspace folder, mint the components:

    a. First, mint the components which don't have any dependency:

    ```bash
    autonomy mint --use-local protocol --key key.txt --nft 1.png --owner 0x8626f6940E2eb28930eFb4CeF49B2d1F2C9C1199 ./packages/valory/protocols/abci/
    autonomy mint --use-local protocol --key key.txt --nft 1.png --owner 0x8626f6940E2eb28930eFb4CeF49B2d1F2C9C1199 ./packages/valory/protocols/abci/
    autonomy mint --use-local protocol --key key.txt --nft 1.png --owner 0x8626f6940E2eb28930eFb4CeF49B2d1F2C9C1199 ./packages/valory/protocols/abci/
    autonomy mint --use-local protocol --key key.txt --nft 1.png --owner 0x8626f6940E2eb28930eFb4CeF49B2d1F2C9C1199 ./packages/valory/protocols/abci/
    autonomy mint --use-local protocol --key key.txt --nft 1.png --owner 0x8626f6940E2eb28930eFb4CeF49B2d1F2C9C1199 ./packages/valory/protocols/abci/
    ```

    b. Next, mint the components that have dependencies. Pay attention to the package IDs displayed below, which might be different in your case:

    ```bash
    autonomy mint --use-local protocol --key key.txt --nft 1.png --owner 0x8626f6940E2eb28930eFb4CeF49B2d1F2C9C1199 ./packages/valory/protocols/abci/
    autonomy mint --use-local protocol --key key.txt --nft 1.png --owner 0x8626f6940E2eb28930eFb4CeF49B2d1F2C9C1199 ./packages/valory/protocols/abci/
    autonomy mint --use-local protocol --key key.txt --nft 1.png --owner 0x8626f6940E2eb28930eFb4CeF49B2d1F2C9C1199 ./packages/valory/protocols/abci/
    autonomy mint --use-local protocol --key key.txt --nft 1.png --owner 0x8626f6940E2eb28930eFb4CeF49B2d1F2C9C1199 ./packages/valory/protocols/abci/
    autonomy mint --use-local protocol --key key.txt --nft 1.png --owner 0x8626f6940E2eb28930eFb4CeF49B2d1F2C9C1199 ./packages/valory/protocols/abci/
    ```

4. **Mint the agent.**

    ```bash
    autonomy mint --use-local connection --key key.txt --nft ../open-autonomy/mints/10.json --owner 0x8626f6940E2eb28930eFb4CeF49B2d1F2C9C1199 ../open-autonomy/packages/valory/connections/ledger/ -d 36 -d 35
    ```

5. **Mint the service.**

    ```bash
    autonomy mint --use-local connection --key key.txt --nft ../open-autonomy/mints/10.json --owner 0x8626f6940E2eb28930eFb4CeF49B2d1F2C9C1199 ../open-autonomy/packages/valory/connections/ledger/ -d 36 -d 35
    ```


## Deploy your service on-chain

### Using the Autonolas Protocol web app



### Using the Open Autonomy CLI






   Account #0: 0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266 (10000 ETH)
Private Key: 0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80
