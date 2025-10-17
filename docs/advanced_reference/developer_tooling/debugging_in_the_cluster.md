!!! info
    This section is under review and will be updated soon.

When debugging deployments, it can be useful to have the option to spin up a hardhat node to enable debugging and testing of the issue within the cluster. First, fetch the AI agent:

```bash
autonomy fetch valory/oracle_hardhat --local --service
cd oracle_hardhat
```

You now need to replace the override in the ```service.yaml``` file: change ```http://host.docker.internal:8545``` to ```http://hardhat:8545```.

Then, build the image:
```bash
autonomy build-image
```

Now, push the image  to make it accessible for the cluster to pull it. You can get the tag from the previous command:
```bash
docker image push <tag>
```

Finally, build the deployment and run it:
```bash
export OPEN_AUTONOMY_PRIVATE_KEY_PASSWORD=${PASSWORD}
autonomy deploy build  ../generated_keys.json --kubernetes --dev
kubectl apply -f abci_build_*/
kubectl apply -f abci_build_*/agent_keys
```

This will deploy a private hardhat container to the cluster, along with the associated AI agents, configured to use the hardhat container.
