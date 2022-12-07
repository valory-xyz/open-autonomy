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

