Tools for replay agent execution.

This command group consists of a number of functionalities for re-running agents using data dumps from previous runs. See the appropriate subcommands for more information. Note that **replay functionalities only work for deployments which were ran in dev mode.**


## `autonomy replay agent`

### Usage
```bash
autonomy replay agent [OPTIONS] AGENT
```

### Description

Re-run agent execution.

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

Find a complete example on how the [execution replay section](../developer_tooling/execution_replay.md).
