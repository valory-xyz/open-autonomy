#!/bin/bash
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2026 Valory AG
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

# Consolidated run_agent.sh — fetches, configures, and runs an agent locally.
# Called by aea-helpers run-agent via Python wrapper.

set -e

# --- Parse arguments ---
AGENT_NAME=""
ENV_FILE=".env"
AGENT_ENV_FILE=""
CONFIG_REPLACE=false
CONFIG_MAPPING=""
CONNECTION_KEY=false
FREE_PORTS=false
SKIP_MAKE_CLEAN=false
ABCI_PORT=${TENDERMINT_ABCI_PORT:-26658}
RPC_PORT=${TENDERMINT_RPC_PORT:-26657}
P2P_PORT=${TENDERMINT_P2P_PORT:-26656}
COM_PORT=${TENDERMINT_COM_PORT:-8080}
HTTP_PORT=${HTTP_SERVER_PORT:-8716}

while [[ $# -gt 0 ]]; do
  case $1 in
    --name) AGENT_NAME="$2"; shift 2 ;;
    --env-file) ENV_FILE="$2"; shift 2 ;;
    --agent-env-file) AGENT_ENV_FILE="$2"; shift 2 ;;
    --config-replace) CONFIG_REPLACE=true; shift ;;
    --config-mapping) CONFIG_MAPPING="$2"; shift 2 ;;
    --connection-key) CONNECTION_KEY=true; shift ;;
    --free-ports) FREE_PORTS=true; shift ;;
    --skip-make-clean) SKIP_MAKE_CLEAN=true; shift ;;
    --abci-port) ABCI_PORT="$2"; shift 2 ;;
    --rpc-port) RPC_PORT="$2"; shift 2 ;;
    --p2p-port) P2P_PORT="$2"; shift 2 ;;
    --com-port) COM_PORT="$2"; shift 2 ;;
    --http-port) HTTP_PORT="$2"; shift 2 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

if [ -z "$AGENT_NAME" ]; then
  echo "Error: --name is required"
  exit 1
fi

# --- Find free port helper ---
find_free_port() {
  local start_port=$1
  local port=$start_port
  while ! python3 -c "
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    s.bind(('127.0.0.1', $port))
    s.close()
    exit(0)
except socket.error:
    s.close()
    exit(1)
" 2>/dev/null; do
    port=$((port + 1))
  done
  echo $port
}

# --- Resolve ports ---
if [ "$FREE_PORTS" = true ]; then
  echo "Finding free ports..."
  DYNAMIC_START=50000
  if [ "${TENDERMINT_ABCI_PORT:-}" = "" ]; then
    ABCI_PORT=$(find_free_port $DYNAMIC_START)
    DYNAMIC_START=$((ABCI_PORT + 10))
  fi
  if [ "${TENDERMINT_RPC_PORT:-}" = "" ]; then
    RPC_PORT=$(find_free_port $DYNAMIC_START)
    DYNAMIC_START=$((RPC_PORT + 10))
  fi
  if [ "${TENDERMINT_P2P_PORT:-}" = "" ]; then
    P2P_PORT=$(find_free_port $DYNAMIC_START)
    DYNAMIC_START=$((P2P_PORT + 10))
  fi
  if [ "${TENDERMINT_COM_PORT:-}" = "" ]; then
    COM_PORT=$(find_free_port $DYNAMIC_START)
    DYNAMIC_START=$((COM_PORT + 10))
  fi
  if [ "${HTTP_SERVER_PORT:-}" = "" ]; then
    HTTP_PORT=$(find_free_port $DYNAMIC_START)
  fi
  echo "Ports: ABCI=$ABCI_PORT RPC=$RPC_PORT P2P=$P2P_PORT COM=$COM_PORT HTTP=$HTTP_PORT"
fi

export TENDERMINT_ABCI_PORT=$ABCI_PORT
export TENDERMINT_RPC_PORT=$RPC_PORT
export TENDERMINT_P2P_PORT=$P2P_PORT
export TENDERMINT_COM_PORT=$COM_PORT
export HTTP_SERVER_PORT=$HTTP_PORT

# --- Cleanup trap ---
cleanup() {
    echo "Terminating tendermint..."
    if kill -0 "$tm_subprocess_pid" 2>/dev/null; then
        kill "$tm_subprocess_pid"
        wait "$tm_subprocess_pid" 2>/dev/null
    fi
    echo "Tendermint terminated"
}
trap cleanup EXIT

# --- Clean previous build ---
if test -d agent; then
    sudo rm -r agent
fi
find . -empty -type d -delete 2>/dev/null || true

if [ "$SKIP_MAKE_CLEAN" = false ]; then
    make clean 2>/dev/null || true
fi

# --- Fetch agent ---
autonomy packages lock
autonomy fetch --local --agent "$AGENT_NAME" --alias agent

# --- Source env and run config replace ---
if [ -f "$ENV_FILE" ]; then
    source "$ENV_FILE"
fi

if [ "$CONFIG_REPLACE" = true ]; then
    if [ -z "$CONFIG_MAPPING" ]; then
        echo "Error: --config-mapping is required when --config-replace is set"
        exit 1
    fi
    aea-helpers config-replace --mapping "$CONFIG_MAPPING" --env-file "$ENV_FILE" --agent-dir agent
fi

# --- Configure agent ---
cd agent

if [ -n "$AGENT_ENV_FILE" ] && [ -f "../$AGENT_ENV_FILE" ]; then
    cp "../$AGENT_ENV_FILE" .
fi

cp ../ethereum_private_key.txt .
aea -s add-key ethereum ethereum_private_key.txt

if [ "$CONNECTION_KEY" = true ]; then
    aea -s add-key ethereum ethereum_private_key.txt --connection
fi

aea -s issue-certificates

# --- Start tendermint ---
rm -r ~/.tendermint 2>/dev/null || true
tendermint init 2>/dev/null

tendermint node \
    --proxy_app=tcp://127.0.0.1:$ABCI_PORT \
    --rpc.laddr=tcp://127.0.0.1:$RPC_PORT \
    --p2p.laddr=tcp://0.0.0.0:$P2P_PORT \
    --p2p.seeds= \
    --consensus.create_empty_blocks=true \
    > /dev/null 2>&1 &
tm_subprocess_pid=$!

# --- Run agent ---
if [ -n "$AGENT_ENV_FILE" ]; then
    aea -s run --env "$AGENT_ENV_FILE"
else
    aea -s run
fi
