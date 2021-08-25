#!/usr/bin/env sh

cp ../configure_agents/keys/ethereum_private_key_0.txt ethereum_private_key.txt
aea config set vendor.valory.skills.price_estimation_abci.models.price_api.args.source_id coingecko
aea config set vendor.valory.skills.price_estimation_abci.models.params.args.consensus.max_participants 4
aea config set vendor.valory.skills.price_estimation_abci.models.params.args.tendermint_url http://node0:26657
aea config set vendor.valory.skills.price_estimation_abci.models.params.args.ethereum_node_url http://hardhat:8545
aea config set vendor.valory.skills.price_estimation_abci.models.params.args.ethereum_node_url http://localhost:8545
aea config set vendor.valory.skills.price_estimation_abci.models.params.args.proxy_contract_address "0x17DC3e46223Cad17c917aB86f3A2aAA53Ad2aB6e"
aea build