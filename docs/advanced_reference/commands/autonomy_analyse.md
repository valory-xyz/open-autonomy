
## Analyse

```
Usage: autonomy analyse [OPTIONS] COMMAND [ARGS]...

  Analyse an agent service.

Options:
  --help  Show this message and exit.

Commands:
  benchmarks  Benchmark aggregator.
  docstrings  Analyse ABCI docstring definitions.
  fsm-specs   Generate ABCI app specs.
  handlers    Check handler definitions.
  logs        Parse logs of an agent service.
```

**Check ABCI app docstrings**

```
Usage: autonomy analyse docstrings [OPTIONS]

  Analyse ABCI docstring definitions.

Options:
  --update  Update docstrings if required.
  --help    Show this message and exit.
```

To analyse docstrings run the command in the directory containing the `packages/` folder

```
$ autonomy analyse docstrings
```

To update the docstrings, run the command with `--update` flag

```
$ autonomy analyse docstrings --update
```

**Analyse FSM specifications**

```
Usage: autonomy analyse fsm-specs [OPTIONS]

  Generate ABCI app specs.

Options:
  --package PATH
  --app-class TEXT
  --update          Update FSM definition if check fails.
  --mermaid         Mermaid file.
  --yaml            Yaml file.
  --json            Json file.
  --help            Show this message and exit.
```

Analyse specification for one skill package using

```
$ autonomy analyse fsm-specs --package PATH_TO_SKILL_PACKAGE
```

To create or update an FSM specification from existing abci app definition run

```
$ autonomy analyse fsm-specs --update --package PATH_TO_SKILL_PACKAGE --app-class NAME_OF_THE_ABCI_CLASS
```

To analyse all available FSM specifications in a local repository, navigate to directory containing `packages/` folder and run

```
$ autonomy analyse fsm-specs
```

**Analyse handler definitions**

```
Usage: autonomy analyse handlers [OPTIONS]

  Check handler definitions.

Options:
  -h, --common-handlers TEXT  Specify which handlers to check. Eg. -h
                              handler_a -h handler_b -h handler_c
  -i, --ignore TEXT           Specify which skills to skip. Eg. -i skill_0 -i
                              skill_1 -i skill_2
  --help                      Show this message and exit.
```

To analyse handlers in a local repository, navigate to directory containing `packages/` folder and run

```
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
$ cd abci_build/
$ docker-compose up
```

You can use this tool to aggregate this data.

```
autonomy analyse benchmarks abci_build/persistent_data/benchmarks
```

By default tool will generate output for all periods but you can specify which period to generate output for, same goes for block types as well.
