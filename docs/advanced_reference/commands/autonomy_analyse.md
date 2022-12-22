Tools for anaysing and verifying agent services.

This command group consists of a number of functionalities to analyse and verify agent services, including {{fsm_app}} skill consistency checks. See the appropriate subcommands for more information.



## `autonomy analyse docstrings `

Analyse {{fsm_app}} skill docstring definitions.

This command verifies that the [`AbciApp` class](../../key_concepts/abci_app_class.md) docstring is follows a standard format.

??? example

    The docstring corresponding to the [Hello World agent service](../../demos/hello_world_demo.md) is


    ```python
    """HelloWorldAbciApp

    Initial round: RegistrationRound

    Initial states: {RegistrationRound}

    Transition states:
        0. RegistrationRound
            - done: 1.
        1. CollectRandomnessRound
            - done: 2.
            - no majority: 1.
            - round timeout: 1.
        2. SelectKeeperRound
            - done: 3.
            - no majority: 0.
            - round timeout: 0.
        3. PrintMessageRound
            - done: 4.
            - round timeout: 0.
        4. ResetAndPauseRound
            - done: 1.
            - no majority: 0.
            - reset timeout: 0.

    Final states: {}

    Timeouts:
        round timeout: 30.0
        reset timeout: 30.0
    """
    ```

### Usage
```bash
autonomy analyse docstrings [OPTIONS]
```

### Options
`--update`
:   Update docstrings if required.

`--help`
:   Show the help message and exit.

### Examples
To analyse all the {{fsm_app}} skill docstrings within the local registry, run the following command in the directory containing the registry:

```bash
autonomy analyse docstrings
```


To update/fix the {{fsm_app}} skill docstrings, run the following command:
```bash
autonomy analyse docstrings --update
```

## `autonomy analyse fsm-specs`

Verify the {{fsm_app}} against its specification or generate the {{fsm_app}} specification file.

### Usage

```bash
Usage: autonomy analyse fsm-specs [OPTIONS]
```

### Options

```
--package PATH
```
:   Path to the package containing the {{fsm_app}} skill.

```
--app-class ABCI_APP_CLASS
```
:   Name of the `AbciApp` class of the {{fsm_app}}.

```
--update
```
:    Update/create the {{fsm_app}} definition file if check fails.

```
--yaml
```
:    YAML file (default).

```
--json
```
:    JSON file.

```
--mermaid
```
:    Mermaid file.

```
--help
```
:    Show the help message and exit.


### Examples
Analyse the {{fsm_app}} specification for the `hello_world_abci`:
```bash
autonomy analyse fsm-specs --package ./packages/valory/skills/hello_world_abci
```

Update/create the {{fsm_app}} specification for the `hello_world_abci` in YAML format:
```bash
autonomy analyse fsm-specs --package ./packages/valory/skills/hello_world_abci --app-class HelloWorldAbciApp --update
```

Export the {{fsm_app}} specification for the `hello_world_abci` in Mermaid format:
```bash
autonomy analyse fsm-specs --package ./packages/valory/skills/hello_world_abci --app-class HelloWorldAbciApp --update --mermaid
```

Analyse all the {{fsm_app}} specifications in a local registry. This command must be executed
in a directory containing the local registry:
```bash
autonomy analyse fsm-specs
```

## autonomy analyse handlers

Verify handler definitions.

### Usage
``` bash
autonomy analyse handlers [OPTIONS]
```

### Options
`-h, --common-handlers HANDLER_NAME`
:   Specify which handlers to check. E.g., `-h handler_a` `-h handler_b` `-h handler_c`.

`-i, --ignore SKILL_NAME`
:   Specify which skills to skip. E.g., `-i skill_0`, `-i skill_1`, `-i skill_2`.

`--help`
:   Show the help message and exit.


### Examples

Analyse handlers in a local registry, navigate to the directory containing the local registry and execute

```bash
$ autonomy analyse handlers -h COMMON_HANDLER_DEFINITION_TO_CHECK -i SKILL_TO_IGNORE
```

**Parse logs from a deployment**

```
Usage: autonomy analyse logs [OPTIONS] FILE
  Parse logs.
Options:
  --help  Show this message and exit.
```

### benchmarks

```
Usage: autonomy analyse benchmarks [OPTIONS] PATH
  Benchmark Aggregator.
Options:
  -b, --block-type [local|consensus|total|all]
  -d, --period INTEGER
  -o, --output FILE
  --help                          Show this message and exit.
```

Aggregating results from deployments.

To use this tool you'll need benchmark data generated from agent runtime. To generate benchmark data run

```
$ autonomy deploy build PATH_RO_KEYS --dev
```

By default this will create a 4 agent runtime where you can wait until all 4 agents are at the end of the first period (you can wait for more periods if you want) and then you can stop the runtime. The data will be stored in `abci_build/persistent_data/benchmarks` folder.

Run deployment using

```
cd abci_build/
docker-compose up
```

You can use this tool to aggregate this data.

```
autonomy analyse benchmarks abci_build/persistent_data/benchmarks
```

By default tool will generate output for all periods but you can specify which period to generate output for, same goes for block types as well.




```
Commands:
  benchmarks  Benchmark aggregator.
  docstrings  Analyse ABCI docstring definitions.
  fsm-specs   Generate ABCI app specs.
  handlers    Check handler definitions.
  logs        Parse logs of an agent service.
```
