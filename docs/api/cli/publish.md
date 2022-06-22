<a id="autonomy.cli.publish"></a>

# autonomy.cli.publish

Implementation of the 'autonomy publish' subcommand.

<a id="autonomy.cli.publish.publish"></a>

#### publish

```python
@click.command(name="publish")
@registry_flag()
@click.option(
    "--push-missing", is_flag=True, help="Push missing components to registry."
)
@click.pass_context
def publish(click_context: click.Context, registry: str, push_missing: bool) -> None
```

Publish the agent to the registry.

<a id="autonomy.cli.publish.publish_service_package"></a>

#### publish`_`service`_`package

```python
def publish_service_package(click_context: click.Context, registry: str) -> None
```

Publish an agent package.

<a id="autonomy.cli.publish.publish_service_ipfs"></a>

#### publish`_`service`_`ipfs

```python
def publish_service_ipfs(public_id: PublicId, package_path: Path) -> None
```

Publish a service package to the IPFS registry.

<a id="autonomy.cli.publish.publish_service_local"></a>

#### publish`_`service`_`local

```python
def publish_service_local(ctx: Context, public_id: PublicId) -> None
```

Publish a service package to the local packages directory.

