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


TENDERMINT_CONFIG_TEMPLATE: str = """/usr/bin/tendermint testnet \
        --config /etc/tendermint/config-template.toml \
        --v {validators} \
        --o . \
        {hosts}
"""

DOCKER_COMPOSE_TEMPLATE: str = """version: "2.4"
services:
{hardhat_node}{acn_node}{tendermint_nodes}{abci_nodes}
networks:
  localnet:
    driver: bridge
    ipam:
      driver: default
      config:
        - subnet: 192.167.11.0/24
"""

ACN_NODE_TEMPLATE: str = """  acn:
    container_name: acn
    image: "{acn_image_name}:{acn_image_version}"
    restart: always
    environment:
      - AEA_P2P_ID=d9e43d3f0266d14b3af8627a626fa734450b1c0fcdec6f88f79bcf5543b4668c
      - AEA_P2P_URI_PUBLIC=0.0.0.0:5000
      - AEA_P2P_URI=0.0.0.0:5000
      - AEA_P2P_DELEGATE_URI=0.0.0.0:11000
      - AEA_P2P_URI_MONITORING=0.0.0.0:8081
    entrypoint: ["python3", "-u", "/acn/node/run_acn_node_standalone.py", "/acn/node/libp2p_node", "--config-from-env"]
    networks:
      localnet:
        ipv4_address: 192.167.11.3
    ports:
      - "9005:9005"
      - "11000:11000"
"""

HARDHAT_NODE_TEMPLATE: str = """  hardhat:
    container_name: hardhat
    image: "{hardhat_image_name}:{hardhat_image_version}"
    ports:
      - "8545:8545"
    networks:
      localnet:
        ipv4_address: 192.167.11.2
"""

TENDERMINT_NODE_TEMPLATE: str = """
  node{node_id}:
    mem_limit: 1024m
    mem_reservation: 256M
    cpus: 0.5
    container_name: node{node_id}
    hostname: node{node_id}
    image: "{tendermint_image_name}:{tendermint_image_version}"
    restart: always
    environment:
      - ID={node_id}
      - PROXY_APP=tcp://abci{node_id}:26658
      - TMHOME=/tendermint/node{node_id}
      - CREATE_EMPTY_BLOCKS=true
      - DEV_MODE=0
      - LOG_FILE=/logs/node_{node_id}.txt
      - LOG_LEVEL={log_level}
    working_dir: /tendermint
    command: ["run", "--no-reload", "--host=0.0.0.0", "--port=8080",]
    depends_on:
      abci{node_id}:
        condition: service_healthy
    networks:
      localnet:
        ipv4_address: 192.167.11.{localnet_address_postfix}
    volumes:
      - ./nodes:/tendermint:Z
      - ./persistent_data/logs:/logs:Z
"""

ABCI_NODE_TEMPLATE: str = """
  abci{node_id}:
    mem_limit: 1024m
    mem_reservation: 256M
    cpus: 1
    container_name: abci{node_id}
    image: {runtime_image}
    environment:
      - PYTHONHASHSEED=0
      - LOG_FILE=/logs/aea_{node_id}.txt
{agent_vars}
    networks:
      localnet:
        ipv4_address: 192.167.11.{localnet_address_postfix}
    volumes:
      - ./persistent_data/logs:/logs:Z
      - ./agent_keys/agent_{node_id}:/agent_key:Z
"""
