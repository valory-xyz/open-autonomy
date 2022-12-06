<a id="autonomy.cli.develop"></a>

# autonomy.cli.develop

Develop CLI module.

<a id="autonomy.cli.develop.develop_group"></a>

#### develop`_`group

```python
@click.group(name="develop")
def develop_group() -> None
```

Develop an agent service.

<a id="autonomy.cli.develop.run_service_locally"></a>

#### run`_`service`_`locally

```python
@develop_group.command(name="service-registry-network")
@click.argument(
    "image",
    type=str,
    required=False,
    default=DEFAULT_SERVICE_REGISTRY_CONTRACTS_IMAGE,
)
def run_service_locally(image: str) -> None
```

Run the service registry contracts on a local network.

<a id="autonomy.cli.develop.publish_component_on_chain"></a>

#### publish`_`component`_`on`_`chain

```python
@develop_group.group("publish")
def publish_component_on_chain() -> None
```

Publish component on-chain.

<a id="autonomy.cli.develop.protocol"></a>

#### protocol

```python
@publish_component_on_chain.command()
@package_path_decorator
@key_path_decorator
@password_decorator
@dependencies_decorator
def protocol(package_path: Path, keys: Path, password: Optional[str], dependencies: Tuple[str]) -> None
```

Publish a protocol component.

