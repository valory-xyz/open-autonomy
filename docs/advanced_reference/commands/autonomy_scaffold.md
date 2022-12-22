Tools for scaffolding agent components.

This command group consists of a number of functionalities that generate boilerplate code that acts as a template to speed up the development of agent components. See the appropriate subcommands for more information.


!!! warning "Important"

    This command group extends the {{open_aea}} command `scaffold` with the subcommand `fsm` to generate boilerplate code for {{fsm_app}} skills. We refer to the {{open_aea_doc}} for more information related the subcommands `connection`, `contract`, `decision-maker-handler`, `error-handler`, `protocol` and `skill`.

## Usage
```bash
autonomy scaffold [OPTIONS] COMMAND [ARGS]
```

## Options
`-tlr, --to-local-registry`
:   Scaffold skill inside a local registry.

`--with-symlinks`
:   Add symlinks from vendor to non-vendor and packages to vendor folders.

`--help`
:   Show the help message and exit.


## `autonomy scaffold fsm`

Scaffold {{fsm_app}} skills based on an {{fsm_app}} specification file (YAML).

This command produces the necessary boilerplate code to create an empty, but functional, {{fsm_app}} skill. The command needs an initialized local registry to work, and it must be called in the folder containing the registry, or one of its direct subfolders.

The command will produce the following files under `<local_repository>/<vendor>/skills/<fsm_app_skill_name>`:

- `__init__.py`: Python package definition file.
- `behaviours.py`: Boilerplate for behaviours and the [`RoundBehaviour` class](../../key_concepts/abci_app_abstract_round_behaviour.md).
- `dialogues.py`: Boilerplate for dialogues.
- `fsm_specification.yaml`: {{fsm_app}} specification file.
- `handlers.py`: Boilerplate for handlers.
- `models.py`: Boilerplate for models.
- `payloads.py`: Boilerplate for payloads.
- `rounds.py`: Boilerplate for rounds and the [`AbciApp` class](../../key_concepts/abci_app_class.md).
- `skill.yaml`: Skill configuration file.
- `tests/`: Directory containing boilerplate for tests.

### Usage
```bash
autonomy scaffold fsm [OPTIONS] SKILL_NAME
```

### Options
`--remote`
:   To use a remote registry.

`--local`
:   To use a local registry.

`--spec FILE`
:   {{fsm_app}} specification file (YAML).

`--help`
:   Show the help message and exit.

### Example
```bash
scaffold -tlr fsm --spec fsm_specification.yaml my_fsm_app_skill
```

Generates an {{fsm_app}} skill named "my_fsm_app_skill" according to the specification described in the file `fsm_specification.yaml`, and stores it to the local registry.
