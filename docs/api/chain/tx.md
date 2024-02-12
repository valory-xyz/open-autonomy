<a id="autonomy.chain.tx"></a>

# autonomy.chain.tx

Tx settlement helper.

<a id="autonomy.chain.tx.should_rebuild"></a>

#### should`_`rebuild

```python
def should_rebuild(error: str) -> bool
```

Check if we should rebuild the transaction.

<a id="autonomy.chain.tx.should_retry"></a>

#### should`_`retry

```python
def should_retry(error: str) -> bool
```

Check an error message to check if we should raise an error or retry the tx

<a id="autonomy.chain.tx.should_reprice"></a>

#### should`_`reprice

```python
def should_reprice(error: str) -> bool
```

Check an error message to check if we should reprice the transaction

<a id="autonomy.chain.tx.TxSettler"></a>

## TxSettler Objects

```python
class TxSettler()
```

Tx settlement helper

<a id="autonomy.chain.tx.TxSettler.__init__"></a>

#### `__`init`__`

```python
def __init__(ledger_api: LedgerApi,
             crypto: Crypto,
             chain_type: ChainType,
             timeout: Optional[float] = None,
             retries: Optional[int] = None,
             sleep: Optional[float] = None) -> None
```

Initialize object.

<a id="autonomy.chain.tx.TxSettler.build"></a>

#### build

```python
def build(method: Callable[[], Dict], contract: str, kwargs: Dict) -> Dict
```

Build transaction.

<a id="autonomy.chain.tx.TxSettler.transact"></a>

#### transact

```python
def transact(method: Callable[[], Dict],
             contract: str,
             kwargs: Dict,
             dry_run: bool = False) -> Dict
```

Make a transaction and return a receipt

<a id="autonomy.chain.tx.TxSettler.process"></a>

#### process

```python
def process(event: str, receipt: Dict, contract: PublicId) -> Dict
```

Process tx receipt.

