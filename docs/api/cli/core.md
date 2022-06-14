<a id="autonomy.cli.core"></a>

# autonomy.cli.core

Core for cli.

<a id="autonomy.cli.core.autonomy_cli"></a>

#### autonomy`_`cli

```python
@click.group(name="autonomy")  # type: ignore
@click.pass_context
def autonomy_cli(click_context: click.Context) -> None
```

Command-line tool for managing agent services of the Open Autonomy framework.

