<a id="autonomy.cli.helpers.chain"></a>

# autonomy.cli.helpers.chain

On-chain interaction helpers.

<a id="autonomy.cli.helpers.chain.mint_component"></a>

#### mint`_`component

```python
def mint_component(package_path: Path, package_type: PackageType, keys: Path, chain_type: ChainType, dependencies: List[int], nft_image_hash: Optional[str] = None, password: Optional[str] = None, skip_hash_check: bool = False) -> None
```

Mint component.

<a id="autonomy.cli.helpers.chain.mint_service"></a>

#### mint`_`service

```python
def mint_service(package_path: Path, keys: Path, chain_type: ChainType, agent_id: int, number_of_slots: int, cost_of_bond: int, threshold: int, nft_image_hash: Optional[str] = None, password: Optional[str] = None, skip_hash_check: bool = False) -> None
```

Mint service component

