
build-docker-localnode:
	@cd networks/local && make
.PHONY: build-docker-localnode

build-docker-aea:
	-docker network ls | grep _localnet | cut -d' ' -f1 | xargs docker network rm
	docker build -f ../../examples/price_estimation/Dockerfile -t valory/price_estimation:0.1.0 ../..
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


# make local cluster
localcluster-start:
	kind create cluster
	TOKEN=$(shell ls /home/$(USER)/.docker/config.json)
	echo "$${TOKEN}"
	if [$${TOKEN} == ""]; then \
		echo "ensure you have an access token ready."; \
		docker login -u valory; else\
		echo "already logged in.";
	fi
	kubectl create secret generic regcred \
	            --from-file=.dockerconfigjson=$${TOKEN} \
	            --type=kubernetes.io/dockerconfigjson
	skaffold config set local-cluster false
	kubectl create serviceaccount dashboard-admin-sa
	kubectl create clusterrolebinding dashboard-admin-sa --clusterrole=cluster-admin --serviceaccount=default:dashboard-admin-sa
	skaffold run --profile dashboard
.ONESHELL: localcluster-start

localcluster-deploy:
	skaffold run --profile minikube
.ONESHELL: localcluster-deploy

kubernetes-dashboard-start:
	kubernetes-dashboard-stop
	bash ./kubernetes_configs/setup_dashboard.sh
.ONESHELL: kubernetes-dashboard-start

kubernetes-dashboard-stop:
	pkill -9 -f "kubectl proxy"
.ONESHELL: kubernetes-dashboard-stop

localcluster-stop:
	kind delete cluster
.PHONY: localcluster-stop