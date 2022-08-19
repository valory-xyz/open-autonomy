# Benchmarks

The benchmarking tools allow measuring the performance of an agent service realised on the {{open_autonomy}} framework.

## How to use benchmarking tools

1. Setup agent runtime environment in dev mode using `autonomy deployment SERVICE_ID KEYS --dev`.

2. Run agents for `1` period and wait until the round where the skill is configured to call the `BenchmarkTool.save` method. (You can also run agents for `N` periods if you want more data).

3. Point the aggregation script to the directory containing the benchmark data. This will generate a `benchmarks.html` file containing benchmark stats in your current directory.

## Example usage

Copy and paste the following Makefile into your local environment:

```bash
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

  autonomy deploy build image valory/oracle_hardhat --dependencies && \
    autonomy deploy build image valory/oracle_hardhat --dev && \
    autonomy deploy build deployment valory/oracle_hardhat deployments/keys/hardhat_keys.json --force --dev && \
    make run-deploy

.PHONY: run-oracle
run-oracle:
	export VERSION=0.1.0
	autonomy deploy build image valory/oracle_hardhat --dependencies && \
		autonomy deploy build image valory/oracle_hardhat && \
		autonomy deploy build deployment valory/oracle_hardhat deployments/keys/hardhat_keys.json --force && \
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
Then define the relevant environment variables.

Run benchmarks for `oracle/price_estimation`:

```bash
make run-oracle
```
or
```bash
make run-oracle-dev
```

and, if you want to use local blockchain, in a separate tab run

```bash
make run-hardhat
```

By default this will create a `4` agent runtime where you can wait until all `4` agents are at the end of the first period (you can wait for more periods if you want) and then you can stop the runtime. The data will be stored in the `abci_build/persistent_data/benchmarks` folder. You can use the following script to aggregate this data:

```bash
autonomy analyse benchmarks abci_build/persistent_data/benchmarks
```

By default the script will generate output for all periods but you can specify which period to generate output for. Similarly, block types aggregation is configurable as well.
