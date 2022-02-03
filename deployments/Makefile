SHELL := /bin/bash
CLUSTERS := $(shell kind get clusters)
TOKENPATH := $(shell ls ~/.docker/config.json)
NUMBER_OF_NODES := 4
RESULT := ""
PODS := $(shell kubectl get pods | grep agent | awk '{print $$1}')
DEPLOYMENTS := $(shell kubectl get deployments | grep agent | awk '{print $$1}')

VERSION := 0.1.0

build-images:
	cd ../
	make build-images
	cd deployments
.PHONY: build-images


localnet-start: localnet-stop build-images
# creates a docker-compose
# hardhat
# price_estimation_deployment
# 4 agents
# configures the build directory for tendermint
# deploys oracle contract
# deploys safe contract
	sudo rm -rf build/*
	cd ../
	python deployments/create_deployment.py \
		-t docker-compose \
		-ct \
		-app oracle_hardhat
	cd deployments/build && docker-compose up --build --force-recreate
.PHONY: localnet-start

cluster-create-deployments:
	sudo python3 configure_agents/create_env.py -n 4 -net hardhat -doc -dsc
.ONESHELL: cluster-create-deployment

# Stop testnet
localnet-stop:
	cd build
	docker-compose down
	sudo rm -rf build
.PHONY: localnet-stop


cluster-setup:
	if [[ "${TOKENPATH}" == "" ]]; then \
		echo "ensure you have an access token ready."; \
		docker login -u valory; \
	fi
	kubectl create secret generic regcred \
	            --from-file=.dockerconfigjson=${TOKENPATH} \
	            --type=kubernetes.io/dockerconfigjson
	kubectl create serviceaccount dashboard-admin-sa
	kubectl create clusterrolebinding dashboard-admin-sa --clusterrole=cluster-admin --serviceaccount=default:dashboard-admin-sa
	skaffold run --profile dashboard
.PHONY: cluster-setup

localcluster-start:
	if [[ "${CLUSTERS}" == "" ]]; then \
		kind create cluster;\
	fi
	skaffold config set local-cluster false
	skaffold run --profile configure-localcluster
	make cluster-setup
	make cluster-create-deployments
	make cluster-deploy
.PHONY: localcluster-start

localcluster-stop:
	kind delete cluster
.PHONY: localcluster-stop

# once a cluster has been initialised, use following to manage
# we can deploy and remove deployments to the cluster
cluster-remove-deploy:
	for pod in ${DEPLOYMENTS} ; do \
		kubectl delete deployment $$pod --force;\
	done
	for pod in ${PODS} ; do \
		kubectl delete pod $$pod --force;\
	done
	kubectl delete deployment hardhat
	kubectl delete svc hardhat
	kubectl delete pv task-pv-volume
	kubectl delete pvc build-vol --force
.PHONY: localcluster-remove-deploy

cluster-create-deployments:
	sudo python3 configure_agents/create_env.py -n 4 -net hardhat -doc -dsc
	python deployments/create_deployment.py \
		-t docker-compose \
		-net ropsten \
		-app valory/price_estimation:0.1.0 \
		-n 4 \
		-c
.ONESHELL: cluster-create-deployment

cluster-deploy:
	skaffold run --profile deploy
.ONESHELL: cluster-deploy

remotecluster-start:
	cd infra && terraform apply
	KUBECONFIG=~/.kube/config:./kubefiles/nemo kubectl config view --flatten > ~/.kube/config
	cd ..
	skaffold config set local-cluster false
	skaffold run --profile configure-remotecluster
	make cluster-setup
	make cluster-create-deployments
	make cluster-deploy
.PHONY: remotecluster-start

remotecluster-stop:
	cd infra && terraform destroy
.PHONY: remotecluster-stop


cluster-dashboard-start:
	kubernetes-dashboard-stop
	bash ./kubernetes_configs/configuration/setup_dashboard.sh
.ONESHELL: kubernetes-dashboard-start

cluster-dashboard-stop:
	pkill -9 -f "kubectl proxy"
.ONESHELL: kubernetes-dashboard-stop
