
build-docker-localnode:
	@cd networks/local && make
.PHONY: build-docker-localnode

build-docker-aea:
	-docker network ls | grep _localnet | cut -d' ' -f1 | xargs docker network rm
	docker build --no-cache -f ./Dockerfile -t valory/price_estimation_dev:0.1.0 .
.PHONY: build-docker-aea

localnet-setup: localnet-stop
	rm -rf ./logs
	mkdir ./logs
	chmod a+r+w ./logs
	chmod a+r ./configure_agents
	chmod a+x ./configure_agents/*.sh
	docker run --rm -v $(CURDIR)/build:/tendermint:Z tendermint/localnode testnet --config /etc/tendermint/config-template.toml --o . --hostname=node0 --hostname=node1 --hostname=node2 --hostname=node3
.PHONY: localnet-setup

localnet-start: localnet-setup
	docker-compose up
.PHONY: localnet-start

localnet-start-fresh: localnet-setup build-docker-localnode build-docker-aea
	docker-compose up --build --force-recreate
.PHONY: localnet-start-fresh

# Stop testnet
localnet-stop:
	docker-compose down
	sudo rm -rf build
.PHONY: localnet-stop