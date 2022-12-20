Tools for replay agent execution.

This command group consists of a number of functionalities for re-running agents using data dumps from previous runs. See the appropriate subcommands for more information. Note that **replay functionalities only work for deployments which were ran in dev mode.**


## `autonomy replay agent`

### Usage
```bash
autonomy replay agent [OPTIONS] AGENT
```

### Description

Re-run agent execution.

### Options
`--build PATH`
:   Path to the build folder.

`--registry PATH`
:   Path to the local registry folder.

`--help`
:   Show the help message and exit.

## `autonomy replay tendermint`

### Usage
```bash
autonomy replay tendermint [OPTIONS]
```

### Description
Tendermint runner.

### Options
`--build PATH`
:   Path to the build folder.

`--help`
:   Show the help message and exit.


## Examples

The example below shows how to replay agent runs from Tendermint dumps.


1.  Copy and paste the following Makefile into your workspace folder:

    ```makefile
    .PHONY: run-hardhat
    run-hardhat:
      docker run -p 8545:8545 -it valory/open-autonomy-hardhat:0.1.0

    # if you get following error
    # PermissionError: [Errno 13] Permission denied: '/open-aea/build/bdist.linux-x86_64/wheel'
    # or similar to PermissionError: [Errno 13] Permission denied: /**/build
    # remove build directory from the folder that you got error for
    # for example here it should be /path/to/open-aea/repo/build
    .PHONY: run-oracle-dev
    run-oracle-dev:
      if [ "${OPEN_AEA_REPO_DIR}" = "" ];\
      then\
        echo "Please ensure you have set the environment variable 'OPEN_AEA_REPO_DIR'"
        exit 1
      fi
      if [ "$(shell ls ${OPEN_AEA_REPO_DIR}/build)" != "" ];\
      then \
        echo "Please remove ${OPEN_AEA_REPO_DIR}/build manually."
        exit 1
      fi

      autonomy build-image valory/oracle_hardhat --dev && \
        autonomy deploy build valory/oracle_hardhat deployments/keys/hardhat_keys.json --force --dev && \
        make run-deploy

    .PHONY: run-deploy
    run-deploy:
      if [ "${PLATFORM_STR}" = "Linux" ];\
      then\
        mkdir -p abci_build/persistent_data/logs
        mkdir -p abci_build/persistent_data/venvs
        sudo chown -R 1000:1000 -R abci_build/persistent_data/logs
        sudo chown -R 1000:1000 -R abci_build/persistent_data/venvs
      fi
      if [ "${DEPLOYMENT_TYPE}" = "docker-compose" ];\
      then\
        cd abci_build/ &&  \
        docker-compose up --force-recreate -t 600 --remove-orphans
        exit 0
      fi
      if [ "${DEPLOYMENT_TYPE}" = "kubernetes" ];\
      then\
        kubectl create ns ${VERSION}|| (echo "failed to deploy to namespace already existing!" && exit 0)
        kubectl create secret generic regcred \
              --from-file=.dockerconfigjson=/home/$(shell whoami)/.docker/config.json \
              --type=kubernetes.io/dockerconfigjson -n ${VERSION} || (echo "failed to create secret" && exit 1)
        cd abci_build/ && \
          kubectl apply -f build.yaml -n ${VERSION} && \
          kubectl apply -f agent_keys/ -n ${VERSION} && \
          exit 0
      fi
      echo "Please ensure you have set the environment variable 'DEPLOYMENT_TYPE'"
      exit 1
    ```

2. Define the relevant environment variables.

3. Run your preferred app in dev mode, for example run oracle in dev mode using `make run-oracle-dev` and in a separate terminal run `make run-hardhat`.

4. Wait until at least one reset (`reset_and_pause` round) has occurred. This is because the Tendermint server will only dump Tendermint data on resets. Once you have a data dump stop the app.

5. Run `autonomy replay tendermint` . This will spawn a Tendermint network with the available dumps.

6. Now  you can run replays for particular agents using `autonomy replay agent AGENT`, where `AGENT` is a number between `0` and the number of available agents `-1`. E.g., `autonomy replay agent 0` will run the replay for the first agent.
