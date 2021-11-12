#!/usr/bin/env sh

cp ../configure_agents/keys/ethereum_private_key_3.txt ethereum_private_key.txt

aea config set vendor.valory.skills.price_estimation_abci.models.price_api.args.url https://api.binance.com/api/v3/ticker/price
aea config set vendor.valory.skills.price_estimation_abci.models.price_api.args.api_id binance
aea config set vendor.valory.skills.price_estimation_abci.models.price_api.args.parameters '[["symbol", "BTCUSDT"]]' --type list
aea config set vendor.valory.skills.price_estimation_abci.models.price_api.args.response_key 'price'

aea config set vendor.valory.skills.price_estimation_abci.models.randomness_api.args.url https://api3.drand.sh/public/latest
aea config set vendor.valory.skills.price_estimation_abci.models.randomness_api.args.api_id protocollabs2

aea config set vendor.valory.skills.price_estimation_abci.models.params.args.consensus.max_participants 4
aea config set vendor.valory.skills.price_estimation_abci.models.params.args.keeper_timeout_seconds 5
aea config set vendor.valory.skills.price_estimation_abci.models.params.args.tendermint_url http://node3:26657
aea config set vendor.valory.connections.ledger.config.ledger_apis.ethereum.address http://hardhat:8545

aea build