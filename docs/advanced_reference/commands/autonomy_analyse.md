Tools for analysing and verifying agent services.

This command group consists of a number of functionalities to analyse and verify agent services, including {{fsm_app}} skill consistency checks. See the appropriate subcommands for more information.



## `autonomy analyse docstrings `

Analyse {{fsm_app}} skill docstring definitions.

This command verifies that the [`AbciApp` class](../../key_concepts/abci_app_class.md) docstring is follows a standard format.

??? example

    The docstring corresponding to the [Hello World agent service](https://docs.autonolas.network/demos/hello-world/) is


    ```python
    """HelloWorldAbciApp

    Initial round: RegistrationRound

    Initial states: {RegistrationRound}

    Transition states:
        1. RegistrationRound
            - done: 1.
        2. CollectRandomnessRound
            - done: 2.
            - no majority: 1.
            - round timeout: 1.
        3. SelectKeeperRound
            - done: 3.
            - no majority: 0.
            - round timeout: 0.
        4. PrintMessageRound
            - done: 4.
            - round timeout: 0.
        5. ResetAndPauseRound
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

## `autonomy analyse handlers`

Verify existence of handler definitions.

This command verifies that all the {{fsm_app}} skills in a local registry (except the explicitly excluded ones) have defined the specified handlers.

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

Ensure that handlers `http` and `signing` are defined in all the {{fsm_app}} skills in a local registry, except the skills `excluded_skill_1` and `excluded_skill_2`:

```bash
autonomy analyse handlers -h http -h signing -i excluded_skill_1 -i excluded_skill_2
```

## `autonomy analyse dialogues`

Check dialogues definitions in a skill package.

This command verifies that all the {{fsm_app}} skills in a local registry (except the explicitly excluded ones) have defined the specified dialogues.

### Usage
``` bash
autonomy analyse dialogues [OPTIONS]
```

### Options
`-d, --dialogue TEXT`
:   Specify which dialogues to check. Eg. `-d dialogue_a`, `-d dialogue_b`, `-d dialogue_c`.

`-i, --ignore SKILL_NAME`
:   Specify which skills to skip. E.g., `-i skill_0`, `-i skill_1`, `-i skill_2`.

`--help`
:   Show the help message and exit.

### Examples

Ensure that dialogues `abci_dialogues` and `http_dialogues` are defined in all the {{fsm_app}} skills in a local registry, except the skills `excluded_skill_1` and `excluded_skill_2`:

```bash
autonomy analyse dialogues -d abci_dialogues -d http_dialogues -i excluded_skill_1 -i excluded_skill_2
```

Or

```bash
autonomy analyse dialogues -d abci -d http -i excluded_skill_1 -i excluded_skill_2
```

Since the command will automatically append the `_dialogues` postfix if not provided by the user.

## `autonomy analyse logs`
Parse logs of an agent service.

### Usage
```bash
autonomy analyse logs [OPTIONS]
```
### Options

`--from-dir PATH`
:   Path to logs directory  [required]

`--reset-db`
:   Use this flag to reset the log database.

`-a, --agent TEXT`
:   Agent IDs to include in analysis

`--start-time TEXT`
:   Start time in `YYYY-MM-DD H:M:S,MS` format

`--end-time TEXT`
:   End time in `YYYY-MM-DD H:M:S,MS` format

`--log-level [INFO|DEBUG|WARNING|ERROR|CRITICAL]`
:   Logging level.

`--period INTEGER`
:   Period ID

`--round TEXT`
:   Round name

`--behaviour TEXT`
:   Behaviour name filter

`--fsm`
:   Print only the FSM execution path

`-ir, --include-regex TEXT`
:   Regex pattern to include in the result.

`-er, --exclude-regex TEXT`
:   Regex pattern to exclude from the result.

`--help`
:   Show the help message and exit.

### Examples
!!! info
    This section will be added soon.


## `autonomy analyse benchmarks`

Aggregate benchmark results from agent service deployments.

This tool requires the benchmark data generated from service agent's runtime.
By default the tool will aggregate the output for all the periods and code block types but you can restrict the aggregation to a specific period and/or a specific block type.

Read the [guide on how to use the benchmarking tool](../developer_tooling/benchmarking.md) for more information.

### Usage
```bash
autonomy analyse benchmarks [OPTIONS] PATH
```

### Options
`-b, --block-type [local|consensus|total|all]`
:   Block type:

    * `local`: only consider `local` code blocks,
    * `consensus`: only consider `consensus` code blocks,
    * `total`: consider `local` + `consensus` code blocks together.
    * `all`: consider `local` and `consensus` code blocks.

`-d, --period PERIOD_NUM`
:   Period.

`-o, --output FILE`
:   Output file name.

`--help`
:  Show the help message and exit.

### Examples

The benchmark data will be stored in the folder `<service_folder>/abci_build/persistent_data/benchmarks`.

To aggregate stats for all periods, execute:

```bash
autonomy analyse benchmarks abci_build/persistent_data/benchmarks
```

To aggregate stats for `consensus` block type in the second period, execute:

```bash
    autonomy analyse benchmarks abci_build/persistent_data/benchmarks --period 2 --block-type consensus
```

## `autonomy analyse service`

Analyse if the service is ready to be deployed or not.

This tool can be used to analyse a service definition and see if there are any potential issues with configuration which can cause issues when running the deployment.

Read the [guide on deployment readiness](../../configure_service/on-chain_deployment_checklist.md) for more information.

### Usage
```bash
autonomy analyse service [OPTIONS]
```

### Options

`--token-id INTEGER`
:  Token ID of the service

`--public-id PUBLIC_ID_OR_HASH`
:   Public ID of the service

`--use-celo-alfajores`            
:   To use `celo-alfajores` chain profile to interact with the contracts

`--use-celo`                      
:   To use `celo` chain profile to interact with the contracts

`--use-base-sepolia`              
:   To use `base-sepolia` chain profile to interact with the contracts

`--use-base`                      
:   To use `base` chain profile to interact with the contracts

`--use-optimistic-sepolia`        
:   To use `optimistic-sepolia` chain profile to interact with the contracts

`--use-optimistic`                
:   To use `optimistic` chain profile to interact with the contracts

`--use-arbitrum-sepolia`          
:   To use `arbitrum-sepolia` chain profile to interact with the contracts

`--use-arbitrum-one`              
:   To use `arbitrum-one` chain profile to interact with the contracts

`--use-chiado`                    
:   To use `chiado` chain profile to interact with the contracts

`--use-gnosis`                    
:   To use `gnosis` chain profile to interact with the contracts

`--use-polygon-mumbai`            
:   To use `polygon-mumbai` chain profile to interact with the contracts

`--use-polygon`                   
:   To use `polygon` chain profile to interact with the contracts

`--use-ethereum`                  
:   To use `ethereum` chain profile to interact with the contracts

`--use-goerli`                    
:   To use `goerli` chain profile to interact with the contracts

`--use-custom-chain`              
:   To use `custom-chain` chain profile to interact with the contracts

`--use-local`                     
:   To use `local` chain profile to interact with the contracts


`--help`
:  Show the help message and exit.

### Examples

Analyse the service `valory/hello_world` using

```bash
autonomy analyse service --public-id valory/hello_world
```

Analyse an on-chain service with token ID `1` using

```bash
autonomy analyse service --token-id 1
```
