This page provides some tips on how to upgrade agent services between different versions of the {{open_autonomy}} framework. For full release notes check the <a href="https://github.com/valory-xyz/open-autonomy/tags" target="_blank">Open-Autonomy repo</a>.

Below we describe the additional manual steps required to upgrade between different versions:


# Open Autonomy

## `v0.15.2` to `v0.16.0`

- The `priority_fee_estimation_trigger` has been removed from the `eip1559` configuration of the ledger connection.
- The `default_priority_fee` is now optional. 
  If it is set to `None`, dynamic pricing will be applied. 
  Otherwise, the specified value will be used.

## `v0.15.1` to `v0.15.2`

No backwards incompatible changes.

## `v0.15.0` to `v0.15.1`

No backwards incompatible changes.

## `v0.14.14.post2` to `v0.15.0`

- After this release, developers do not need to make sure that cross-period persisted keys preexist in the database
  before the first period ends anymore. 
  You may remove any additional logic you had in place to protect from that (#2131).
- The cross-period persisted keys are now initialized by the framework during startup. 
  The corresponding property is used to get the value. 
  If a property with the same name does not exist, then the pre-existing value in the db is used, otherwise `None`.
- You need to keep the above in mind when:
  1. Reading cross-period values from the db.
  2. Implementing properties for cross-period keys, 
     as the returned value will end up being the one that will be writen to the db during startup.

## `v0.14.14` to `v0.14.14.post2`

No backwards incompatible changes.

## `v0.14.14.post1` to `v0.14.14.post2`

The breaking feature introduced in `v0.14.14` and `v0.14.14.post1` has been removed.
For more information please check the `HISTORY.md` file.

## `v0.14.14` to `v0.14.14.post1`

A breaking feature was introduced. 
We suggest using the `v0.14.14.post2` release instead.
For more information please check the `HISTORY.md` file.

## `v0.14.13` to `v0.14.14`

A breaking feature was introduced. 
We suggest using the `v0.14.14.post2` release instead.
For more information please check the `HISTORY.md` file.

## `v0.14.12` to `v0.14.13`

No backwards incompatible changes

## `v0.14.11.post1` to `v0.14.12`

- This release pins `click>=8.1.0,<9` so update your environments to avoid dependency conflicts

## `v0.14.11` to `v0.14.11.post1`

No backwards incompatible changes

## `v0.14.10` to `v0.14.11`

No backwards incompatible changes

## `v0.14.9` to `v0.14.10`

No backwards incompatible changes

## `v0.14.8` to `v0.14.9`

No backwards incompatible changes

## `v0.14.7` to `v0.14.8`

No backwards incompatible changes

## `v0.14.6` to `v0.14.7`

No backwards incompatible changes

## `v0.14.5` to `v0.14.6`

No backwards incompatible changes

## `v0.14.4` to `v0.14.5`

No backwards incompatible changes

## `v0.14.3.post1` to `v0.14.4`

No backwards incompatible changes

## `v0.14.3` to `v0.14.3.post1`

No backwards incompatible changes

## `v0.14.2` to `v0.14.3`

No backwards incompatible changes

## `v0.14.1` to `v0.14.2`

No backwards incompatible changes

## `v0.14.0` to `v0.14.1`

No backwards incompatible changes

## `v0.13.10` to `v0.14.0`

- This release introduces automated dependency verification on the minting tools, this means when minting a package you will have to mint all of the dependencies beforehand. The minting tools uses a subgraph to verify dependencies so you might have to wait for a small amount of time before you can mint the package after you mint the dependencies. 
- Since the dependency verification is automated the `--skip-hash-check` and `--skip-dependencies-check` flags have been deprecated on the `autonomy mint/service` command groups

## `v0.13.9.post1` to `v0.13.10`

No backwards incompatible changes

## `v0.13.9` to `v0.13.9.post1`

No backwards incompatible changes

## `v0.13.8` to `v0.13.9`

No backwards incompatible changes

## `v0.13.7` to `v0.13.8`

No backwards incompatible changes

## `v0.13.6` to `v0.13.7`

No backwards incompatible changes

## `v0.13.5` to `v0.13.6`

No backwards incompatible changes

## `v0.13.4` to `v0.13.5`

No backwards incompatible changes

## `v0.13.3` to `v0.13.4`

No backwards incompatible changes

## `v0.13.2` to `v0.13.3`

No backwards incompatible changes

## `v0.13.1` to `v0.13.2`

- The usage `--password` of flag has been deprecated on `autonomy deploy` command group. Use `OPEN_AUTONOMY_PRIVATE_KEY_PASSWORD` environment variable to export the private key password string when running `autonomy deploy build/run` commands.

## `v0.13.1` to `v0.13.1.post1`

No backwards incompatible changes

## `v0.13.0` to `v0.13.1`

- This release introduces support for defining service level dependencies, which means you can define python dependencies at the service level which will take priority over the agent or component level dependencies. The `dependencies` parameter is currently optional to make the upgrading easier. But this will be required in the next release, so please update your services accordingly.

## `v0.12.1.post4` to `v0.13.0`

- `open-aea-web3` has been replaced with `web3py`
- `protobuf` has been bumped to `protobuf>=4.21.6,<5.0.0`, this means you will have to bump your protocol generator to `v24.3` and generate your protocol packages again.
- The `valory/open-autonomy` image will use Python 3.11 as default interpreter for running agents

## `v0.12.1.post3` to `v0.12.1.post4`

No backwards incompatible changes

## `v0.12.1.post2` to `v0.12.1.post3`

No backwards incompatible changes

## `v0.12.1.post1` to `v0.12.1.post2`

No backwards incompatible changes

## `v0.12.1` to `v0.12.1.post1`

- Environment variable names have changed for custom contract address, refer to the `mint/service` CLI tools documentation regarding the changes.

## `v0.12.0` to `v0.12.1`

No backwards incompatible changes

## `v0.11.1` to `v0.12.0`

- Renamed the `background_behaviour_cls` in `AbstractRoundBehaviour` to `termination_behaviour_cls`. 
 *Should be taken into consideration for all the apps that are utilizing the termination.*
- Renamed the `background_behaviour` in `AbstractRoundBehaviour` to `termination_behaviour`.
- Renamed the `is_background_behaviour_set` property in `AbstractRoundBehaviour` to `is_termination_set`.
- Renamed the `background_round_cls` argument of the `add_termination` method in `AbciApp` to `termination_round_cls`. 
 *Should be taken into consideration for all the apps that are utilizing the termination.*
- Renamed the `background_round_cls` attribute of the `AbciApp` to `termination_round_cls`.
- Renamed the `_background_round` attribute of the `AbciApp` to `_termination_round`.
- Renamed the `background_round` property of the `AbciApp` to `termination_round`.
- The `AbstractRound` class now requires a `SkillContext` positional argument. 
 To accommodate this change, 
 all round tests will need to be modified to include a mocked context in addition to the synchronized data.

1 && 4 should be taken into consideration for all the apps that are utilizing the termination.

## `v0.11.0` to `v0.11.1`

The `autonomy deploy run` command now handles the exists from deployment and to do this we're running the deployments in detached mode and waiting for the user to cancel what that means is from now on when running the deployments the logs won't be printed out by default. If you want to check out the logs for containers you can use `docker logs` command.

## `v0.10.11.post1` to `v0.11.0`

- `web3py` has been replaced with `open-aea-web3` and we forked this from `web3py@v6.0.0`, that means the method names will use the `snake_case` and the `camelCase` naming has been deprecated
- Support for `Python 3.7` has been deprecated

## `v0.10.11` to `v0.10.11.post1`

No backwards incompatible changes

## `v0.10.10.post1` to `v0.10.11`

No backwards incompatible changes

## `v0.10.10` to `v0.10.10.post1`

No backwards incompatible changes

## `v0.10.9` to `v0.10.10`

No backwards incompatible changes

## `v0.10.8` to `v0.10.9`

No backwards incompatible changes

## `v0.10.7` to `v0.10.8`

No backwards incompatible changes

## `v0.10.6` to `v0.10.7`

No backwards incompatible changes

## `v0.10.5.post2` to `v0.10.6`

No backwards incompatible changes

## `v0.10.5.post1` to `v0.10.5.post2`

No backwards incompatible changes

## `v0.10.4` to `v0.10.5.post1`

No backwards incompatible changes

## `v0.10.3` to `v0.10.4`

No backwards incompatible changes

## `v0.10.2` to `v0.10.3`

No backwards incompatible changes

## `v0.10.1` to `v0.10.2`

No backwards incompatible changes

## `v0.10.0.post2` to `v0.10.1`

This version fixes a bug on the build tools which will introduce a change on the expected output of the deployment builds. Before this bug fix the deployment tools did not index the agents on the manual builds, which lead to the behaviour where if you built the deployment using just one key or `--n` flag the agents were indexed from `0` instead. With this bug fix the deployment tools will use the `all_participants` list to index the agents before building the deployments.

## `v0.10.0.post1` to `v0.10.0.post2`

No backwards incompatible changes

## `v0.10.0` to `v0.10.0.post1`

No backwards incompatible changes

## `v0.9.1` to `v0.10.0`

Breaking changes

- The `AbciAppDB`'s `create()` is responsible for setting the cross-period keys for the new period and converting the 
  corresponding data to the correct format. The skills using the `create()` method now do not need to manually set the 
  data for the next period as this is handled automatically via the cross-period keys.
- The setup parameters should not be defined as lists anymore.
- `observation_interval` has been renamed to `reset_pause_duration`.
- The services which are currently using termination will need to set `use_termination: True` 
  in their configuration in order to continue using it. Otherwise, `use_termination: False` should be used.
- Before this update the `autonomy mint/service` command groups used to have key file as a required argument, 
  but it's been made optional since the usage of hardware wallet does not require a key file.
- Autonomy deploy build does not support the usage of `--force` flag to remove the existing build directories.
- The service components need to be updated. The service configurations needs to specify the new `deployment` parameter, 
  which is used in order to expose agent ports when using the deployment commands. It can be empty (`deployment: {}`) 
  if you do not intend to override the generated compose file for the deployments to expose agent ports.
- The agent configurations will need to be updated with regard to the following overrides:
  - In the ABCI skill override don't use `TENDERMINT_URL` and `TENDERMINT_COM_URL` for Tendermint parameters.
  - In the ABCI connection override don't use `ABCI_HOST` and `ABCI_PORT` for ABCI connection parameters.
  - Tendermint and ABCI connection parameters now use the same environment variables' pattern as all other 
    configurations.

## `v0.9.0` to `v0.9.1`

No backwards incompatible changes

## `v0.8.0` to `v0.9.0`

Breaking changes

- On the skill configuration
  - The `max_participants` parameter has been removed. If the `consensus` configuration is empty after removing `max_participants`, it should be removed as well.
  - The `consensus_threshold` should now be specified in the `setup` parameters. If `null`, the recommended setting, then it is calculated automatically from the participants provided.
- The synchronized database is now `serializable` and `hashable`. This means that the data inserted into the database are now enforced to be primitive or non-primitive built-in types only, except for `sets` and `frozensets` since an error is raised as they cannot be `serialized`/`hashed` and therefore cannot be inserted into the database. In essence, the data should be `json serializable`.
- The usage of local Tendermint Consensus Gadget is optional in the deployment setup, use `-ltm, --local-tm-setup` when building a deployment using `autonomy deploy build` command to include a Tendermint Consensus Gadget setup.
- The `cross_period_persisted_keys` and database conditions needs to be defined as sets as part of the `AbciApp` class, before this they were defined using a list
- On the round class implementation
  - `payload_attribute` attribute has been removed
  - Usage of payloads with multiple attributes has been simplified since the user can now specify a tuple of keys in order to store all the data of a payload to the database.
- Round `selection_key` is now a tuple for multiple-attribute payloads.

## `v0.7.0` to `v0.8.0`

- Support for `--rpc` and `--sca` flags has been deprecated on `autonomy deploy from-token` command. Refer to the CLI documentation to understand how to use custom `RPC`.
- The transaction payload classes needs to be defined using the data classes and needs to be immutable
- `Transaction` is a data class
- IPFS connection and protocol need to be added to your `aea-config.yaml`, if they utilize `valory/abstract_round_abci` skill.
- IPFS dialogues and handler need to be specified.
- `send_to_ipfs` and `get_from_ipfs` are now moved to `BaseBehaviour` and are generators.
- E2E tests now utilize a local deployment of the IPFS, as such you will need to import the `ipfs_daemon` and `ipfs_domain` fixtures from `aea_test_autonomy.fixture_helpers`.

## `v0.6.0` to `v0.7.0`

Breaking changes

- The new `AbstractRound` and `BaseBehaviour` meta classes enforce checks on the class attributes. For concrete classes inheriting from `AbstractRound` the developer must set `synchronized_data_class`, `allowed_tx_type` and `payload_attribute`. For concrete classes inheriting from `BaseBehaviour` the developer must set `matching_round`. These assumptions were present before but not enforced at the class definition level by the framework.
- The set of `all_participants` is now retrieved from the safe instance referenced by `safe_contract_address` and assumed to be present on the target chain.
- The usage of `safe_deployment_abci` has been deprecated and support for the package has been dropped. From now on, use the development tools for running a local development image with pre-configured safe to test your applications.

## `v0.5.0.post2` to `v0.6.0`

Breaking changes

- Optional: The developer can update to use the auto-generated behaviour and round ids. In this case, the `behaviour_id` and `round_id` need no longer be set on the class. When accessing the auto generated ids on the class use `auto_behaviour_id()` and `auto_round_id()` class methods. On the instance `behaviour_id` and `round_id` properties resolve the auto id class methods, so no change is required.
- Required: The pre- (`db_pre_conditions`) and post- (`db_post_conditions`) conditions on the synchronized data need to be defined for each initial and final state in an `AbciApp`. See `transaction_settlement_abci` for an example.


## `v0.5.0.post1` to `v0.5.0.post2`


No backwards incompatible changes


## `v0.5.0` to `v0.5.0.post1`


No backwards incompatible changes

## `v0.4.0` to `v0.5.0`


One backwards incompatible change
## Service component

- This release introduces a new format for defining multiple overrides for an agent on a service configuration. Please follow this [guide](./configure_service/service_configuration_file.md) to update your service configurations accordingly.

## `v0.3.5` to `v0.4.0`

Multiple backwards incompatible changes

### Autonomy CLI module

- `autonomy analyse abci` command group has been deprecated

- `autonomy analyse abci check-app-specs` and `autonomy analyse generate-app-specs` has been merged into `autonomy analyse fsm-specs`
  - The usage of `--infile` flag has been deprecated and replaced with the usage of the `--package` flag
  - Input format for `--app-class` has been changed from `packages.author.skills.skill_name.rounds.SomeAbciApp` to `SomeAbciApp`
  - Users will have to manually switch to the newer version, i.e., remove the path prefix in all their FSM specifications. For example an FSM specification with a `label: packages.author.skills.my_abci.rounds.MyAbciApp` now becomes `label: MyAbciApp`

- `autonomy analyse abci check-handlers` has been moved to `autonomy analyse handlers`
  - `--packages-dr` flag has been deprecated, use `--registry-path` at top level instead
  - Input format for common handlers and skip skills options has been updated
    - Old format - `--common abci,http,contract_api,ledger_api,signing --skip abstract_abci,counter,counter_client,hello_world_abci`
    - New format `-h abci -h http -h contract_api -h ledger_api -h signing -i abstract_abci -i counter -i counter_client -i hello_world_abci`

- `autonomy analyse abci docstrings` has been moved to `autonomy analyse docstrings`
  - `--check` flag has been deprecated and the command will perform the check by default
  - `--update` flag has been introduced to update the docstring if necessary

- `autonomy analyse abci logs` has been moved to `autonomy analyse logs`

### Autonomy test plugin

- `tag` property has been renamed to `image` on `aea_test_autonomy.docker.base.DockerImage` class

### Core packages

- `_HarHatHelperIntegration` has been renamed to `HardHatHelperIntegration` in `packages/valory/skills/abstract_round_abci/test_tools/integration.py`
- `ResetPauseABCIApp` has been renamed to `ResetPauseAbciApp` in `packages/valory/skills/reset_pause_abci/rounds.py`
- `ApiSpecs` now use `dataclasses` in order to encapsulate data, which means that `response_key`, and `response_type` can be accessed via the `response_info` instance attribute. Moreover, this attribute now includes the new `response_index` and `error_key`, `error_index`, `error_type`, `error_data`. The `retries_info` instance attribute gives access to the `retries_attempted` and `retries` which are now public and also includes the new `backoff_factor`.

### Test tools

- The `packages.valory.skills.abstract_round_abci.test_tools.apis` module which contained the `DummyMessage` has been removed. `MagicMock` can be used instead. For example, `DummyMessage(my_test_body)` can be converted to `MagicMock(body=my_test_body)`.

## `v0.3.4` to `v0.3.5`

No backwards incompatible changes

### Upgrade guide

This release introduces a new format for `packages.json` file, the older version is still supported but will be deprecated on `v1.0.0` so make sure to update your projects to use the new format.

## `v0.3.3` to `v0.3.4`

No backwards incompatible changes

## `v0.3.2` to `v0.3.3`

No backwards incompatible changes

## `v0.3.1` to `v0.3.2`

No backwards incompatible changes

## `v0.3.0` to `v0.3.1`

No backwards incompatible changes

## `v0.2.2` to `v0.3.0`

No backwards incompatible changes except:

- Deprecated the usage of `hashes.csv` and replaces it with `packages.json`, which is maintained by `autonomy packages lock`
- `--check` flag is deprecated from `autonomy hash all`, from now package consistencies can be verified by `autonomy packages lock --check`
- Various test fixtures have moved and been renamed.

## `v0.2.1.post1` to `v0.2.2`

No backwards incompatible changes except:

All imports from `autonomy.test_tools.*` are now found at `aea_test_autonomy.*`, after installing `open-aea-test-autonomy`.

## `v0.2.1` to `v0.2.1.post1`

No backwards incompatible changes

## `v0.2.0` to `v0.2.1`

- `build-images` command has been renamed to `build-image`
- Build support for dependency has been removed from the `build-image` command
- `autonomy deploy build deployment` has been renamed to `autonomy deploy build`

Refer to quick start docs for more information on the updated deployment flow.

## `v0.1.6` to `v0.2.0`

Multiple backwards incompatible changes:

- The service config no longer accepts the `network` key on the first YAML page. The network can now be defined via the package overrides.
- Dependency specifications are now checked against imports for all packages, this means initially packages might need modifying to reference/unreference missing/irrelevant dependencies.
- The global configuration file for the `aea`/`autonomy` CLI has a breaking change. Please remove `~/.aea/cli_config.yaml` and rerun `autonomy init --remote`.

## `v0.1.5` to `v0.1.6`

No backwards incompatible changes

## `v0.1.4` to `v0.1.5`

No backwards incompatible changes

## `v0.1.3` to `v0.1.4`

This release changes the build process for docker images and service deployments. Refer to documentation for more information.

## `v0.1.2` to `v0.1.3`

This release introduces the usage of CID v1 hashes.

## `v0.1.1` to `v0.1.2`

No backwards incompatible changes

## `v0.1.0` to `v0.1.1`

No backwards incompatible changes

## `v0.1.0rc1/2` to `v0.1.0`
