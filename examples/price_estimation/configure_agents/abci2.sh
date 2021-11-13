#!/usr/bin/env sh

cp ../configure_agents/keys/ethereum_private_key_2.txt ethereum_private_key.txt

aea config set vendor.valory.skills.price_estimation_abci.models.price_api.args.url https://api.coinbase.com/v2/prices/BTC-USD/buy
aea config set vendor.valory.skills.price_estimation_abci.models.price_api.args.api_id coinbase
aea config set vendor.valory.skills.price_estimation_abci.models.price_api.args.response_key "data:amount"

aea config set vendor.valory.skills.price_estimation_abci.models.randomness_api.args.url https://api2.drand.sh/public/latest
aea config set vendor.valory.skills.price_estimation_abci.models.randomness_api.args.api_id protocollabs2


aea config set vendor.valory.skills.price_estimation_abci.models.params.args.consensus.max_participants 4 --type int
aea config set vendor.valory.skills.price_estimation_abci.models.params.args.keeper_timeout_seconds 5 --type int
aea config set vendor.valory.skills.price_estimation_abci.models.params.args.tendermint_url "http://node2:26657"
aea config set vendor.valory.skills.price_estimation_abci.models.params.args.observation_interval 1200 --type int
aea config set vendor.valory.skills.price_estimation_abci.models.params.args.period_setup.safe_contract_address "0x7AbCC2424811c342BC9A9B52B1621385d7406676"
aea config set vendor.valory.skills.price_estimation_abci.models.params.args.period_setup.oracle_contract_address "0xB555E44648F6Ff759F64A5B451AB845B0450EA57"
aea config set vendor.valory.connections.ledger.config.ledger_apis.ethereum.address "https://ropsten.infura.io/v3/2980beeca3544c9fbace4f24218afcd4"
aea config set vendor.valory.connections.ledger.config.ledger_apis.ethereum.chain_id 3 --type int
aea build
