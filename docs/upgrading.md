This page provides some tips on how to upgrade agent services between different versions of the {{open_autonomy}} framework. For full release notes check the <a href="https://github.com/valory-xyz/open-autonomy/tags" target="_blank">Open-Autonomy repo</a>.

Below we describe the additional manual steps required to upgrade between different versions:


# Open Autonomy

## `v0.5.0` to `v0.5.0.post1`


No backwards incompatible changes

## `v0.4.0` to `v0.5.0`


One backwards incompatible change
## Service component

- This release introduces a new format for defining multiple overrides for an agent on a service configuration. Please follow this [guide](https://github.com/valory-xyz/open-autonomy/blob/main/docs/guides/service_configuration_file.md) to update your service configurations accordingly. 

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
