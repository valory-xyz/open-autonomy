
build-docker-localnode:
	@cd networks/local && make
.PHONY: build-docker-localnode

build-docker-aea:
	docker build -f ../../examples/price_estimation/Dockerfile -t valory/price_estimation:0.1.0 ../..
.PHONY: build-docker-aea

localnet-start: localnet-stop build-docker-localnode build-docker-aea
	docker run --rm -v $(CURDIR)/build:/tendermint:Z tendermint/localnode testnet --config /etc/tendermint/config-template.toml --o . --starting-ip-address 192.167.11.2
	docker-compose up
.PHONY: localnet-start

# Stop testnet
localnet-stop:
	docker-compose down
	sudo rm -rf build
.PHONY: localnet-stop