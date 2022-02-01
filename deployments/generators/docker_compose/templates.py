# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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

"""Deployment Templates."""

TENDERMINT_CONFIG_TEMPLATE: str = """docker run --rm -v $(pwd)/deployments/build/build:/tendermint:Z \
--entrypoint=/usr/bin/tendermint \
valory/consensus-algorithms-tendermint:0.1.0 \
    testnet \
        --config /etc/tendermint/config-template.toml \
        --v {validators} \
        --o . \
        {hosts}
"""


DOCKER_COMPOSE_TEMPLATE: str = """version: "3"
services:
{hardhat_chain}
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

HARDHAT_NODE_TEMPLATE: str = """
  hardhat:
    container_name: hardhat
    image: "valory/consensus-algorithms-hardhat:0.1.0"
    ports:
      - "8545:8545"
    working_dir: /home/ubuntu/build
    networks:
      localnet:
        ipv4_address: 192.167.11.2
"""

TENDERMINT_NODE_TEMPLATE: str = """
  node{node_id}:
    container_name: node{node_id}
    image: "valory/consensus-algorithms-tendermint:0.1.0"
    environment:
      - ID={node_id}
      - LOG=${{LOG:-tendermint.log}}
      - PROXY_APP=tcp://abci{node_id}:26658
      - TMHOME=/tendermint/node{node_id}
      - CREATE_EMPTY_BLOCKS=true
    volumes:
      - ./build:/tendermint:Z
    working_dir: /tendermint
    entrypoint: /bin/bash
    command:  wrapper.sh node --consensus.create_empty_blocks=true --proxy_app=tcp://abci{node_id}:26658
    networks:
      localnet:
        ipv4_address: 192.167.11.{localnet_address_postfix}
"""

ABCI_NODE_TEMPLATE: str = """
  abci{node_id}:
    container_name: abci{node_id}
    image: "valory/consensus-algorithms-open-aea:0.1.0"
    volumes:
      - ./logs/:/logs:z
    environment:
{agent_vars}
    networks:
      localnet:
        ipv4_address: 192.167.11.{localnet_address_postfix}
    depends_on:
      - node{node_id}
"""
