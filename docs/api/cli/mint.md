<a id="autonomy.cli.mint"></a>

# autonomy.cli.mint

Mint command group definitions.

<a id="autonomy.cli.mint.mint"></a>

#### mint

```python
@click.group("mint")
@pass_ctx
@chain_selection_flag_()
def mint(ctx: Context, chain_type: str) -> None
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
def protocol(ctx: Context, package_path: Path, keys: Path, password: Optional[str], dependencies: Tuple[str], nft: Optional[str]) -> None
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
def contract(ctx: Context, package_path: Path, keys: Path, password: Optional[str], dependencies: Tuple[str], nft: Optional[str]) -> None
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
def connection(ctx: Context, package_path: Path, keys: Path, password: Optional[str], dependencies: Tuple[str], nft: Optional[str]) -> None
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
def skill(ctx: Context, package_path: Path, keys: Path, password: Optional[str], dependencies: Tuple[str], nft: Optional[str]) -> None
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
def agent(ctx: Context, package_path: Path, keys: Path, password: Optional[str], dependencies: Tuple[str], nft: Optional[str]) -> None
```

Mint an agent component.

