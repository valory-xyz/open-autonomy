# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021 Valory AG
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

"""Script templates for dev environment."""

BASE_SETUP = """#!/usr/bin/bash
sudo chown -R ubuntu:ubuntu /logs
"""

ABCI_CONFIG_SCRIPT: str = """#!/usr/bin/bash

cd /home/ubuntu/
rm -rf price_estimation
aea --registry-path=/packages fetch --local valory/price_estimation:0.1.0
cd price_estimation

echo -n "{eth_key}" >  ethereum_private_key.txt
aea add-key ethereum

aea config set agent.skill_exception_policy "just_log"
aea config set agent.connection_exception_policy "just_log"
aea config set vendor.valory.connections.abci.config.host "abci{node_id}"
aea config set vendor.valory.connections.abci.config.port 26658 --type int
aea config set vendor.valory.connections.abci.config.use_tendermint False
aea config set vendor.valory.skills.price_estimation_abci.models.params.args.consensus.max_participants {max_participants}
aea config set vendor.valory.skills.price_estimation_abci.models.params.args.round_timeout_seconds 5
aea config set vendor.valory.skills.price_estimation_abci.models.params.args.tendermint_url http://node{node_id}:26657
aea config set vendor.valory.skills.price_estimation_abci.models.params.args.tendermint_com_url "http://node{node_id}:8080"
aea config set vendor.valory.skills.price_estimation_abci.models.params.args.reset_tendermint_after 10 --type int
aea config set vendor.valory.skills.price_estimation_abci.models.params.args.observation_interval 3 --type int
aea config set vendor.valory.skills.price_estimation_abci.models.params.args.max_healthcheck 10 --type int
aea config set vendor.valory.skills.price_estimation_abci.models.params.args.safe_tx_gas 4000000 --type int
aea config set vendor.valory.connections.ledger.config.ledger_apis.ethereum.address "http://hardhat:8545"
aea config set vendor.valory.connections.ledger.config.ledger_apis.ethereum.chain_id 31337 --type int

{extra_config}

aea install
aea build
aea run
"""

DOCKER_COMPOSE_TEMPLATE: str = """version: "3"

services:
  hardhat:
    container_name: hardhat
    image: "node:16.7.0"
    ports:
      - "8545:8545"
    volumes:
      - {root_dir}/third_party/safe-contracts:/home/ubuntu/build
    working_dir: /home/ubuntu/build
    entrypoint: "/bin/bash"
    command: [ "/usr/local/bin/yarn", "run", "hardhat", "node", "--port", "8545"]
    networks:
      localnet:
        ipv4_address: 192.167.11.2
{tendermint_nodes}
{abci_nodes}
networks:
  localnet:
    driver: bridge
    ipam:
      driver: default
      config:
        - subnet: 192.167.11.0/24
"""

TENDERMINT_NODE_TEMPLATE: str = """
  node{node_id}:
    container_name: node{node_id}
    image: "tendermint/localnode"
    cpus: 0.1
    environment:
      - ID={node_id}
      - LOG=${{LOG:-tendermint.log}}
      - FLASK_APP=/app/app.py
      - PROXY_APP=tcp://abci{node_id}:26658
      - TMHOME=/tendermint/node{node_id}
      - CREATE_EMPTY_BLOCKS=true
    volumes:
      - ./build:/tendermint:Z
    working_dir: /tendermint
    entrypoint: /bin/bash
    command: wait-for-it.sh -t 120 hardhat:8545 -- flask run --no-reload --host="0.0.0.0" --port=8080
    networks:
      localnet:
        ipv4_address: 192.167.11.{localnet_address_postfix}
    depends_on:
      - hardhat
"""

ABCI_NODE_TEMPLATE: str = """
  abci{node_id}:
    container_name: abci{node_id}
    image: "valory/price_estimation_dev:0.1.0"
    environment:
      - ID={node_id}
      - TENDERMINT_COM_URL=http://node{node_id}:8080
      - MAX_PARTICIPANTS={max_participants}
    build:
      context: ./
      dockerfile: ./Dockerfile
    volumes:
      - ./logs/:/logs:Z
      - ./configure_agents/:/configure_agents:Z
      - {root_dir}/packages:/packages:Z
    command: ["/usr/bin/wait-for-it", "-t", "120", "hardhat:8545", "--", "python3", "-u", "/home/ubuntu/watcher.py"]
    networks:
      localnet:
        ipv4_address: 192.167.11.{localnet_address_postfix}
    depends_on:
      - hardhat
      - node{node_id}
"""