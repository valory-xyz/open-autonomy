# Agent Runtime With Hot Reload Mode

The hot reload mode enables hot code swapping and reflects changes on the agent code as well as the local `open-aea` repository without rebuilding or restarting containers manually.

## General Guide

Arbitrary agent services built with the {{open_autonomy}} framework can be run with the hot reload functionality.

### Environment setup

Fetch the required service or if you already have a service defined navigate to the service directory and run

```bash
# build dev deployment using
$ autonomy deploy build --dev --packages-dir PATH_TO_PACKAGES_DIR --open-aea-dir PATH_TO_LOCAL_OPEN_AEA_REPO --open-autonomy-dir PATH_TO_LOCAL_OPEN_AUTONOMY_DIR
# build the required images using
$ autonomy build-image --dev
```

This will create a deployment with hot reload enabled for agents. You can run it using the same methods as normal deployments. Use `autonomy deploy run` or `docker-compose up --force-recreate` to start the deployment and enjoy building the services.

**The `open-aea` repository can be cloned from [here]( https://github.com/valory-xyz/open-aea).**

And - if you want to use local hardhat - in a separate terminal run:
```bash
docker run -p 8545:8545 -it valory/open-autonomy-hardhat:0.1.0
```

Once the agents are running, you can make changes to the agent's packages as well as the `open-aea` and it will trigger the restarts.

The trigger is caused by any python file closing in either `open-autonomy/packages` or `open-aea/` directory. So even if you haven't made any change and still want to restart the agent, just open any python file press `ctrl+s` or save it from file menu and it will trigger the restart.


## Debugging in the cluster

When debugging deployments, it can be useful to have the option to spin up a hardhat node to enable debugging and testing of the issue within the cluster. First, fetch the service:

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
autonomy deploy build  ../generated_keys.json --force --password ${PASSWORD} --kubernetes --dev
kubectl apply -f abci_build/
kubectl apply -f abci_build/agent_keys
```

This will deploy a private hardhat container to the cluster, along with the associated agent service, configured to use the hardhat container.
