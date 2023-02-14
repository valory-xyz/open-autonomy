<a id="autonomy.cli.mint"></a>

# autonomy.cli.mint

Mint command group definitions.

<a id="autonomy.cli.mint.mint"></a>

#### mint

```python
@click.group("mint")
@pass_ctx
@chain_selection_flag()
@timeout_flag
@click.option(
    "--skip-hash-check",
    is_flag=True,
    help="Skip hash check when verifying dependencies on chain",
)
def mint(ctx: Context, chain_type: str, skip_hash_check: bool,
         timeout: float) -> None
```

Mint component on-chain.

<a id="autonomy.cli.mint.protocol"></a>

#### protocol

```python
@mint.command()
@package_path_decorator
@key_path_decorator
@password_decorator
@dependencies_decorator
@nft_decorator
@pass_ctx
def protocol(ctx: Context, package_path: Path, keys: Path,
             password: Optional[str], dependencies: Tuple[str],
             nft: Optional[str]) -> None
```

Mint a protocol component.

<a id="autonomy.cli.mint.contract"></a>

#### contract

```python
@mint.command()
@package_path_decorator
@key_path_decorator
@password_decorator
@dependencies_decorator
@nft_decorator
@pass_ctx
def contract(ctx: Context, package_path: Path, keys: Path,
             password: Optional[str], dependencies: Tuple[str],
             nft: Optional[str]) -> None
```

Mint a contract component.

<a id="autonomy.cli.mint.connection"></a>

#### connection

```python
@mint.command()
@package_path_decorator
@key_path_decorator
@password_decorator
@dependencies_decorator
@nft_decorator
@pass_ctx
def connection(ctx: Context, package_path: Path, keys: Path,
               password: Optional[str], dependencies: Tuple[str],
               nft: Optional[str]) -> None
```

Mint a connection component.

<a id="autonomy.cli.mint.skill"></a>

#### skill

```python
@mint.command()
@package_path_decorator
@key_path_decorator
@password_decorator
@dependencies_decorator
@nft_decorator
@pass_ctx
def skill(ctx: Context, package_path: Path, keys: Path,
          password: Optional[str], dependencies: Tuple[str],
          nft: Optional[str]) -> None
```

Mint a skill component.

<a id="autonomy.cli.mint.agent"></a>

#### agent

```python
@mint.command()
@package_path_decorator
@key_path_decorator
@password_decorator
@dependencies_decorator
@nft_decorator
@pass_ctx
def agent(ctx: Context, package_path: Path, keys: Path,
          password: Optional[str], dependencies: Tuple[str],
          nft: Optional[str]) -> None
```

Mint an agent.

<a id="autonomy.cli.mint.service"></a>

#### service

```python
@mint.command()
@package_path_decorator
@key_path_decorator
@password_decorator
@nft_decorator
@pass_ctx
@click.option(
    "-a",
    "--agent-id",
    type=int,
    help="Canonical agent ID",
    required=True,
)
@click.option(
    "-n",
    "--number-of-slots",
    type=int,
    help="Number of agent instances for the agent",
    required=True,
)
@click.option(
    "-c",
    "--cost-of-bond",
    type=int,
    help="Cost of bond for the agent (Wei)",
    required=True,
)
@click.option(
    "--threshold",
    type=int,
    required=True,
    help="Threshold for the minimum numbers required to run the service",
)
def service(ctx: Context, package_path: Path, keys: Path, agent_id: int,
            number_of_slots: int, cost_of_bond: int, threshold: int,
            password: Optional[str], nft: Optional[str]) -> None
```

Mint a service

