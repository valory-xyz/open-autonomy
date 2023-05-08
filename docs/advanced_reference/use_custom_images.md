The {{open_autonomy}} framework uses up to 6 different Docker images when building a service deployment with the command `autonomy deploy build`. Some of these images are for testing purposes and they are only included if indicated explicitly.

## Images used in production and testing

`valory/open-autonomy`

: Base image that contains all the required Python packages and a virtual environment required to deploy an agent. The deployment builder will use `valory/open-autonomy` as the name and the current version of the framework as the version tag. You can change the name and the version tag of the image by exporting the environment variables `AUTONOMY_IMAGE_NAME` and `AUTONOMY_IMAGE_VERSION`, respectively.


`valory/oar-<author>/<agent_package>:<package_hash>`

: This image extends the base image `valory/open-autonomy`. It contains the agent package for a service and a deployment environment for the same agent. This image is built through the `autonomy build-image` command.

`valory/open-autonomy-tendermint`

: Defines a Tendermint node in the deployment setup. The deployment builder will use `valory/open-autonomy-tendermint` as the name and the current version of the framework as the version tag. You can change the name and the version tag of the image by exporting the environment variables `TENDERMINT_IMAGE_NAME` and `TENDERMINT_IMAGE_VERSION`, respectively.

## Images used in testing only

`valory/open-autonomy-hardhat`

: Base image that contains a pre-configured Hardhat node which can be used as a test blockchain for testing services locally and running end-to-end tests for the agent packages.

`valory/autonolas-registries`

: This image extends the base image `valory/open-autonomy-hardhat`.
It comes with the Autonolas Protocol registry contracts pre-deployed. The deployment builder will use `valory/open-autonomy-hardhat` as the name and `latest` as the version tag. You can change the name and the version tag of the image by exporting the environment variables  `HARDHAT_IMAGE_NAME` and `HARDHAT_IMAGE_VERSION`, respectively, to `valory/autonolas-registries:latest`.

    !!! warning "Important"

        This image is only included if explicitly indicated through the flag `--use-hardhat` when building the service deployment (`autonomy deploy build` command).

        This image should only be used when working with the `dev` mode.

    If you require specific custom contracts to test your service, read the [guide to include custom contracts](https://github.com/valory-xyz/autonolas-registries/blob/main/docs/running_with_custom_contracts.md).

`valory/open-acn-node`

: Defines an `ACN` node in the deployment setup, which can be used for direct agent to agent communication. The deployment builder will use `valory/open-acn-node` as the name and `latest` as the version tag. You can change the name and the version tag of the image by exporting the environment variables `ACN_IMAGE_NAME` and `ACN_IMAGE_VERSION`, respectively.

    !!! warning "Important"

        This image is only included if explicitly indicated through the flag `--use-acn` when building the service deployment (`autonomy deploy build` command).

        This image should only be used when working with the `dev` mode.
