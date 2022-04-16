# Agent Runtime With Developer Mode

The developer mode enables hot code swapping and reflects changes on local `open-aea` repository without rebuilding or restarting containers.


## How to use agent runtime with developer mode

### Environment setup

```bash
OPEN_AEA_REPO_PATH="/path/to/open-aea-repo"
DEPLOYMENT_TYPE="docker-compose"
DEPLOYMENT_SPEC="/path/to/deployment-spec"
```
Default deployment specifications are stored in `deployments/deployment_specifications`

*Tip: You can also store above variables in .bashrc file*

```bash
export VERSION=dev
make build-deploy
make run-deployment
```

and in a separate terminal run if you want to use local hardhat

```bash
make run-hardhat
```

This build latest docker images and launch docker compose. Wait for environment setup to be completed inside your docker containers, it may take some time. Also don't make any changes on either open-aea or consensus-algorithms repository while environment is being set up it may cause some unexpected errors. Once the agents are running, you can make changes it'll trigger the restarts.

Also, the trigger is caused by any python file closing in either `consensus-algorithms/packages` or `open-aea/` directory. So even if you haven't made any change and still want to restart the agent, just open any python file press `ctrl+s` or save it from file menu and it'll trigger the restart.


We also have make targets for oracle app, just run

```bash
make run-oracle-dev
```