
build-docker-localnode:
	@cd networks/local && make
.PHONY: build-docker-localnode


localnet-start: localnet-stop build-docker-localnode
	docker run --rm -v $(CURDIR)/build:/tendermint:Z tendermint/localnode testnet --config /etc/tendermint/config-template.toml --o . --starting-ip-address 192.167.10.2
	docker-compose up
.PHONY: localnet-start

# Stop testnet
localnet-stop:
	docker-compose down
	sudo rm -rf build
.PHONY: localnet-stop