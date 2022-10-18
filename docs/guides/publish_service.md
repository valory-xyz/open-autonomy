Publishing a service is simply the process of storing the service into a registry (or in other words, a repository), either locally or remotely. The {{open_autonomy}} framework supports three types of registries: local, remote [IPFS](https://ipfs.io/), and remote HTTP. Remote registries allow to make the service available to other developers.

This guide assumes that your terminal is located in the service folder that you want to deploy. that is, the folder containing the `service.yaml` file.

## What will you learn
In this guide, you will learn how to:

  * Publish a service on a local registry.
  * Publish a service on an IPFS registry.
  * Publish a service on an HTTP registry.

## Publish a service locally

!!! info
    This section will be added soon.

## Publish a service on an IPFS registry

1. **Check the prerequisites.** Ensure that the framework has been initiated with the options `--remote --ipfs`.

2. **Publish the service.** Publish the service by executing the following command within the service parent folder:

    ```bash
    autonomy publish --remote
    ```

    You should see an output similar to this:
    ```
    Service "<your_service_name>" successfully published on the IPFS registry.
        PublicId: <your_name>/<your_service_name>:<version>
        Package hash: bafybei01234567890abcdefghijklmnopqrstuvwxyz01234567890abcd
    ```
    Note down these values.

3. **Check the registry.** You can check that your service has been successfully uploaded to the [IPFS](https://ipfs.io/) registry by accessing the gateway https://gateway.autonolas.tech/ipfs/`<hash>`, where `<hash>` is the IPFS hash value returned by the previous command (`bafybei01234567890abcdefghijklmnopqrstuvwxyz01234567890abcd` in the example).


## Publish a service on an HTTP registry

!!! info
    This section will be added soon.
