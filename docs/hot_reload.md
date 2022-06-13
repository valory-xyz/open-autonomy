# Agent Runtime With Hot Reload Mode

The hot reload mode enables hot code swapping and reflects changes on the agent code as well as the local `open-aea` repository without rebuilding or restarting containers manually.

## General Guide

Arbitrary {{agent_service}}s built with the {{open_autonomy}} framework can be run with the hot start functionality.

### Environment setup

Export the following environment variables (where you replace the paths with valid ones):
```bash
export OPEN_AEA_REPO_PATH="/path/to/open-aea-repo"
export DEPLOYMENT_TYPE="docker-compose"
export DEPLOYMENT_SPEC="/path/to/deployment-spec"
export VERSION=dev
```

The default deployment specifications are stored in `deployments/deployment_specifications`.

The `open-aea` repository can be cloned from here: https://github.com/valory-xyz/open-aea

*Tip: You can also store above variables in your .bashrc file*


### Prepare images & run

Execute the following:
```bash
make build-deploy
```
This builds the latest docker images and launches docker compose. Wait for environment setup to be completed inside your docker containers, it may take some time. Also don't make any changes on either open-aea or open-autonomy repository while environment is being set up it may cause some unexpected errors.

Then run:
```bash
make run-deploy
```

And - if you want to use local hardhat - in a separate terminal run:
```bash
make run-hardhat
```

Once the agents are running, you can make changes to the agent's packages as well as the `open-aea` and it will trigger the restarts.

The trigger is caused by any python file closing in either `open-autonomy/packages` or `open-aea/` directory. So even if you haven't made any change and still want to restart the agent, just open any python file press `ctrl+s` or save it from file menu and it will trigger the restart.


## Quick start for oracle

We have a single make target for the oracle app, just run the following command and it will build and run the oracle.
```bash
make run-oracle-dev
```

## Debugging in the cluster

When debugging deployments, it can be useful to have the option to spin up a hardhat node to enable debugging and testing of the issue within the cluster.


```bash
VERSION=cluster-dev
DEPLOYMENT_TYPE=kubernetes
DEPLOYMENT_KEYS=deployments/keys/hardhat_keys.json
SERVICE_ID=valory/oracle_hardhat

make push-images build-deploy run-deploy
```

This will deploy a private hardhat container to the cluster, along with the associated agent service, configured to use the hardhat container.
