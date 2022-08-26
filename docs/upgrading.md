This page provides some tips on how to upgrade agent services between different versions of the {{open_autonomy}} framework. For full release notes check the <a href="https://github.com/valory-xyz/open-autonomy/tags" target="_blank">Open-Autonomy repo</a>.

Below we describe the additional manual steps required to upgrade between different versions:


# Open Autonomy

## `v0.2.0` to `v0.2.1`

- `build-images` command has been renamed to `build-image` 
- Build support for dependency has been removed from the `build-image` command

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
