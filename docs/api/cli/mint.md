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

