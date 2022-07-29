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
    help="Provide a local alias for the agent.",
    default=True,
    flag_value=AGENT,
)
@click.option(
    "--service",
    "package_type",
    help="Provide a local alias for the agent.",
    flag_value=SERVICE,
)
@click.argument("public-id", type=PublicIdParameter(), required=True)
@click.pass_context
def fetch(click_context: click.Context, public_id: PublicId, alias: str, package_type: str, registry: str) -> None
```

Fetch an agent from the registry.

<a id="autonomy.cli.fetch.fetch_service"></a>

#### fetch`_`service

```python
def fetch_service(ctx: Context, public_id: PublicId) -> Path
```

Fetch service.

<a id="autonomy.cli.fetch.fetch_service_ipfs"></a>

#### fetch`_`service`_`ipfs

```python
def fetch_service_ipfs(public_id: PublicId) -> Path
```

Fetch service from IPFS node.

<a id="autonomy.cli.fetch.fetch_service_local"></a>

#### fetch`_`service`_`local

```python
def fetch_service_local(ctx: Context, public_id: PublicId) -> Path
```

Fetch service from local directory.

