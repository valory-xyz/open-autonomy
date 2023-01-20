The current deployment setup uses 5 docker images.

1. `valory/open-autonomy` 
   
    This image contains all the required python packages and a virtual environment required to deploy an agent. When building a deployment, the deployment builder will use `valory/open-autonomy` as the name and the current version of the framework as the version tag. If you want to change that you can change the name and the version of the image using `AUTONOMY_IMAGE_NAME` and `AUTONOMY_IMAGE_VERSION` environment variables respectively.
   
2. `valory/oar-{agent}` 
    
    This image contains an agent package and a deployment environment for the same agent. This image uses the open `valory/open-autonomy` image as the base. You cannot change the name of the image but you can overwrite the version tag using the `--image-version` flag when building the deployment.

3. `valory/open-autonomy-tendermint`
   
   This image contains the deployment setup for a `tendermint` node. When building a deployment, the deployment builder will use `valory/open-autonomy-tendermint` as the name and the current version of the framework as the version tag. If you want to change that you can change the name and the version of the image using `TENDERMINT_IMAGE_NAME` and `TENDERMINT_IMAGE_VERSION` environment variables respectively.

4. `valory/open-autonomy-hardhat` 
   
   This image comes with the Autonolas registry contracts pre deployed. This image should only be used when working with the `dev` mode. When building a deployment, the deployment builder will use `valory/open-autonomy-hardhat` as the name and `latest` as the version tag. If you want to change that you can change the name and the version of the image using `HARDHAT_IMAGE_NAME` and `HARDHAT_IMAGE_VERSION` environment variables respectively.

   If you want to include custom contracts in this image read [here](https://github.com/valory-xyz/autonolas-registries/blob/main/docs/running_with_custom_contracts.md) on how to do it.

5. `valory/open-acn-node` 
   
   This image contains the deployment setup for an `ACN` node which can be used for direct agent to agent communication. This image should only be used when working with the `dev` mode. When building a deployment, the deployment builder will use `valory/open-acn-node` as the name and `latest` as the version tag. If you want to change that you can change the name and the version of the image using `ACN_IMAGE_NAME` and `ACN_IMAGE_VERSION` environment variables respectively.
