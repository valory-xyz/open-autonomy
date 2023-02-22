# Release History - `open-autonomy`

# 0.9.1 (2023-02-22)

Autonomy:
- Updates the `docker-compose` template to enable the usage of `host.docker.internal` as host machine gateway

Tests:
- Adds test coverage for newly introduced commands on `autonomy analyse` group

Docs:
- Updates the documentation on the usage of custom images in agent deployments.

Chore:
- Updates the `tomte` version in the `Pipfile`

# 0.9.0 (2023-02-16)

Autonomy:
- Updates the on-chain interaction functionalities to wait for the relevant event to make sure the interaction was successful
- Makes the usage of local tendermint chain optional in the deployment setup
- Introduces `autonomy analyse dialogues` command for analysing the dialogue definitions in a skill package
- Introduces `autonomy analyse service` command for checking the deployment readiness of a service
- Introduces `autonomy analyse logs` command for analysing the agent runtime logs
- Adds support for defining custom author name for docker images on the `autonomy build-image` command
- Removes the usage of `MAX_PARTICIPANTS` environment variable from deployment setup
- Adds support for updating the consensus threshold at the runtime using the on-chain metadata

Packages:
- Makes the synchronized database `serializable` and `hashable`
- Backports the `makerDAO multicall2` contract from [`agent-academy-1`](https://github.com/valory-xyz/agent-academy-1) repository
- Simplifies the way the initial height is set on resets. Now, the initial height will always be `0`
- Removes the need for declaring the `payload_attribute` on the round class implementation
- Updates the base rounds to simplify the usage when payloads have multiple attributes
- Adds support for synchronizing the database on registration so that agents can rejoin at any point
- Removes `reset_index` from `AbciApp` implementation
- Adds restrictions on which agents can submit in late message round
- Fixes overlapping blocks by setting unique chain Ids among the tendermint resets
- Updates the rejoin mechanism to
  - Restart tendermint whenever there's a connection drop, from the abci or otherwise
  - Makes sure monitoring is performed even when tendermint is reset by the tendermint server
  - Clean up `timeouts` and `last_timestamp` before trying to restore state received from peers
  - Don't wait for the observation interval in cases when reset is performed for recovery
  - Enables `ACN` communication for rejoining agents, by accepting `requests/responses` from `all_participants`
- Removes `consensus` parameter from the skills' configurations and replaces the `max_participants` with the length of the `all_participants` list
- Updates the `BaseParams` implementation to enforce minimum values for `observation_interval`
- Updates the `AbciAppDB` implementation to make sure `cross_period_keys` and the database conditions are defined as sets


Tests:
- Adds test coverage for registry contracts
- Adds test for building and running the base autonomy image, the agent runtime image and the tendermint server image
- Re-enables the fuzzer tests for the `valory/abci` connection on windows platform

Docs:
- Removes the usage of `max_participants` parameter
- Rearranges the on-chain registration section to match with the Autonolas protocol documentation
- Adds a link to the `whitepaper`
- Adds documentation on the deployment readiness checks for a service
- Adds a guide on initializing an empty local packages repository 

Chores:
- Increases `CI` timeout for the tests from `70` minutes to `90` minutes
- Bumps `tomte` to `v0.2.2`

# 0.8.0 (2023-01-20)

Autonomy:
- Adds support for minting components using the `autonomy mint` command group
- Adds support for managing on chain services using the `autonomy service` group
- Updates the `autonomy deploy from-token` command to use APIs from `autonomy.chain` module
- Fixes the bug on the `autonomy analyse handlers` command by loading all of the dependencies before running a check

Packages:
- Introduces type checking utility as part of the `abstract_round_abci` skill
- Adds support for sharing the recovery parameters on the tendermint protocol and handler
- Introduces `valory/ipfs` protocol and connection for handling `IPFS` uploads and downloads
- Updates `TendermintRecoveryParams` implementation to make it compatible for sharing the parameters using the `ACN`
- Updates the recovery mechanism in order to first retrieve the `Tendermint` recovery parameters via the `ACN` before attempting to reset
- Enables the usage of `libp2p` connection on `TestTendermintResetInterrup` and `DEBUG` as default logging level
- Updates the implementation of the base transaction payload class to use data classes and makes them immutable
- Updates various skill packages to use the new payload class design
- `Transaction` is implemented using data class now

Plugins:
- Updates the `TendermintRecoveryParams` to clean up the images at the end of the test
- Adds a fixture for the local `IPFS` node address

Tests:
- Adds test coverage for `packages/valory/skills/abstract_round_abci/abci_app_chain.py`

Docs:
- Updates documentation on the developer tooling to better explain the usage of benchmarking tools
- Adds documentation on the usage of the custom docker images for the deployment setup
- Adds documentation for `autonomy mint` and `autonomy service` command groups

Chores:
- Updates `tendermint` docker image to use local `wait-for-it.sh` script instead of downloading from source

# 0.7.0 (2023-01-04)

Autonomy:
- Adds support for updating the participants list at the runtime using the on chain metadata of a service
- Enables the usage of `gRPC` channel when communicating with the `abci` connection
- Updates the tendermint image name constant to make sure it's up to date with the latest framework version

Packages:
- Adds validation for the setup data and raises early if necessary data are not provided instead of waiting for the first round to happen
- Removes the fast forward round because it is not meaningful since the setup data cannot be empty
- Moves `all_participants` to the setup data
- Enables the usage of `gRPC` channel when communicating with the tendermint node
- Adds meta classes for the `AbstractRound` and the `BaseBehaviour` classes to enforce additional checks
- Fixes typing issues on the synchronized database class
- Removes the inappropriate usage of the `# type: ignore` marker and addresses the typing issues properly

Tests:
- Test coverage for `BaseTestEnd2End` in the test plugin
- Test coverage for the `abci` connection
- Test coverage for tendermint protocol dialogues
- Updates hello world `e2e` test to test the usage of `gRPC` channel on tendermint node
- Fixes the inconsistencies regarding the usage of `setup` and `setup_class` methods in the test classes
- Introduces base class for testing test tools
- Adds tests for transaction settlement integration test tools

Docs:
- Updates the guide for running a service on different networks
- Reorganizes the developer tooling section

Chores:
- Updates the coverage collection in the CI to aggregate the coverage for both framework and the packages


# 0.6.0 (2022-12-16)

Autonomy:
- Removes the need for the agent project when scaffolding an `FSM` app using specification. Now when scaffolding the FSM app using the `-tlr` flag, the skill will be directly scaffolded to the local packages directory
- Updates the FMM scaffolding templates to support defining pre and post conditions for the synchronized data
- Updates the tendermint communication server
  - `GET /params` endpoint to return `peer_id` for the local tendermint node
  - `POST /params` endpoint to update `persistent_peers` when updating the chain config

Packages:
- Fixes the `fast_forward_to_behaviour` in the `abci` skill test tools by setting the `_current_round_cls` which is necessary for retrieving the correct class for the synchronized data
- Adds support for auto generated behaviour IDs
- Adds support for auto-generated round IDs
- Introduces the `get_name` method as part of the `abstract_round_abci`skill to retrieve the name of a property dynamically
- Updates the various packages to to newly introduced auto generate functionalities
- Removes sleep on `reset_tendermint_with_wait` on startup
- Updates the `a2a` transaction logic to wait for block production to begin before sending an `a2a` transaction via tendermint
- Updates the `RegistrationStartupBehaviour` and `TendermintHandler` to make sure we update the persistent peers when establishing a new chain
- Adds support for specifying the external host name for the tendermint P2P connection
- Introduces pre and post conditions on the synchronized data for each initial and final state of an FSM app (including default pre conditions). These are verified during chaining of the apps
- Updates all FSM apps to specify their pre- and post-conditions
- Added message handling support to `TmManager`.
- Reset the app hash to the app hash in the begging of the period when hard resetting for recovery

Tests
- Adds tests for `termination_abci`
- Adds tests for docstring analyser when no `AbciApp` definition is found in the provided module
- Adds test coverage for `autonomy develop` command group
- Introduces pre and post conditions checks on the `SynchronizedData` for each initial and final state
- Adds tests for `abci` connection
- Adds an e2e test to showcase hard reset being used as a recovery mechanism


# 0.5.0.post2 (2022-12-09)

Packages:
- Fixes synchronized data for safe deployment
- Ensures that the synchronized data class is set everywhere and added a warning when it is not

Tests:
- Adds tests for checking `PUBLIC_ID` in `__init__.py` files
- Adds tests for small coverage gaps in `open-autonomy`
- Adds tests for registration behaviours
- Adds tests for `abstract_round_abci` skill

Chores:
- Pins `tox` using `tomte` on CI


# 0.5.0.post1 (2022-12-08)

Autonomy:
- Patches packages command group to adapt latest changes from `open-aea`

Packages:
- Fixes version specifiers for `open-aea-test-autonomy` and `open-aea-ledger-ethereum`

# 0.5.0 (2022-12-05)

Autonomy:
- Introduces more flexible approach to defining the overrides for multiple agents in a service component
- Deprecates the usage of `autonomy hash all` command, `autonomy packages lock` can be used to perform package dependency hash updates and checks
- Updates the override serialisation mechanism to be consistent with the environment variable parser
- Extends the `from-token` command to provide password for encrypted private keys at the runtime
- Updates the process of overriding the safe contract address at the runtime to be more generalised
- Fixes a bug that allowed the image build to continue even after a command run failed when building the image on `build-image` command
 
Packages:
- Fixes the `AbciApp` initialization to ensure that synchronized data is retrieved as an instance of the `synchronized_data_class` specified on the round.
- Updates the `IPFSInteract` tool to
  - Catch the broken connection exceptions
  - Remove the correct path before downloading
- Fixes the tendermint reset mechanism to 
  - Avoid race conditions when performing a hard reset
  - Not update the initial height and genesis time when resetting for recovering agent to tendermint communication
  - Update the waiting interval

Tests:
- Tests for the service config loader
- Adds test coverage for `autonomy` framework

Docs:
- Adds documentation on the usage of the service level overrides
- Makes sure that naming convention for autonomous services is consistent throughout the documentation


# 0.4.0 (2022-11-17)

Autonomy:
- Deprecates `autonomy analyse abci` command group
- Merges `autonomy analyse abci check-app-specs` and `autonomy analyse generate-app-specs` into `autonomy analyse fsm-specs`
- Moves `autonomy analyse abci check-handlers`  to `autonomy analyse handlers`  
- Moves `autonomy analyse abci docstrings` to `autonomy analyse docstrings`
- Moves `autonomy analyse abci logs` has been moved to `autonomy analyse logs`
- Refactors the FSM command definition and extract the code to core and helper modules
- Updates the error messages on `autonomy build-image` command
- Improves error handling on `autonomy deploy` command group

Plugins:
- Renames the `tag` property to `image` on `aea_test_autonomy.docker.base.DockerImage` class

Packages:
- Updates the `abstract_round_abci` skill to ignore Tendermint blocks with a height lower than the initial height of the Tendermint chain
- Adds yield statement in `CheckTransactionHistoryBehaviour._check_tx_history` to avoid freezing the entire behaviour
- Moves the Tendermint healthcheck from individual round behaviours to the `AbstractRoundBehaviour` to ensure that Tendermint would reset when the communication is unhealthy
- Extends `ApiSpecs` to support getting the response from a list
- Adds better error `logging` in the `ApiSpecs`
- Adds support to parse error responses to the `ApiSpecs`
- Adds backoff logic to the `ApiSpecs`

Tests:
- Increases the sleep time in `test_async_behaviour_sleep` and `TestRegistrationStartupBehaviour` tests to avoid flakiness
- Tests for newly introduced code in the `ApiSpecs` implementation
- Adds tests for integration test tools on `abstract_round_abci` skill


# 0.3.5 (2022-11-10)

Autonomy:
- Updates the storage class to `nfs-ephemeral` in kubernetes template
- Updates the autonomy image constant  use the framework version as the default tag version
- Extends the `autonomy packages` command group to use new package manager API
- Updates the `autonomy fetch` command to raise proper errors

Packages:
- Updates exit mechanism on the degenerate round to avoid excessive looping
- Adds the functionality to terminate (shutdown) the agent when there are not enough peers in the service
- Removes `round_count` checks from the background round payload validation

Tests:
- Refactors the gnosis safe tests.

Chores:
- Improves the table hash regex to account for markdown quotes on package list generator
- Updates release process to use `tox` command instead of direct command invocations
- Updates `packages.json` to the new format

# 0.3.4 (2022-11-02)

Autonomy:
- Updates service component to use new override policies

Packages:
- Adds `get_service_owner` on the `ServiceRegistry` contract implementation
- Introduces `termination_abci` skill to support service termination
- Extends `abstract_round_abci` to support running the `termination_abci` skill concurrently with the main FSM in order to periodically check for the termination signal.
- Introduces `register_termination` skill and `register_termination` agent to demonstrate `termination_abci` skill
- Extends gnosis safe contract implementation with
  - `get_swap_owner_data` to encode a transaction to swap a safe owner
  - `get_remove_owner_data` to encode a transaction to remove a safe owner
  - `get_zero_transfer_events` to retrieve 0 value transfer events sent to the safe
  - `get_removed_owner_events` to retrieve safe owner removal events

Tests:
- Adds test coverage for core packages
- Extracts the `background_round` (`termination_round`) to it's own skill

Docs:
- Removes redundant documentation on package publishing

# 0.3.3 (2022-10-21)

Autonomy:

- Introduces support for specifying tag versions for runtime image builds.
- Adds the benchmark tool definition in the newly scaffolded FSM skill.
- Adds improvements on the FSM scaffolding.
- Adds support for ACN and hardhat node in deployment setup using build flags.
- Fixes regex in `autonomy analyse` to avoid capturing empty strings.

Tests:

- Adds tests to make sure that scaffolded FSM modules can be tested using the CLI command `autonomy test`.
- Adds test coverage for the app specification module.
- Cleans up various test class usage across `tests/test_autonomy/test_cli`.

Packages:

- Extracts following packages to their respective `GitHub` repositories
  - APY skills, agent, and service.
  - Liquidity rebalancing skills.
  - Price oracle skills, agent, and service.
- Fixes the URL check on the tendermint handler in `abstract_round_abci`.

Docs:

- Improves the quickstart section. 
- Improves the on-chain protocol guides.
- Simplifies and cleans up the demo sections.
- Changes the images to follow the new colour scheme.
- Removes redundant information and redirects to corresponding documentation sections.
- Replaces the usage of oracle service in CLI documentation with the hello world service. 

Chores:

- Fixes make target for image release to avoid issues on different shells.
- Updates some scripts that perform multiple network requests to use parallelization.
- Restructures `Running on other networks` section.


# 0.3.2 (2022-09-30)

Autonomy:
- Fixes issues related to `IP/Host` resolving on windows
- Fixes several issues with dev mode to make it work again

Packages:
- Sets an initial fallback gas and propagates the logs

Docs:
- Address several doc issues, updates FAQ
- Updates scaffolding guide
- Splits `set up` section as a guide to be referenced commonly by the rest of guides
- Separates the deployment part to be in a separate section to be referenced when required
- Moves scaffolding contents to its appropriate place and rewrites some parts of the text
- Updates language in several docs
- Adds cost table and threat model to the docs
- Updates FAQ to use pure markdown
- Adds a link to our contract development guide

Chores:
- Extends the hash fixing script to also fix the hash table in the docs
- Simplifies linter configuration for `pylint`
- Bumps `open-aea` to 1.21.0
- Adds lock check for all platforms

Tests:
- Fixes APY tests after the `setup` and `setup_class` changes
- Fixes counter client behaviour tests.
- Fixes use os specific paths when comparing file names
- Fixes path resolution on Windows
- Fixes `TestTendermintBufferFailing` on windows
- Fixes pandas timestamps conversion to `UNIX`
- Increases `test_get_app_hash` sleep tolerance
- Avoids indirectly handle `NotFittedError`

# 0.3.1 (2022-09-20)

# Autonomy
- Factors out scaffolding templates
- Updates CLI help messages
- Fixes the scaffold `FSM` command so that a skill can be loaded once created
- Adds `valory/open-autonomy-user` Docker image with latest open-autonomy framework installed

# Packages
- Point to ACN Docker image instead of staging ACN nodes
- Removes unnecessary dependency of `transaction_settlement_abci` skill on the `offchain_aggregator` contract
- Adds environment variables for the RPC endpoints of all service specifications
- De duplicates `open_aea` packages by pulling from registry
- Increases the validate timeout by an order of magnitude in `Polygon` service

# Tests
- Fixes build image test

# Docs
- Adds a doc section to explain package management
- Fixes broken links on documentation

# Chores
- Fixes `release-image` target on the `Makefile` to use `packages.json`
- Check hashes in `packages.json` instead of `hashes.csv`
- Removes changelog
- Updates command regex to reflect latest changes

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
