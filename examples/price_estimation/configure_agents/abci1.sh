#!/usr/bin/env sh

cp ../configure_agents/keys/ethereum_private_key_1.txt ethereum_private_key.txt

aea config set vendor.valory.skills.price_estimation_abci.models.price_api.args.url https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest
aea config set vendor.valory.skills.price_estimation_abci.models.price_api.args.api_id coinmarketcap
aea config set vendor.valory.skills.price_estimation_abci.models.price_api.args.headers "Accepts:application/json;X-CMC_PRO_API_KEY:2142662b-985c-4862-82d7-e91457850c2a"
aea config set vendor.valory.skills.price_estimation_abci.models.price_api.args.parameters "symbol:BTC;convert:USD"
aea config set vendor.valory.skills.price_estimation_abci.models.price_api.args.response_key "data:BTC:quote:USD:price"

aea config set vendor.valory.skills.price_estimation_abci.models.randomness_api.args.url https://api.drand.sh/public/latest
aea config set vendor.valory.skills.price_estimation_abci.models.randomness_api.args.api_id protocollabs1

aea config set vendor.valory.skills.price_estimation_abci.models.params.args.consensus.max_participants 4
aea config set vendor.valory.skills.price_estimation_abci.models.params.args.keeper_timeout_seconds 5
aea config set vendor.valory.skills.price_estimation_abci.models.params.args.tendermint_url http://node1:26657
aea config set vendor.valory.connections.ledger.config.ledger_apis.ethereum.address http://hardhat:8545
aea build