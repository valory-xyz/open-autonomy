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
    "--force",
    "force_overwrite",
    is_flag=True,
    default=False,
    help="Remove existing build and overwrite with new one.",
)
@click.option(
    "--log-level",
    type=click.Choice(choices=LOGGING_LEVELS, case_sensitive=True),
    help="Logging level for runtime.",
    default=INFO,
)
@click.option("--packages-dir",
              type=click.Path(),
              help="Path to packages dir (Use with dev mode)")
@click.option(
    "--open-aea-dir",
    type=click.Path(),
    help="Path to open-aea repo (Use with dev mode)",
)
@click.option(
    "--open-autonomy-dir",
    type=click.Path(),
    help="Path to open-autonomy repo (Use with dev mode)",
)
@click.option(
    "--aev",
    is_flag=True,
    default=False,
    help="Apply environment variable when loading service config.",
)
@click.option(
    "--use-hardhat",
    is_flag=True,
    default=False,
    help="Include a hardhat node in the deployment setup.",
)
@click.option(
    "--use-acn",
    is_flag=True,
    default=False,
    help="Include an ACN node in the deployment setup.",
)
@click.option(
    "-ltm",
    "--local-tm-setup",
    "use_tm_testnet_setup",
    is_flag=True,
    default=False,
    help="Use local tendermint chain setup.",
)
@click.option("--image-version",
              type=str,
              help="Define runtime image version.")
@registry_flag()
@password_option(confirmation_prompt=True)
@image_author_option
@click.pass_context
def build_deployment_command(click_context: click.Context,
                             keys_file: Optional[Path],
                             deployment_type: str,
                             output_dir: Optional[Path],
                             dev_mode: bool,
                             force_overwrite: bool,
                             registry: str,
                             number_of_agents: Optional[int] = None,
                             password: Optional[str] = None,
                             open_aea_dir: Optional[Path] = None,
                             packages_dir: Optional[Path] = None,
                             open_autonomy_dir: Optional[Path] = None,
                             log_level: str = INFO,
                             aev: bool = False,
                             image_version: Optional[str] = None,
                             use_hardhat: bool = False,
                             use_acn: bool = False,
                             use_tm_testnet_setup: bool = False,
                             image_author: Optional[str] = None) -> None
```

Build deployment setup for n agents.

<a id="autonomy.cli.deploy.run"></a>

#### run

```python
@deploy_group.command(name="run")
@click.option(
    "--build-dir",
    type=click.Path(),
)
@click.option(
    "--no-recreate",
    is_flag=True,
    default=False,
    help="If containers already exist, don't recreate them.",
)
@click.option(
    "--remove-orphans",
    is_flag=True,
    default=False,
    help="Remove containers for services not defined in the Compose file.",
)
def run(build_dir: Path, no_recreate: bool, remove_orphans: bool) -> None
```

Run deployment.

<a id="autonomy.cli.deploy.run_deployment_from_token"></a>

#### run`_`deployment`_`from`_`token

```python
@deploy_group.command(name="from-token")
@click.argument("token_id", type=int)
@click.argument("keys_file", type=click.Path())
@click.option("--n",
              type=int,
              help="Number of agents to include in the build.")
@click.option("--skip-image",
              is_flag=True,
              default=False,
              help="Skip building images.")
@click.option(
    "--aev",
    is_flag=True,
    default=False,
    help="Apply environment variable when loading service config.",
)
@chain_selection_flag(
    help_string_format="Use {} chain to resolve the token id.")
@click.pass_context
@password_option(confirmation_prompt=True)
def run_deployment_from_token(click_context: click.Context,
                              token_id: int,
                              keys_file: Path,
                              chain_type: ChainType,
                              skip_image: bool,
                              n: Optional[int],
                              aev: bool = False,
                              password: Optional[str] = None) -> None
```

Run service deployment.

