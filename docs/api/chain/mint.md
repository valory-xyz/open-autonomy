<a id="autonomy.chain.mint"></a>

# autonomy.chain.mint

Helpers for minting components

<a id="autonomy.chain.mint.transact"></a>

#### transact

```python
def transact(ledger_api: LedgerApi, crypto: Crypto, tx: Dict) -> Dict
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

<a id="autonomy.chain.mint.wait_for_component_to_mint"></a>

#### wait`_`for`_`component`_`to`_`mint

```python
def wait_for_component_to_mint(token_retriever: Callable[[], Optional[int]],
                               timeout: Optional[float] = None,
                               sleep: float = 1.0) -> int
```

Wait for service activation.

<a id="autonomy.chain.mint.mint_component"></a>

#### mint`_`component

```python
def mint_component(ledger_api: LedgerApi,
                   crypto: Crypto,
                   metadata_hash: str,
                   component_type: UnitType,
                   chain_type: ChainType,
                   dependencies: Optional[List[int]] = None,
                   timeout: Optional[float] = None) -> Optional[int]
```

Publish component on-chain.

<a id="autonomy.chain.mint.mint_service"></a>

#### mint`_`service

```python
def mint_service(ledger_api: LedgerApi,
                 crypto: Crypto,
                 metadata_hash: str,
                 chain_type: ChainType,
                 agent_ids: List[int],
                 number_of_slots_per_agent: List[int],
                 cost_of_bond_per_agent: List[int],
                 threshold: int,
                 timeout: Optional[float] = None) -> Optional[int]
```

Publish component on-chain.

