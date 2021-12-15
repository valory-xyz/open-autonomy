#!/bin/bash

cp ../configure_agents/keys/ethereum_private_key_1.txt ethereum_private_key.txt

aea add-key ethereum
aea config set vendor.valory.connections.abci.config.use_tendermint False

aea config set vendor.valory.skills.price_estimation_abci.models.price_api.args.url https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest
aea config set vendor.valory.skills.price_estimation_abci.models.price_api.args.api_id coinmarketcap
aea config set vendor.valory.skills.price_estimation_abci.models.price_api.args.headers '[{"Accepts": "application/json"}, {"X-CMC_PRO_API_KEY": "27d2cd0d-80c3-4ec3-9305-4f3d9ad34e41"}]'  --type list
aea config set vendor.valory.skills.price_estimation_abci.models.price_api.args.parameters '[["symbol","BTC"], ["convert","USD"]]'  --type list
aea config set vendor.valory.skills.price_estimation_abci.models.price_api.args.response_key 'data:BTC:quote:USD:price'
aea config set vendor.valory.skills.price_estimation_abci.models.randomness_api.args.url https://api.drand.sh/public/latest
aea config set vendor.valory.skills.price_estimation_abci.models.randomness_api.args.api_id protocollabs1
aea config set vendor.valory.skills.price_estimation_abci.models.params.args.consensus.max_participants 4 --type int
aea config set vendor.valory.skills.price_estimation_abci.models.params.args.round_timeout_seconds 7 --type int
aea config set vendor.valory.skills.price_estimation_abci.models.params.args.tendermint_url "http://node1:26657"
aea config set vendor.valory.skills.price_estimation_abci.models.params.args.observation_interval 300 --type int
aea config set vendor.valory.skills.price_estimation_abci.models.params.args.max_healthcheck 43200 --type int
aea config set vendor.valory.skills.price_estimation_abci.models.params.args.period_setup.safe_contract_address "0x7AbCC2424811c342BC9A9B52B1621385d7406676"
aea config set vendor.valory.skills.price_estimation_abci.models.params.args.period_setup.oracle_contract_address "0xB555E44648F6Ff759F64A5B451AB845B0450EA57"
aea config set vendor.valory.connections.ledger.config.ledger_apis.ethereum.address "https://ropsten.infura.io/v3/2980beeca3544c9fbace4f24218afcd4"
aea config set vendor.valory.connections.ledger.config.ledger_apis.ethereum.chain_id 3 --type int
aea build
