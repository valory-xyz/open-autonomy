# Release History - `open-autonomy`

# 0.3.0 (2022-09-14)

# Autonomy

- Adds `PYTHONHASHSEED` in Kubernetes deployment template
- Moves all fixtures into `aea_test_autonomy` plugin.
- Adds `service-registry-network` cli command for starting a local hardhat node. 

# Packages

- Replaces `third-party` dependencies with docker images. 
- Fixes import from tests folder and `path_to_skill` in FSM scaffolding
- Moves remaining tests into packages, in particular agents.

# Chores

- Adds README header
- Removes `quickstart` skip on command test
- Removes unnecessary shebangs from several non-script files
- Adds a script to validates commands in the docs and Makefile
- Cleans the `README.md` and `AUTHORS.md` to reflect changes

# 0.2.2 (2022-08-09)

# AEA

- Adds support for registry flags on `autonomy scaffold fsm` command
- Adds support for scaffolding
  - Dialogues
  - Payloads
  - Tests
- Adds support for specifying version for runtime images
- Removes the need for `NESTED_FIELDS_ALLOWED_TO_UPDATE` from service config class
- Uses local file for service registry ABI rather than fetching from staging server
- Replaces the usage of staging chain with locally deployed chain

# Packages
- Adds support for broadcasting APY estimates to a backend server.
- Replaces API keys with environment variable placeholders
- Ports tests for packages to their respective package folders

# Plugins
- Introduces `aea-test-autonomy` plugin

# Chores
- Fixes tendermint logging issues
- Updates skaffold config for building runtime images for agents
- Bumps autonolas registries sub module to latest

# Tests
- Replaces the usage of staging chain with local registry deployments
- Fixes flaky `test_fetch_behaviour_non_indexed_block` test
- Fixes flaky registry tests
- Adds tests for `autonomy scaffold fsm`

# Docs
- Restructures documentation to introduce new index
- Adds tutorials on creating a service using an existing agent
- Updates quick start documentation
- Adds overview for service development process
- Adds docs for fsm scaffolding tool

# 0.2.1.post1 (2022-08-29)

Autonomy:
- Fix stream logging for docker SDK interactions
- Use docker SDK to build tendermint testnet config

# 0.2.1 (2022-08-26)

Autonomy:
- Introduces base autonomy image and agent runtime image for performance improvements.
- Removes the need for building the dependency images at the runtime.
- Updates the deployment flow to utilize the newly improved images.
- Removes the support for pushing the images using the Open Autonomy CLI tool.
- Removes `skaffold` as a framework dependency.
- Adds support for remote registries in the fsm scaffold utility.
- Bumps `open-aea` and its plugins to version `1.17.0`.

Packages:
- Adds support for parsing all the gnosis GS codes and print relevant messages.
- Renames `io` module in `abstract_round_abci` to `io_` to avoid possible namespace conflicts with standard `io` module
- Refactors `io_` module to move `Loaders` and `Storers` classes to relevant skill
- Decreases validation timeout on `Polygon`

Chores:
- Updates `tox` definitions and `Makefile` targets to reflect the latest state of the repository.
- Fixes spell check in the CI.
- Pins the machine learning libraries to stable versions
- Updates `scripts/check_doc_ipfs_hashes.py` with more generalized regex

Tests:
- Adds tests for `scripts/check_doc_ipfs_hashes.py`
- Fixes ledger connection test
- Fixes test for `from-token` command

# 0.2.0 (2022-08-21)

Autonomy:
- Introduces the intended deployment flow, including changes to service configurations.
- Bumps `open-aea` and its plugins to version `1.16.0`.
- Introduces support for partial deployments referencing on-chain agent instances.
- Adds `autonomy scaffold fsm` command.
- Adds support for fetching and updating the multisig safe address when deploying from tokens.
- Adds `--log-level` flag on deploy command to support specifying log levels for agent and tendermint runtimes.
- Remove the need for `THIRD_PARTY` constant and updates the base image classes to set the third party contracts path on runtime.
- Includes data files for the test tools in the `setup.py`.
- Updates the `autonomy deploy build` command to re-enable the dev mode.

Packages:
- Improves gas estimation in `gnosis_safe` and packages depending on it.
- Addresses dependency inconsistencies in various packages detected with the new `open-aea` version.
- Fixes a `ledger` connection issue caused by wrong usage of the `asyncio.wait()` method.
- Fixes oracle service configurations to only broadcast from `goerli` and `polygon`.
- Adds an APY service specification.
- Adds the simple abci service specification.
- Fills coverage gaps in `abstract_round_abci`.
- Fixes a circular resolution issue with the `abstract_round_abci` and `transaction_settlement_abci` introduced in the previous release.

Tests:
- Adds a retry strategy for the subgraph tests which depend on the network and may fail occasionally.
- Adds package check test to ensure package consistency with respect to dependencies.

Chores:
- Backports various functionalities from other Valory repos using packages.
- Adds coverage to handlers and log parser.
- Updates readme to reflect all currently required dependencies and their versions.
- Adds the `gitleaks` scan job.
- Improves inference of package type in the doc IPFS hash checker script.
- Adds data on minted components, agents and services.

Docs:
- Makes docs independent of repositories `Makefile` by explicitly replacing make commands or adding code snippets.
- Fixes edit URI on docs.
- Updates the docs to describe the latest dev mode usage.
- Change Tendermint flow diagram to a custom diagram to avoid copyright issues.
- Adds a section to discuss agent services in context of other architectures.
- Adds documentation on CLI commands `fetch` and `run`.
- Reorganize demos to give a consistent and homogeneous structure.


# 0.1.6 (2022-08-01)

Autonomy:
- Extracts generic test utils into `autonomy.test_tools`

Packages:
- Ports the tendermint GRPC package and test tools from `agent-academy-1` repo
- Moves base test classes into `abstract_round_abci` skill package

Chore:
- Bumps `mistune` to `2.0.3`
- Updates `skaffold` to latest version

Docs:
- Updates the demo section
- Adds info about Docker Desktop on MacOS and Windows

# 0.1.5 (2022-07-29)

Autonomy:
- Depends on `open-aea>=1.14.0.post1`
- Cleans up Dockerfiles and aligns them

Packages:
- Adds support to handle the `{'code': -32000, 'message': 'already known'}` response in the `transaction_settlement_abci`
- Adds environment variables support for debugging
- Extends consistency checks of events in `abstract_round_abci`
- Removes unused events and handles unhandled events
- Updates oracle staging URLs
- Adds support for Goerli oracle
- Updates service registry to on-chain deployment v1
- Fixes logic error in the retry logic of `get_transaction_receipt` in the `ledger` connection

Tests:
- Generalises various base classes for easier re-use
- Adds tests to ensure better docs integrity
- Adds additional tests for the `transaction_settlement_abci`
- Improves `apy_estimation_abci` end-to-end and unit tests
- Fixes registration reset end-to-end test edge case

Docs:
- Adds various clarifications in the docs based on user feedback and internal proof readings
- Adds various fixes and consistency improvements
- Lists relevant dependencies and their versions

Misc:
- Cleans up skaffold and Dockerfiles


# 0.1.4 (2022-07-20)

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

## 0.1.3 (2022-07-15)

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
