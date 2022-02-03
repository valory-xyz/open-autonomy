SHELL := /bin/bash

VERSION := 0.1.0

build-images:
	cd ../
	make build-images
	cd deployments
.PHONY: build-images


localnet-start: build-images
# creates a docker-compose
# hardhat
# price_estimation_deployment
# 4 agents
# configures the build directory for tendermint
	cd ../
	python deployments/create_deployment.py \
		-t docker-compose \
		-ct \
		-app oracle_hardhat
	cd deployments/build && docker-compose up --build --force-recreate
.PHONY: localnet-start

# Stop testnet
localnet-stop:
	cd build
	docker-compose down
.ONESHELL: localnet-stop

