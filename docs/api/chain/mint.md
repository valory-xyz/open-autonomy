<a id="autonomy.chain.mint"></a>

# autonomy.chain.mint

Helpers for minting components

<a id="autonomy.chain.mint.transact"></a>

#### transact

```python
def transact(ledger_api: LedgerApi,
             crypto: Crypto,
             tx: Dict,
             max_retries: int = 5,
             sleep: float = 5.0,
             timeout: Optional[float] = None) -> Dict
```

Make a transaction and return a receipt

<a id="autonomy.chain.mint.sort_service_dependency_metadata"></a>

#### sort`_`service`_`dependency`_`metadata

```python
def sort_service_dependency_metadata(
        agent_ids: List[int], number_of_slots_per_agents: List[int],
        cost_of_bond_per_agent: List[int]) -> Tuple[List[int], ...]
```

Sort service dependencies and their respective parameters

<a id="autonomy.chain.mint.get_min_threshold"></a>

#### get`_`min`_`threshold

```python
def get_min_threshold(n: int) -> int
```

Calculate minimum threshold required for N number of agents.

<a id="autonomy.chain.mint.MintManager"></a>

## MintManager Objects

```python
class MintManager()
```

Mint helper.

<a id="autonomy.chain.mint.MintManager.__init__"></a>

#### `__`init`__`

```python
def __init__(ledger_api: LedgerApi,
             crypto: Crypto,
             chain_type: ChainType,
             dry_run: bool = False,
             timeout: Optional[float] = None,
             retries: Optional[int] = None,
             sleep: Optional[float] = None) -> None
```

Initialize object.

<a id="autonomy.chain.mint.MintManager.validate_address"></a>

#### validate`_`address

```python
def validate_address(address: str) -> str
```

Validate address string.

<a id="autonomy.chain.mint.MintManager.mint_component"></a>

#### mint`_`component

```python
def mint_component(metadata_hash: str,
                   component_type: UnitType,
                   owner: Optional[str] = None,
                   dependencies: Optional[List[int]] = None) -> Optional[int]
```

Publish component on-chain.

<a id="autonomy.chain.mint.MintManager.update_component"></a>

#### update`_`component

```python
def update_component(metadata_hash: str, unit_id: int,
                     component_type: UnitType) -> Optional[int]
```

Update component on-chain.

<a id="autonomy.chain.mint.MintManager.mint_service"></a>

#### mint`_`service

```python
def mint_service(metadata_hash: str,
                 agent_ids: List[int],
                 number_of_slots_per_agent: List[int],
                 cost_of_bond_per_agent: List[int],
                 threshold: Optional[int] = None,
                 token: Optional[str] = None,
                 owner: Optional[str] = None) -> Optional[int]
```

Publish component on-chain.

<a id="autonomy.chain.mint.MintManager.update_service"></a>

#### update`_`service

```python
def update_service(metadata_hash: str,
                   service_id: int,
                   agent_ids: List[int],
                   number_of_slots_per_agent: List[int],
                   cost_of_bond_per_agent: List[int],
                   threshold: Optional[int] = None,
                   token: Optional[str] = None) -> Optional[int]
```

Publish component on-chain.

