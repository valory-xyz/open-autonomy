#!/usr/bin/env sh

AGENT_ID=$(echo $HOSTNAME | grep -Eo '[0-9]{1,4}')

echo -n $AEA_KEY  ethereum_private_key.txt

# cp ../configure_agents/keys/ethereum_private_key_"${AGENT_ID}".txt ethereum_private_key.txt
aea config set vendor.valory.skills.price_estimation_abci.models.price_api.args.source_id coingecko
# aea config set vendor.valory.skills.price_estimation_abci.models.price_api.args.source_id $API_ID
aea config set vendor.valory.skills.price_estimation_abci.models.params.args.consensus.max_participants 4
aea config set vendor.valory.skills.price_estimation_abci.models.params.args.keeper_timeout_seconds 5
aea config set vendor.valory.skills.price_estimation_abci.models.params.args.tendermint_url http://localhost:26657
aea config set vendor.fetchai.connections.ledger.config.ledger_apis.ethereum.address http://hardhat:8545
sed -i "s/gas_price_api_key: null/gas_price_api_key: null\n      chain_id: 31337/" vendor/fetchai/connections/ledger/connection.yaml
aea build
