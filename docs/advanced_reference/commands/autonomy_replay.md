[← Back to CLI Reference](../../cli_overview.md)

Tools for replaying agent execution from previous runs.

This command group provides functionality to re-run agents and their associated CometBFT nodes using data dumps from previous executions. This is particularly useful for:

* Debugging agent behavior by replaying specific scenarios
* Testing modifications to agent code against real transaction data
* Analyzing agent responses to specific blockchain states

**Important**: Replay functionalities only work for deployments that were run in development mode. Development mode saves the necessary state and transaction data required for replay.


## `autonomy replay agent`

### Usage
```bash
autonomy replay agent [OPTIONS] AGENT
```

### Description

Re-run a specific agent's execution using saved state data. This command allows you to replay the behavior of a single agent from a previous deployment, which is useful for debugging or analyzing the agent's responses to specific scenarios.

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
Run a CometBFT node using saved state data. This command starts a local CometBFT node that replays the blockchain state from a previous deployment, which is necessary when replaying agent execution to ensure the correct blockchain state is available.

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
autonomy replay agent 0 --build ./abci_build_123456
```

### Replaying the CometBFT Node

To replay the CometBFT node with saved state:

```bash
# Start the CometBFT node using the default build directory
autonomy replay tendermint

# Or specify a custom build directory
autonomy replay tendermint --build ./abci_build_123456
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

For more detailed information about execution replay and debugging techniques, see the [Execution Replay Guide](../developer_tooling/execution_replay.md).
