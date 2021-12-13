#!/usr/bin/env sh

cp ../configure_agents/keys/ethereum_private_key_1.txt ethereum_private_key.txt

aea config set vendor.valory.skills.apy_estimation_abci.models.spooky_subgraph.args.url https://api.thegraph.com/subgraphs/name/eerieeight/spookyswap
aea config set vendor.valory.skills.apy_estimation_abci.models.spooky_subgraph.args.api_id spookyswap
aea config set vendor.valory.skills.apy_estimation_abci.models.spooky_subgraph.args.response_key 'data'
aea config set vendor.valory.skills.apy_estimation_abci.models.spooky_subgraph.args.top_n_pools 100 --type int
aea config set vendor.valory.skills.apy_estimation_abci.models.spooky_subgraph.args.bundle_id 1 --type int
aea config set vendor.valory.skills.apy_estimation_abci.models.spooky_subgraph.args.headers "Content-Type: application/json"
aea config set vendor.valory.skills.apy_estimation_abci.models.randomness_api.args.url https://api.drand.sh/public/latest
aea config set vendor.valory.skills.apy_estimation_abci.models.randomness_api.args.api_id protocollabs1
aea config set vendor.valory.skills.apy_estimation_abci.models.fantom_subgraph.args.url https://api.thegraph.com/subgraphs/name/matthewlilley/fantom-blocks
aea config set vendor.valory.skills.apy_estimation_abci.models.fantom_subgraph.args.api_id fantom
aea config set vendor.valory.skills.apy_estimation_abci.models.params.args.consensus.max_participants 4 --type int
aea config set vendor.valory.skills.apy_estimation_abci.models.params.args.round_timeout_seconds 1000 --type int
aea config set vendor.valory.skills.apy_estimation_abci.models.params.args.tendermint_url "http://node1:26657"
aea config set vendor.valory.skills.apy_estimation_abci.models.params.args.observation_interval 86400 --type int
aea config set vendor.valory.skills.apy_estimation_abci.models.params.args.max_healthcheck 43200 --type int
aea config set vendor.valory.connections.ledger.config.ledger_apis.ethereum.address "http://hardhat:8545"
aea config set vendor.valory.connections.ledger.config.ledger_apis.ethereum.chain_id 31337 --type int
aea config set vendor.valory.skills.apy_estimation_abci.models.params.args.data_folder data
aea config set vendor.valory.skills.apy_estimation_abci.models.params.args.drand_public_key 868f005eb8e6e4ca0a47c8a77ceaa5309a47978a7c71bc5cce96366b5d7a569937c529eeda66c7293784a9402801af31
aea config set vendor.valory.skills.apy_estimation_abci.models.params.args.estimation.steps_forward 1
aea config set vendor.valory.skills.apy_estimation_abci.models.params.args.history_duration 6
aea config set vendor.valory.skills.apy_estimation_abci.models.params.args.estimation.optimizer.n_trials 10 --type int
aea config set vendor.valory.skills.apy_estimation_abci.models.params.args.estimation.optimizer.timeout None
aea config set vendor.valory.skills.apy_estimation_abci.models.params.args.estimation.optimizer.n_jobs 1 --type int
aea config set vendor.valory.skills.apy_estimation_abci.models.params.args.estimation.optimizer.show_progress_bar false
aea config set vendor.valory.skills.apy_estimation_abci.models.params.args.estimation.optimizer.scoring pinball
aea config set vendor.valory.skills.apy_estimation_abci.models.params.args.estimation.optimizer.alpha 0.25
aea config set vendor.valory.skills.apy_estimation_abci.models.params.args.estimation.pair_id 0x2b4c76d0dc16be1c31d4c1dc53bf9b45987fc75c
aea config set vendor.valory.skills.apy_estimation_abci.models.params.args.estimation.sleep_time 10
aea build
