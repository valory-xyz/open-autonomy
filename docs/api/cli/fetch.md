<a id="autonomy.cli.fetch"></a>

# autonomy.cli.fetch

Implementation of the 'autonomy fetch' subcommand.

<a id="autonomy.cli.fetch.fetch"></a>

#### fetch

```python
@click.command(name="fetch")
@registry_flag()
@click.option(
    "--alias",
    type=str,
    required=False,
    help="Provide a local alias for the agent.",
)
@click.option(
    "--agent",
    "package_type",
    help="Specify the package type as agent (default).",
    default=True,
    flag_value=AGENT,
)
@click.option(
    "--service",
    "package_type",
    help="Specify the package type as service.",
    flag_value=SERVICE,
)
@click.argument("public-id", type=PublicIdParameter(), required=True)
@click.pass_context
def fetch(click_context: click.Context, public_id: PublicId, alias: str,
          package_type: str, registry: str) -> None
```

Fetch an agent from the registry.

