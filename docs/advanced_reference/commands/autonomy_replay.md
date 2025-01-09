Tools for replay agent execution.

This command group consists of a number of functionalities for re-running agents using data dumps from previous runs.
This command allows you to replay the behavior of a single agent from a previous deployment, which is useful for debugging or analyzing the agent's responses to specific scenarios.
See the appropriate subcommands for more information. Note that **replay functionalities only work for deployments which were ran in dev mode.**

### Usage
```bash
autonomy replay agent [OPTIONS] AGENT
```

### Options
`--build PATH`
:   Path to the build folder.

`--registry PATH`
:   Path to the local registry folder.

`--help`
:   Show the help message and exit.

## `autonomy replay tendermint`

### Usage
```bash
autonomy replay tendermint [OPTIONS]
```

### Description
Tendermint runner.

### Options
`--build PATH`
:   Path to the build folder.

`--help`
:   Show the help message and exit.


## Examples

### Replaying a Single Agent

To replay the execution of agent 0 from a specific build:

```bash
# Navigate to your service directory
cd your_service_directory

# Replay agent 0's execution using the default build directory
autonomy replay agent 0

# Or specify a custom build directory
autonomy replay agent 0 --build ./abci_build_hAsH
```

### Replaying the Tendermint Node

To replay the Tendermint node with saved state:

```bash
# Start the Tendermint node using the default build directory
autonomy replay tendermint

# Or specify a custom build directory
autonomy replay tendermint --build ./abci_build_hAsH
```

### Complete Replay Workflow

For a complete replay of a previous execution:

1. Start the CometBFT node replay in one terminal:
   ```bash
   autonomy replay tendermint --build ./your_build_directory
   ```

2. In another terminal, start the agent replay:
   ```bash
   autonomy replay agent 0 --build ./your_build_directory
   ```

Find a complete example on how the [execution replay section](../developer_tooling/execution_replay.md).
