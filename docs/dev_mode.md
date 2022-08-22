# Agent Runtime With Hot Reload Mode

The hot reload mode enables hot code swapping and reflects changes on the agent code as well as the local `open-aea` repository without rebuilding or restarting containers manually.

## General Guide

Arbitrary agent services built with the {{open_autonomy}} framework can be run with the hot start functionality.

### Environment setup

Fetch the required service or if you already have a service defined navigate to the service directory and run

```bash
# build dev deployment using
$ autonomy deploy build --dev --packages-dir PATH_TO_PACKAGES_DIR --open-aea-dir PATH_TO_LOCAL_OPEN_AEA_REPO --open-autonomy-dir PATH_TO_LOCAL_OPEN_AUTONOMY_DIR
# build the required images using
$ autonomy build-images --dependencies
$ autonomy build-images --dev
```

This will create a deployment with hot reload enabled for agents. You can run it using the same methods as normal deployments. Use `autonomy deploy run` or `docker-compose up --force-recreate` to start the deployment and enjoy building the services.

**The `open-aea` repository can be cloned from here: https://github.com/valory-xyz/open-aea**

And - if you want to use local hardhat - in a separate terminal run:
```bash
docker run -p 8545:8545 -it valory/open-autonomy-hardhat:0.1.0
```

Once the agents are running, you can make changes to the agent's packages as well as the `open-aea` and it will trigger the restarts.

The trigger is caused by any python file closing in either `open-autonomy/packages` or `open-aea/` directory. So even if you haven't made any change and still want to restart the agent, just open any python file press `ctrl+s` or save it from file menu and it will trigger the restart.


## Debugging in the cluster

When debugging deployments, it can be useful to have the option to spin up a hardhat node to enable debugging and testing of the issue within the cluster.

```bash
VERSION=cluster-dev
DEPLOYMENT_TYPE=kubernetes
DEPLOYMENT_KEYS=deployments/keys/hardhat_keys.json
SERVICE_ID=valory/oracle_hardhat

make push-images build-deploy run-deploy
```

where the Makefile can be copied from here:
```bash
.ONESHELL: build-images
build-images:
	if [ "${VERSION}" = "" ];\
	then\
		echo "Ensure you have exported a version to build!";\
		exit 1
	fi
	autonomy deploy build image ${SERVICE_ID} --dependencies || (echo failed && exit 1)
	if [ "${VERSION}" = "dev" ];\
	then\
		echo "building dev images!";\
	 	autonomy deploy build image ${SERVICE_ID} \
			--dev && exit 0
		exit 1
	fi
	autonomy deploy build image ${SERVICE_ID} --version ${VERSION} && exit 0
	exit 1

.ONESHELL: build-images push-images
push-images:
	if [ "${VERSION}" = "" ];\
	then\
		echo "Ensure you have exported a version to build!";\
		exit 1
	fi
	autonomy deploy build image ${SERVICE_ID} --dependencies --push || (echo failed && exit 1)
	if [ "${VERSION}" = "dev" ];\
	then\
		echo "building dev images!";\
		autonomy deploy build image ${SERVICE_ID} --dev --push || (echo failed && exit 1)
		exit 0
	fi
	autonomy deploy build image ${SERVICE_ID} --version ${VERSION} --prod --push || (echo failed && exit 1)
	exit 0

.PHONY: build-deploy
build-deploy:
	if [ "${DEPLOYMENT_TYPE}" = "" ];\
	then\
		echo "Please ensure you have set the environment variable 'DEPLOYMENT_TYPE'"
		exit 1
	fi
	if [ "${SERVICE_ID}" = "" ];\
	then\
		echo "Please ensure you have set the environment variable 'SERVICE_ID'"
		exit 1
	fi
	if [ "${DEPLOYMENT_KEYS}" = "" ];\
	then\
		echo "Please ensure you have set the environment variable 'DEPLOYMENT_KEYS'"
		exit 1
	fi
	echo "Building deployment for ${DEPLOYMENT_TYPE} ${DEPLOYMENT_KEYS} ${SERVICE_ID}"

	if [ "${DEPLOYMENT_TYPE}" = "kubernetes" ];\
	then\
		if [ "${VERSION}" = "cluster-dev" ];\
		then\
			autonomy deploy build deployment ${SERVICE_ID} ${DEPLOYMENT_KEYS} --kubernetes --force --dev
			exit 0
		fi
		autonomy deploy build deployment ${SERVICE_ID} ${DEPLOYMENT_KEYS} --kubernetes --force
		exit 0
	fi
	if [ "${VERSION}" = "dev" ];\
	then\
		autonomy deploy build deployment ${SERVICE_ID} ${DEPLOYMENT_KEYS} --docker --dev --force
		exit 0
	fi
	autonomy deploy build deployment ${SERVICE_ID} ${DEPLOYMENT_KEYS} --docker

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

This will deploy a private hardhat container to the cluster, along with the associated agent service, configured to use the hardhat container.
