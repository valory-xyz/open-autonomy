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

# Consolidated run_service.sh — builds and deploys a service.
# Called by aea-helpers run-service via Python wrapper.

set -e

# --- Parse arguments ---
SERVICE_NAME=""
ENV_FILE=".env"
KEYS_FILE="keys.json"
NUM_AGENTS=4
AUTHOR="valory"
CPU_LIMIT=""
MEMORY_LIMIT=""
MEMORY_REQUEST=""
DETACH=false
DOCKER_CLEANUP=false
SKIP_INIT=false
PRE_DEPLOY_CMD=""
POST_DEPLOY_CMD=""

while [[ $# -gt 0 ]]; do
  case $1 in
    --name) SERVICE_NAME="$2"; shift 2 ;;
    --env-file) ENV_FILE="$2"; shift 2 ;;
    --keys-file) KEYS_FILE="$2"; shift 2 ;;
    --agents) NUM_AGENTS="$2"; shift 2 ;;
    --author) AUTHOR="$2"; shift 2 ;;
    --cpu-limit) CPU_LIMIT="$2"; shift 2 ;;
    --memory-limit) MEMORY_LIMIT="$2"; shift 2 ;;
    --memory-request) MEMORY_REQUEST="$2"; shift 2 ;;
    --detach) DETACH=true; shift ;;
    --docker-cleanup) DOCKER_CLEANUP=true; shift ;;
    --skip-init) SKIP_INIT=true; shift ;;
    --pre-deploy-cmd) PRE_DEPLOY_CMD="$2"; shift 2 ;;
    --post-deploy-cmd) POST_DEPLOY_CMD="$2"; shift 2 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

if [ -z "$SERVICE_NAME" ]; then
  echo "Error: --name is required"
  exit 1
fi

# Extract short name from service name (e.g. valory/trader -> trader)
SERVICE_SHORT_NAME="${SERVICE_NAME##*/}"
REPO_PATH=$PWD

# --- Docker cleanup ---
if [ "$DOCKER_CLEANUP" = true ]; then
    echo "Cleaning up Docker containers..."
    docker container stop $(docker container ls -q --filter name="abci") 2>/dev/null || true
    docker container stop $(docker container ls -q --filter name="tm_") 2>/dev/null || true
    docker container rm $(docker container ls -aq --filter name="abci") 2>/dev/null || true
    docker container rm $(docker container ls -aq --filter name="tm_") 2>/dev/null || true
fi

# --- Clean previous build ---
if test -d "$SERVICE_SHORT_NAME"; then
    sudo rm -r "$SERVICE_SHORT_NAME"
fi

# Find and clean previous abci_build directories
for prev_build in $(find . -maxdepth 1 -type d -name "abci_build_*" 2>/dev/null); do
    echo "Removing previous build: $prev_build"
    sudo rm -rf "$prev_build"
done

# --- Source env ---
if [ -f "$ENV_FILE" ]; then
    set -o allexport
    source "$ENV_FILE"
    set +o allexport
fi

# --- Initialize ---
if [ "$SKIP_INIT" = false ]; then
    autonomy init --reset --author "$AUTHOR" --remote --ipfs --ipfs-node "/dns/registry.autonolas.tech/tcp/443/https"
fi

# --- Build ---
make clean 2>/dev/null || true
autonomy packages lock
autonomy push-all
autonomy fetch --local --service "$SERVICE_NAME" && cd "$SERVICE_SHORT_NAME"
autonomy build-image

# --- Copy keys ---
cp "$REPO_PATH/$KEYS_FILE" ./keys.json

# --- Pre-deploy command ---
if [ -n "$PRE_DEPLOY_CMD" ]; then
    echo "Running pre-deploy command: $PRE_DEPLOY_CMD"
    eval "$PRE_DEPLOY_CMD"
fi

# --- Build deployment ---
DEPLOY_FLAGS="-ltm"

if [ -n "$CPU_LIMIT" ]; then
    DEPLOY_FLAGS="$DEPLOY_FLAGS --agent-cpu-limit $CPU_LIMIT"
fi
if [ -n "$MEMORY_LIMIT" ]; then
    DEPLOY_FLAGS="$DEPLOY_FLAGS --agent-memory-limit $MEMORY_LIMIT"
fi
if [ -n "$MEMORY_REQUEST" ]; then
    DEPLOY_FLAGS="$DEPLOY_FLAGS --agent-memory-request $MEMORY_REQUEST"
fi
if [ "$NUM_AGENTS" != "4" ]; then
    DEPLOY_FLAGS="$DEPLOY_FLAGS --n $NUM_AGENTS"
fi

eval "autonomy deploy build $DEPLOY_FLAGS"

# --- Find build directory ---
BUILD_DIR=$(find . -maxdepth 1 -type d -name "abci_build_*" -print -quit)
if [ -z "$BUILD_DIR" ]; then
    # Fall back to non-suffixed directory
    BUILD_DIR="abci_build"
fi

if [ ! -d "$BUILD_DIR" ]; then
    echo "Error: build directory not found"
    exit 1
fi

# --- Post-deploy command ---
if [ -n "$POST_DEPLOY_CMD" ]; then
    echo "Running post-deploy command: $POST_DEPLOY_CMD"
    eval "$POST_DEPLOY_CMD"
fi

# --- Run deployment ---
if [ "$DETACH" = true ]; then
    autonomy deploy run --build-dir "$BUILD_DIR" --detach
else
    autonomy deploy run --build-dir "$BUILD_DIR"
fi
