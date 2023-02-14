<a id="autonomy.cli.service"></a>

# autonomy.cli.service

Implementation of the `autonomy service` command

<a id="autonomy.cli.service.service"></a>

#### service

```python
@click.group("service")
@pass_ctx
@chain_selection_flag()
@timeout_flag
def service(ctx: Context, chain_type: str, timeout: float) -> None
```

Manage on-chain services.

<a id="autonomy.cli.service.activate"></a>

#### activate

```python
@service.command()
@pass_ctx
@click.argument("service_id", type=int)
@key_path_decorator
@password_decorator
def activate(ctx: Context, service_id: int, keys: Path,
             password: Optional[str]) -> None
```

Activate service.

<a id="autonomy.cli.service.register"></a>

#### register

```python
@service.command()
@pass_ctx
@click.argument("service_id", type=int)
@click.option(
    "-i",
    "--instance",
    "instances",
    type=str,
    required=True,
    multiple=True,
    help="Agent instance address",
)
@click.option(
    "-a",
    "--agent-id",
    "agent_ids",
    type=int,
    required=True,
    multiple=True,
    help="Agent ID",
)
@key_path_decorator
@password_decorator
def register(ctx: Context, service_id: int, instances: List[str],
             agent_ids: List[int], keys: Path,
             password: Optional[str]) -> None
```

Register instances.

<a id="autonomy.cli.service.deploy"></a>

#### deploy

```python
@service.command()
@pass_ctx
@click.argument("service_id", type=int)
@click.option(
    "-d",
    "--deployment-payload",
    type=int,
    help="Deployment payload value",
)
@key_path_decorator
@password_decorator
def deploy(ctx: Context, service_id: int, keys: Path, password: Optional[str],
           deployment_payload: Optional[str]) -> None
```

Activate service.

