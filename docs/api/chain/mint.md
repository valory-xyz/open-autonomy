<a id="autonomy.chain.mint"></a>

# autonomy.chain.mint

Helpers for minting components

<a id="autonomy.chain.mint.transact"></a>

#### transact

```python
def transact(ledger_api: LedgerApi, crypto: Crypto, tx: Dict) -> Dict
```

Make a transaction and return a receipt

<a id="autonomy.chain.mint.mint_component"></a>

#### mint`_`component

```python
def mint_component(ledger_api: LedgerApi, crypto: Crypto, metadata_hash: str, component_type: UnitType, chain_type: ChainType, dependencies: Optional[List[int]] = None) -> Optional[int]
```

Publish component on-chain.

<a id="autonomy.chain.mint.verify_and_fetch_token_id_from_event"></a>

#### verify`_`and`_`fetch`_`token`_`id`_`from`_`event

```python
def verify_and_fetch_token_id_from_event(ledger_api: LedgerApi, events: List[Dict], metadata_hash: str, unit_type: UnitType) -> Optional[int]
```

Verify and extract token id from a registry event

