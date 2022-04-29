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

from deployments.constants import IMAGE_VERSION


TENDERMINT_CONFIG_TEMPLATE: str = (
    """docker run --rm -v $(pwd)/deployments/build/build:/tendermint:Z \
--entrypoint=/usr/bin/tendermint \
valory/consensus-algorithms-tendermint:%s  \
    testnet \
        --config /etc/tendermint/config-template.toml \
        --v {validators} \
        --o . \
        {hosts}
"""
    % IMAGE_VERSION
)

DOCKER_COMPOSE_TEMPLATE: str = """version: "2.4"
services:
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

HARDHAT_NODE_TEMPLATE: str = (
    """
  hardhat:
    container_name: hardhat
    image: "valory/consensus-algorithms-hardhat:%s "
    ports:
      - "8545:8545"
    working_dir: /home/ubuntu/build
    networks:
      localnet:
        ipv4_address: 192.167.11.2
"""
    % IMAGE_VERSION
)

TENDERMINT_NODE_TEMPLATE: str = (
    """
  node{node_id}:
    mem_limit: 1024m
    mem_reservation: 256M
    cpus: 0.5
    container_name: node{node_id}
    hostname: node{node_id}
    image: "valory/consensus-algorithms-tendermint:%s"
    restart: always
    environment:
      - ID={node_id}
      - PROXY_APP=tcp://abci{node_id}:26658
      - TMHOME=/tendermint/node{node_id}
      - CREATE_EMPTY_BLOCKS=true
      - DEV_MODE=0
      - LOG_FILE=/logs/node_{node_id}.txt
    working_dir: /tendermint
    command: ["run", "--no-reload", "--host=0.0.0.0", "--port=8080",]
    depends_on:
      abci{node_id}:
        condition: service_healthy
    networks:
      localnet:
        ipv4_address: 192.167.11.{localnet_address_postfix}
    volumes:
      - ./build:/tendermint:Z
      - ../persistent_data/logs:/logs:Z
"""
    % IMAGE_VERSION
)

ABCI_NODE_TEMPLATE: str = (
    """
  abci{node_id}:
    mem_limit: 1024m
    mem_reservation: 256M
    cpus: 0.5
    container_name: abci{node_id}
    image: "valory/consensus-algorithms-open-aea:{valory_app}V%s"
    environment:
      - LOG_FILE=/logs/aea_{node_id}.txt
{agent_vars}
    networks:
      localnet:
        ipv4_address: 192.167.11.{localnet_address_postfix}
    volumes:
      - ../persistent_data/logs:/logs:Z
"""
    % IMAGE_VERSION
)

if IMAGE_VERSION == "dev":
    ABCI_NODE_TEMPLATE += "      - ../../packages:/home/ubuntu/packages:rw\n"
    ABCI_NODE_TEMPLATE += "      - ../../../open-aea/:/open-aea\n"
    ABCI_NODE_TEMPLATE += "      - ../persistent_data/benchmarking:/benchmarking:Z\n"
    TENDERMINT_NODE_TEMPLATE += "      - ../persistent_data/tm_state:/tm_state:Z"
    TENDERMINT_NODE_TEMPLATE = TENDERMINT_NODE_TEMPLATE.replace(
        "DEV_MODE=0", "DEV_MODE=1"
    )
