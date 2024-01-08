<a id="autonomy.cli.scaffold_fsm"></a>

# autonomy.cli.scaffold`_`fsm

Implement a scaffold sub-command to scaffold ABCI skills.

This module patches the 'aea scaffold' command so to add a new subcommand for scaffolding a skill
 starting from FSM specification.

<a id="autonomy.cli.scaffold_fsm.fsm"></a>

#### fsm

```python
@scaffold.command()
@registry_flag()
@click.argument("skill_name", type=str, required=True)
@click.option("--spec",
              type=click.Path(exists=True, dir_okay=False),
              required=True)
@pass_ctx
def fsm(ctx: Context, registry: str, skill_name: str, spec: str) -> None
```

Add an ABCI skill scaffolding from an FSM specification.

