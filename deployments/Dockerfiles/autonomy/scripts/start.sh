#! /bin/bash

# ensure hard exit on any failure
set -e
export PYTHONWARNINGS="ignore"

# Debug mode
if [ "$DEBUG" == "1" ]; then
    echo "Debugging..."
    while true; do
        echo "waiting"
        sleep 2
    done
fi

function generateKey() {
    if [ "$AEA_PASSWORD" != "" ]; then
        echo "Generating key $1 with a password!"
        aea generate-key $1 --password $AEA_PASSWORD
    else
        echo "Generating key $1 without a password!"
        aea generate-key $1
    fi
}

function checkKey() {
    export FILE=/agent_key/$(echo $1)_private_key.txt
    echo "Checking to see if $FILE exists"
    if [ -f "$FILE" ]; then
        echo "AEA key provided. Copying to agent."
        cp $FILE .
    else
        # we now check the dependecies, and generate keys we need, if not present.
        if grep open-aea-ledger-$1 aea-config.yaml -q; then
            echo "AEA key not provided yet is required. Generating."
            generateKey $1
        fi
    fi
    addKey $1
}

function handleFlashbotsKey() {
    if grep "open-aea-ledger-ethereum-flashbots" aea-config.yaml -q; then
        echo "Copying ethereum key to ethereum flashbots key"
        cp ethereum_private_key.txt ethereum_flashbots_private_key.txt
    fi
}

function handleCosmosConnectionKeyAndCerts() {
    echo "Generating cosmos key for libp2p connection"
    if [ ! -f "cosmos_private_key.txt" ]; then
        generateKey cosmos
    fi

    if [[ "$AEA_PASSWORD" != "" ]]; then
        echo "Issuing certificates with password"
        aea add-key cosmos --connection --password $AEA_PASSWORD
        aea issue-certificates --password $AEA_PASSWORD
    else
        echo "Issuing certificates without password"
        aea add-key cosmos --connection
        aea issue-certificates
    fi
}

function runAgent() {
    if [[ "$AEA_PASSWORD" != "" ]]; then
        aea run --password $AEA_PASSWORD
    else
        aea run
    fi
}

function addKey() {
    FILE=$(echo $1)_private_key.txt
    if [ -f "$FILE" ]; then
        echo "$1 key provided. Adding to agent."
        if [[ "$AEA_PASSWORD" != "" ]]; then
            aea add-key $1 --password $AEA_PASSWORD
        else
            aea add-key $1
        fi
    fi
}

function main() {
    echo "Running the aea with $(aea --version)"

    echo "Checking keys"
    checkKey ethereum
    checkKey cosmos
    checkKey solana

    echo "Checking autonomy specific connection keys"
    handleFlashbotsKey
    handleCosmosConnectionKeyAndCerts

    echo "Running the aea"
    runAgent
}

cd agent
main
