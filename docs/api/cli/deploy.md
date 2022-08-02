<a id="autonomy.cli.deploy"></a>

# autonomy.cli.deploy

Deploy CLI module.

<a id="autonomy.cli.deploy.deploy_group"></a>

#### deploy`_`group

```python
@click.group(name="deploy")
@click.pass_context
def deploy_group(click_context: click.Context) -> None
```

Deploy an agent service.

<a id="autonomy.cli.deploy.build_deployment_command"></a>

#### build`_`deployment`_`command

```python
@deploy_group.command(name="build")
@click.argument("keys_file", type=str, required=False)
@click.option(
    "--o",
    "output_dir",
    type=click.Path(exists=False, dir_okay=True),
    help="Path to output dir.",
)
@click.option(
    "--n",
    "number_of_agents",
    type=int,
    default=None,
    help="Number of agents.",
)
@click.option(
    "--docker",
    "deployment_type",
    flag_value=DockerComposeGenerator.deployment_type,
    default=True,
    help="Use docker as a backend.",
)
@click.option(
    "--kubernetes",
    "deployment_type",
    flag_value=KubernetesGenerator.deployment_type,
    help="Use kubernetes as a backend.",
)
@click.option(
    "--dev",
    "dev_mode",
    is_flag=True,
    default=False,
    help="Create development environment.",
)
@click.option(
    "--version",
    "version",
    help="Specify deployment version.",
)
@click.option(
    "--force",
    "force_overwrite",
    is_flag=True,
    default=False,
    help="Remove existing build and overwrite with new one.",
)
@registry_flag()
@password_option(confirmation_prompt=True)
@click.pass_context
def build_deployment_command(click_context: click.Context, keys_file: Optional[Path], deployment_type: str, output_dir: Optional[Path], dev_mode: bool, force_overwrite: bool, registry: str, number_of_agents: Optional[int] = None, password: Optional[str] = None, version: Optional[str] = None) -> None
```

Build deployment setup for n agents.

<a id="autonomy.cli.deploy.run_deployment"></a>

#### run`_`deployment

```python
@deploy_group.command(name="run")
@click.argument("token_id", type=int, required=False)
@click.argument("keys_file", type=click.Path(), required=False)
@registry_flag()
@click.pass_context
def run_deployment(click_context: click.Context, token_id: Optional[int], keys_file: Optional[Path], registry: str) -> None
```

Run service deployment.

<a id="autonomy.cli.deploy.run_existing_deployment"></a>

#### run`_`existing`_`deployment

```python
def run_existing_deployment() -> None
```

Run deployment using docker-compose.

<a id="autonomy.cli.deploy.get_abi"></a>

#### get`_`abi

```python
def get_abi(url: str) -> Dict
```

Get ABI from provided URL

<a id="autonomy.cli.deploy.resolve_token_id"></a>

#### resolve`_`token`_`id

```python
def resolve_token_id(token_id: int) -> Dict
```

Resolve token id using on-chain contracts.

<a id="autonomy.cli.deploy.run_deployment_from_token_id"></a>

#### run`_`deployment`_`from`_`token`_`id

```python
def run_deployment_from_token_id(ctx: Context, token_id: int, keys_file: Path) -> None
```

Run a deployment from on-chain token id.

<a id="autonomy.cli.deploy.build_deployment"></a>

#### build`_`deployment

```python
def build_deployment(keys_file: Path, build_dir: Path, deployment_type: str, dev_mode: bool, force_overwrite: bool, number_of_agents: Optional[int] = None, password: Optional[str] = None, version: Optional[str] = None) -> None
```

Build deployment.

