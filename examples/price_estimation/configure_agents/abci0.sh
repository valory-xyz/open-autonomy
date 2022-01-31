#!/usr/bin/bash

cp ../configure_agents/keys/ethereum_private_key_0.txt ethereum_private_key.txt

aea add-key ethereum
aea config set agent.skill_exception_policy "just_log"
aea config set agent.connection_exception_policy "just_log"
aea config set vendor.valory.connections.abci.config.host "abci0"
aea config set vendor.valory.connections.abci.config.port 26658 --type int
aea config set vendor.valory.connections.abci.config.use_tendermint False
aea config set vendor.valory.skills.price_estimation_abci.models.price_api.args.url https://api.coingecko.com/api/v3/simple/price
aea config set vendor.valory.skills.price_estimation_abci.models.price_api.args.api_id coingecko
aea config set vendor.valory.skills.price_estimation_abci.models.price_api.args.parameters '[["ids", "bitcoin"],["vs_currencies", "usd"]]'  --type list
aea config set vendor.valory.skills.price_estimation_abci.models.price_api.args.response_key 'bitcoin:usd'
aea config set vendor.valory.skills.price_estimation_abci.models.randomness_api.args.url https://drand.cloudflare.com/public/latest
aea config set vendor.valory.skills.price_estimation_abci.models.randomness_api.args.api_id cloudflare
aea config set vendor.valory.skills.price_estimation_abci.models.params.args.consensus.max_participants 4 --type int
aea config set vendor.valory.skills.price_estimation_abci.models.params.args.round_timeout_seconds 7.0 --type float
aea config set vendor.valory.skills.price_estimation_abci.models.params.args.tendermint_url "http://node0:26657"
aea config set vendor.valory.skills.price_estimation_abci.models.params.args.tendermint_com_url "http://node0:8080"
aea config set vendor.valory.skills.price_estimation_abci.models.params.args.reset_tendermint_after 2 --type int
aea config set vendor.valory.skills.price_estimation_abci.models.params.args.observation_interval 3 --type int
aea config set vendor.valory.skills.price_estimation_abci.models.params.args.max_healthcheck 1200 --type int
aea config set vendor.valory.connections.ledger.config.ledger_apis.ethereum.address "http://hardhat:8545"
aea config set vendor.valory.connections.ledger.config.ledger_apis.ethereum.chain_id 31337 --type int


aea build
