#!/usr/bin/env sh

cp ../configure_agents/keys/ethereum_private_key_0.txt ethereum_private_key.txt

aea config set vendor.valory.skills.price_estimation_abci.models.price_api.args.url https://api.coingecko.com/api/v3/simple/price
aea config set vendor.valory.skills.price_estimation_abci.models.price_api.args.api_id coingecko
aea config set vendor.valory.skills.price_estimation_abci.models.price_api.args.parameters "ids:bitcoin;vs_currencies:usd"
aea config set vendor.valory.skills.price_estimation_abci.models.price_api.args.response_key "bitcoin:usd"

aea config set vendor.valory.skills.price_estimation_abci.models.randomness_api.args.url https://drand.cloudflare.com/public/latest
aea config set vendor.valory.skills.price_estimation_abci.models.randomness_api.args.api_id cloudflare


aea config set vendor.valory.skills.price_estimation_abci.models.params.args.consensus.max_participants 4
aea config set vendor.valory.skills.price_estimation_abci.models.params.args.keeper_timeout_seconds 5
aea config set vendor.valory.skills.price_estimation_abci.models.params.args.tendermint_url http://node0:26657
aea config set vendor.valory.connections.ledger.config.ledger_apis.ethereum.address http://hardhat:8545
aea build