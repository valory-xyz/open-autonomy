#! /bin/bash
echo Running the aea with $(aea --version)
echo "Loading $AEA_AGENT"

aea fetch $AEA_AGENT --alias agent
cd agent

echo "Installing the necessary dependencies!"
aea -v DEBUG install

echo "Copying agent key"
cp /agent_key/ethereum_private_key.txt .
cp /agent_key/ethereum_private_key.txt ethereum_flashbots_private_key.txt

echo "Running the aea without a password!"
aea generate-key cosmos --connection
aea add-key cosmos --connection || (echo "Failed to generate the cosmos key needed for libp2p connection" && exit 1)
aea add-key ethereum
aea add-key ethereum_flashbots
aea issue-certificates --aev || (echo "Failed to add cosmos key needed for libp2p connection" && exit 1)
aea run --aev
