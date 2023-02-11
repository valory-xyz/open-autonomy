<a id="autonomy.cli.publish"></a>

# autonomy.cli.publish

Implementation of the 'autonomy publish' subcommand.

<a id="autonomy.cli.publish.publish"></a>

#### publish

```python
@click.command(name="publish")
@registry_flag()
@click.option("--push-missing",
              is_flag=True,
              help="Push missing components on the registry.")
@click.pass_context
def publish(click_context: click.Context, registry: str,
            push_missing: bool) -> None
```

Publish the agent or service on the registry.

