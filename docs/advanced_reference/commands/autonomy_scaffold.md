## Scaffold

The scaffold tool lets users generate boilerplate code that acts as a template to speed-up the development of packages.


```
Usage: autonomy scaffold [OPTIONS] COMMAND [ARGS]...

  Scaffold a package for the agent.

Options:
  -tlr, --to-local-registry  Scaffold skill inside a local registry.
  --with-symlinks            Add symlinks from vendor to non-vendor and
                             packages to vendor folders.
  --help                     Show this message and exit.

Commands:
  connection              Add a connection scaffolding to the configuration file and agent.
  contract                Add a connection scaffolding to the configuration file and agent.
  decision-maker-handler  Add a decision maker scaffolding to the configuration file and agent.
  error-handler           Add an error scaffolding to the configuration file and agent.
  fsm                     Add an ABCI skill scaffolding from an FSM specification.
  protocol                Add a protocol scaffolding to the configuration file and agent.
  skill                   Add a skill scaffolding to the configuration file and agent.

```

#### Example


```
autonomy scaffold connection my_connection
```
