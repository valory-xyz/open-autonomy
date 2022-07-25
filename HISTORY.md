# Release History - `open-autonomy`

# 0.1.4 (2022-20-08)

Autonomy:
- Ports deployment resources as data files
- Adds support for the usage of remote registry when building a service deployment
- Updates the image build process

Packages:
- Makes Registration ABCI abstract
- Adds check to make sure FSM chaining only involves abstract skills
- Sets a deadline for dict serializer hypothesis test in order to resolve flakiness

Docs:
- Adds docs on publishing packages

## 0.1.3 (2022-15-08)

Autonomy:
- Adds support for CID v1 hashes

Packages:
- Fixes `verify_contract` method so it does not return a hardcoded value
- Replaces `history_duration` with `history_start`, `history_interval_in_unix` and `history_end` in APY skill.
- Bumps the service registry contract to the latest version

Chores:
- Fixes the persistent peers' configurations for the e2e tests.
- Updates ACN nodes in agent config files
- Fixes tendermint subprocess termination issues on macOS
- Fixes several flaky tests


## 0.1.2 (2022-07-08)

Autonomy:
- Updates `hash all` command to update agent hashes on service components when hashing service components
- Adds tests for missing coverage

Packages:
- Adds service for `hello_world` agent
- Introduces `raise_on_try` parameter in nested contract calls
- Introduces mechanism to enforce round id uniqueness
- Adds a method to clean the current period history for every parameter in the DB
- Adds parameter that users can optionally configure so period history is cleaned on every reset
- Fixes list representation in config YAML files
- Adds check for `unsafe-reset-all` to verify if the command exited successfully

Chores:
- Fixes `atheris` installation
- Adds CodeQL analysis

Docs:
- Adds documentation for `TendermintHandler` class
- Updates communication flows.
- Updates fonts and colours

## 0.1.1 (2022-06-22)

Autonomy:
- Patches `push-all`, `publish` and `fetch` to support service packages
- Fixes click context issue on CLI tool

Packages:
- Adds support for `Proof Of Authority` chains
- Adds pricing strategy for `Polygon` chain

Chores:
- Adds multi os and multi python interpreter CI matrix.
- Adds script to check links in docs
- Bumps `Tendermint` to `v0.34.19`

Docs:
- Removes SVN command usage with `aea fetch/add` and IPFS hashes

## 0.1.0 (2022-06-15)

- Release of the initial package.

## 0.1.0rc2 (2022-06-13)

- Second release candidate of the initial package.

## 0.1.0rc1 (2022-06-13)

- First release candidate of the initial package.
