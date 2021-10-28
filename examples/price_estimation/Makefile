
build-docker-localnode:
	@cd networks/local && make
.PHONY: build-docker-localnode

build-docker-aea:
	-docker network ls | grep _localnet | cut -d' ' -f1 | xargs docker network rm
	docker build -f ../../examples/price_estimation/Dockerfiles/aea/Dockerfile -t valory/price_estimation:0.1.0 ../..
.PHONY: build-docker-aea

localnet-start: localnet-stop build-docker-localnode build-docker-aea
	docker run --rm -v $(CURDIR)/build:/tendermint:Z tendermint/localnode testnet --config /etc/tendermint/config-template.toml --o . --starting-ip-address 192.167.11.3
	docker-compose up
.PHONY: localnet-start

# Stop testnet
localnet-stop:
	docker-compose down
	sudo rm -rf build
.PHONY: localnet-stop

SHELL := /bin/bash
CLUSTERS := $(shell kind get clusters)
TOKENPATH := $(shell ls ~/.docker/config.json)
NUMBER_OF_NODES := 8
RESULT := ""

localcluster-start:
	if [[ "${CLUSTERS}" == "" ]]; then \
		kind create cluster;\
	fi
	if [[ "${TOKENPATH}" == "" ]]; then \
		echo "ensure you have an access token ready."; \
		docker login -u valory; \
	fi
	kubectl create secret generic regcred \
	            --from-file=.dockerconfigjson=${TOKENPATH} \
	            --type=kubernetes.io/dockerconfigjson
	skaffold config set local-cluster false
	kubectl create serviceaccount dashboard-admin-sa
	kubectl create clusterrolebinding dashboard-admin-sa --clusterrole=cluster-admin --serviceaccount=default:dashboard-admin-sa
	skaffold run --profile dashboard
	sudo configure_agents/create_env.py -n ${NUMBER_OF_NODES}
	skaffold run --profile configure
	echo "Waiting for cluster configuration to be completed..."
	kubectl wait --for=condition=complete job/config-nodes --timeout=300s
.ONESHELL: localcluster-start

# 	if [[ "${OSTYPE}" == "linux-gnu"* ]]; then \
# 	    TOKEN="$(shell ls /home/$(USER)/.docker/config.json)"; \
# 	elif [[ "${OSTYPE}" == "darwin"* ]]; then \
# 	    TOKEN="$(shell ls ~/.docker/config.json)"; \
# 	else \
# 	    TOKEN="$(shell ls /home/$(USER)/.docker/config.json)"; \
# 	fi

localcluster-create-deployments: 

	echo "creating deployment configs for ${NUMBER_OF_NODES}"
	RESULT = $(shell python create_env.py ${NUMBER_OF_NODES})
	if [[ "${RESULT}" == "" ]]; then \
		echo "Error creating deployments ${NUMBER_OF_NODES} agents";
	else\
	fi
#	if [[ "${RESULT}" == ""]]; then \
#		echo "Error creating deployments ${NUMBER_OF_NODES} agents";\
#		exit 1;\
	skaffold run --profile minikube;
.ONESHELL: localcluster-create-deployment

localcluster-deploy: 
	skaffold run --profile deploy
.ONESHELL: localcluster-deploy

localcluster-dashboard-start:
	kubernetes-dashboard-stop
	bash ./kubernetes_configs/configuration/setup_dashboard.sh
.ONESHELL: kubernetes-dashboard-start

localcluster-dashboard-stop:
	pkill -9 -f "kubectl proxy"
.ONESHELL: kubernetes-dashboard-stop

localcluster-stop:
	kind delete cluster
.PHONY: localcluster-stop

PODS := $(shell kubectl get pods | grep agent | awk '{print $$1}')
DEPLOYMENTS := $(shell kubectl get deployments | grep agent | awk '{print $$1}')
localcluster-remove-deploy:
	for pod in ${DEPLOYMENTS} ; do \
		kubectl delete deployment $$pod --force;\
	done
	for pod in ${PODS} ; do \
		kubectl delete pod $$pod --force;\
	done
	kubectl delete job config-nodes

.PHONY: localcluster-remove-deploy
