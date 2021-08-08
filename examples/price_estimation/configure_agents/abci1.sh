#!/usr/bin/env sh

aea generate-key ethereum
aea config set vendor.valory.skills.price_estimation_abci.models.price_api.args.source_id coinmarketcap
aea config set vendor.valory.skills.price_estimation_abci.models.price_api.args.api_key 2142662b-985c-4862-82d7-e91457850c2a
aea config set vendor.valory.skills.price_estimation_abci.models.params.args.consensus.max_participants 4
aea config set vendor.valory.skills.price_estimation_abci.models.params.args.tendermint_url http://node1:26657
aea build