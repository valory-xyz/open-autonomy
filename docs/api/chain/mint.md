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

<a id="autonomy.chain.mint.mint_component"></a>

#### mint`_`component

```python
def mint_component(ledger_api: LedgerApi,
                   crypto: Crypto,
                   metadata_hash: str,
                   component_type: UnitType,
                   chain_type: ChainType,
                   owner: Optional[str] = None,
                   dependencies: Optional[List[int]] = None) -> Optional[int]
```

Publish component on-chain.

<a id="autonomy.chain.mint.update_component"></a>

#### update`_`component

```python
def update_component(ledger_api: LedgerApi, crypto: Crypto, unit_id: int,
                     metadata_hash: str, component_type: UnitType,
                     chain_type: ChainType) -> Optional[int]
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
                 token: Optional[str] = None,
                 owner: Optional[str] = None) -> Optional[int]
```

Publish component on-chain.

<a id="autonomy.chain.mint.update_service"></a>

#### update`_`service

```python
def update_service(ledger_api: LedgerApi, crypto: Crypto, service_id: int,
                   metadata_hash: str, chain_type: ChainType,
                   agent_ids: List[int], number_of_slots_per_agent: List[int],
                   cost_of_bond_per_agent: List[int],
                   threshold: int) -> Optional[int]
```

Publish component on-chain.

